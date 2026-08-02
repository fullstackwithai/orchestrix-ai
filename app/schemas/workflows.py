from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator


NodeType = Literal[
    "trigger",
    "action",
    "condition",
    "ai_agent",
    "human_approval",
    "delay",
    "webhook",
    "end",
]


class Position(BaseModel):
    x: float = 0
    y: float = 0


class WorkflowNode(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    type: NodeType
    label: str = Field(min_length=1, max_length=160)
    config: dict[str, Any] = Field(default_factory=dict)
    position: Position = Field(default_factory=Position)


class WorkflowEdge(BaseModel):
    source: str
    target: str
    label: str | None = None
    condition: str | None = None


class WorkflowDefinition(BaseModel):
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]

    @model_validator(mode="after")
    def validate_graph(self):
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("Node IDs must be unique.")
        known = set(ids)
        for edge in self.edges:
            if edge.source not in known or edge.target not in known:
                raise ValueError("Every edge must reference existing nodes.")
        if not any(node.type == "trigger" for node in self.nodes):
            raise ValueError("A workflow requires at least one trigger node.")
        if not any(node.type == "end" for node in self.nodes):
            raise ValueError("A workflow requires at least one end node.")
        return self


class WorkflowCreate(BaseModel):
    workspace_id: int = 1
    name: str = Field(min_length=3, max_length=160)
    description: str = ""
    definition: WorkflowDefinition
    change_note: str = "Initial version"


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    definition: WorkflowDefinition
    change_note: str = "Updated workflow"


class RunCreate(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)


class ApprovalDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    actor: str = "Arsim Shefkiu"
    note: str = ""
