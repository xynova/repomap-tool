#!/usr/bin/env python3
# enhanced_api_server.py

from flask import Flask, request, jsonify
import subprocess  # nosec B404
import os
import re
import logging
from typing import Set, Dict, Any, List, Optional

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


class EnhancedRepoMapAPI:
    def __init__(self, docker_image: str = "repomap-tool") -> None:
        self.docker_image = docker_image

    def extract_mentioned_files(self, message_text: str) -> Set[str]:
        """Extract mentioned filenames from message text"""
        mentioned_files = set()

        # Look for file patterns like "src/main.py", "utils/helper.py", etc.
        file_patterns = [
            r"`([^`]+\.(py|js|ts|java|cpp|c|go|rs|php|rb|swift|kt|scala|md|txt|yml|yaml|json|xml|html|css|sql))`",
            r'"([^"]+\.(py|js|ts|java|cpp|c|go|rs|php|rb|swift|kt|scala|md|txt|yml|yaml|json|xml|html|css|sql))"',
            r"'([^']+\.(py|js|ts|java|cpp|c|go|rs|php|rb|swift|kt|scala|md|txt|yml|yaml|json|xml|html|css|sql))'",
            r"([a-zA-Z0-9_\-/]+\.(py|js|ts|java|cpp|c|go|rs|php|rb|swift|kt|scala|md|txt|yml|yaml|json|xml|html|css|sql))",
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, message_text)
            for match in matches:
                if isinstance(match, tuple):
                    filename = match[0]
                else:
                    filename = match
                mentioned_files.add(filename)

        return mentioned_files

    def extract_mentioned_identifiers(self, message_text: str) -> Set[str]:
        """Extract mentioned identifiers (function names, class names, etc.) from message text"""
        mentioned_idents = set()

        # Look for identifier patterns
        identifier_patterns = [
            r"`([a-zA-Z_][a-zA-Z0-9_]*)`",  # Backticks around identifiers
            r'"([a-zA-Z_][a-zA-Z0-9_]*)"',  # Quotes around identifiers
            r"'([a-zA-Z_][a-zA-Z0-9_]*)'",  # Single quotes around identifiers
            r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",  # Function calls
            r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)",  # Class definitions
            r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)",  # Function definitions
        ]

        for pattern in identifier_patterns:
            matches = re.findall(pattern, message_text)
            for match in matches:
                if isinstance(match, tuple):
                    identifier = match[0]
                else:
                    identifier = match
                mentioned_idents.add(identifier)

        return mentioned_idents

    def get_identifier_filename_matches(self, mentioned_idents: Set[str]) -> Set[str]:
        """Find filenames that match mentioned identifiers"""
        filename_matches = set()

        for ident in mentioned_idents:
            # Common patterns for identifier to filename mapping
            patterns = [
                f"{ident}.py",
                f"{ident}.js",
                f"{ident}.ts",
                f"{ident}.java",
                f"{ident}.cpp",
                f"{ident}.c",
                f"{ident}.go",
                f"{ident}.rs",
                f"{ident}.php",
                f"{ident}.rb",
                f"{ident}.swift",
                f"{ident}.kt",
                f"{ident}.scala",
                f"{ident}.md",
                f"{ident}.txt",
                f"{ident}.yml",
                f"{ident}.yaml",
                f"{ident}.json",
                f"{ident}.xml",
                f"{ident}.html",
                f"{ident}.css",
                f"{ident}.sql",
            ]

            filename_matches.update(patterns)

        return filename_matches

    def generate_dynamic_repo_map(
        self,
        project_path: str,
        message_text: str,
        chat_files: Optional[List[str]] = None,
        map_tokens: int = 1024,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Generate repo map dynamically based on conversation context"""

        if chat_files is None:
            chat_files = []

        # Extract context from message
        mentioned_fnames: Set[str] = self.extract_mentioned_files(message_text)
        mentioned_idents: Set[str] = self.extract_mentioned_identifiers(message_text)

        # Add filename matches for mentioned identifiers
        mentioned_fnames.update(self.get_identifier_filename_matches(mentioned_idents))

        # Convert to absolute paths
        chat_abs_files = [
            os.path.join(project_path, f)
            for f in chat_files
            if os.path.exists(os.path.join(project_path, f))
        ]
        mentioned_abs_files = [
            os.path.join(project_path, f)
            for f in mentioned_fnames
            if os.path.exists(os.path.join(project_path, f))
        ]

        try:
            # Comprehensive security validation
            if not self._validate_project_path(project_path):
                return {"success": False, "error": "Invalid project path"}

            # Validate Docker image name
            if not self._validate_docker_image():
                return {"success": False, "error": "Invalid Docker image configuration"}

            # Validate and sanitize all inputs
            chat_abs_files = self._sanitize_file_paths(chat_abs_files)
            mentioned_abs_files = self._sanitize_file_paths(mentioned_abs_files)
            mentioned_idents_sanitized = self._sanitize_identifiers(mentioned_idents)

            # Validate input lengths to prevent DoS
            if not self._validate_input_lengths(chat_abs_files, mentioned_abs_files, mentioned_idents_sanitized):
                return {"success": False, "error": "Input too large"}

            # Build Docker command with context
            cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{project_path}:/project",
                "-v",
                f"{os.getcwd()}/cache:/app/cache",
                self.docker_image,
                "/project",
                "--map-tokens",
                str(map_tokens),
                "--chat-files",
                ",".join(chat_abs_files),
                "--mentioned-files",
                ",".join(mentioned_abs_files),
                "--mentioned-idents",
                ",".join(mentioned_idents_sanitized),
            ]

            if force_refresh:
                cmd.append("--force-refresh")

            # Run the command with additional security measures
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                shell=False,  # nosec B603 - shell=False prevents shell injection
                cwd=None,  # Don't change working directory
                env=None,  # Don't pass environment variables
                check=False,  # Don't raise exception on non-zero exit
            )

            if result.returncode == 0:
                # Read the generated repo map
                repo_map_file = os.path.join(project_path, "repo_map.txt")
                if os.path.exists(repo_map_file):
                    with open(repo_map_file, "r", encoding="utf-8") as f:
                        repo_content = f.read()

                    return {
                        "success": True,
                        "repo_map": repo_content,
                        "content_length": len(repo_content),
                        "estimated_tokens": len(repo_content) // 4,
                        "context": {
                            "mentioned_files": list(mentioned_fnames),
                            "mentioned_identifiers": list(mentioned_idents),
                            "chat_files": chat_files,
                            "map_tokens_used": map_tokens,
                        },
                    }
                else:
                    return {"success": False, "error": "Repo map file not generated"}
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "return_code": result.returncode,
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Timeout: Repo map generation took too long",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_repo_map(
        self, project_path: str, map_tokens: int = 1024, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Generate basic repo map (backward compatibility)"""
        return self.generate_dynamic_repo_map(
            project_path=project_path,
            message_text="",
            chat_files=[],
            map_tokens=map_tokens,
            force_refresh=force_refresh,
        )

    def _validate_project_path(self, project_path: str) -> bool:
        """Validate project path for security"""
        try:
            # Must be absolute path
            if not os.path.isabs(project_path):
                return False
            
            # No path traversal
            if ".." in project_path or "~" in project_path:
                return False
            
            # Must exist and be a directory
            if not os.path.exists(project_path) or not os.path.isdir(project_path):
                return False
            
            # Path length limit
            if len(project_path) > 1000:
                return False
            
            # Only allow alphanumeric, forward slashes, hyphens, underscores, dots
            if not re.match(r'^[a-zA-Z0-9/_.-]+$', project_path):
                return False
            
            return True
        except Exception:
            return False

    def _validate_docker_image(self) -> bool:
        """Validate Docker image name for security"""
        try:
            # Must not be empty
            if not self.docker_image or not self.docker_image.strip():
                return False
            
            # Length limit
            if len(self.docker_image) > 200:
                return False
            
            # Only allow alphanumeric, hyphens, underscores, colons, forward slashes
            if not re.match(r'^[a-zA-Z0-9/_.-:]+$', self.docker_image):
                return False
            
            # Must not contain dangerous patterns
            dangerous_patterns = ['..', '~', '$', '`', ';', '|', '&', '(', ')', '{', '}', '[', ']']
            if any(pattern in self.docker_image for pattern in dangerous_patterns):
                return False
            
            return True
        except Exception:
            return False

    def _sanitize_file_paths(self, file_paths: List[str]) -> List[str]:
        """Sanitize file paths to prevent command injection"""
        sanitized = []
        for path in file_paths:
            try:
                # Remove any potentially dangerous characters
                sanitized_path = re.sub(r'[;&|`$(){}[\]"\'\\~]', "", path)
                
                # Ensure it's still a valid path after sanitization
                if sanitized_path and len(sanitized_path) <= 500:
                    sanitized.append(sanitized_path)
            except Exception:
                # Skip invalid paths
                continue
        return sanitized

    def _sanitize_identifiers(self, identifiers: Set[str]) -> List[str]:
        """Sanitize identifiers to prevent command injection"""
        sanitized = []
        for ident in identifiers:
            try:
                # Remove any potentially dangerous characters
                sanitized_ident = re.sub(r'[;&|`$(){}[\]"\'\\~]', "", ident)
                
                # Ensure it's still valid after sanitization
                if sanitized_ident and len(sanitized_ident) <= 200:
                    sanitized.append(sanitized_ident)
            except Exception:
                # Skip invalid identifiers
                continue
        return sanitized

    def _validate_input_lengths(self, chat_files: List[str], mentioned_files: List[str], identifiers: List[str]) -> bool:
        """Validate input lengths to prevent DoS attacks"""
        try:
            # Limit number of files
            if len(chat_files) > 100 or len(mentioned_files) > 100:
                return False
            
            # Limit number of identifiers
            if len(identifiers) > 200:
                return False
            
            # Limit total string length
            total_length = sum(len(f) for f in chat_files) + sum(len(f) for f in mentioned_files) + sum(len(i) for i in identifiers)
            if total_length > 10000:
                return False
            
            return True
        except Exception:
            return False


# Initialize the API
enhanced_api = EnhancedRepoMapAPI()


@app.route("/health", methods=["GET"])
def health() -> Any:
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "enhanced-repo-map-api"})


