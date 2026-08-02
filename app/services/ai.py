from app.core.config import get_settings
from app.services.langgraph_adapter import run_governed_agent

settings = get_settings()


def _execute_model(rendered: str, context: dict) -> dict:
    if settings.openai_api_key:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.responses.create(
            model=settings.openai_model,
            input=rendered,
        )
        return {"output": response.output_text, "mode": "openai"}

    return {
        "output": (
            "Orchestrix deterministic AI result: "
            + rendered[:300]
            + " | Recommendation: route through governed approval before external delivery."
        ),
        "mode": "offline-demo",
    }


def execute_ai_node(prompt: str, state: dict, config: dict) -> dict:
    template = config.get("template") or prompt
    rendered = template.format(**{k: str(v) for k, v in state.items()})
    result = run_governed_agent(rendered, state, _execute_model)
    return {
        "output": result["output"],
        "mode": result.get("mode", "offline-demo"),
        "reviewer_note": result["reviewer_note"],
        "orchestrator": result["orchestrator"],
    }
