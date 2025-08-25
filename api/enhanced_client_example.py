#!/usr/bin/env python3
# enhanced_client_example.py

import requests
import json
import os
from typing import Dict, Any, List, Optional

class EnhancedRepoMapClient:
    def __init__(self, api_url: str = "http://localhost:5000"):
        self.api_url = api_url
        self.conversation_history = []
        self.chat_files = []
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def add_chat_file(self, file_path: str):
        """Add a file to the chat context"""
        if file_path not in self.chat_files:
            self.chat_files.append(file_path)
    
    def remove_chat_file(self, file_path: str):
        """Remove a file from the chat context"""
        if file_path in self.chat_files:
            self.chat_files.remove(file_path)
    
    def get_dynamic_repo_map(self, project_path: str, message_text: str = None, 
                           map_tokens: int = 1024, force_refresh: bool = False) -> Dict[str, Any]:
        """Generate repo map dynamically based on conversation context"""
        
        # Use the latest message if not provided
        if message_text is None and self.conversation_history:
            message_text = self.conversation_history[-1]["content"]
        elif message_text is None:
            message_text = ""
        
        payload = {
            "project_path": project_path,
            "message_text": message_text,
            "chat_files": self.chat_files,
            "map_tokens": map_tokens,
            "force_refresh": force_refresh
        }
        
        response = requests.post(f"{self.api_url}/repo-map/dynamic", json=payload)
        return response.json()
    
    def analyze_context(self, message_text: str) -> Dict[str, Any]:
        """Analyze message text to extract mentioned files and identifiers"""
        payload = {"message_text": message_text}
        response = requests.post(f"{self.api_url}/context/analyze", json=payload)
        return response.json()
    
    def get_repo_map(self, project_path: str, map_tokens: int = 1024, force_refresh: bool = False) -> Dict[str, Any]:
        """Generate basic repo map (backward compatibility)"""
        payload = {
            "project_path": project_path,
            "map_tokens": map_tokens,
            "force_refresh": force_refresh
        }
        
        response = requests.post(f"{self.api_url}/repo-map", json=payload)
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = requests.get(f"{self.api_url}/health")
        return response.json()

class ConversationManager:
    def __init__(self, repo_map_client: EnhancedRepoMapClient, project_path: str):
        self.repo_map_client = repo_map_client
        self.project_path = project_path
        self.current_context = None
    
    def start_conversation(self, initial_message: str = None):
        """Start a new conversation"""
        if initial_message:
            self.repo_map_client.add_message("user", initial_message)
            self.update_context(initial_message)
    
    def update_context(self, message: str):
        """Update the conversation context based on a new message"""
        # Analyze the message for context
        context_analysis = self.repo_map_client.analyze_context(message)
        
        if context_analysis["success"]:
            print(f"Context Analysis:")
            print(f"  Mentioned files: {context_analysis['mentioned_files']}")
            print(f"  Mentioned identifiers: {context_analysis['mentioned_identifiers']}")
            print(f"  Filename matches: {context_analysis['filename_matches']}")
        
        # Get dynamic repo map
        result = self.repo_map_client.get_dynamic_repo_map(
            project_path=self.project_path,
            message_text=message
        )
        
        if result["success"]:
            self.current_context = result
            return result["repo_map"]
        else:
            print(f"Error updating context: {result['error']}")
            return None
    
    def send_message(self, message: str, map_tokens: int = 1024) -> str:
        """Send a message and get updated context"""
        # Add message to history
        self.repo_map_client.add_message("user", message)
        
        # Update context
        repo_map = self.update_context(message)
        
        if repo_map:
            # Create context for LLM
            context = f"""Here is the updated codebase context for your request:

{repo_map}

User request: {message}

Based on this codebase structure, please help with the request.

Remember:
- Files shown above are for context only
- Ask to see specific files if you need to make changes
- Suggest which files would need to be modified for this request
"""
            return context
        else:
            return f"Error: Could not generate repo map for request: {message}"
    
    def add_file_to_chat(self, file_path: str):
        """Add a file to the chat context"""
        self.repo_map_client.add_chat_file(file_path)
        print(f"Added {file_path} to chat context")
    
    def remove_file_from_chat(self, file_path: str):
        """Remove a file from the chat context"""
        self.repo_map_client.remove_chat_file(file_path)
        print(f"Removed {file_path} from chat context")

