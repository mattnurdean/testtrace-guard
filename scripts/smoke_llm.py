import logging
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("smoke_llm")

def run_smoke_test() -> int:
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()

    base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:8000/v1")
    api_key: str = os.getenv("LLM_API_KEY", "")
    model: str = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")

    if not api_key:
        logger.error("LLM_API_KEY is empty. Set it in .env before testing.")
        return 1

    logger.info("Connecting to AMD Droplet endpoint: %s", base_url)
    logger.info("Target model: %s", model)

    client = OpenAI(base_url=base_url, api_key=api_key)

    prompt: str = "Acknowledge receipt in under 10 words. Confirm readiness for hardware diagnostic analysis."
    messages = [{"role": "user", "content": prompt}]

    start_time: float = time.perf_counter()
    first_token_time: float | None = None
    chunks: list[str] = []
    token_count: int = 0

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.0,
            max_tokens=64,
            stream=True,
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                content = chunk.choices[0].delta.content
                chunks.append(content)
                token_count += 1

        total_time: float = time.perf_counter() - start_time
        ttft: float = (first_token_time - start_time) if first_token_time is not None else total_time
        generated_text: str = "".join(chunks).strip()
        tokens_per_sec: float = token_count / (total_time - ttft) if (total_time - ttft) > 0.001 else 0.0

        logger.info("=== AMD vLLM SMOKE TEST RESULT ===")
        logger.info("Response Text: %s", generated_text)
        logger.info("TTFT (Time-to-first-token): %.4f s", ttft)
        logger.info("Total Latency: %.4f s", total_time)
        logger.info("Generated Tokens (est): %d", token_count)
        logger.info("Generation Speed: %.2f tokens/s", tokens_per_sec)

        if not generated_text:
            logger.error("Empty response received from endpoint.")
            return 1

        return 0

    except OpenAIError as exc:
        logger.error("OpenAI client error connecting to AMD endpoint: %s", str(exc))
        return 1
    except Exception as exc:
        logger.error("Unexpected error during smoke test: %s", str(exc))
        return 1

if __name__ == "__main__":
    sys.exit(run_smoke_test())