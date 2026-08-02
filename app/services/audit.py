import json
from sqlalchemy.orm import Session
from app.models.entities import AuditEvent


def record_event(
    db: Session,
    *,
    workspace_id: int,
    event_type: str,
    actor: str = "system",
    workflow_id: int | None = None,
    run_id: int | None = None,
    evidence: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        workspace_id=workspace_id,
        workflow_id=workflow_id,
        run_id=run_id,
        event_type=event_type,
        actor=actor,
        evidence_json=json.dumps(evidence or {}, default=str),
    )
    db.add(event)
    db.flush()
    return event
