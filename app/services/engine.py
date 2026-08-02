import json
from datetime import UTC, datetime
from sqlalchemy.orm import Session
from app.models.entities import ApprovalTask, Workflow, WorkflowRun, WorkflowVersion
from app.services.ai import execute_ai_node
from app.services.audit import record_event


def _definition(db: Session, workflow: Workflow, version: int) -> dict:
    row = (
        db.query(WorkflowVersion)
        .filter(
            WorkflowVersion.workflow_id == workflow.id,
            WorkflowVersion.version == version,
        )
        .one()
    )
    return json.loads(row.definition_json)


def _next_edges(definition: dict, node_id: str) -> list[dict]:
    return [edge for edge in definition["edges"] if edge["source"] == node_id]


def _condition_matches(expression: str | None, state: dict) -> bool:
    if not expression:
        return True
    if "==" in expression:
        key, expected = [part.strip() for part in expression.split("==", 1)]
        expected = expected.strip("'\"")
        return str(state.get(key)) == expected
    if ">=" in expression:
        key, expected = [part.strip() for part in expression.split(">=", 1)]
        return float(state.get(key, 0)) >= float(expected)
    if "<" in expression:
        key, expected = [part.strip() for part in expression.split("<", 1)]
        return float(state.get(key, 0)) < float(expected)
    return False


def run_workflow(db: Session, run: WorkflowRun) -> WorkflowRun:
    workflow = db.get(Workflow, run.workflow_id)
    if workflow is None:
        raise ValueError("Workflow not found.")

    definition = _definition(db, workflow, run.version)
    nodes = {node["id"]: node for node in definition["nodes"]}
    state = json.loads(run.state_json or run.input_json or "{}")
    run.started_at = run.started_at or datetime.now(UTC)
    run.status = "running"

    if run.current_node:
        current_id = run.current_node
    else:
        trigger = next(node for node in definition["nodes"] if node["type"] == "trigger")
        current_id = trigger["id"]

    steps = 0
    while current_id and steps < 200:
        steps += 1
        node = nodes[current_id]
        run.current_node = current_id
        config = node.get("config", {})
        node_type = node["type"]

        record_event(
            db,
            workspace_id=workflow.workspace_id,
            workflow_id=workflow.id,
            run_id=run.id,
            event_type="node.started",
            evidence={"node_id": current_id, "type": node_type, "label": node["label"]},
        )

        if node_type == "trigger":
            state["triggered"] = True

        elif node_type in {"action", "webhook"}:
            key = config.get("output_key", current_id)
            state[key] = config.get("value", f"Executed {node['label']}")

        elif node_type == "ai_agent":
            prompt = config.get("prompt", "Analyze workflow state: {input}")
            result = execute_ai_node(prompt, state, config)
            state[config.get("output_key", "ai_result")] = result["output"]
            state["ai_mode"] = result["mode"]

        elif node_type == "condition":
            pass

        elif node_type == "delay":
            state[f"delay_{current_id}"] = config.get("seconds", 0)

        elif node_type == "human_approval":
            prior = (
                db.query(ApprovalTask)
                .filter(ApprovalTask.run_id == run.id, ApprovalTask.node_id == current_id)
                .order_by(ApprovalTask.id.desc())
                .first()
            )
            if prior is None:
                task = ApprovalTask(
                    run_id=run.id,
                    node_id=current_id,
                    title=config.get("title", node["label"]),
                    instructions=config.get("instructions", "Review the workflow evidence."),
                )
                db.add(task)
                run.status = "waiting_approval"
                run.state_json = json.dumps(state, default=str)
                db.commit()
                return run
            if prior.status == "pending":
                run.status = "waiting_approval"
                run.state_json = json.dumps(state, default=str)
                db.commit()
                return run
            state["approval_decision"] = prior.status
            state["approval_note"] = prior.decision_note or ""

        elif node_type == "end":
            run.status = "completed"
            run.completed_at = datetime.now(UTC)
            run.current_node = current_id
            run.state_json = json.dumps(state, default=str)
            record_event(
                db,
                workspace_id=workflow.workspace_id,
                workflow_id=workflow.id,
                run_id=run.id,
                event_type="run.completed",
                evidence={"steps": steps, "state_keys": sorted(state.keys())},
            )
            db.commit()
            return run

        record_event(
            db,
            workspace_id=workflow.workspace_id,
            workflow_id=workflow.id,
            run_id=run.id,
            event_type="node.completed",
            evidence={"node_id": current_id, "state_keys": sorted(state.keys())},
        )

        outgoing = _next_edges(definition, current_id)
        if node_type == "condition" or node_type == "human_approval":
            chosen = next(
                (edge for edge in outgoing if _condition_matches(edge.get("condition"), state)),
                None,
            )
        else:
            chosen = outgoing[0] if outgoing else None
        current_id = chosen["target"] if chosen else None

    run.status = "failed"
    run.error = "Execution exceeded the step limit or reached a dead end."
    run.state_json = json.dumps(state, default=str)
    db.commit()
    return run
