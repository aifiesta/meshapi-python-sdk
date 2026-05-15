from meshapi import ResponsesParams
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

reply = client.responses.create(
    ResponsesParams(
        model="openai/o4-mini",
        input="Explain the halting problem in two sentences.",
        reasoning={"effort": "medium"},
        max_output_tokens=512,
    )
)

print(reply.output)
