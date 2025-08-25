# Docker RepoMap - Feature Development Guide

## 🎯 **How to Use Docker RepoMap for Feature Development**

When developing a new feature in aider (or any codebase), you need to understand the existing codebase structure, patterns, and dependencies. Here's how to use docker-repomap effectively:

## 🚀 **Practical Example: Adding `aider export` Command**

Let's walk through adding a new `aider export` command that exports the current conversation to a file.

### **Step 1: Understand the Codebase Structure**

```bash
# Get overview of main entry points and command structure
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-files 'aider/main.py,aider/commands.py' \
  --mentioned-idents 'main,command,cli'
```

**What this gives you:**
- How `main.py` initializes the application
- How `commands.py` handles command routing
- The overall CLI structure

### **Step 2: Understand the Command System**

```bash
# Focus on command handling and argument parsing
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-files 'aider/commands.py,aider/args.py' \
  --mentioned-idents 'command,argparse,parser,add_argument'
```

**What this gives you:**
- How commands are defined (`def cmd_*`)
- How arguments are parsed
- Command routing patterns

### **Step 3: Learn from Existing Commands**

```bash
# Analyze existing commands to understand patterns
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'cmd_,def cmd_'
```

**What this gives you:**
- Existing command patterns
- Common helper functions
- Error handling approaches

### **Step 4: Understand Related Systems**

```bash
# Focus on conversation and history management
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-files 'aider/history.py,aider/io.py' \
  --mentioned-idents 'history,conversation,chat,save,load'
```

**What this gives you:**
- How conversations are stored
- File I/O patterns
- Data persistence approaches

### **Step 5: Focus on File I/O Patterns**

```bash
# Focus on file I/O and export functionality
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'write,read,export,save,file,io'
```

**What this gives you:**
- Existing file writing patterns
- Error handling for file operations
- Output formatting approaches

### **Step 6: Detailed Analysis of Target Files**

```bash
# Detailed analysis of files you'll modify
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 8192 \
  --mentioned-files 'aider/commands.py,aider/history.py,aider/io.py' \
  --mentioned-idents 'export,conversation,history,file'
```

**What this gives you:**
- Complete understanding of the files you'll modify
- All related functions and classes
- Dependencies and imports

## 🔄 **Ongoing Development Workflow**

### **When Working on Specific Files**

```bash
# When working on commands.py
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --chat-files 'aider/commands.py' \
  --mentioned-idents 'export,conversation,history'
```

### **When Working on Related Files**

```bash
# When working on history.py
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --chat-files 'aider/history.py,aider/commands.py' \
  --mentioned-idents 'save,export,file'
```

### **When Testing Your Feature**

```bash
# When testing the feature
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-files 'aider/commands.py,aider/history.py,aider/io.py' \
  --mentioned-idents 'test,export,conversation'
```

## 📋 **Feature Development Checklist**

### **Before Starting Development:**

1. **Understand the codebase structure**
   ```bash
   docker run --rm -v $PWD:/project repomap-tool /project \
     --map-tokens 8192 \
     --mentioned-files 'main.py,commands.py' \
     --mentioned-idents 'main,command,cli'
   ```

2. **Identify related systems**
   ```bash
   docker run --rm -v $PWD:/project repomap-tool /project \
     --map-tokens 4096 \
     --mentioned-idents 'your_feature_keywords'
   ```

3. **Analyze existing patterns**
   ```bash
   docker run --rm -v $PWD:/project repomap-tool /project \
     --map-tokens 4096 \
     --mentioned-idents 'similar_existing_feature'
   ```

### **During Development:**

1. **Focus on specific files you're working on**
   ```bash
   docker run --rm -v $PWD:/project repomap-tool /project \
     --map-tokens 4096 \
     --chat-files 'file1.py,file2.py' \
     --mentioned-idents 'your_feature'
   ```

2. **Understand dependencies**
   ```bash
   docker run --rm -v $PWD:/project repomap-tool /project \
     --map-tokens 4096 \
     --mentioned-files 'dependency1.py,dependency2.py' \
     --mentioned-idents 'import,require,need'
   ```

3. **Check for conflicts**
   ```bash
   docker run --rm -v $PWD:/project repomap-tool /project \
     --map-tokens 4096 \
     --mentioned-idents 'conflicting_feature,similar_function'
   ```

### **After Development:**

1. **Verify integration**
   ```bash
   docker run --rm -v $PWD:/project repomap-tool /project \
     --map-tokens 4096 \
     --mentioned-files 'all_modified_files' \
     --mentioned-idents 'your_feature,integration'
   ```

2. **Check for missing pieces**
   ```bash
   docker run --rm -v $PWD:/project repomap-tool /project \
     --map-tokens 4096 \
     --mentioned-idents 'error,missing,undefined'
   ```

## 🎯 **Real-World Examples**

### **Example 1: Adding a New CLI Command**

```bash
# Understand command structure
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-files 'commands.py,args.py' \
  --mentioned-idents 'cmd_,def cmd_'

# Understand argument parsing
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'add_argument,parser,argparse'
```

### **Example 2: Adding a New API Endpoint**

```bash
# Understand API structure
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-files 'api.py,routes.py' \
  --mentioned-idents 'route,endpoint,api'

# Understand request handling
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'request,response,json'
```

### **Example 3: Adding a New Database Model**

```bash
# Understand model structure
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-files 'models.py,schema.py' \
  --mentioned-idents 'class,model,schema'

# Understand database patterns
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'database,db,table,column'
```

## 🚀 **Benefits for Feature Development**

### **1. Rapid Codebase Understanding**
- **No need to manually explore files**
- **Intelligent focus on relevant code**
- **Pattern recognition from existing features**

### **2. Consistent Implementation**
- **Follow existing patterns and conventions**
- **Use established helper functions**
- **Maintain code style consistency**

### **3. Dependency Awareness**
- **Know which files you'll need to modify**
- **Understand import dependencies**
- **Avoid breaking existing functionality**

### **4. Efficient Development**
- **Focus on implementation, not exploration**
- **Reduce time spent understanding the codebase**
- **Faster feature delivery**

### **5. Quality Assurance**
- **Understand error handling patterns**
- **Follow testing conventions**
- **Maintain code quality standards**

## 🎉 **Key Takeaways**

1. **Start with broad understanding** (8192 tokens)
2. **Focus on specific areas** (4096 tokens)
3. **Use dynamic context** as you work
4. **Follow existing patterns** you discover
5. **Leverage the intelligent filtering** to avoid irrelevant code

The docker-repomap tool gives you the same level of codebase understanding that aider's internal RepoMap provides, but as an external tool that you can use for any project! 🎯
