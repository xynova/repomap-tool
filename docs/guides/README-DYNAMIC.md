# Dynamic RepoMap API: Conversation-Aware Codebase Context

This guide explains how to use the **Dynamic RepoMap API** that provides conversation-aware codebase context, similar to how `aider` works internally.

## The Problem with Static RepoMap

The basic RepoMap API provides a **static snapshot** of the codebase:

```python
# Static approach - same context every time
result = client.get_repo_map("/path/to/project", map_tokens=2048)
```

**Problems:**
- ❌ Same context for every message
- ❌ No personalization based on conversation
- ❌ No relevance to current user request
- ❌ Wastes tokens on irrelevant code

## The Dynamic Solution

The Dynamic RepoMap API provides **conversation-aware context**:

```python
# Dynamic approach - context adapts to conversation
result = client.get_dynamic_repo_map(
    project_path="/path/to/project",
    message_text="How does the `process_data` function work?",
    chat_files=["src/main.py"],
    map_tokens=2048
)
```

**Benefits:**
- ✅ Context adapts to each message
- ✅ Personalization based on mentioned files/identifiers
- ✅ Relevance to current user request
- ✅ Efficient token usage

## How It Works

### 1. **Context Extraction**
The API analyzes each message to extract:
- **Mentioned files**: `src/main.py`, `utils/helpers.py`
- **Mentioned identifiers**: `process_data`, `User`, `authenticate`
- **Chat files**: Files currently in the conversation

### 2. **Dynamic Ranking**
The RepoMap tool uses this context to:
- **Boost relevance**: Files/identifiers mentioned get higher PageRank
- **Personalize results**: Chat files influence the ranking
- **Filter content**: Focus on relevant parts of the codebase

### 3. **Adaptive Token Budget**
- **Simple questions**: 1024 tokens (overview)
- **Medium complexity**: 2048 tokens (specific changes)
- **Complex refactoring**: 4096 tokens (architectural changes)

## API Endpoints

### POST /repo-map/dynamic
Generate repo map dynamically based on conversation context.

**Request:**
```json
{
  "project_path": "/path/to/project",
  "message_text": "How does the process_data function work?",
  "chat_files": ["src/main.py", "src/utils/helpers.py"],
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
  "estimated_tokens": 375,
  "context": {
    "mentioned_files": ["src/main.py"],
    "mentioned_identifiers": ["process_data"],
    "chat_files": ["src/main.py", "src/utils/helpers.py"],
    "map_tokens_used": 2048
  }
}
```

### POST /context/analyze
Analyze message text to extract mentioned files and identifiers.

**Request:**
```json
{
  "message_text": "I want to modify the process_data function in src/main.py"
}
```

**Response:**
```json
{
  "success": true,
  "mentioned_files": ["src/main.py"],
  "mentioned_identifiers": ["process_data"],
  "filename_matches": ["process_data.py"],
  "all_mentioned_files": ["src/main.py", "process_data.py"]
}
```

## Usage Examples

### 1. **Basic Dynamic Usage**

```python
import requests

def get_dynamic_context(project_path, message):
    response = requests.post("http://localhost:5000/repo-map/dynamic", json={
        "project_path": project_path,
        "message_text": message,
        "map_tokens": 2048
    })
    return response.json()

# Usage
result = get_dynamic_context("/path/to/project", "How does the process_data function work?")
if result["success"]:
    print(result["repo_map"])
```

### 2. **Conversation Manager**

```python
from enhanced_client_example import ConversationManager, EnhancedRepoMapClient

# Initialize
client = EnhancedRepoMapClient("http://localhost:5000")
conversation = ConversationManager(client, "/path/to/project")

# Start conversation
conversation.start_conversation("I need help with this codebase")

# Send messages - context updates automatically
context1 = conversation.send_message("What is the main entry point?")
context2 = conversation.send_message("How does the process_data function work?")
context3 = conversation.send_message("I want to add error handling to the authentication system")

# Add files to chat context
conversation.add_file_to_chat("src/auth.py")
context4 = conversation.send_message("Now modify the authentication logic")
```

### 3. **OpenAI Integration**

```python
import openai
from enhanced_client_example import ConversationManager, EnhancedRepoMapClient

# Initialize
client = EnhancedRepoMapClient("http://localhost:5000")
conversation = ConversationManager(client, "/path/to/project")

# User message
user_message = "How does the process_data function work?"

# Get dynamic context
context = conversation.send_message(user_message)

# Send to OpenAI
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an expert software developer."},
        {"role": "user", "content": context}
    ]
)

print(response.choices[0].message.content)
```

### 4. **LangChain Integration**

```python
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from enhanced_client_example import ConversationManager, EnhancedRepoMapClient

# Initialize
client = EnhancedRepoMapClient("http://localhost:5000")
conversation = ConversationManager(client, "/path/to/project")

# Create chain
template = """
Use this codebase context to help with the user's request:

{context}

User request: {user_request}

Please provide specific recommendations.
"""

prompt = PromptTemplate(input_variables=["context", "user_request"], template=template)
llm = OpenAI(temperature=0)
chain = LLMChain(llm=llm, prompt=prompt)

# Process message
user_message = "Add error handling to the process_data function"
context = conversation.send_message(user_message)
result = chain.run(context=context, user_request=user_message)
print(result)
```

