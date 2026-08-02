TEMPLATES = [
    {
        "key": "ai-sales-proposal",
        "name": "AI Sales Proposal Automation",
        "category": "Sales",
        "description": "Validate a lead, qualify with AI, require approval, and route delivery.",
        "nodes": ["trigger", "action", "ai_agent", "human_approval", "action", "end"],
    },
    {
        "key": "support-escalation",
        "name": "AI Support Escalation",
        "category": "Customer Support",
        "description": "Classify a support request, retrieve guidance, and escalate high-risk cases.",
        "nodes": ["trigger", "ai_agent", "condition", "human_approval", "action", "end"],
    },
    {
        "key": "security-incident",
        "name": "Security Incident Triage",
        "category": "Security",
        "description": "Analyze an alert, assign severity, require containment approval, and preserve evidence.",
        "nodes": ["webhook", "ai_agent", "condition", "human_approval", "action", "end"],
    },
]


def list_templates() -> list[dict]:
    return TEMPLATES
