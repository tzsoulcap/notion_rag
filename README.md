# Notion RAG FastAPI

FastAPI application that integrates with Notion to process and index content using RAG (Retrieval-Augmented Generation) functionality.

## Features

- **FastAPI Web Framework** with CORS support
- **Notion Integration** for content processing
- **RAG Functionality** for document indexing
- **Docker Support** for easy deployment
- **REST API** endpoints for content processing

## Project Structure

```
.
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── notion/
│   ├── notion_rag.py      # NotionRAG class
│   ├── api.py             # Notion API wrapper
│   └── processor.py       # Content processing utilities
└── README.md              # Project documentation
```

## Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- Notion API Key
- Access to Notion databases/pages you want to process

## Installation & Setup

### Option 1: Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd notion_rag
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   NOTION_API_KEY=your_notion_api_key_here
   ```

4. **Run the application**
   ```bash
   python main.py
   ```
   
   Or with uvicorn:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Option 2: Docker Development

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Run in detached mode**
   ```bash
   docker-compose up -d --build
   ```

3. **Stop the services**
   ```bash
   docker-compose down
   ```

### Option 3: Docker Only

1. **Build the Docker image**
   ```bash
   docker build -t fastapi-notion .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 fastapi-notion
   ```

3. **Run with environment variables**
   ```bash
   docker run -p 8000:8000 -e NOTION_API_KEY=your_key_here fastapi-notion
   ```

## API Documentation

Once the application is running, you can access:

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **API Base URL**: http://localhost:8000

### Endpoints

#### `GET /`
Simple health check endpoint.

**Response:**
```json
"hello world"
```

#### `POST /notion_content`
Process Notion content and return indexed text.

**Request Body:**
```json
{
  "notion_api_key": "secret_xxxxx",
  "database_ids": ["database_id_1", "database_id_2"],
  "page_ids": ["page_id_1", "page_id_2"]
}
```

**Parameters:**
- `notion_api_key` (optional): Notion API key (can also be set via environment variable)
- `database_ids` (optional): List of Notion database IDs to process
- `page_ids` (optional): List of individual page IDs to process

**Response:**
```json
{
  "text": "Combined content from all processed Notion documents..."
}
```

## Usage Examples

### Using curl

```bash
# Health check
curl http://localhost:8000/

# Process Notion content
curl -X POST "http://localhost:8000/notion_content" \
  -H "Content-Type: application/json" \
  -d '{
    "notion_api_key": "secret_xxxxx",
    "database_ids": ["your_database_id"],
    "page_ids": ["your_page_id"]
  }'
```

### Using Python requests

```python
import requests

# Health check
response = requests.get("http://localhost:8000/")
print(response.text)

# Process Notion content
data = {
    "notion_api_key": "secret_xxxxx",
    "database_ids": ["your_database_id"],
    "page_ids": ["your_page_id"]
}

response = requests.post("http://localhost:8000/notion_content", json=data)
result = response.json()
print(result["text"])
```

## Docker Commands Reference

### Development Commands

```bash
# Build and start services
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up --build --force-recreate
```

### Production Commands

```bash
# Build production image
docker build -t notion-rag-api:latest .

# Run production container
docker run -d \
  --name notion-rag-api \
  -p 8000:8000 \
  -e NOTION_API_KEY=your_key_here \
  notion-rag-api:latest

# View container logs
docker logs notion-rag-api

# Stop container
docker stop notion-rag-api
```

### Utility Commands

```bash
# View running containers
docker ps

# View all containers
docker ps -a

# Remove stopped containers
docker container prune

# View images
docker images

# Remove unused images
docker image prune
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NOTION_API_KEY` | Your Notion integration API key | Yes |
| `PYTHONPATH` | Python path (set to `/app` in Docker) | No |

## Getting Notion API Key

1. Go to [Notion Developers](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Give it a name and select workspace
4. Copy the "Internal Integration Token"
5. Share your databases/pages with the integration

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure the `notion/` directory contains all required files
2. **Notion API Error**: Verify your API key and ensure the integration has access to your pages/databases
3. **Port Already in Use**: Change the port mapping in docker-compose.yml or stop other services using port 8000
4. **Permission Denied**: Ensure Docker has proper permissions on your system

### Debug Commands

```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs fastapi-app

# Execute shell in running container
docker-compose exec fastapi-app /bin/bash

# Check container resource usage
docker stats
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]