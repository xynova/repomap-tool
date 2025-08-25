#!/usr/bin/env python3
# client_example.py

import requests
import json
import os
from typing import Dict, Any, Optional

class RepoMapClient:
    def __init__(self, api_url: str = "http://localhost:5000"):
        self.api_url = api_url
    
    def generate_repo_map(self, project_path: str, map_tokens: int = 1024, force_refresh: bool = False) -> Dict[str, Any]:
        """Generate repo map for a project"""
        payload = {
            "project_path": project_path,
            "map_tokens": map_tokens,
            "force_refresh": force_refresh
        }
        
        response = requests.post(f"{self.api_url}/repo-map", json=payload)
        return response.json()
    
    def get_cache_stats(self, project_path: str) -> Dict[str, Any]:
        """Get cache statistics"""
        payload = {"project_path": project_path}
        response = requests.post(f"{self.api_url}/cache/stats", json=payload)
        return response.json()
    
    def clear_cache(self, project_path: str) -> Dict[str, Any]:
        """Clear the cache"""
        payload = {"project_path": project_path}
        response = requests.post(f"{self.api_url}/cache/clear", json=payload)
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = requests.get(f"{self.api_url}/health")
        return response.json()

class LLMIntegrationExample:
    def __init__(self, repo_map_client: RepoMapClient):
        self.repo_map_client = repo_map_client
    
    def get_codebase_context(self, project_path: str, user_request: str) -> str:
        """Get relevant codebase context for an LLM"""
        
        # Determine appropriate token budget based on request complexity
        map_tokens = self._estimate_token_budget(user_request)
        
        # Generate repo map
        result = self.repo_map_client.generate_repo_map(
            project_path=project_path,
            map_tokens=map_tokens
        )
        
        if not result["success"]:
            return f"Error generating repo map: {result['error']}"
        
        repo_map = result["repo_map"]
        
        # Create context for LLM
        context = f"""Here is a summary of the codebase structure for your request:

{repo_map}

Based on this codebase structure, please help with: {user_request}

Remember:
- Files shown above are for context only
- Ask to see specific files if you need to make changes
- Suggest which files would need to be modified for this request
"""
        
        return context
    
    def _estimate_token_budget(self, user_request: str) -> int:
        """Estimate appropriate token budget based on request complexity"""
        request_lower = user_request.lower()
        
        # Simple requests
        if any(word in request_lower for word in ["explain", "what", "how", "where"]):
            return 1024
        
        # Medium complexity
        if any(word in request_lower for word in ["add", "modify", "change", "update"]):
            return 2048
        
        # Complex requests
        if any(word in request_lower for word in ["refactor", "restructure", "architect", "design"]):
            return 4096
        
        return 2048  # Default

def example_usage():
    """Example of how an external LLM would use the RepoMap API"""
    
    # Initialize client
    client = RepoMapClient("http://localhost:5000")
    
    # Check API health
    health = client.health_check()
    print(f"API Health: {health}")
    
    # Example project path
    project_path = "/path/to/your/project"
    
    # Example 1: Simple question
    print("\n=== Example 1: Simple Question ===")
    llm_integration = LLMIntegrationExample(client)
    
    context = llm_integration.get_codebase_context(
        project_path=project_path,
        user_request="What is the main entry point of this application?"
    )
    
    print("Context for LLM:")
    print(context[:500] + "..." if len(context) > 500 else context)
    
    # Example 2: Code modification request
    print("\n=== Example 2: Code Modification Request ===")
    
    context = llm_integration.get_codebase_context(
        project_path=project_path,
        user_request="Add error handling to the data processing function"
    )
    
    print("Context for LLM:")
    print(context[:500] + "..." if len(context) > 500 else context)
    
    # Example 3: Check cache stats
    print("\n=== Example 3: Cache Statistics ===")
    cache_stats = client.get_cache_stats(project_path)
    print(f"Cache Stats: {json.dumps(cache_stats, indent=2)}")

def openai_integration_example():
    """Example of integrating with OpenAI API"""
    import openai
    
    # Initialize clients
    repo_map_client = RepoMapClient("http://localhost:5000")
    llm_integration = LLMIntegrationExample(repo_map_client)
    
    # Example project
    project_path = "/path/to/your/project"
    user_request = "Add logging to the main processing function"
    
    # Get codebase context
    context = llm_integration.get_codebase_context(project_path, user_request)
    
    # Send to OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are an expert software developer. Use the provided codebase context to help with user requests."
            },
            {
                "role": "user",
                "content": context
            }
        ],
        max_tokens=1000
    )
    
    print("OpenAI Response:")
    print(response.choices[0].message.content)

def langchain_integration_example():
    """Example of integrating with LangChain"""
    from langchain.llms import OpenAI
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    
    # Initialize clients
    repo_map_client = RepoMapClient("http://localhost:5000")
    llm_integration = LLMIntegrationExample(repo_map_client)
    
    # Example project
    project_path = "/path/to/your/project"
    user_request = "Refactor the authentication system"
    
    # Get codebase context
    context = llm_integration.get_codebase_context(project_path, user_request)
    
    # Create LangChain prompt
    template = """
    You are an expert software developer. Use the following codebase context to help with the user's request.
    
    Codebase Context:
    {context}
    
    User Request: {user_request}
    
    Please provide:
    1. Analysis of the current codebase structure
    2. Which files would need to be modified
    3. Specific recommendations for the changes
    """
    
    prompt = PromptTemplate(
        input_variables=["context", "user_request"],
        template=template
    )
    
    # Create LLM chain
    llm = OpenAI(temperature=0)
    chain = LLMChain(llm=llm, prompt=prompt)
    
    # Run the chain
    result = chain.run(context=context, user_request=user_request)
    
    print("LangChain Response:")
    print(result)

if __name__ == "__main__":
    print("RepoMap Client Examples")
    print("======================")
    
    # Run examples
    example_usage()
    
    # Uncomment to see OpenAI integration
    # openai_integration_example()
    
    # Uncomment to see LangChain integration
    # langchain_integration_example()
