import json
from datetime import UTC, datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.models.entities import (
    ApprovalTask,
    AuditEvent,
    Workflow,
    WorkflowRun,
    WorkflowVersion,
    Workspace,
)
from app.schemas.workflows import (
    ApprovalDecision,
    RunCreate,
    WorkflowCreate,
    WorkflowUpdate,
)
from app.services.audit import record_event
from app.services.engine import run_workflow

router = APIRouter(prefix="/api")
settings = get_settings()


def _workflow_payload(db: Session, workflow: Workflow) -> dict:
    version = (
        db.query(WorkflowVersion)
        .filter(
            WorkflowVersion.workflow_id == workflow.id,
            WorkflowVersion.version == workflow.active_version,
        )
        .one()
    )
    return {
        "id": workflow.id,
        "workspace_id": workflow.workspace_id,
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status,
        "active_version": workflow.active_version,
        "created_by": workflow.created_by,
        "definition": json.loads(version.definition_json),
        "updated_at": workflow.updated_at.isoformat(),
    }


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "ai_mode": "openai" if settings.openai_api_key else "offline-demo",
    }


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    total_runs = db.query(WorkflowRun).count()
    completed = db.query(WorkflowRun).filter(WorkflowRun.status == "completed").count()
    return {
        "workflows": db.query(Workflow).count(),
        "runs": total_runs,
        "success_rate": round(completed / total_runs * 100, 1) if total_runs else 0,
        "pending_approvals": db.query(ApprovalTask).filter(ApprovalTask.status == "pending").count(),
        "audit_events": db.query(AuditEvent).count(),
    }


@router.get("/workspaces")
def workspaces(db: Session = Depends(get_db)) -> list[dict]:
    return [{"id": row.id, "name": row.name, "slug": row.slug} for row in db.query(Workspace).all()]


@router.get("/workflows")
def workflows(db: Session = Depends(get_db)) -> list[dict]:
    return [_workflow_payload(db, row) for row in db.query(Workflow).order_by(Workflow.id.desc()).all()]


@router.get("/workflows/{workflow_id}")
def workflow(workflow_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.get(Workflow, workflow_id)
    if row is None:
        raise HTTPException(404, "Workflow not found.")
    return _workflow_payload(db, row)


@router.post("/workflows")
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)) -> dict:
    if len(payload.definition.nodes) > settings.max_workflow_nodes:
        raise HTTPException(400, "Workflow exceeds the node limit.")
    row = Workflow(
        workspace_id=payload.workspace_id,
        name=payload.name,
        description=payload.description,
        active_version=1,
    )
    db.add(row)
    db.flush()
    version = WorkflowVersion(
        workflow_id=row.id,
        version=1,
        definition_json=payload.definition.model_dump_json(),
        change_note=payload.change_note,
    )
    db.add(version)
    record_event(
        db,
        workspace_id=row.workspace_id,
        workflow_id=row.id,
        event_type="workflow.created",
        actor="Arsim Shefkiu",
        evidence={"version": 1, "nodes": len(payload.definition.nodes)},
    )
    db.commit()
    return _workflow_payload(db, row)


@router.put("/workflows/{workflow_id}")
def update_workflow(workflow_id: int, payload: WorkflowUpdate, db: Session = Depends(get_db)) -> dict:
    row = db.get(Workflow, workflow_id)
    if row is None:
        raise HTTPException(404, "Workflow not found.")
    row.name = payload.name or row.name
    row.description = payload.description if payload.description is not None else row.description
    row.status = payload.status or row.status
    row.active_version += 1
    version = WorkflowVersion(
        workflow_id=row.id,
        version=row.active_version,
        definition_json=payload.definition.model_dump_json(),
        change_note=payload.change_note,
    )
    db.add(version)
    record_event(
        db,
        workspace_id=row.workspace_id,
        workflow_id=row.id,
        event_type="workflow.versioned",
        actor="Arsim Shefkiu",
        evidence={"version": row.active_version, "change_note": payload.change_note},
    )
    db.commit()
    return _workflow_payload(db, row)


@router.post("/workflows/{workflow_id}/run")
def run(workflow_id: int, payload: RunCreate, db: Session = Depends(get_db)) -> dict:
    workflow = db.get(Workflow, workflow_id)
    if workflow is None:
        raise HTTPException(404, "Workflow not found.")
    row = WorkflowRun(
        workflow_id=workflow.id,
        version=workflow.active_version,
        input_json=json.dumps(payload.input),
        state_json=json.dumps(payload.input),
    )
    db.add(row)
    db.flush()
    record_event(
        db,
        workspace_id=workflow.workspace_id,
        workflow_id=workflow.id,
        run_id=row.id,
        event_type="run.created",
        actor="api",
        evidence={"version": row.version, "input_keys": sorted(payload.input.keys())},
    )
    db.commit()
    row = run_workflow(db, row)
    return {
        "id": row.id,
        "status": row.status,
        "current_node": row.current_node,
        "state": json.loads(row.state_json),
        "error": row.error,
    }


@router.get("/runs")
def runs(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(WorkflowRun).order_by(WorkflowRun.id.desc()).limit(100).all()
    return [{
        "id": row.id,
        "workflow_id": row.workflow_id,
        "version": row.version,
        "status": row.status,
        "current_node": row.current_node,
        "created_at": row.created_at.isoformat(),
    } for row in rows]


@router.get("/approvals")
def approvals(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(ApprovalTask).order_by(ApprovalTask.id.desc()).all()
    return [{
        "id": row.id,
        "run_id": row.run_id,
        "node_id": row.node_id,
        "title": row.title,
        "instructions": row.instructions,
        "status": row.status,
        "created_at": row.created_at.isoformat(),
    } for row in rows]


@router.post("/approvals/{approval_id}/decision")
def decide(approval_id: int, payload: ApprovalDecision, db: Session = Depends(get_db)) -> dict:
    task = db.get(ApprovalTask, approval_id)
    if task is None:
        raise HTTPException(404, "Approval task not found.")
    if task.status != "pending":
        raise HTTPException(409, "Approval task has already been decided.")
    task.status = payload.decision
    task.decision_by = payload.actor
    task.decision_note = payload.note
    task.decided_at = datetime.now(UTC)
    run = db.get(WorkflowRun, task.run_id)
    workflow = db.get(Workflow, run.workflow_id)
    record_event(
        db,
        workspace_id=workflow.workspace_id,
        workflow_id=workflow.id,
        run_id=run.id,
        event_type=f"approval.{payload.decision}",
        actor=payload.actor,
        evidence={"approval_id": task.id, "note": payload.note},
    )
    db.commit()
    run.current_node = task.node_id
    db.commit()
    run = run_workflow(db, run)
    return {"approval_id": task.id, "decision": task.status, "run_status": run.status}


@router.get("/audit")
def audit(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(AuditEvent).order_by(AuditEvent.id.desc()).limit(200).all()
    return [{
        "id": row.id,
        "event_type": row.event_type,
        "actor": row.actor,
        "workflow_id": row.workflow_id,
        "run_id": row.run_id,
        "evidence": json.loads(row.evidence_json),
        "created_at": row.created_at.isoformat(),
    } for row in rows]
