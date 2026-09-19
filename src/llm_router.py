import os
import requests
import time
from typing import Optional
from dotenv import load_dotenv
from src.utils.observability import logger, metrics_tracker

load_dotenv()

# MODEL POOL: Valid and active models in GroqCloud
MODELS_POOL = [
    "openai/gpt-oss-20b",          # Primary: 1000 t/s, extremely fast, perfect for Q&A
    "openai/gpt-oss-120b",         # Secondary: 500 t/s, brilliant for ranking and writing
    "qwen/qwen3.8-27b",            # Fallback 1
    "openai/gpt-oss-safeguard-20b" # Fallback 2 (Last resort)
]

class LLMFallbackRouter:
    def __init__(self, temperature: float = 0.1):
        self.temperature = temperature
        self.groq_api_key = os.getenv("GROQ_API_KEY")

    def invoke(self, prompt: str, system_prompt: str = "", preferred_model: Optional[str] = None) -> str:
        if not self.groq_api_key:
            raise RuntimeError("No GROQ_API_KEY found in the .env file.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }

        candidate_models = list(MODELS_POOL)
        if preferred_model and preferred_model in candidate_models:
            candidate_models.remove(preferred_model)
            candidate_models.insert(0, preferred_model)

        last_error = ""

        # Attempt up to 2 full loops across all available models
        for big_attempt in range(2):
            for model in candidate_models:
                try:
                    payload = {
                        "model": model,
                        "messages": messages,
                        "temperature": self.temperature
                    }
                    
                    start_time = time.time()
                    response = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=15
                    )
                    latency = time.time() - start_time

                    if response.status_code == 200:
                        data = response.json()
                        content = data['choices'][0]['message']['content']
                        
                        # ESTRAZIONE TOKENS ESATTI DALL'API
                        usage = data.get('usage', {})
                        prompt_tokens = usage.get('prompt_tokens', 0)
                        comp_tokens = usage.get('completion_tokens', 0)
                        
                        # REGISTRAZIONE NEL TRACKER GLOBALE
                        metrics_tracker.record_call(model, prompt_tokens, comp_tokens, latency)
                        
                        logger.debug(f"LLM Call Success: {model} | {prompt_tokens} in / {comp_tokens} out | {round(latency, 2)}s")
                        
                        return content

                    # IF MODEL DOES NOT EXIST (e.g., account restrictions)
                    if response.status_code == 404:
                        logger.warning(f"[Groq 404] Model {model} is not enabled on your account.")
                        last_error = "Model 404"
                        continue

                    # RATE LIMIT HANDLING (429)
                    if response.status_code == 429 or "rate_limit" in response.text.lower():
                        logger.warning(f"[Groq RateLimit] {model} is saturated. Immediate switch to fallback...")
                        last_error = response.text
                        continue 

                    # OTHER HTTP ERRORS
                    else:
                        logger.warning(f"Error {response.status_code} on {model}: {response.text}")
                        last_error = response.text
                        continue

                except requests.exceptions.RequestException as e:
                    logger.warning(f"Timeout or network error with {model}: {e}")
                    last_error = str(e)
                    continue
            
            # If we reach this point, ALL models in the pool failed.
            if big_attempt == 0:
                logger.info("[Wait State] All models saturated. Pausing for 15s before the second attempt...")
                time.sleep(15)

        logger.error("Critical Failure: All Groq models are offline or saturated.", extra={"component": "llm_router"})
        raise RuntimeError(f"Unable to retrieve a response. Last error: {last_error}")

llm_router = LLMFallbackRouter()