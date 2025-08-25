# Docker RepoMap - Refactoring Guide

## 🎯 **The Problem You Identified**

You're absolutely right! The original default of **1024 tokens** was too small for serious refactoring work. Here's what we've fixed:

### **Before (1024 tokens):**
- **8,227 bytes** (334 lines) - Too small for refactoring
- **Basic overview only** - Missing critical details
- **Insufficient context** - Not enough information for complex changes

### **After (4096 tokens default):**
- **18,225 bytes** (764 lines) - Much more comprehensive
- **Detailed analysis** - Includes classes, methods, functions
- **Rich context** - Sufficient for most refactoring tasks

## 🚀 **Refactoring-Optimized Usage**

### **1. Default Command (Now 4096 tokens)**
```bash
# This now gives you 4x more detail by default!
docker run --rm -v $PWD:/project repomap-tool /project
```

### **2. Comprehensive Analysis (8192 tokens)**
```bash
# For major refactoring projects
docker run --rm -v $PWD:/project repomap-tool /project --map-tokens 8192
```

### **3. Focused Refactoring Commands**
```bash
# Architecture refactoring
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-files 'main.py,app.py,index.js,__init__.py' \
  --mentioned-idents 'main,init,setup,config,app'

# Data model refactoring
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'model,schema,database,db,table,entity'

# API refactoring
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'api,route,endpoint,controller,handler'
```

## 📊 **Token Budget Comparison**

| Token Budget | File Size | Lines | Use Case |
|-------------|-----------|-------|----------|
| **1024** | ~8KB | ~334 | Quick overview |
| **4096** | ~18KB | ~764 | **Default - Good for refactoring** |
| **8192** | ~38KB | ~1,632 | **Comprehensive refactoring** |

## 🔧 **Refactoring Workflow**

### **Step 1: Initial Analysis**
```bash
# Get comprehensive overview
docker run --rm -v $PWD:/project repomap-tool /project --map-tokens 8192
```

### **Step 2: Focus on Specific Areas**
```bash
# Based on what you're refactoring, use focused commands
# Example: Refactoring authentication system
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'auth,login,authenticate,user,session'
```

### **Step 3: Dynamic Context for Ongoing Work**
```bash
# As you work on specific files, add them to context
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --chat-files 'src/auth.py,src/models.py' \
  --mentioned-files 'src/config/settings.py' \
  --mentioned-idents 'refactor,optimize,improve'
```

### **Step 4: Force Refresh After Changes**
```bash
# After making significant changes
docker run --rm -v $PWD:/project repomap-tool /project \
  --force-refresh --map-tokens 8192
```

## 🎯 **Refactoring-Specific Features**

### **1. Smart File Selection**
The RepoMap algorithm intelligently selects the most relevant files for refactoring:
- **High PageRank files** (most connected/important)
- **Core architecture files** (main, init, config)
- **Related functions and classes**
- **Dependencies and imports**

### **2. Dynamic Context Adaptation**
- **Mentioned files**: Focus on specific files you're working on
- **Mentioned identifiers**: Focus on specific functions/classes
- **Chat files**: Include files from your conversation context
- **Token budget**: Adjust based on complexity of refactoring

### **3. Caching for Performance**
- **Fast subsequent runs** after initial analysis
- **Cache invalidation** when files change
- **Force refresh** option for major changes

## 📋 **Refactoring Checklist**

### **Before Starting Refactoring:**
- [ ] Run comprehensive analysis (8192 tokens)
- [ ] Identify affected modules and dependencies
- [ ] Check cache stats to ensure fresh data
- [ ] Plan your refactoring approach

### **During Refactoring:**
- [ ] Use focused commands for specific areas
- [ ] Add relevant files to chat context
- [ ] Use mentioned identifiers for specific functions
- [ ] Monitor cache stats for performance

### **After Refactoring:**
- [ ] Force refresh to get updated analysis
- [ ] Run comprehensive analysis again
- [ ] Verify all changes are captured
- [ ] Update documentation if needed

## 🛠 **Advanced Refactoring Commands**

### **Class Hierarchy Refactoring**
```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'class,extends,inherits,abstract,interface'
```

### **Database Schema Refactoring**
```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'migration,schema,table,column,foreign_key'
```

### **API Version Refactoring**
```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'version,api,v1,v2,deprecated'
```

### **Performance Optimization Refactoring**
```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'performance,optimize,cache,async,thread'
```

## 🎉 **Benefits for Refactoring**

### **1. Comprehensive Context**
- **Full codebase understanding** before making changes
- **Dependency analysis** to avoid breaking changes
- **Impact assessment** of proposed refactoring

### **2. Intelligent Focus**
- **PageRank-based selection** of most important code
- **Dynamic context** based on your current work
- **Smart filtering** to avoid irrelevant code

### **3. Performance Optimization**
- **Efficient caching** for fast repeated analysis
- **Token budget management** to balance detail vs. cost
- **Incremental updates** as you make changes

### **4. Quality Assurance**
- **Consistent analysis** across the entire codebase
- **Relationship mapping** between components
- **Change tracking** through cache invalidation

## 🚀 **Quick Start for Refactoring**

1. **Install and build** the docker-repomap tool
2. **Run comprehensive analysis**: `--map-tokens 8192`
3. **Use focused commands** for specific refactoring areas
4. **Leverage dynamic context** for ongoing work
5. **Force refresh** after significant changes

The docker-repomap tool is now **optimized for refactoring work** with a default that provides sufficient detail for most refactoring tasks! 🎯