## Context Extraction Patterns

The API automatically detects:

### **File Mentions**
- Backticks: `` `src/main.py` ``
- Quotes: `"utils/helpers.py"`
- Plain text: `src/main.py`

### **Identifier Mentions**
- Backticks: `` `process_data` ``
- Function calls: `process_data(`
- Class definitions: `class User`
- Function definitions: `def authenticate`

### **Smart Matching**
- `process_data` → `process_data.py`, `process_data.js`, etc.
- `User` → `user.py`, `user.js`, `User.java`, etc.

## Conversation Flow Example

```python
# 1. Initial question
context1 = conversation.send_message("What is this codebase about?")
# Result: General overview with main files

# 2. Specific file mention
context2 = conversation.send_message("Explain `src/main.py`")
# Result: Focused on main.py and related files

# 3. Function mention
context3 = conversation.send_message("How does `process_data` work?")
# Result: Focused on process_data function and its dependencies

# 4. Add file to chat
conversation.add_file_to_chat("src/auth.py")
context4 = conversation.send_message("Now modify the authentication")
# Result: Focused on auth.py and authentication-related code

# 5. Complex refactoring
context5 = conversation.send_message("Refactor the entire authentication system")
# Result: Comprehensive view of authentication system with higher token budget
```

## Token Budget Strategy

The API automatically adjusts token budget based on request complexity:

```python
def estimate_token_budget(user_request):
    request_lower = user_request.lower()
    
    if any(word in request_lower for word in ["explain", "what", "how", "where"]):
        return 1024  # Simple questions
    elif any(word in request_lower for word in ["add", "modify", "change", "update"]):
        return 2048  # Medium complexity
    elif any(word in request_lower for word in ["refactor", "restructure", "architect", "design"]):
        return 4096  # Complex changes
    else:
        return 2048  # Default
```

## Performance Benefits

### **Before (Static)**
```
Message 1: "What is the main entry point?"
Context: 2048 tokens of general codebase

Message 2: "How does process_data work?"
Context: 2048 tokens of general codebase (same)

Message 3: "Add error handling to auth"
Context: 2048 tokens of general codebase (same)
Total: 6144 tokens, mostly irrelevant
```

### **After (Dynamic)**
```
Message 1: "What is the main entry point?"
Context: 1024 tokens focused on main files

Message 2: "How does process_data work?"
Context: 1024 tokens focused on process_data and dependencies

Message 3: "Add error handling to auth"
Context: 2048 tokens focused on authentication system
Total: 4096 tokens, all relevant
```

## Best Practices

### 1. **Use Conversation Manager**
```python
# Good: Maintains conversation state
conversation = ConversationManager(client, project_path)
conversation.send_message("First question")
conversation.send_message("Follow-up question")

# Bad: Loses context between messages
client.get_dynamic_repo_map(project_path, "First question")
client.get_dynamic_repo_map(project_path, "Follow-up question")
```

### 2. **Add Files to Chat Context**
```python
# When user wants to work on specific files
conversation.add_file_to_chat("src/auth.py")
conversation.add_file_to_chat("src/models.py")
context = conversation.send_message("Modify these files")
```

### 3. **Use Appropriate Token Budgets**
```python
# Simple questions
context = conversation.send_message("What is this?", map_tokens=1024)

# Complex changes
context = conversation.send_message("Refactor the entire system", map_tokens=4096)
```

### 4. **Monitor Context Analysis**
```python
# Check what the API detected
analysis = client.analyze_context("Modify the process_data function")
print(f"Detected files: {analysis['mentioned_files']}")
print(f"Detected identifiers: {analysis['mentioned_identifiers']}")
```

## Migration from Static to Dynamic

### **Before (Static)**
```python
# Old static approach
result = client.get_repo_map("/path/to/project", map_tokens=2048)
context = result["repo_map"]
```

### **After (Dynamic)**
```python
# New dynamic approach
result = client.get_dynamic_repo_map(
    project_path="/path/to/project",
    message_text=user_message,
    map_tokens=2048
)
context = result["repo_map"]
```

## Error Handling

```python
def safe_dynamic_repo_map(client, project_path, message):
    try:
        result = client.get_dynamic_repo_map(
            project_path=project_path,
            message_text=message
        )
        
        if result["success"]:
            return result["repo_map"]
        else:
            print(f"Error: {result['error']}")
            # Fallback to static repo map
            return client.get_repo_map(project_path)["repo_map"]
            
    except Exception as e:
        print(f"Exception: {e}")
        return None
```

This dynamic approach provides **conversation-aware, efficient, and relevant** codebase context that adapts to each user request, just like `aider` does internally! 🎯
