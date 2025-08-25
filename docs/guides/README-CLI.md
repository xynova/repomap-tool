# Docker RepoMap Command-Line Interface

This guide shows how to use the docker-repomap tool directly from the command line.

## Quick Start

### 1. **Basic Usage**
```bash
# Generate repo map for current directory
docker run --rm -v $PWD:/project repomap-tool /project

# Generate repo map for specific project
docker run --rm -v /path/to/your/project:/project repomap-tool /project
```

### 2. **Custom Token Budget**
```bash
# Generate with 2048 tokens (more detailed)
docker run --rm -v $PWD:/project repomap-tool /project --map-tokens 2048

# Generate with 4096 tokens (comprehensive)
docker run --rm -v $PWD:/project repomap-tool /project --map-tokens 4096
```

## Command-Line Options

### **Basic Options**
- `project_root` - Path to the project directory (required)
- `--map-tokens N` - Maximum tokens for repo map (default: 1024)
- `--output FILE` - Output file path (default: repo_map.txt in project root)
- `--verbose` - Verbose output
- `--force-refresh` - Force refresh (ignore cache)

### **Dynamic Context Options**
- `--chat-files FILES` - Comma-separated list of files currently in chat
- `--mentioned-files FILES` - Comma-separated list of mentioned files
- `--mentioned-idents IDENTS` - Comma-separated list of mentioned identifiers

### **Cache Management**
- `--cache-stats` - Show cache statistics
- `--clear-cache` - Clear the cache

## Usage Examples

### **1. Basic RepoMap Generation**
```bash
# Generate basic repo map
docker run --rm -v $PWD:/project repomap-tool /project

# Generate with custom token budget
docker run --rm -v $PWD:/project repomap-tool /project --map-tokens 2048

# Generate with verbose output
docker run --rm -v $PWD:/project repomap-tool /project --verbose
```

### **2. Dynamic Context Examples**

#### **Focus on Specific Files**
```bash
# Focus on main files
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-files 'src/main.py,src/app.py'

# Focus on utility files
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-files 'src/utils/helpers.py,src/utils/validators.py'
```

#### **Focus on Specific Functions/Classes**
```bash
# Focus on authentication functions
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'authenticate,login,logout,register'

# Focus on data processing functions
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'process_data,validate_input,transform_data'
```

#### **Chat Files Context**
```bash
# Consider files currently in chat
docker run --rm -v $PWD:/project repomap-tool /project \
  --chat-files 'src/auth.py,src/models.py'
```

#### **Combined Context**
```bash
# Complex example with all context types
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 2048 \
  --chat-files 'src/auth.py' \
  --mentioned-files 'src/main.py,src/config/settings.py' \
  --mentioned-idents 'authenticate,process_data,User'
```

### **3. Cache Management**
```bash
# Show cache statistics
docker run --rm -v $PWD:/project repomap-tool /project --cache-stats

# Clear cache
docker run --rm -v $PWD:/project repomap-tool /project --clear-cache

# Force refresh (ignore cache)
docker run --rm -v $PWD:/project repomap-tool /project --force-refresh
```

### **4. Output Options**
```bash
# Save to custom file
docker run --rm -v $PWD:/project repomap-tool /project \
  --output /tmp/my_repo_map.txt

# Save with timestamp
docker run --rm -v $PWD:/project repomap-tool /project \
  --output /tmp/repo_map_$(date +%Y%m%d_%H%M%S).txt
```

## Conversation Simulation

### **Step-by-Step Conversation**
```bash
# 1. Initial question
docker run --rm -v $PWD:/project repomap-tool /project --map-tokens 1024

# 2. Focus on specific file
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-files 'src/main.py' --map-tokens 1024

# 3. Focus on specific function
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'process_data' --map-tokens 1024

# 4. Add file to chat context
docker run --rm -v $PWD:/project repomap-tool /project \
  --chat-files 'src/auth.py' \
  --mentioned-idents 'authenticate' \
  --map-tokens 2048

# 5. Complex refactoring request
docker run --rm -v $PWD:/project repomap-tool /project \
  --chat-files 'src/auth.py,src/models.py' \
  --mentioned-files 'src/config/settings.py' \
  --mentioned-idents 'authenticate,jwt,token,user' \
  --map-tokens 4096
```