def example_conversation():
    """Example of a dynamic conversation with repo map updates"""
    
    # Initialize client
    client = EnhancedRepoMapClient("http://localhost:5000")
    
    # Check API health
    health = client.health_check()
    print(f"API Health: {health}")
    
    # Example project path
    project_path = "/path/to/your/project"
    
    # Initialize conversation manager
    conversation = ConversationManager(client, project_path)
    
    # Start conversation
    print("\n=== Starting Conversation ===")
    conversation.start_conversation("I want to understand this codebase")
    
    # Message 1: General question
    print("\n=== Message 1: General Question ===")
    context1 = conversation.send_message("What is the main entry point of this application?")
    print("Context for LLM:")
    print(context1[:500] + "..." if len(context1) > 500 else context1)
    
    # Message 2: Specific file mention
    print("\n=== Message 2: Specific File Mention ===")
    context2 = conversation.send_message("Can you explain what happens in `src/main.py`?")
    print("Context for LLM:")
    print(context2[:500] + "..." if len(context2) > 500 else context2)
    
    # Message 3: Function mention
    print("\n=== Message 3: Function Mention ===")
    context3 = conversation.send_message("How does the `process_data` function work?")
    print("Context for LLM:")
    print(context3[:500] + "..." if len(context3) > 500 else context3)
    
    # Message 4: Add file to chat
    print("\n=== Message 4: Add File to Chat ===")
    conversation.add_file_to_chat("src/utils/helpers.py")
    context4 = conversation.send_message("Now I want to modify the helper functions")
    print("Context for LLM:")
    print(context4[:500] + "..." if len(context4) > 500 else context4)
    
    # Message 5: Complex request
    print("\n=== Message 5: Complex Request ===")
    context5 = conversation.send_message("I need to refactor the authentication system to use JWT tokens")
    print("Context for LLM:")
    print(context5[:500] + "..." if len(context5) > 500 else context5)

def openai_integration_example():
    """Example of integrating with OpenAI using dynamic context"""
    import openai
    
    # Initialize clients
    repo_map_client = EnhancedRepoMapClient("http://localhost:5000")
    conversation = ConversationManager(repo_map_client, "/path/to/your/project")
    
    # Start conversation
    conversation.start_conversation("I need help with this codebase")
    
    # User messages
    user_messages = [
        "What is the main entry point?",
        "How does the `process_data` function work?",
        "I want to add error handling to the authentication system"
    ]
    
    for i, message in enumerate(user_messages, 1):
        print(f"\n=== Processing Message {i} ===")
        print(f"User: {message}")
        
        # Get dynamic context
        context = conversation.send_message(message)
        
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
        
        print(f"OpenAI Response: {response.choices[0].message.content}")
        
        # Add response to conversation history
        conversation.repo_map_client.add_message("assistant", response.choices[0].message.content)

def langchain_integration_example():
    """Example of integrating with LangChain using dynamic context"""
    from langchain.llms import OpenAI
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    
    # Initialize clients
    repo_map_client = EnhancedRepoMapClient("http://localhost:5000")
    conversation = ConversationManager(repo_map_client, "/path/to/your/project")
    
    # Start conversation
    conversation.start_conversation("I need help with this codebase")
    
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
    
    # User messages
    user_messages = [
        "What is the main entry point?",
        "How does the `process_data` function work?",
        "I want to add error handling to the authentication system"
    ]
    
    for i, message in enumerate(user_messages, 1):
        print(f"\n=== Processing Message {i} ===")
        print(f"User: {message}")
        
        # Get dynamic context
        context = conversation.send_message(message)
        
        # Run the chain
        result = chain.run(context=context, user_request=message)
        
        print(f"LangChain Response: {result}")
        
        # Add response to conversation history
        conversation.repo_map_client.add_message("assistant", result)

if __name__ == "__main__":
    print("Enhanced RepoMap Client Examples")
    print("================================")
    
    # Run examples
    example_conversation()
    
    # Uncomment to see OpenAI integration
    # openai_integration_example()
    
    # Uncomment to see LangChain integration
    # langchain_integration_example()
