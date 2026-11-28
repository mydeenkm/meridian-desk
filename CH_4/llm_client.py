import random
import sys
import time
from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError
from config import FALLBACK_PRICING_PER_1M, CHUNK_TEMPLATE, USER_PROMPT_TEMPLATE
from ingestion import query_chunks

def build_user_prompt(
    question: str,
    collection_name: str = "policies",
    top_k: int = 4,
    debug: bool = False,
) -> str:
    """Retrieves top-k chunks and constructs the user prompt using config templates."""
    matches = query_chunks(collection_name=collection_name, question=question, top_k=top_k)
    if not matches:
        if debug:
            print("\n[DEBUG] No chunks retrieved.")
        return question

    if debug:
        print("\n[DEBUG] Retrieved Chunks:")
        for idx, m in enumerate(matches, start=1):
            preview = m["text"].replace("\n", " ")[:100]
            print(f"  {idx}. [{m['document_name']}#{m.get('chunk_index', idx)}] score={m['similarity']:.4f} | {preview}...")

    context_blocks = [
        CHUNK_TEMPLATE.format(
            filename=m["document_name"],
            chunk_index=m.get("chunk_index", idx),
            text=m["text"],
        )
        for idx, m in enumerate(matches, start=1)
    ]
    context_str = "\n\n".join(context_blocks)
    return USER_PROMPT_TEMPLATE.format(context=context_str, question=question)

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
    temperature: float | None = 1,
    debug: bool = False,
) -> dict:
    max_attempts = 3
    base_delay = 1.0

    messages.append({
        "role": "user",
        "content": build_user_prompt(question=question, collection_name="policies", debug=debug),
    })

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