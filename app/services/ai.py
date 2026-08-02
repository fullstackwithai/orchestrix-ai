from app.core.config import get_settings

settings = get_settings()


def execute_ai_node(prompt: str, state: dict, config: dict) -> dict:
    template = config.get("template") or prompt
    rendered = template.format(**{k: str(v) for k, v in state.items()})
    if settings.openai_api_key:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.responses.create(
            model=settings.openai_model,
            input=rendered,
        )
        output = response.output_text
        mode = "openai"
    else:
        output = (
            "Orchestrix deterministic AI result: "
            + rendered[:300]
            + " | Recommendation: route through governed approval before external delivery."
        )
        mode = "offline-demo"
    return {"output": output, "mode": mode}
