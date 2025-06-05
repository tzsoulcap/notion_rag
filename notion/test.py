from notion_rag import NotionRAG
from processor import NotionProcessor
from api import NotionAPI

agent = NotionRAG(
    notion_api_key="ntn_MMA99645691YrxOtSP5mYXG6pDLopUudlxVx9Ub74tY5U1",
    database_ids=[],
    page_ids=["111005f078fb812088c1db2280011c5c"],
    # embedding_model="nomic-embed-text",
    # llm_model="llama3.1:8b",
)

agent.index_notion_content()