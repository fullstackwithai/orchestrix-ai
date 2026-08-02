import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.core.database import Base, SessionLocal, engine
from app.models.entities import Workflow, WorkflowVersion, Workspace

app = FastAPI(
    title="Orchestrix AI",
    version="1.0.0",
    description="Enterprise workflow automation and governed AI-agent orchestration platform.",
)
Base.metadata.create_all(bind=engine)


def seed() -> None:
    db = SessionLocal()
    try:
        workspace = db.query(Workspace).filter(Workspace.slug == "designhubmk").first()
        if workspace is None:
            workspace = Workspace(name="DesignHubMK Automation Lab", slug="designhubmk")
            db.add(workspace)
            db.flush()

        if db.query(Workflow).count() == 0:
            definition = {
                "nodes": [
                    {"id": "lead", "type": "trigger", "label": "Lead Webhook", "config": {}, "position": {"x": 60, "y": 160}},
                    {"id": "validate", "type": "action", "label": "Validate Lead", "config": {"output_key": "validated", "value": True}, "position": {"x": 270, "y": 160}},
                    {"id": "score", "type": "ai_agent", "label": "AI Qualification", "config": {"prompt": "Qualify lead {company} with budget {budget}", "output_key": "qualification"}, "position": {"x": 480, "y": 160}},
                    {"id": "approve", "type": "human_approval", "label": "Manager Approval", "config": {"title": "Approve AI Sales Proposal", "instructions": "Review qualification evidence before external delivery."}, "position": {"x": 690, "y": 160}},
                    {"id": "send", "type": "action", "label": "Send Proposal", "config": {"output_key": "proposal_sent", "value": True}, "position": {"x": 900, "y": 110}},
                    {"id": "reject", "type": "action", "label": "Record Rejection", "config": {"output_key": "proposal_rejected", "value": True}, "position": {"x": 900, "y": 240}},
                    {"id": "done", "type": "end", "label": "Complete", "config": {}, "position": {"x": 1110, "y": 160}},
                ],
                "edges": [
                    {"source": "lead", "target": "validate"},
                    {"source": "validate", "target": "score"},
                    {"source": "score", "target": "approve"},
                    {"source": "approve", "target": "send", "condition": "approval_decision == approved", "label": "approved"},
                    {"source": "approve", "target": "reject", "condition": "approval_decision == rejected", "label": "rejected"},
                    {"source": "send", "target": "done"},
                    {"source": "reject", "target": "done"},
                ],
            }
            workflow = Workflow(
                workspace_id=workspace.id,
                name="AI Sales Proposal Automation",
                description="Webhook to validation, AI qualification, human approval, proposal delivery, and audit evidence.",
                status="active",
                active_version=1,
            )
            db.add(workflow)
            db.flush()
            db.add(WorkflowVersion(
                workflow_id=workflow.id,
                version=1,
                definition_json=json.dumps(definition),
                change_note="Seeded signature workflow",
            ))
            db.commit()
    finally:
        db.close()


seed()
app.include_router(router)
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def home():
    return FileResponse(static_dir / "index.html")
