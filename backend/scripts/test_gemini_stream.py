import asyncio
import sys
from pathlib import Path

# Ensure backend/ is on sys.path when run as a script.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from providers.llm import get_llm_provider
from config import settings


async def main() -> None:
    llm = get_llm_provider()
    prompt = "In one short paragraph, explain why customer support should cite sources."

    print(f"Streaming response from Gemini model: {settings.GEMINI_MODEL}")
    print(
        f"Thinking budget: {settings.GEMINI_THINKING_BUDGET}, "
        f"Max output tokens: {settings.GEMINI_MAX_OUTPUT_TOKENS}\n"
    )
    try:
        async with asyncio.timeout(45):
            async for token in llm.stream(prompt):
                print(token, end="", flush=True)
    except TimeoutError:
        print("\n\nTimed out waiting for Gemini response. Check API key, network, and quota.")
    except RuntimeError as exc:
        print(f"\n\nGemini request failed: {exc}")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
