"""
Notion API connection and content retrieval.
"""
import os
import requests
import json
import logging
from typing import Dict, List, Any, Set
import time
from datetime import datetime


class NotionAPI:
    """
    Class for interacting with the Notion API to fetch pages, databases, and content.
    """
    
    def __init__(self, notion_api_key: str, notion_version: str = "2022-06-28", log_dir: str = "logs"):
        """
        Initialize the Notion API client.
        
        Args:
            notion_api_key: Notion API key.
            notion_version: Notion API version to use.
            log_dir: Directory to store API logs.
        """
        self.headers = {
            "Authorization": f"Bearer {notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": notion_version
        }
        # Track visited blocks to prevent infinite recursion with synced blocks
        self.visited_blocks = set()
        
        # Setup logging
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Configure basic logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("NotionAPI")
    
    def _log_response(self, block_id: str, response_data: dict, is_error: bool = False):
        """
        Log API response to a file.
        
        Args:
            block_id: The block ID of the request.
            response_data: The response data from the API.
            is_error: Whether this is an error response.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        status = "error" if is_error else "success"
        log_filename = f"{self.log_dir}/notion_api_{status}_{block_id}_{timestamp}.json"
        
        # Create a log entry with metadata
        log_entry = {
            "timestamp": timestamp,
            "block_id": block_id,
            "status": status,
            "response": response_data
        }
        
        # try:
            # with open(log_filename, "w", encoding="utf-8") as f:
            #     json.dump(log_entry, f, indent=2, ensure_ascii=False)
        #     self.logger.info(f"API response logged to {log_filename}")
        # except Exception as e:
        #     self.logger.error(f"Failed to log API response: {str(e)}")
    
    def fetch_database_pages(self, database_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all pages from a Notion database.
        
        Args:
            database_id: The ID of the Notion database.
            
        Returns:
            List of page objects from the database.
        """
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        
        pages = []
        has_more = True
        next_cursor = None
        
        while has_more:
            body = {}
            if next_cursor:
                body["start_cursor"] = next_cursor
                
            response = requests.post(url, headers=self.headers, json=body)
            data = response.json()
            
            if response.status_code != 200:
                self._log_response(database_id, data, is_error=True)
                print(f"Error fetching database pages: {data.get('message', response.text)}")
                break
                
            pages.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")
        
        print(f"Fetched {len(pages)} pages from database {database_id}")
        return pages
    
    def get_database_info(self, database_id: str) -> Dict[str, Any]:
        """
        Get information about a Notion database.
        
        Args:
            database_id: The ID of the Notion database.
            
        Returns:
            Database information as a dictionary.
        """
        print(f"Fetching info for database: {database_id}")
        url = f"https://api.notion.com/v1/databases/{database_id}"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            data = response.json()
            self._log_response(database_id, data, is_error=True)
            error_message = data.get('message', response.text)
            print(f"Error fetching database info: {error_message}")
            return {}
            
        database_data = response.json()
        self._log_response(database_id, database_data)
        return database_data
    
    def get_page_content(self, block_id: str, visited_blocks: Set[str] = None) -> List[Dict[str, Any]]:
        """
        Get the content of a Notion page or block.
        
        Args:
            block_id: The ID of the Notion page or block.
            visited_blocks: Set of already visited block IDs to prevent infinite recursion.
            
        Returns:
            Page/block content as a list of block dictionaries.
        """


        
        if visited_blocks is None:
            visited_blocks = set()
            
        # Skip already visited blocks to prevent infinite recursion
        if block_id in visited_blocks:
            print(f"Skipping already visited block: {block_id}")
            return []
            
        visited_blocks.add(block_id)
        
        print(f"Fetching content for block: {block_id}")
        url = f"https://api.notion.com/v1/blocks/{block_id}/children"
        
        blocks = []
        has_more = True
        next_cursor = None
        
        while has_more:
            params = {}
            if next_cursor:
                params["start_cursor"] = next_cursor
                
            response = requests.get(url, headers=self.headers, params=params)
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
            
            if response.status_code != 200:
                data = response.json()
                self._log_response(block_id, data, is_error=True)
                print(f"Error fetching content for block {block_id}: {data.get('message', response.text)}")
                break
                
            data = response.json()
            
            # Log the successful response
            self._log_response(block_id, data)
            
            blocks.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")
        
        # Process child_database blocks specially
        for block in blocks:
            if block.get("type") == "child_database":
                # Get database ID
                database_id = block.get("id")
                
                if database_id:
                    print(f"Found child_database with ID: {database_id}")
                    
                    # Get database info
                    database_info = self.get_database_info(database_id)
                    if database_info:
                        # Store database info in the block for later use
                        block["database_info"] = database_info
                    
                    # Get database pages
                    database_pages = self.fetch_database_pages(database_id)
                    if "children" not in block:
                        block["children"] = []
                    
                    # Process each page as a virtual child of the database
                    for page in database_pages:
                        # Add the page to the database's children
                        block["children"].append(page)
                        
                        # Get the page's content
                        if page.get("id") and page.get("id") not in visited_blocks:
                            page_content = self.get_page_content(page["id"], visited_blocks)
                            if "page_content" not in page:
                                page["page_content"] = []
                            page["page_content"].extend(page_content)
        
        # Process remaining children for each block
        for block in blocks:
            if block.get("has_children", False):
                block_type = block.get("type")
                
                # Handle special cases for different block types
                if block_type == "synced_block":
                    # Handle synced blocks - fetch the original content if this is a reference
                    synced_block_data = block.get("synced_block", {})
                    if synced_block_data.get("synced_from"):
                        # This is a reference to the original block
                        original_block_id = synced_block_data["synced_from"].get("block_id")
                        if original_block_id and original_block_id not in visited_blocks:
                            print(f"Fetching original content for synced block: {original_block_id}")
                            original_content = self.get_page_content(original_block_id, visited_blocks)
                            if "children" not in block:
                                block["children"] = []
                            block["children"].extend(original_content)
                    else:
                        # This is the original synced block
                        child_blocks = self.get_page_content(block["id"], visited_blocks)
                        if "children" not in block:
                            block["children"] = []
                        block["children"].extend(child_blocks)
                
                # Handle table blocks - fetch rows
                elif block_type == "table":
                    child_blocks = self.get_page_content(block["id"], visited_blocks)
                    if "children" not in block:
                        block["children"] = []
                    block["children"].extend(child_blocks)
                
                # Handle column_list specially to ensure we fetch all columns
                elif block_type == "column_list":
                    child_blocks = self.get_page_content(block["id"], visited_blocks)
                    if "children" not in block:
                        block["children"] = []
                    block["children"].extend(child_blocks)
                    
                    # Now process each column
                    for column_block in block["children"]:
                        if column_block.get("type") == "column" and column_block.get("has_children", False):
                            column_children = self.get_page_content(column_block["id"], visited_blocks)
                            if "children" not in column_block:
                                column_block["children"] = []
                            column_block["children"].extend(column_children)
                
                # For all other block types with children
                else:
                    child_blocks = self.get_page_content(block["id"], visited_blocks)
                    if "children" not in block:
                        block["children"] = []
                    block["children"].extend(child_blocks)
        
        return blocks
    
    def get_page_info(self, page_id: str) -> Dict[str, Any]:
        """
        Get basic information about a Notion page.
        
        Args:
            page_id: The ID of the Notion page.
            
        Returns:
            Page information as a dictionary.
        """

        # page_id = "f452ddc4ba7e44f090df76d26c142cd8"

        print(f"Fetching info for page: {page_id}")
        url = f"https://api.notion.com/v1/pages/{page_id}"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            data = response.json()
            self._log_response(page_id, data, is_error=True)
            error_message = data.get('message', response.text)
            print(f"Error fetching page info: {error_message}")
            if "page_id should be a valid uuid" in error_message:
                print(f"It appears the page ID format is incorrect. Make sure to use just the UUID part without any page title prefix.")
                print(f"Example: For a URL like 'https://www.notion.so/Page-Title-1d1debae43f7805aad97fd68225520f6'")
                print(f"Use only the last part: '1d1debae43f7805aad97fd68225520f6'")
            return {}
            
        page_data = response.json()
        self._log_response(page_id, page_data)
        return page_data 