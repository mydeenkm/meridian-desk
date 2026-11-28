import json
import time
from openai import OpenAI
from pydantic import ValidationError
from config import EMAIL_PARSER_SYSTEM_PROMPT
from schema import OrderRequest
from dotenv import load_dotenv


def parser_agent(
    client: OpenAI,
    model: str,
    mail: str,
    temperature: float | None = 0.1,
) -> dict:
    max_attempts = 3
    messages = [
        {"role": "system", "content": EMAIL_PARSER_SYSTEM_PROMPT},
        {"role": "user", "content": f"Extract the structured OrderRequest from this email:\n\n{mail}"},
    ]
    completion_tokens = 0
    prompt_tokens = 0
    provider_cost = 0.0
    last_error = None
    start_time = time.perf_counter()

    # Build a valid OpenAI JSON Schema response_format payload
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "OrderRequest",
            "schema": OrderRequest.model_json_schema(),
        },
    }

    for attempt in range(1, max_attempts + 1):
        raw_reply = ""
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                response_format=response_format,  #
                timeout=30.0,
            )
            if response.usage:
                prompt_tokens += response.usage.prompt_tokens or 0
                completion_tokens += response.usage.completion_tokens or 0
                usage_dict = response.usage.model_dump() if hasattr(response.usage, "model_dump") else {}
                raw_cost = usage_dict.get("cost")
                if raw_cost is not None and float(raw_cost) > 0:
                    provider_cost += float(raw_cost)

            raw_reply = (response.choices[0].message.content or "").strip()
            if raw_reply.startswith("```"):
                lines = raw_reply.splitlines()
                raw_reply = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()

            data = json.loads(raw_reply)
            validated = OrderRequest.model_validate(data)
            print("{} Completed, Output Validated".format(attempt))
            total_tokens = prompt_tokens + completion_tokens
            time_taken = time.perf_counter() - start_time
            return {
                "status": "valid",
                "attempts": attempt,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost_usd": round(provider_cost, 6),
                "latency_sec": round(time_taken, 2),
                "data": validated.model_dump(mode="json"),
            }
        except (json.JSONDecodeError, ValidationError) as err:
            last_error = str(err)
            print("{} Completed, Output not Validated : {}".format(attempt,raw_reply))
            if attempt < max_attempts:
                messages.append({"role": "assistant", "content": raw_reply})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Validation failed with error:\n{last_error}\n\n"
                            "Return ONLY corrected JSON matching the exact OrderRequest schema."
                        ),
                    }
                )
        except Exception as api_err:
            last_error = f"API error: {api_err}"
            break

    total_tokens = prompt_tokens + completion_tokens
    time_taken = time.perf_counter() - start_time
    return {
        "status": "need_review",
        "attempts": attempt,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost_usd": round(provider_cost, 6),
        "latency_sec": round(time_taken, 2),
        "data": raw_reply,
        "error": last_error,
    }
