import json
import logging
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field, ValidationError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("json_smoke")

class SmokePayload(BaseModel):
    iteration_id: int = Field(..., ge=0)
    station_status: str = Field(..., min_length=1)
    diagnostic_code: str = Field(..., min_length=1)
    requires_escalation: bool

def run_json_smoke(iterations: int = 10) -> int:
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

    client = OpenAI(base_url=base_url, api_key=api_key)
    valid_json_count: int = 0
    total_time: float = 0.0

    system_prompt = (
        "You are an industrial diagnostics JSON emitter. Output ONLY raw JSON. "
        "Do not include markdown codeblocks (no ```json). Do not include conversational text."
    )

    logger.info("Beginning %d JSON smoke evaluations against model '%s'...", iterations, model)

    for i in range(iterations):
        user_prompt = (
            f"Generate an anomaly record with schema: "
            f'{{"iteration_id": {i}, "station_status": "ONLINE", "diagnostic_code": "ERR_{i:03d}", "requires_escalation": false}}'
        )

        iter_start = time.perf_counter()
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                max_tokens=150,
            )
            elapsed = time.perf_counter() - iter_start
            total_time += elapsed

            raw_text = response.choices[0].message.content or ""
            cleaned_text = raw_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            parsed = json.loads(cleaned_text)
            validated = SmokePayload.model_validate(parsed)

            if validated.iteration_id == i:
                valid_json_count += 1
                logger.info("Iter [%d/%d] PASS (%.3f s)", i + 1, iterations, elapsed)
            else:
                logger.warning(
                    "Iter [%d/%d] ID mismatch: expected %d, got %d",
                    i + 1,
                    iterations,
                    i,
                    validated.iteration_id,
                )

        except (json.JSONDecodeError, ValidationError) as parse_err:
            logger.warning("Iter [%d/%d] JSON/Schema FAIL: %s", i + 1, iterations, str(parse_err))
        except OpenAIError as api_err:
            logger.error("Iter [%d/%d] API FAIL: %s", i + 1, iterations, str(api_err))

    avg_time = total_time / iterations if iterations > 0 else 0.0
    logger.info("=== JSON SMOKE SUMMARY ===")
    logger.info("Valid schema responses: %d/%d", valid_json_count, iterations)
    logger.info("Average latency per call: %.4f s", avg_time)

    if valid_json_count >= 9:
        logger.info("GATE G0 DoD requirement MET (>= 9/10).")
        return 0
    else:
        logger.error("GATE G0 DoD requirement FAILED (%d/10 < 9/10).", valid_json_count)
        return 1

if __name__ == "__main__":
    sys.exit(run_json_smoke(10))