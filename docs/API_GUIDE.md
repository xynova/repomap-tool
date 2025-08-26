# RepoMap Tool API Guide

This guide covers the REST API for programmatic access to RepoMap Tool functionality.

## 🚀 Quick Start

### **Starting the API Server**

```bash
# From the project root
cd src/repomap_tool/api
python api_server.py
```

The API server will start on `http://localhost:5000`

### **Basic Usage**

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

## 📋 API Endpoints

### **GET /health**
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "enhanced-repo-map-api"
}
```

### **POST /repo-map**
Generate a basic repo map for a project.

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

### **POST /repo-map/dynamic**
Generate a dynamic repo map based on conversation context.

**Request:**
```json
{
  "project_path": "/path/to/your/project",
  "message_text": "I need to understand the authentication system",
  "chat_files": ["src/auth.py", "src/models.py"],
  "map_tokens": 2048,
  "force_refresh": false
}
```

**Response:**
```json
{
  "success": true,
  "repo_map": "Dynamic repo map content...",
  "mentioned_files": ["src/auth.py", "src/models.py"],
  "mentioned_identifiers": ["authenticate", "login", "User"],
  "content_length": 1800,
  "estimated_tokens": 450
}
```

### **POST /context/analyze**
Analyze message text to extract mentioned files and identifiers.

**Request:**
```json
{
  "message_text": "I need to modify the user authentication in src/auth.py and the User model"
}
```

**Response:**
```json
{
  "success": true,
  "mentioned_files": ["src/auth.py"],
  "mentioned_identifiers": ["user", "authentication", "User"],
  "filename_matches": ["user.py", "authentication.py", "User.py"],
  "all_mentioned_files": ["src/auth.py", "user.py", "authentication.py", "User.py"]
}
```

## 🔧 Client Usage

### **Python Client Example**

```python
import requests
import json

class RepoMapClient:
    def __init__(self, api_url="http://localhost:5000"):
        self.api_url = api_url
    
    def generate_repo_map(self, project_path, map_tokens=1024, force_refresh=False):
        """Generate repo map for a project"""
        payload = {
            "project_path": project_path,
            "map_tokens": map_tokens,
            "force_refresh": force_refresh
        }
        
        response = requests.post(f"{self.api_url}/repo-map", json=payload)
        return response.json()
    
    def analyze_context(self, message_text):
        """Analyze message text for mentioned files and identifiers"""
        payload = {"message_text": message_text}
        response = requests.post(f"{self.api_url}/context/analyze", json=payload)
        return response.json()
    
    def health_check(self):
        """Check API health"""
        response = requests.get(f"{self.api_url}/health")
        return response.json()

# Usage example
client = RepoMapClient()

# Generate repo map
result = client.generate_repo_map("/path/to/project", map_tokens=2048)
if result["success"]:
    print("Repo map generated successfully!")
    print(result["repo_map"])

# Analyze context
context = client.analyze_context("I need to modify the authentication system")
print(f"Mentioned files: {context['mentioned_files']}")
print(f"Mentioned identifiers: {context['mentioned_identifiers']}")
```

### **JavaScript/Node.js Client**

```javascript
class RepoMapClient {
    constructor(apiUrl = 'http://localhost:5000') {
        this.apiUrl = apiUrl;
    }

