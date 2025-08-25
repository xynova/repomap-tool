# Portable Aider Tool Migration Plan

## 🎯 **Goal: Portable Aider-Based Tool**

Create a standalone tool that:
- ✅ Uses aider libraries (that's the point!)
- ✅ Can be installed and used in other projects
- ✅ Self-contained as a deployable tool
- ✅ Leverages all aider's powerful features

## 📦 **What This Means**

### **Still Uses Aider (Good!)**
```python
# This is exactly what we want - leveraging aider's libraries
from aider.repomap import RepoMap
from aider.special import filter_important_files
from aider.dump import dump
```

### **But Can Be Installed Anywhere**
```bash
# Install the tool
pip install repomap-tool

# Use it in any project
repomap-tool /path/to/project --fuzzy-match --adaptive-semantic
```

## 🔧 **Simplified Migration Plan**

### **Phase 1: Package Structure (Week 1)**

1. **Create Package Structure**
   ```
   repomap-tool/
   ├── src/repomap_tool/
   │   ├── __init__.py
   │   ├── external_repomap.py      # Main tool
   │   ├── fuzzy_matcher.py         # ✅ Ready
   │   ├── adaptive_semantic_matcher.py # ✅ Ready
   │   ├── hybrid_matcher.py        # ✅ Ready
   │   └── semantic_matcher.py      # ✅ Ready
   ├── docker/                      # ✅ Ready
   ├── docs/                        # ✅ Ready
   ├── tests/                       # ✅ Ready
   ├── pyproject.toml              # 🔄 Create
   └── README.md                    # 🔄 Update
   ```

2. **Create pyproject.toml**
   ```toml
   [project]
   name = "repomap-tool"
   version = "0.1.0"
   description = "Portable code analysis tool using aider libraries"
   dependencies = [
       "aider-chat",  # Main aider dependency
       "networkx>=3.0",
       "fuzzywuzzy>=0.18.0",
       "python-Levenshtein>=0.21.0",
       # ... other dependencies
   ]
   
   [project.scripts]
   repomap-tool = "repomap_tool.external_repomap:main"
   ```

### **Phase 2: CLI Interface (Week 1-2)**

1. **Add CLI Entry Point**
   ```python
   # In external_repomap.py
   import click
   
   @click.command()
   @click.argument('project_path')
   @click.option('--fuzzy-match', is_flag=True)
   @click.option('--adaptive-semantic', is_flag=True)
   def main(project_path, **kwargs):
       # Initialize DockerRepoMap and run
   ```

2. **Update Docker Integration**
   ```dockerfile
   # Updated Dockerfile
   FROM python:3.11-slim
   
   # Install repomap-tool
   RUN pip install repomap-tool
   
   # Use the tool
   ENTRYPOINT ["repomap-tool"]
   ```

### **Phase 3: Documentation Updates (Week 2)**

1. **Update README**
   ```markdown
   # RepoMap Tool
   
   A portable code analysis tool that leverages aider's powerful libraries
   for intelligent code discovery and analysis.
   
   ## Installation
   ```bash
   pip install repomap-tool
   ```
   
   ## Usage
   ```bash
   repomap-tool /path/to/project --fuzzy-match --adaptive-semantic
   ```
   ```

2. **Update All Documentation**
   - Remove references to "docker-repomap"
   - Update installation instructions
   - Keep all technical explanations

## 📊 **File Migration Status**

### **✅ Ready to Move (No Changes Needed)**
- `fuzzy_matcher.py`
- `adaptive_semantic_matcher.py`
- `hybrid_matcher.py`
- `semantic_matcher.py`
- All Docker files
- All documentation files
- All test files
- All example files

### **🔄 Minor Updates Needed**
- `external_repomap.py` - Add CLI entry point
- `requirements.txt` - Update to include aider
- Create `pyproject.toml`
- Update `README.md`

### **❌ No Changes Needed**
- None! Everything can be moved with minimal changes

## 🚀 **Implementation Steps**

### **Step 1: Create Package Structure**
```bash
mkdir -p repomap-tool/src/repomap_tool
mkdir -p repomap-tool/{docker,docs,tests,examples}
```

### **Step 2: Move Files**
```bash
# Core implementation
cp external_repomap.py repomap-tool/src/repomap_tool/
cp fuzzy_matcher.py repomap-tool/src/repomap_tool/
cp adaptive_semantic_matcher.py repomap-tool/src/repomap_tool/
cp hybrid_matcher.py repomap-tool/src/repomap_tool/
cp semantic_matcher.py repomap-tool/src/repomap_tool/

# Docker files
cp Dockerfile repomap-tool/docker/
cp docker-compose.yml repomap-tool/docker/
# ... other docker files

# Documentation
cp README_INTEGRATION_SUMMARY.md repomap-tool/docs/
cp SIMPLE_INTEGRATION_GUIDE.md repomap-tool/docs/
# ... other docs

# Tests and examples
cp test_*.py repomap-tool/tests/
cp *.sh repomap-tool/examples/
```

### **Step 3: Create Package Files**
```bash
# Create __init__.py
echo "# RepoMap Tool Package" > repomap-tool/src/repomap_tool/__init__.py

# Create pyproject.toml
# [Create pyproject.toml content as shown above]

# Update README.md
# [Update README content as shown above]
```

### **Step 4: Add CLI Entry Point**
```python
# Add to external_repomap.py
if __name__ == "__main__":
    main()
```

## 🎯 **Benefits of This Approach**

1. **Leverages Aider's Power**: Uses all aider's sophisticated code analysis
2. **Easy Migration**: Minimal code changes required
3. **Portable**: Can be installed and used anywhere
4. **Maintainable**: Benefits from aider updates
5. **Familiar**: Uses existing, tested aider libraries

## 📋 **Final Package Structure**

```
repomap-tool/
├── 📁 src/repomap_tool/
│   ├── __init__.py
│   ├── external_repomap.py          # Main tool (uses aider)
│   ├── fuzzy_matcher.py             # ✅ Self-contained
│   ├── adaptive_semantic_matcher.py # ✅ Self-contained
│   ├── hybrid_matcher.py            # ✅ Self-contained
│   └── semantic_matcher.py          # ✅ Self-contained
├── 📁 docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── [other docker files...]
├── 📁 docs/
│   ├── README_INTEGRATION_SUMMARY.md
│   ├── SIMPLE_INTEGRATION_GUIDE.md
│   ├── INTEGRATION_DIAGRAMS.md
│   ├── ARCHITECTURE_DIAGRAM.md
│   ├── HYBRID_VS_SEMANTIC_ANALYSIS.md
│   └── [other docs...]
├── 📁 tests/
│   ├── test_adaptive_matcher.py
│   ├── test_hybrid_matcher.py
│   └── [other tests...]
├── 📁 examples/
│   ├── simple_hybrid_demo.py
│   ├── fuzzy_matching_examples.sh
│   └── [other examples...]
├── pyproject.toml                   # Package configuration
├── setup.py                         # Alternative setup
└── README.md                        # Updated README
```

## 🚀 **Usage After Migration**

```bash
# Install the tool
pip install repomap-tool

# Use it anywhere
repomap-tool /path/to/any/project --fuzzy-match --adaptive-semantic

# Or use Docker
docker run -v /path/to/project:/project repomap-tool /project --fuzzy-match
```

This approach gives you the best of both worlds: a portable, installable tool that leverages all of aider's powerful capabilities!
