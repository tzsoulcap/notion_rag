"""
Main NotionRAG class that implements the RAG functionality with Notion content.
"""
import os
from typing import List, Dict, Any, Optional

from langchain.schema import Document


from .api import NotionAPI
from .processor import NotionProcessor



class NotionRAG:
    """
    A RAG system that uses Notion as a knowledge base.
    
    This system uses Ollama for both embeddings (vector creation) and LLM generation.
    Make sure you have Ollama running locally with appropriate models installed.
    
    The embedding model is determined by the OLLAMA_EMBEDDING_MODEL environment variable.
    Set this in your .env file to control which embedding model is used.
    Recommended embedding models: nomic-embed-text (default), mxbai-embed-large
    """
    
    def __init__(
        self, 
        notion_api_key: Optional[str] = None,
        database_ids: Optional[List[str]] = None,
        page_ids: Optional[List[str]] = None,
    ):
        """
        Initialize the Notion RAG system.
        
        Args:
            notion_api_key: Notion API key. If not provided, uses NOTION_API_KEY from environment.
            database_ids: List of Notion database IDs to fetch content from.
            page_ids: List of Notion page IDs to fetch content from directly.
            embedding_model: Ollama model to use for embeddings (e.g., "nomic-embed-text").
            llm_model: Ollama model to use for generation (e.g., "llama3:8b").
            persist_directory: Directory to persist the vector database.
            log_dir: Directory to store API logs.
        """
        self.notion_api_key = notion_api_key or os.getenv("NOTION_API_KEY")
        if not self.notion_api_key:
            raise ValueError("Notion API key is required. Set NOTION_API_KEY in .env file.")
        
        self.database_ids = database_ids or []
        self.page_ids = page_ids or []
        
        # Initialize the Notion API
        self.notion_api = NotionAPI(self.notion_api_key)
        

    
    def process_page_to_document(self, page: Dict[str, Any]) -> Document:
        """
        Process a Notion page into a Document object.
        
        Args:
            page: Notion page object.
            
        Returns:
            Document object with the page's content.
        """
        page_id = page.get("id", "")
        page_content = self.notion_api.get_page_content(page_id, set())
        return NotionProcessor.process_page_to_document(page, page_content)
    
    def process_direct_page_to_document(self, page_id: str) -> Document:
        """
        Process a Notion page directly by its ID into a Document object.
        This works with any Notion page, not just those from databases.
        
        Args:
            page_id: The ID of the Notion page.
            
        Returns:
            Document object with the page's content.
        """
        # Get page info
        page_info = self.notion_api.get_page_info(page_id)
        
        # Check if page_info is None or empty
        if not page_info:
            raise ValueError(f"Could not retrieve page info for page ID: {page_id}. Please check if the page ID is correct and you have access to it.")
        
        # Get page content
        page_content = self.notion_api.get_page_content(page_id, set())
        
        return NotionProcessor.process_direct_page_to_document(page_info, page_content)
    
    def index_notion_content(self) -> None:
        """
        Index all content from specified Notion sources (databases and/or pages).
        
        Args:
            chunk_size: Size of text chunks for indexing.
            chunk_overlap: Overlap between chunks.
        """
        
        all_documents = []
        
        # Process database pages
        for database_id in self.database_ids:
            print(f"Fetching pages from database {database_id}...")
            # Fetch all pages from database
            pages = self.notion_api.fetch_database_pages(database_id)
            
            # Process each page into a document
            for page in pages:
                document = self.process_page_to_document(page)
                all_documents.append(document)
                print(f"Processed page: {document.metadata.get('title', 'Untitled')}")
        
        # Process direct pages
        for page_id in self.page_ids:
            print(f"Processing page {page_id}...")
            try:
                document = self.process_direct_page_to_document(page_id)
                all_documents.append(document)
                print(f"Processed page: {document.metadata.get('title', 'Untitled')}")
            except Exception as e:
                print(f"Error processing page {page_id}: {str(e)}")
        
        if not all_documents:
            print("No documents found to index. Please provide valid database_ids or page_ids.")
            return
        else:
            print(f"========== Document processed successfully")
    
            # Save the processed document content to a file
            # with open(f"document_{page_id}.txt", "w", encoding="utf-8") as f:
            #     f.writelines(list(map(lambda x: x.page_content, all_documents)))
            
            # print(f"========== Document content saved to document_{page_id}.txt")
        return list(map(lambda x: x.page_content, all_documents))