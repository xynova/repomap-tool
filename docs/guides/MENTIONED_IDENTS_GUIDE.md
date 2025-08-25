# Docker RepoMap - Mentioned Identifiers Guide

## 🎯 **What is `--mentioned-idents`?**

`--mentioned-idents` is a powerful feature that allows you to **focus the repo map on specific functions, classes, variables, or other code identifiers** that you're interested in. It's like telling the tool: "I want to see code related to these specific functions/classes."

## 🔍 **How It Works**

### **1. Identifier Extraction**
The system extracts identifiers from your input using these patterns:
- **Function names**: `process_data`, `authenticate_user`, `save_file`
- **Class names**: `UserModel`, `DatabaseConnection`, `ConfigManager`
- **Variable names**: `user_data`, `config_settings`, `api_client`
- **Method names**: `get_user`, `set_config`, `validate_input`

### **2. Smart Matching**
The system then finds files that contain these identifiers and **boosts their importance** in the repo map by:
- **10x multiplier** for mentioned identifiers
- **Path component matching** (if a file path contains the identifier)
- **Function/class definition matching**
- **Reference matching** (where the identifier is used)

### **3. Personalization**
Files containing mentioned identifiers get **higher priority** in the repo map, ensuring you see the most relevant code.

## 🚀 **Practical Examples**

### **Example 1: Focus on Authentication Functions**

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'authenticate,login,logout,register'
```

**What this does:**
- Finds files containing `authenticate`, `login`, `logout`, `register` functions
- Boosts those files' importance in the repo map
- Shows you authentication-related code

### **Example 2: Focus on Database Operations**

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'save,load,query,delete,update'
```

**What this does:**
- Finds files with database operation functions
- Shows you data persistence patterns
- Highlights CRUD operations

### **Example 3: Focus on Configuration Management**

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'config,settings,env,load_config'
```

**What this does:**
- Finds configuration-related code
- Shows settings management patterns
- Highlights environment handling

## 🎯 **How It Differs from `--mentioned-files`**

| Feature | `--mentioned-files` | `--mentioned-idents` |
|---------|-------------------|---------------------|
| **What it matches** | File paths/names | Function/class names |
| **Example** | `src/auth.py` | `authenticate_user` |
| **Use case** | "I want to see this specific file" | "I want to see code related to this function" |
| **Scope** | Exact file match | Cross-file function matching |

## 🔧 **Advanced Usage Patterns**

### **1. Function-Specific Focus**

```bash
# Focus on specific functions you're working on
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'process_data,validate_input,format_output'
```

### **2. Class Hierarchy Focus**

```bash
# Focus on specific classes and their methods
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'User,UserModel,UserService,get_user,create_user'
```

### **3. API Endpoint Focus**

```bash
# Focus on API-related functions
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'get,post,put,delete,api,route'
```

### **4. Error Handling Focus**

```bash
# Focus on error handling patterns
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'error,exception,handle,log,raise'
```

## 🎯 **Real-World Scenarios**

### **Scenario 1: Debugging a Specific Function**

```bash
# You're debugging the `process_payment` function
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'process_payment,validate_payment,payment_error'
```

### **Scenario 2: Understanding Data Flow**

```bash
# You want to understand how data flows through the system
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'transform_data,process_data,validate_data,save_data'
```

### **Scenario 3: Learning from Existing Patterns**

```bash
# You want to see how other features are implemented
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'export,import,backup,restore'
```

## 🔍 **How the Algorithm Works**

### **1. Identifier Detection**
```python
# The system extracts identifiers from your input
def get_ident_mentions(text):
    # Split on non-alphanumeric characters
    words = set(re.split(r"\W+", text))
    return words
```

### **2. File Matching**
```python
# Files are matched based on:
# - Function/class definitions containing the identifier
# - File paths containing the identifier
# - References to the identifier in the code
```

### **3. Importance Boosting**
```python
# Files with mentioned identifiers get boosted:
if ident in mentioned_idents:
    mul *= 10  # 10x importance boost
```

## 🎯 **Best Practices**

### **1. Use Specific Identifiers**
```bash
# Good: Specific function names
--mentioned-idents 'authenticate_user,process_payment,validate_input'

# Less effective: Generic terms
--mentioned-idents 'user,data,file'
```

### **2. Combine with File Focus**
```bash
# Combine identifier focus with file focus
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-files 'src/auth.py' \
  --mentioned-idents 'authenticate,login'
```

### **3. Use Related Identifiers**
```bash
# Include related functions/classes
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'User,UserModel,create_user,update_user,delete_user'
```

### **4. Progressive Refinement**
```bash
# Start broad, then focus
# Step 1: Broad understanding
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'auth,user'

# Step 2: Specific focus
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'authenticate_user,validate_credentials'
```

## 🎉 **Benefits**

### **1. Intelligent Focus**
- **Automatic discovery** of related code
- **Cross-file relationships** between functions
- **Smart prioritization** of relevant code

### **2. Efficient Exploration**
- **No need to know file names** in advance
- **Function-based navigation** through codebase
- **Pattern recognition** across files

### **3. Context-Aware Analysis**
- **Related function discovery**
- **Dependency mapping**
- **Usage pattern identification**

## 🚀 **Quick Reference**

### **Common Identifier Patterns**
```bash
# Functions
--mentioned-idents 'function_name,another_function'

# Classes
--mentioned-idents 'ClassName,AnotherClass'

# Methods
--mentioned-idents 'method_name,another_method'

# Variables
--mentioned-idents 'variable_name,config_setting'

# Mixed
--mentioned-idents 'User,authenticate,login,user_data'
```

### **Combined Usage**
```bash
# Combine with other parameters
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-files 'src/main.py' \
  --mentioned-idents 'process_data,validate' \
  --chat-files 'src/utils.py'
```

The `--mentioned-idents` feature gives you **function-level precision** in focusing your codebase analysis, making it perfect for understanding specific functionality or debugging particular features! 🎯