    async generateRepoMap(projectPath, mapTokens = 1024, forceRefresh = false) {
        const response = await fetch(`${this.apiUrl}/repo-map`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                project_path: projectPath,
                map_tokens: mapTokens,
                force_refresh: forceRefresh
            })
        });
        return response.json();
    }

    async analyzeContext(messageText) {
        const response = await fetch(`${this.apiUrl}/context/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message_text: messageText
            })
        });
        return response.json();
    }

    async healthCheck() {
        const response = await fetch(`${this.apiUrl}/health`);
        return response.json();
    }
}

// Usage example
const client = new RepoMapClient();

// Generate repo map
client.generateRepoMap('/path/to/project', 2048)
    .then(result => {
        if (result.success) {
            console.log('Repo map generated successfully!');
            console.log(result.repo_map);
        }
    })
    .catch(error => console.error('Error:', error));
```

## 🎯 Integration Examples

### **LLM Integration**

```python
class LLMIntegration:
    def __init__(self, repo_map_client):
        self.repo_map_client = repo_map_client
    
    def get_codebase_context(self, project_path, user_request):
        """Get relevant codebase context for an LLM"""
        
        # Analyze the user request
        context_analysis = self.repo_map_client.analyze_context(user_request)
        
        # Generate dynamic repo map
        result = self.repo_map_client.generate_repo_map(
            project_path=project_path,
            map_tokens=2048
        )
        
        if not result["success"]:
            return f"Error generating repo map: {result['error']}"
        
        # Create context for LLM
        context = f"""Here is a summary of the codebase structure for your request:

{result['repo_map']}

Based on this codebase structure, please help with: {user_request}

Remember:
- Files shown above are for context only
- Ask to see specific files if you need to make changes
- Suggest which files would need to be modified for this request
"""
        
        return context

# Usage
client = RepoMapClient()
llm_integration = LLMIntegration(client)

context = llm_integration.get_codebase_context(
    "/path/to/project",
    "I need to add user authentication to the application"
)
print(context)
```

### **IDE Plugin Integration**

```python
class IDEPlugin:
    def __init__(self, api_url):
        self.client = RepoMapClient(api_url)
    
    def get_relevant_files(self, current_file, user_query):
        """Get relevant files for a user query"""
        
        # Analyze the query
        context = self.client.analyze_context(user_query)
        
        # Get project path from current file
        project_path = self._get_project_root(current_file)
        
        # Generate repo map
        result = self.client.generate_repo_map(project_path)
        
        if result["success"]:
            return {
                "mentioned_files": context["mentioned_files"],
                "repo_map": result["repo_map"],
                "suggestions": self._generate_suggestions(context, result)
            }
        
        return {"error": result["error"]}
    
    def _get_project_root(self, file_path):
        """Extract project root from file path"""
        # Implementation depends on IDE
        pass
    
    def _generate_suggestions(self, context, result):
        """Generate file suggestions based on context"""
        suggestions = []
        
        # Add mentioned files
        suggestions.extend(context["mentioned_files"])
        
        # Add files from repo map that match identifiers
        for ident in context["mentioned_identifiers"]:
            # Find files that might contain this identifier
            # Implementation depends on specific logic
            pass
        
        return suggestions
```

## 🔧 Configuration

### **Environment Variables**
- `FLASK_ENV` - Flask environment (development, production)
- `PYTHONPATH` - Python path for imports
- `CACHE_DIR` - Cache directory path

### **Docker Deployment**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-api.txt .
RUN pip install -r requirements-api.txt

COPY src/repomap_tool/api/ ./api/

EXPOSE 5000

CMD ["python", "api/api_server.py"]
```

## 🚨 Error Handling

### **Common Error Responses**

**400 Bad Request:**
```json
{
  "success": false,
  "error": "project_path is required"
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "error": "Project path does not exist: /invalid/path"
}
```

### **Error Handling in Clients**

```python
def safe_api_call(client, method, *args, **kwargs):
    try:
        result = method(*args, **kwargs)
        
        if not result.get("success", False):
            print(f"API Error: {result.get('error', 'Unknown error')}")
            return None
        
        return result
    
    except requests.exceptions.RequestException as e:
        print(f"Network Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return None

# Usage
result = safe_api_call(client, client.generate_repo_map, "/path/to/project")
if result:
    print("Success:", result["repo_map"])
```

## 📚 Next Steps

- Read the **[CLI Guide](README-CLI.md)** for command-line usage
- Check **[Matching Algorithms](MATCHING_ALGORITHM_GUIDE.md)** for technical details
- Explore **[Architecture](../diagrams/ARCHITECTURE_DIAGRAM.md)** for system design
