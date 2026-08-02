from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ConnectorDefinition:
    key: str
    name: str
    category: str
    status: str
    description: str


CONNECTORS = [
    ConnectorDefinition("webhook", "Webhook", "Triggers", "available", "Receive or send structured HTTP events."),
    ConnectorDefinition("postgresql", "PostgreSQL", "Data", "available", "Read and write governed workflow data."),
    ConnectorDefinition("openai", "OpenAI", "AI", "available", "Run bounded LLM generation through the AI adapter."),
    ConnectorDefinition("gmail", "Gmail", "Communication", "planned", "Send governed email actions."),
    ConnectorDefinition("slack", "Slack", "Communication", "planned", "Publish channel messages and approval alerts."),
    ConnectorDefinition("github", "GitHub", "Engineering", "planned", "Create issues and trigger engineering workflows."),
    ConnectorDefinition("google_sheets", "Google Sheets", "Data", "planned", "Read and append spreadsheet records."),
]


def list_connectors() -> list[dict]:
    return [asdict(connector) for connector in CONNECTORS]
