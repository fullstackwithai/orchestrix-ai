def test_health(client):
    data = client.get("/api/health").json()
    assert data["status"] == "ok"
    assert data["service"] == "Orchestrix AI"


def test_seeded_workflow_is_valid(client):
    rows = client.get("/api/workflows").json()
    assert len(rows) == 1
    workflow = rows[0]
    assert workflow["name"] == "AI Sales Proposal Automation"
    assert any(node["type"] == "human_approval" for node in workflow["definition"]["nodes"])
    assert any(node["type"] == "ai_agent" for node in workflow["definition"]["nodes"])


def test_run_pauses_for_human_approval(client):
    workflow_id = client.get("/api/workflows").json()[0]["id"]
    response = client.post(
        f"/api/workflows/{workflow_id}/run",
        json={"input": {"company": "Northstar Labs", "budget": 18000}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "waiting_approval"
    approvals = client.get("/api/approvals").json()
    assert approvals[0]["status"] == "pending"


def test_approval_resumes_and_completes_run(client):
    pending = [a for a in client.get("/api/approvals").json() if a["status"] == "pending"]
    if not pending:
        workflow_id = client.get("/api/workflows").json()[0]["id"]
        client.post(
            f"/api/workflows/{workflow_id}/run",
            json={"input": {"company": "Northstar Labs", "budget": 18000}},
        )
        pending = [a for a in client.get("/api/approvals").json() if a["status"] == "pending"]
    response = client.post(
        f"/api/approvals/{pending[0]['id']}/decision",
        json={"decision": "approved", "actor": "Arsim Shefkiu", "note": "Verified for delivery."},
    )
    assert response.status_code == 200
    assert response.json()["run_status"] == "completed"


def test_workflow_versioning(client):
    workflow = client.get("/api/workflows").json()[0]
    payload = {
        "name": workflow["name"],
        "description": workflow["description"],
        "status": "active",
        "definition": workflow["definition"],
        "change_note": "Test version increment",
    }
    updated = client.put(f"/api/workflows/{workflow['id']}", json=payload).json()
    assert updated["active_version"] == workflow["active_version"] + 1


def test_audit_contains_governance_events(client):
    events = client.get("/api/audit").json()
    event_types = {e["event_type"] for e in events}
    assert "approval.approved" in event_types
    assert "run.completed" in event_types


def test_connector_registry(client):
    connectors = client.get("/api/connectors").json()
    keys = {item["key"] for item in connectors}
    assert {"webhook", "postgresql", "openai"}.issubset(keys)


def test_workflow_templates(client):
    templates = client.get("/api/templates").json()
    assert len(templates) >= 3
    assert any(item["key"] == "security-incident" for item in templates)


def test_ai_node_uses_governed_graph(client):
    workflow_id = client.get("/api/workflows").json()[0]["id"]
    result = client.post(
        f"/api/workflows/{workflow_id}/run",
        json={"input": {"company": "Graph Labs", "budget": 22000}},
    ).json()
    assert result["state"]["ai_mode"] == "offline-demo"
    assert "qualification" in result["state"]