## Language-Specific Examples

### **Python Projects**
```bash
# Focus on Python-specific patterns
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-files 'main.py,app.py,__init__.py' \
  --mentioned-idents 'main,app,init,setup'
```

### **JavaScript/TypeScript Projects**
```bash
# Focus on JS/TS patterns
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-files 'index.js,app.js,main.ts' \
  --mentioned-idents 'main,app,init,setup'
```

### **Go Projects**
```bash
# Focus on Go patterns
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-files 'main.go,go.mod' \
  --mentioned-idents 'main,init,setup'
```

## Integration with Scripts

### **Bash Script Example**
```bash
#!/bin/bash
PROJECT_PATH="/path/to/your/project"

# Generate repo map
REPO_MAP=$(docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 2048)

# Save to file
echo "$REPO_MAP" > /tmp/repo_map.txt

# Show statistics
echo "Repo map generated with ${#REPO_MAP} characters"
```

### **Python Script Example**
```python
import subprocess
import json

def generate_repo_map(project_path, mentioned_files=None, mentioned_idents=None):
    cmd = ["docker", "run", "--rm", "-v", f"{project_path}:/project", "repomap-tool", "/project"]
    
    if mentioned_files:
        cmd.extend(["--mentioned-files", mentioned_files])
    
    if mentioned_idents:
        cmd.extend(["--mentioned-idents", mentioned_idents])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

# Usage
repo_map = generate_repo_map("/path/to/project", "src/main.py", "process_data")
print(repo_map)
```

## One-Liner Examples

### **Quick Commands**
```bash
# Quick overview
docker run --rm -v $PWD:/project repomap-tool /project

# Detailed analysis
docker run --rm -v $PWD:/project repomap-tool /project --map-tokens 4096

# Focus on authentication
docker run --rm -v $PWD:/project repomap-tool /project --mentioned-idents 'auth,login,authenticate'

# Focus on main files
docker run --rm -v $PWD:/project repomap-tool /project --mentioned-files 'main.py,app.py,index.js'

# Save to file
docker run --rm -v $PWD:/project repomap-tool /project --output /tmp/repo_map.txt
```

### **Common Patterns**
```bash
# Authentication system
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'auth,login,logout,register,user,password'

# Data processing
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'process,data,transform,validate,input,output'

# Configuration
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-files 'config.py,settings.py,.env,config.json'

# Database
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'database,db,model,schema,query,connection'
```

## Performance Tips

### **Token Budget Guidelines**
- **1024 tokens**: Quick overview, simple questions
- **2048 tokens**: Specific changes, medium complexity
- **4096 tokens**: Complex refactoring, architectural changes

### **Caching Strategy**
```bash
# Check cache first
docker run --rm -v $PWD:/project repomap-tool /project --cache-stats

# Use cache for repeated requests
docker run --rm -v $PWD:/project repomap-tool /project

# Force refresh when files change
docker run --rm -v $PWD:/project repomap-tool /project --force-refresh
```

### **Efficient Usage**
```bash
# Start with overview
docker run --rm -v $PWD:/project repomap-tool /project --map-tokens 1024

# Focus on specific areas
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-files 'src/main.py' --map-tokens 1024

# Get comprehensive view for complex tasks
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 --mentioned-idents 'auth,user,login'
```

## Troubleshooting

### **Common Issues**
```bash
# Permission denied
sudo docker run --rm -v $PWD:/project repomap-tool /project

# Project not found
docker run --rm -v /absolute/path/to/project:/project repomap-tool /project

# Cache issues
docker run --rm -v $PWD:/project repomap-tool /project --clear-cache --force-refresh
```

### **Debug Mode**
```bash
# Verbose output for debugging
docker run --rm -v $PWD:/project repomap-tool /project --verbose

# Check cache status
docker run --rm -v $PWD:/project repomap-tool /project --cache-stats
```

This command-line interface provides **full access** to all the dynamic RepoMap functionality, allowing you to generate context-aware codebase summaries directly from your terminal! 🎯
