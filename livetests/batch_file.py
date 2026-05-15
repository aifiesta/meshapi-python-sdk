from meshapi import (
    UploadBatchFileParams,
    BatchRequestItem,
    CreateBatchParams,
)
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


# 1. Upload the batch input
# file = client.files.upload(
#     UploadBatchFileParams(
#         purpose="batch",
#         requests=[
#             BatchRequestItem(
#                 custom_id="req-1",
#                 body={
#                     "model": "openai/gpt-4.1-mini",
#                     "messages": [{"role": "user", "content": "Say hi."}],
#                 },
#             ),
#             BatchRequestItem(
#                 custom_id="req-2",
#                 body={
#                     "model": "openai/gpt-4.1-mini",
#                     "messages": [{"role": "user", "content": "Say bye."}],
#                 },
#             ),
#         ],
#     )
# )

# 2. Create the batch
# batch = client.batches.create(
#     CreateBatchParams(
#         input_file_id=file.id,
#         endpoint="/v1/chat/completions",
#         completion_window="24h",
#     )
# )

# print("batch id is: ", batch.id)

# 3. Poll later
status = client.batches.get("batch_6a038d038ad481908c22ced67b7001c1")
print("batch status is: ", status)

if status.status == "completed" and status.output_file_id:
    output_bytes = client.files.content(status.output_file_id)
    print(output_bytes)
    # output_bytes is JSONL
