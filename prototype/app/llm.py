"""AI model adapters. Swap models with LLM_PROVIDER in .env, without changing any other code."""
import json
import re

from . import config


class AnthropicLLM:
    def __init__(self, model: str = config.ANTHROPIC_MODEL):
        import anthropic  # imported here so offline mode works without the package
        self.client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
        self.model = model
        self.usage = {"input_tokens": 0, "output_tokens": 0, "calls": 0}

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        self.usage["calls"] += 1
        self.usage["input_tokens"] += response.usage.input_tokens
        self.usage["output_tokens"] += response.usage.output_tokens
        # The model may return thinking blocks first; keep only the text.
        return "".join(block.text for block in response.content if block.type == "text")


def parse_json(text: str) -> dict:
    """Pulls the first JSON object out of a model reply."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in model reply: {text[:200]}")
    return json.loads(match.group(0))


def get_llm():
    if config.LLM_PROVIDER == "fake":
        from .fake_llm import FakeLLM
        return FakeLLM()
    return AnthropicLLM()
