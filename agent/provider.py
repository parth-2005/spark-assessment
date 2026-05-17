import os

MODEL_MAP = {
    "gemma_26b":    "gemma-4-26b-a4b-it",
    "gemma_31b":    "gemma-4-31b-it",
    "gemini_flash": "gemini-2.5-flash",
    "ollama":       "gemma4:27b",
}


def get_model_id() -> str:
    provider = os.environ.get("LLM_PROVIDER", "gemma_26b")
    return MODEL_MAP.get(provider, MODEL_MAP["gemma_26b"])
