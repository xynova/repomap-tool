# RepoMap API Integration Guide

This guide shows how external LLMs can interact with the docker-repomap tool through a REST API.

## Quick Start

### 1. Start the API Server

```bash
# Build and start the API server
docker-compose -f docker-compose-api.yml up --build

# Or start just the API server
docker-compose -f docker-compose-api.yml up repomap-api
```

### 2. Test the API

```bash
# Health check
curl http://localhost:5000/health

# Generate repo map
curl -X POST http://localhost:5000/repo-map \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "/path/to/your/project",
    "map_tokens": 2048
  }'
```

## API Endpoints

### POST /repo-map
Generate a repo map for a project.

**Request:**
```json
{
  "project_path": "/path/to/your/project",
  "map_tokens": 2048,
  "force_refresh": false
}
```

**Response:**
```json
{
  "success": true,
  "repo_map": "src/main.py:\n  main: def main():\n  process_data: def process_data(input_data):\n...",
  "content_length": 1500,
  "estimated_tokens": 375
}
```

### POST /cache/stats
Get cache statistics for a project.

**Request:**
```json
{
  "project_path": "/path/to/your/project"
}
```

**Response:**
```json
{
  "success": true,
  "stats": {
    "cache_path": "/path/to/your/project/.aider.tags.cache.v4",
    "cache_size_bytes": 2621440,
    "cache_size_mb": 2.5,
    "cache_files": 150,
    "exists": true,
    "last_modified": "2024-01-15T10:30:00"
  }
}
```

### POST /cache/clear
Clear the cache for a project.

**Request:**
```json
{
  "project_path": "/path/to/your/project"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Cleared cache at /path/to/your/project/.aider.tags.cache.v4"
}
```

## Integration Examples

### 1. Python Client

```python
import requests

class RepoMapClient:
    def __init__(self, api_url="http://localhost:5000"):
        self.api_url = api_url
    
    def get_repo_map(self, project_path, map_tokens=1024):
        response = requests.post(f"{self.api_url}/repo-map", json={
            "project_path": project_path,
            "map_tokens": map_tokens
        })
        return response.json()

# Usage
client = RepoMapClient()
result = client.get_repo_map("/path/to/project", map_tokens=2048)
if result["success"]:
    print(result["repo_map"])
```

### 2. OpenAI Integration

```python
import openai
import requests

def get_codebase_context(project_path, user_request):
    # Get repo map
    response = requests.post("http://localhost:5000/repo-map", json={
        "project_path": project_path,
        "map_tokens": 2048
    })
    result = response.json()
    
    if not result["success"]:
        return f"Error: {result['error']}"
    
    # Create context for OpenAI
    context = f"""Here is the codebase structure:

{result['repo_map']}

User request: {user_request}

Based on this codebase, please help with the request."""
    
    return context

# Send to OpenAI
context = get_codebase_context("/path/to/project", "Add error handling")
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an expert software developer."},
        {"role": "user", "content": context}
    ]
)
print(response.choices[0].message.content)
```

### 3. LangChain Integration

```python
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import requests

def create_repo_map_chain():
    # Get repo map
    def get_repo_map(project_path):
        response = requests.post("http://localhost:5000/repo-map", json={
            "project_path": project_path,
            "map_tokens": 2048
        })
        return response.json()["repo_map"]
    
    # Create prompt template
    template = """
    You are an expert software developer. Use this codebase context:
    
    {repo_map}
    
    User request: {user_request}
    
    Please provide specific recommendations.
    """
    
    prompt = PromptTemplate(
        input_variables=["repo_map", "user_request"],
        template=template
    )
    
    # Create chain
    llm = OpenAI(temperature=0)
    chain = LLMChain(llm=llm, prompt=prompt)
    
    return chain, get_repo_map

# Usage
chain, get_repo_map = create_repo_map_chain()
repo_map = get_repo_map("/path/to/project")
result = chain.run(repo_map=repo_map, user_request="Add logging")
print(result)
```

