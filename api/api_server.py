#!/usr/bin/env python3
# api_server.py

from flask import Flask, request, jsonify
import subprocess
import json
import os
import tempfile
import logging
from pathlib import Path

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

class RepoMapAPI:
    def __init__(self, docker_image="repomap-tool"):
        self.docker_image = docker_image
    
    def generate_repo_map(self, project_path, map_tokens=1024, force_refresh=False):
        """Generate repo map using Docker container"""
        try:
            # Build Docker command
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{project_path}:/project",
                "-v", f"{os.getcwd()}/cache:/app/cache",
                self.docker_image,
                "/project",
                "--map-tokens", str(map_tokens)
            ]
            
            if force_refresh:
                cmd.append("--force-refresh")
            
            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Read the generated repo map
                repo_map_file = os.path.join(project_path, "repo_map.txt")
                if os.path.exists(repo_map_file):
                    with open(repo_map_file, 'r', encoding='utf-8') as f:
                        repo_content = f.read()
                    
                    return {
                        "success": True,
                        "repo_map": repo_content,
                        "content_length": len(repo_content),
                        "estimated_tokens": len(repo_content) // 4
                    }
                else:
                    return {
                        "success": False,
                        "error": "Repo map file not generated"
                    }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "return_code": result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Timeout: Repo map generation took too long"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_cache_stats(self, project_path):
        """Get cache statistics"""
        try:
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{project_path}:/project",
                self.docker_image,
                "/project",
                "--cache-stats"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                try:
                    stats = json.loads(result.stdout)
                    return {"success": True, "stats": stats}
                except json.JSONDecodeError:
                    return {"success": False, "error": "Invalid JSON response"}
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def clear_cache(self, project_path):
        """Clear the cache"""
        try:
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{project_path}:/project",
                self.docker_image,
                "/project",
                "--clear-cache"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return {
                "success": result.returncode == 0,
                "message": result.stdout if result.returncode == 0 else result.stderr
            }
                
        except Exception as e:
            return {"success": False, "error": str(e)}

# Initialize the API
repo_map_api = RepoMapAPI()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "repo-map-api"})

@app.route('/repo-map', methods=['POST'])
def generate_repo_map():
    """Generate repo map for a project"""
    try:
        data = request.get_json()
        
        if not data or 'project_path' not in data:
            return jsonify({
                "success": False,
                "error": "project_path is required"
            }), 400
        
        project_path = data['project_path']
        map_tokens = data.get('map_tokens', 1024)
        force_refresh = data.get('force_refresh', False)
        
        # Validate project path
        if not os.path.exists(project_path):
            return jsonify({
                "success": False,
                "error": f"Project path does not exist: {project_path}"
            }), 400
        
        # Generate repo map
        result = repo_map_api.generate_repo_map(
            project_path=project_path,
            map_tokens=map_tokens,
            force_refresh=force_refresh
        )
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/cache/stats', methods=['POST'])
def get_cache_stats():
    """Get cache statistics"""
    try:
        data = request.get_json()
        
        if not data or 'project_path' not in data:
            return jsonify({
                "success": False,
                "error": "project_path is required"
            }), 400
        
        project_path = data['project_path']
        
        if not os.path.exists(project_path):
            return jsonify({
                "success": False,
                "error": f"Project path does not exist: {project_path}"
            }), 400
        
        result = repo_map_api.get_cache_stats(project_path)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear the cache"""
    try:
        data = request.get_json()
        
        if not data or 'project_path' not in data:
            return jsonify({
                "success": False,
                "error": "project_path is required"
            }), 400
        
        project_path = data['project_path']
        
        if not os.path.exists(project_path):
            return jsonify({
                "success": False,
                "error": f"Project path does not exist: {project_path}"
            }), 400
        
        result = repo_map_api.clear_cache(project_path)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
