# import os
# import asyncio
# from src.api.chat import send_chat_message, ChatMessageRequest

# # Set environment variables
# os.environ['QDRANT_URL'] = 'http://localhost:6333'
# os.environ['GEMINI_API_KEY'] = 'test-key'

# async def test_chat_flow():
#     print("Testing the exact flow that's failing...")

#     # Create a request like the one that fails
#     request = ChatMessageRequest(content="Hello", context_window=1)

#     try:
#         # This is the exact call that's failing
#         result = await send_chat_message("test_session_123", request)
#         print("SUCCESS: Chat message processed without 500 error!")
#         print(f"Result: {result}")
#     except Exception as e:
#         error_str = str(e)
#         print(f"ERROR: {type(e).__name__}: {error_str}")
#         if "dimension" in error_str.lower() or "dim:" in error_str or "1024" in error_str or "384" in error_str:
#             print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
#             print("THIS IS THE DIMENSION ERROR WE'RE LOOKING FOR!")
#             print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

# if __name__ == "__main__":
#     asyncio.run(test_chat_flow())









from qdrant_client import QdrantClient

def retrieve_context(
    qdrant_client: QdrantClient,
    collection_name: str,
    query_vector: list[float],
    top_k: int = 5
):
    results = qdrant_client.search_points(
        collection_name=collection_name,
        vector=query_vector,
        limit=top_k,
        with_payload=True
    )

    texts = []
    for point in results:
        payload = point.payload or {}
        if "text" in payload:
            texts.append(payload["text"])

    return texts
