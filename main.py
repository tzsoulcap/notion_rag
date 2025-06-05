from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import sys

# Add the notion directory to the path so we can import the NotionRAG class
from notion.notion_rag import NotionRAG

# Create FastAPI instance
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Pydantic model for the request body
class NotionContentRequest(BaseModel):
    notion_api_key: Optional[str] = None
    database_ids: Optional[List[str]] = None
    page_ids: Optional[List[str]] = None

@app.get("/")
async def root():
    return "hello world"

@app.post("/notion_content")
async def process_notion_content(request: NotionContentRequest):
    """
    Process Notion content and return the indexed text.
    
    Args:
        request: NotionContentRequest containing notion_api_key, database_ids, and page_ids
        
    Returns:
        dict: {"text": "combined content from all processed documents"}
    """
    try:
        # Initialize NotionRAG with the provided parameters
        notion_rag = NotionRAG(
            notion_api_key=request.notion_api_key,
            database_ids=request.database_ids or [],
            page_ids=request.page_ids or []
        )
        
        # Index the notion content and get the results
        content_list = notion_rag.index_notion_content()
        
        # Combine all content into a single string
        if content_list:
            combined_text = "\n\n".join(content_list)
        else:
            combined_text = "No content found or processed."
        
        return {"text": combined_text}
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 