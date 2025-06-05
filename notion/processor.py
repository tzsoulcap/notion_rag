"""
Notion content processing and text extraction utilities.
"""
from typing import Dict, Any, List
from langchain.schema import Document


class NotionProcessor:
    """
    Process Notion pages and blocks into usable text.
    """
    
    @staticmethod
    def _extract_text_from_block(block: Dict[str, Any]) -> str:
        """
        Extract text content from a Notion block.
        
        Args:
            block: Notion block object.
            
        Returns:
            Text content of the block.
        """
        block_type = block.get("type")
        
        if not block_type or block_type not in block:
            return ""
            
        block_content = block[block_type]
        text = ""
        
        if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "quote"]:
            text = " ".join([text_obj.get("plain_text", "") for text_obj in block_content.get("rich_text", [])])
            
            # Add appropriate formatting based on block type
            if block_type == "heading_1":
                text = f"# {text}"
            elif block_type == "heading_2":
                text = f"## {text}"
            elif block_type == "heading_3":
                text = f"### {text}"
            elif block_type == "bulleted_list_item":
                text = f"• {text}"
            elif block_type == "numbered_list_item":
                text = f"1. {text}"  # We'll just use 1. for all items for simplicity
            elif block_type == "quote":
                text = f"> {text}"
            
        elif block_type == "code":
            code_text = " ".join([text_obj.get("plain_text", "") for text_obj in block_content.get("rich_text", [])])
            text = f"Code ({block_content.get('language', 'unknown')}): {code_text}"
            
        elif block_type == "image":
            caption = " ".join([text_obj.get("plain_text", "") for text_obj in block_content.get("caption", [])])
            text = f"Image: {caption}"
            
        elif block_type == "to_do":
            checked = "☑" if block_content.get("checked", False) else "☐"
            item_text = " ".join([text_obj.get("plain_text", "") for text_obj in block_content.get("rich_text", [])])
            text = f"{checked} {item_text}"
            
        elif block_type == "toggle":
            toggle_text = " ".join([text_obj.get("plain_text", "") for text_obj in block_content.get("rich_text", [])])
            text = f"Toggle: {toggle_text}"
            
        elif block_type == "callout":
            callout_text = " ".join([text_obj.get("plain_text", "") for text_obj in block_content.get("rich_text", [])])
            emoji = block_content.get("icon", {}).get("emoji", "")
            text = f"Callout {emoji}: {callout_text}"
            
        elif block_type == "table":
            text = "Table:"  # We'll add the content from child rows
            
        elif block_type == "table_row":
            # Extract content from cells
            cells = block_content.get("cells", [])
            row_content = []
            
            for cell in cells:
                cell_text = ""
                # Each cell contains a list of text objects
                if cell:
                    cell_text = " ".join([text_obj.get("plain_text", "") for text_obj in cell])
                row_content.append(cell_text)
            
            # Format the row content
            if row_content:
                text = "| " + " | ".join(row_content) + " |"
            else:
                text = "| Empty row |"
            
        elif block_type == "divider":
            text = "---"
            
        elif block_type == "bookmark":
            url = block_content.get("url", "")
            caption = " ".join([text_obj.get("plain_text", "") for text_obj in block_content.get("caption", [])])
            text = f"Bookmark: {url} - {caption}"
            
        elif block_type == "equation":
            text = f"Equation: {block_content.get('expression', '')}"
            
        elif block_type == "file":
            caption = " ".join([text_obj.get("plain_text", "") for text_obj in block_content.get("caption", [])])
            text = f"File: {caption}"
            
        elif block_type == "column_list":
            text = "Column List:"
            
        elif block_type == "column":
            text = "Column:"
            
        elif block_type == "synced_block":
            # Check if this is the original or a synced copy
            if block_content.get("synced_from"):
                original_block_id = block_content.get("synced_from").get("block_id")
                text = f"Synced content (from block {original_block_id}):"
            else:
                text = "Synced content (original):"
                
        elif block_type == "table_of_contents":
            text = "Table of Contents"
            
        elif block_type == "embed":
            text = f"Embedded content: {block_content.get('url', '')}"
            
        elif block_type == "link_preview":
            text = f"Link preview: {block_content.get('url', '')}"
            
        elif block_type == "link_to_page":
            if "page_id" in block_content:
                text = f"Link to page: {block_content.get('page_id')}"
            elif "database_id" in block_content:
                text = f"Link to database: {block_content.get('database_id')}"
                
        elif block_type == "child_page":
            text = f"Child page: {block_content.get('title', '')}"
            
        elif block_type == "child_database":
            database_title = block_content.get("title", "")
            text = f"Child database: {database_title}"
            
            # Check if we have database info and pages
            if "database_info" in block:
                database_info = block.get("database_info", {})
                db_title = database_info.get("title", [])
                if db_title:
                    db_title_text = " ".join([text_obj.get("plain_text", "") for text_obj in db_title])
                    text = f"Database: {db_title_text}"
                
                # Get database properties as columns
                properties = database_info.get("properties", {})
                property_names = list(properties.keys())
                if property_names:
                    text += f"\nColumns: {', '.join(property_names)}"
            
            # Process child pages if present
            if "children" in block and block["children"]:
                # Get count of pages
                page_count = len(block["children"])
                text += f"\nContains {page_count} pages:"
                
                # Extract titles of all pages (ไม่จำกัดแค่ 5 อันแรก)
                page_titles = []
                for page in block["children"]:  # ลบ [:5] ออกเพื่อแสดงทุกเพจ
                    props = page.get("properties", {})
                    for prop_name, prop_value in props.items():
                        if prop_value.get("type") == "title":
                            title_text = " ".join([text_obj.get("plain_text", "") for text_obj in prop_value.get("title", [])])
                            if title_text:
                                page_titles.append(title_text)
                                break
                
                if page_titles:
                    text += "\n- " + "\n- ".join(page_titles)
                
                # Process full content of each page
                detailed_pages = []
                for i, page in enumerate(block["children"]):
                    if "page_content" in page:
                        title = ""
                        # Get page title
                        props = page.get("properties", {})
                        for prop_name, prop_value in props.items():
                            if prop_value.get("type") == "title":
                                title = " ".join([text_obj.get("plain_text", "") for text_obj in prop_value.get("title", [])])
                                break
                        
                        page_text = f"\n--- Page {i+1}: {title} ---\n"
                        for content_block in page.get("page_content", []):
                            content_text = NotionProcessor._extract_text_from_block(content_block)
                            if content_text:
                                # Indent page content
                                indented_text = "\n".join([f"    {line}" for line in content_text.split("\n")])
                                page_text += indented_text + "\n"
                        detailed_pages.append(page_text)
                
                # Include detailed page content
                if detailed_pages:
                    text += "\n\nDetailed page content:\n" + "\n".join(detailed_pages)
        
        else:
            # Handle unknown block types
            text = f"[{block_type}]"
        
        # Process child blocks if present
        child_text = ""
        if "children" in block and block["children"]:
            child_texts = []
            
            # Special handling for column_list
            if block_type == "column_list":
                for column_block in block["children"]:
                    if column_block.get("type") == "column":
                        column_content = NotionProcessor._extract_text_from_block(column_block)
                        if column_content and column_content != "Column:":
                            child_texts.append(column_content)
            # Special handling for tables to create a formatted table
            elif block_type == "table":
                # First, gather all row content
                rows = []
                for row_block in block["children"]:
                    if row_block.get("type") == "table_row":
                        row_content = NotionProcessor._extract_text_from_block(row_block)
                        if row_content:
                            rows.append(row_content)
                
                if rows:
                    # Check if the first row should be treated as a header
                    has_header = block_content.get("has_column_header", False)
                    
                    # Add header row
                    if has_header and len(rows) > 0:
                        header_row = rows[0]
                        child_texts.append(header_row)
                        
                        # Add divider line after header
                        if len(rows) > 1:
                            # Create a separator row with the same number of cells
                            cell_count = header_row.count("|") - 1
                            divider = "| " + " | ".join(["---"] * cell_count) + " |"
                            child_texts.append(divider)
                            
                            # Add remaining rows
                            child_texts.extend(rows[1:])
                    else:
                        # No header, just add all rows
                        child_texts.extend(rows)
            else:
                # Standard processing for other block types
                for child_block in block["children"]:
                    child_content = NotionProcessor._extract_text_from_block(child_block)
                    if child_content:
                        child_texts.append(child_content)
            
            if child_texts:
                child_text = "\n".join(child_texts)
                
                # For tables, don't indent to maintain table formatting
                if block_type == "table":
                    text = f"{text}\n{child_text}" if text else child_text
                else:
                    # Indent child content for better readability
                    child_text = "\n".join([f"  {line}" for line in child_text.split("\n")])
                    
                    # Special case for column_list: don't repeat "Column List:" prefix
                    if block_type == "column_list":
                        text = child_text
                    elif block_type == "column":
                        # For columns, we don't want the "Column:" prefix
                        text = child_text
                    else:
                        text = f"{text}\n{child_text}" if text else child_text
        
        return text
    
    @staticmethod
    def process_page_to_document(page: Dict[str, Any], page_content: list) -> Document:
        """
        Process a Notion page into a Document object.
        
        Args:
            page: Notion page object.
            page_content: Content blocks of the page.
            
        Returns:
            Document object with the page's content.
        """
        # Extract page properties
        properties = page.get("properties", {})
        page_id = page.get("id", "")
        
        # Extract title, if available
        title = ""
        for _, prop in properties.items():
            if prop.get("type") == "title":
                title = " ".join([text_obj.get("plain_text", "") for text_obj in prop.get("title", [])])
                break
                
        # Extract text from each block
        content_texts = []
        for block in page_content:
            text = NotionProcessor._extract_text_from_block(block)
            if text:
                content_texts.append(text)
        
        # Join all text with newlines
        content = "\n".join(content_texts)
        
        # Create metadata
        metadata = {
            "page_id": page_id,
            "title": title,
            "url": page.get("url", ""),
            "created_time": page.get("created_time", ""),
            "last_edited_time": page.get("last_edited_time", "")
        }
        
        # Include all properties in metadata
        for prop_name, prop_value in properties.items():
            prop_type = prop_value.get("type", "")
            if prop_type == "rich_text":
                metadata[prop_name] = " ".join([text_obj.get("plain_text", "") for text_obj in prop_value.get("rich_text", [])])
            elif prop_type == "number":
                metadata[prop_name] = prop_value.get("number", 0)
            elif prop_type == "select":
                select_obj = prop_value.get("select", {})
                if select_obj:
                    metadata[prop_name] = select_obj.get("name", "")
            elif prop_type == "multi_select":
                multi_select_objs = prop_value.get("multi_select", [])
                if multi_select_objs:
                    metadata[prop_name] = [obj.get("name", "") for obj in multi_select_objs]
            elif prop_type == "date":
                date_obj = prop_value.get("date", {})
                if date_obj:
                    metadata[prop_name] = date_obj.get("start", "")
            elif prop_type == "checkbox":
                metadata[prop_name] = prop_value.get("checkbox", False)
            elif prop_type == "url":
                metadata[prop_name] = prop_value.get("url", "")
            elif prop_type == "email":
                metadata[prop_name] = prop_value.get("email", "")
            elif prop_type == "phone_number":
                metadata[prop_name] = prop_value.get("phone_number", "")
        
        return Document(page_content=f"{title}\n\n{content}", metadata=metadata)
    
    @staticmethod
    def process_direct_page_to_document(page_info: Dict[str, Any], page_content: list) -> Document:
        """
        Process a direct Notion page into a Document object.
        
        Args:
            page_info: Notion page info.
            page_content: Content blocks of the page.
            
        Returns:
            Document object with the page's content.
        """
        # Check if page_info is None or empty
        if not page_info:
            raise ValueError("Could not retrieve page info. Please check if the page ID is correct and you have access to it.")
        
        page_id = page_info.get("id", "")
        
        # Extract basic metadata
        page_title = ""
        # Try to get title from page info
        if "properties" in page_info:
            for _, prop in page_info.get("properties", {}).items():
                if prop.get("type") == "title":
                    page_title = " ".join([text_obj.get("plain_text", "") for text_obj in prop.get("title", [])])
                    break
        print(f"Page Title: {page_title}")
        
        # Extract text from each block
        content_texts = []
        
        # Check for database content
        has_databases = False
        
        for block in page_content:
            # Enable detailed database content extraction
            if block.get("type") == "child_database":
                has_databases = True
            
            text = NotionProcessor._extract_text_from_block(block)
            if text:
                content_texts.append(text)
        
        # Join all text with newlines
        content = "\n".join(content_texts)

        # Create metadata
        metadata = {
            "page_id": page_id,
            "title": page_title,
            "url": page_info.get("url", ""),
            "created_time": page_info.get("created_time", ""),
            "last_edited_time": page_info.get("last_edited_time", ""),
            "has_database_content": has_databases
        }
        print(f"Metadata: {metadata}")
        
        return Document(page_content=f"{page_title}\n\n{content}", metadata=metadata) 