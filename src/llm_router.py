import os
import time

import requests
from dotenv import load_dotenv

from src.config import LLM_MODEL_POOL
from src.utils.observability import logger, metrics_tracker

load_dotenv()


class LLMFallbackRouter:
    """Groq router with explicit fallback order and per-model observability."""

    def __init__(self, temperature: float = 0.1):
        self.temperature = temperature
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.model_pool = list(LLM_MODEL_POOL)

    def invoke(
        self,
        prompt: str,
        system_prompt: str = "",
        preferred_model: str | None = None,
    ) -> str:
        if not self.groq_api_key:
            raise RuntimeError("No GROQ_API_KEY found in the .env file.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }

        candidate_models = list(self.model_pool)
        if preferred_model and preferred_model in candidate_models:
            candidate_models.remove(preferred_model)
            candidate_models.insert(0, preferred_model)

        last_error = ""

        for big_attempt in range(2):
            for model in candidate_models:
                try:
                    payload = {
                        "model": model,
                        "messages": messages,
                        "temperature": self.temperature,
                    }

                    start_time = time.time()
                    response = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=15,
                    )
                    latency = time.time() - start_time

                    if response.status_code == 200:
                        data = response.json()
                        content = data["choices"][0]["message"]["content"]

                        usage = data.get("usage", {})
                        prompt_tokens = usage.get("prompt_tokens", 0)
                        completion_tokens = usage.get("completion_tokens", 0)

                        call_cost = metrics_tracker.record_call(
                            model=model,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            latency=latency,
                        )

                        logger.info(
                            "LLM call succeeded",
                            extra={
                                "component": "llm_router",
                                "metrics": {
                                    "model": model,
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "latency_ms": round(latency * 1000, 2),
                                    "estimated_cost_usd": round(call_cost, 8),
                                },
                            },
                        )
                        return content

                    if response.status_code == 404:
                        last_error = f"Model unavailable: {model}"
                    elif response.status_code == 429 or "rate_limit" in response.text.lower():
                        last_error = f"Rate limited: {model}"
                    else:
                        last_error = f"HTTP {response.status_code}: {model}"

                    logger.warning(
                        "LLM model attempt failed",
                        extra={
                            "component": "llm_router",
                            "metrics": {
                                "model": model,
                                "status_code": response.status_code,
                                "attempt": big_attempt + 1,
                            },
                        },
                    )

                except requests.exceptions.RequestException as exc:
                    last_error = str(exc)
                    logger.warning(
                        "LLM request failed",
                        extra={
                            "component": "llm_router",
                            "metrics": {
                                "model": model,
                                "attempt": big_attempt + 1,
                            },
                        },
                    )

            if big_attempt == 0:
                logger.info(
                    "All configured LLM models failed; retrying fallback pool",
                    extra={"component": "llm_router"},
                )
                time.sleep(15)

        raise RuntimeError(f"Unable to retrieve a response. Last error: {last_error}")


llm_router = LLMFallbackRouter()