@app.route("/repo-map/dynamic", methods=["POST"])
def generate_dynamic_repo_map() -> Any:
    """Generate repo map dynamically based on conversation context"""
    try:
        data = request.get_json()

        if not data or "project_path" not in data:
            return jsonify({"success": False, "error": "project_path is required"}), 400

        project_path = data["project_path"]
        message_text = data.get("message_text", "")
        chat_files = data.get("chat_files", [])
        map_tokens = data.get("map_tokens", 1024)
        force_refresh = data.get("force_refresh", False)

        # Validate project path
        if not os.path.exists(project_path):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Project path does not exist: {project_path}",
                    }
                ),
                400,
            )

        # Generate dynamic repo map
        result = enhanced_api.generate_dynamic_repo_map(
            project_path=project_path,
            message_text=message_text,
            chat_files=chat_files,
            map_tokens=map_tokens,
            force_refresh=force_refresh,
        )

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/repo-map", methods=["POST"])
def generate_repo_map() -> Any:
    """Generate basic repo map (backward compatibility)"""
    try:
        data = request.get_json()

        if not data or "project_path" not in data:
            return jsonify({"success": False, "error": "project_path is required"}), 400

        project_path = data["project_path"]
        map_tokens = data.get("map_tokens", 1024)
        force_refresh = data.get("force_refresh", False)

        # Validate project path
        if not os.path.exists(project_path):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Project path does not exist: {project_path}",
                    }
                ),
                400,
            )

        # Generate repo map
        result = enhanced_api.generate_repo_map(
            project_path=project_path,
            map_tokens=map_tokens,
            force_refresh=force_refresh,
        )

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/context/analyze", methods=["POST"])
def analyze_context() -> Any:
    """Analyze message text to extract mentioned files and identifiers"""
    try:
        data = request.get_json()

        if not data or "message_text" not in data:
            return jsonify({"success": False, "error": "message_text is required"}), 400

        message_text = data["message_text"]

        # Extract context
        mentioned_files = enhanced_api.extract_mentioned_files(message_text)
        mentioned_idents = enhanced_api.extract_mentioned_identifiers(message_text)
        filename_matches = enhanced_api.get_identifier_filename_matches(
            mentioned_idents
        )

        return jsonify(
            {
                "success": True,
                "mentioned_files": list(mentioned_files),
                "mentioned_identifiers": list(mentioned_idents),
                "filename_matches": list(filename_matches),
                "all_mentioned_files": list(mentioned_files.union(filename_matches)),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    # In production, use: app.run(host="127.0.0.1", port=5000, debug=False)
    app.run(host="127.0.0.1", port=5000, debug=False)