### 4. JavaScript/Node.js Integration

```javascript
const axios = require('axios');

class RepoMapClient {
    constructor(apiUrl = 'http://localhost:5000') {
        this.apiUrl = apiUrl;
    }
    
    async generateRepoMap(projectPath, mapTokens = 1024) {
        try {
            const response = await axios.post(`${this.apiUrl}/repo-map`, {
                project_path: projectPath,
                map_tokens: mapTokens
            });
            return response.data;
        } catch (error) {
            console.error('Error generating repo map:', error.response?.data || error.message);
            throw error;
        }
    }
    
    async getCacheStats(projectPath) {
        const response = await axios.post(`${this.apiUrl}/cache/stats`, {
            project_path: projectPath
        });
        return response.data;
    }
}

// Usage
const client = new RepoMapClient();
client.generateRepoMap('/path/to/project', 2048)
    .then(result => {
        if (result.success) {
            console.log('Repo map:', result.repo_map);
        }
    })
    .catch(error => console.error('Error:', error));
```

### 5. cURL Examples

```bash
# Generate repo map
curl -X POST http://localhost:5000/repo-map \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "/path/to/project",
    "map_tokens": 2048,
    "force_refresh": false
  }'

# Get cache stats
curl -X POST http://localhost:5000/cache/stats \
  -H "Content-Type: application/json" \
  -d '{"project_path": "/path/to/project"}'

# Clear cache
curl -X POST http://localhost:5000/cache/clear \
  -H "Content-Type: application/json" \
  -d '{"project_path": "/path/to/project"}'
```

## Advanced Usage

### Dynamic Token Budget

```python
def estimate_token_budget(user_request):
    """Estimate appropriate token budget based on request complexity"""
    request_lower = user_request.lower()
    
    if any(word in request_lower for word in ["explain", "what", "how"]):
        return 1024  # Simple questions
    elif any(word in request_lower for word in ["add", "modify", "change"]):
        return 2048  # Medium complexity
    elif any(word in request_lower for word in ["refactor", "restructure", "architect"]):
        return 4096  # Complex changes
    else:
        return 2048  # Default
```

### Caching Strategy

```python
def get_repo_map_with_caching(project_path, user_request):
    # Check cache stats first
    cache_response = requests.post("http://localhost:5000/cache/stats", json={
        "project_path": project_path
    })
    cache_stats = cache_response.json()
    
    # If cache is fresh, use it
    if cache_stats["success"] and cache_stats["stats"]["exists"]:
        force_refresh = False
    else:
        force_refresh = True
    
    # Generate repo map
    response = requests.post("http://localhost:5000/repo-map", json={
        "project_path": project_path,
        "map_tokens": estimate_token_budget(user_request),
        "force_refresh": force_refresh
    })
    
    return response.json()
```

## Error Handling

```python
def safe_repo_map_generation(project_path, map_tokens=1024):
    try:
        response = requests.post("http://localhost:5000/repo-map", json={
            "project_path": project_path,
            "map_tokens": map_tokens
        }, timeout=300)  # 5 minute timeout
        
        result = response.json()
        
        if result["success"]:
            return result["repo_map"]
        else:
            print(f"Error: {result['error']}")
            return None
            
    except requests.exceptions.Timeout:
        print("Timeout: Repo map generation took too long")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

## Performance Tips

1. **Use caching**: The API automatically caches results for better performance
2. **Adjust token budget**: Use smaller budgets for simple questions, larger for complex changes
3. **Monitor cache stats**: Check cache performance and clear when needed
4. **Handle timeouts**: Set appropriate timeouts for large projects
5. **Batch requests**: Consider batching multiple requests for efficiency

## Security Considerations

1. **Validate project paths**: Ensure the API only accesses allowed directories
2. **Rate limiting**: Implement rate limiting for production use
3. **Authentication**: Add authentication for production deployments
4. **Input validation**: Validate all input parameters
5. **Error handling**: Don't expose sensitive information in error messages
