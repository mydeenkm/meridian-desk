import random
import sys
import time
from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError
from config import FALLBACK_PRICING_PER_1M



def estimate_cost(usage, model: str) -> float:
    if usage is None:
        return 0.0
    raw_cost = getattr(usage, "cost", None)
    if raw_cost is not None:
        return float(raw_cost)
    if model.endswith(":free"):
        return 0.0

    in_rate, out_rate = FALLBACK_PRICING_PER_1M.get(model, (0.0, 0.0))
    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
    completion_tokens = getattr(usage, "completion_tokens", 0) or 0
    return (prompt_tokens / 1_000_000) * in_rate + (completion_tokens / 1_000_000) * out_rate


def ask_desk(
    client: OpenAI,
    model: str,
    messages: list[dict],
    question: str,
    temperature: float | None = 0.1,
) -> dict:
    max_attempts = 3
    base_delay = 1.0
    messages.append({"role": "user", "content": question})

    for attempt in range(1, max_attempts + 1):
        start_time = time.perf_counter()
        chunks_received = []
        usage = None
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                timeout=30.0,
                stream=True,
                stream_options={"include_usage": True},
            )
            print("\nDesk: ", end="", flush=True)
            for chunk in stream:
                if getattr(chunk, "usage", None) is not None:
                    usage = chunk.usage
                if chunk.choices:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        print(delta, end="", flush=True)
                        chunks_received.append(delta)
            print()

            reply = "".join(chunks_received)
            return {
                "reply": reply,
                "input_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                "output_tokens": getattr(usage, "completion_tokens", 0) or 0,
                "latency": time.perf_counter() - start_time,
                "cost": estimate_cost(usage, model),
            }

        except (RateLimitError, APITimeoutError, APIConnectionError) as exc:
            if attempt == max_attempts:
                messages.pop()
                raise RuntimeError(f"Request failed after {max_attempts} attempts: {exc}") from exc

            sleep_time = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.25)
            print(
                f"[Retry {attempt}/{max_attempts - 1}] {type(exc).__name__} — waiting {sleep_time:.2f}s...",
                file=sys.stderr,
            )
            time.sleep(sleep_time)
        except Exception:
            messages.pop()
            raise