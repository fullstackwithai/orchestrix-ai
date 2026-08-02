from typing import Any, TypedDict

try:
    from langgraph.graph import StateGraph, START, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


class AgentState(TypedDict, total=False):
    prompt: str
    context: dict[str, Any]
    output: str
    reviewer_note: str
    mode: str
    orchestrator: str


def _plan(state: AgentState) -> AgentState:
    keys = ", ".join(sorted(state.get("context", {}).keys())) or "none"
    return {**state, "prompt": f"{state['prompt']}\nAvailable context keys: {keys}"}


def _execute(state: AgentState, executor) -> AgentState:
    result = executor(state["prompt"], state.get("context", {}))
    return {**state, "output": result["output"], "mode": result["mode"]}


def _review(state: AgentState) -> AgentState:
    output = state.get("output", "")
    note = (
        "Review passed: output exists and should remain behind human approval."
        if output.strip()
        else "Review failed: no output was produced."
    )
    return {**state, "reviewer_note": note}


def run_governed_agent(prompt: str, context: dict[str, Any], executor) -> dict[str, Any]:
    if not LANGGRAPH_AVAILABLE:
        state: AgentState = {"prompt": prompt, "context": context}
        state = _plan(state)
        state = _execute(state, executor)
        state = _review(state)
        state["orchestrator"] = "orchestrix-compatible-fallback"
        return state

    graph = StateGraph(AgentState)
    graph.add_node("planner", _plan)
    graph.add_node("executor", lambda state: _execute(state, executor))
    graph.add_node("reviewer", _review)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "reviewer")
    graph.add_edge("reviewer", END)
    result = graph.compile().invoke({"prompt": prompt, "context": context})
    result["orchestrator"] = "langgraph"
    return result
