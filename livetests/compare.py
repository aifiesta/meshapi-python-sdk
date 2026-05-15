from meshapi import CompareParams, ChatMessage
from meshapi import (
    ChatCompletionParams,
    ChatMessage,
    Tool,
    ToolFunction,
    MeshAPI,
    MeshAPIError,
)
from config import BASE_URL, TOKEN

client = MeshAPI(base_url=BASE_URL, token=TOKEN)

stream = client.compare.stream(
    CompareParams(
        models=[
            # "openai/gpt-4o-mini",
            # "anthropic/claude-sonnet-4.5",
            "google/gemini-2.5-flash",
            "openai/gpt-4o",
        ],
        messages=[
            ChatMessage(
                role="user", content="Summarize this paragraph in one sentence: ..."
            )
        ],
        stream=True,
    )
)

for event in stream:
    print(event)
    if event.delta:
        print(event.delta, end="", flush=True)
