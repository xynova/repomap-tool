# Docker RepoMap - Existing Identifiers Guide

## 🎯 **Important: Identifiers Must Exist in the Codebase**

You're absolutely right! The identifiers you pass to `--mentioned-idents` **must actually exist in the codebase** for the matching to be effective. The RepoMap system can only match what's actually there.

## 🔍 **How to Find Existing Identifiers**

### **1. Use the Tool to Discover Identifiers**

```bash
# Start with a broad search to see what's available
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 8192 \
  --verbose
```

This will show you all the functions, classes, and identifiers in the codebase.

### **2. Use File-Specific Searches**

```bash
# Focus on specific files to see their identifiers
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-files 'src/main.py,src/auth.py' \
  --verbose
```

### **3. Use Pattern-Based Discovery**

```bash
# Find all authentication-related functions
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'auth,login,user' \
  --verbose
```

## 🚀 **Practical Examples**

### **Example 1: Discovering What Exists**

Let's say you want to work on authentication. First, discover what authentication functions actually exist:

```bash
# Step 1: Find authentication-related code
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'auth,login,user'
```

**Output shows:**
- `authenticate_user()` - ✅ **Exists**
- `login_handler()` - ✅ **Exists**
- `validate_credentials()` - ✅ **Exists**
- `process_payment()` - ❌ **Doesn't exist in this codebase**

### **Example 2: Using Only Existing Identifiers**

```bash
# Good: Use identifiers that actually exist
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'get_repo_map,process_data,validate_input'
```

**What happens:**
- ✅ `get_repo_map` - **Found and boosted**
- ✅ `process_data` - **Found and boosted** (if it exists)
- ✅ `validate_input` - **Found and boosted** (if it exists)

### **Example 3: Non-Existent Identifiers**

```bash
# Less effective: Using identifiers that don't exist
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'authenticate_user,process_payment,validate_input'
```

**What happens:**
- ❌ `authenticate_user` - **Not found, no boost**
- ❌ `process_payment` - **Not found, no boost**
- ❌ `validate_input` - **Not found, no boost**
- Result: **Same as no mentioned-idents at all**

## 🔧 **Discovery Strategies**

### **1. Start with File Names**

```bash
# Look at files with relevant names
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-files 'auth.py,user.py,login.py'
```

### **2. Use Directory Names**

```bash
# Look at entire directories
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-files 'auth/,models/,api/'
```

### **3. Use Common Patterns**

```bash
# Use common naming patterns
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'get_,set_,create_,update_,delete_'
```

## 🎯 **Best Practices**

### **1. Discover First, Then Focus**

```bash
# Step 1: Discover what exists
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 8192 \
  --mentioned-files 'src/' \
  --verbose

# Step 2: Focus on discovered identifiers
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'discovered_function1,discovered_function2'
```

### **2. Use Progressive Refinement**

```bash
# Step 1: Broad search
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'auth'

# Step 2: Specific focus
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'authenticate_user,validate_credentials'
```

### **3. Combine with File Focus**

```bash
# Combine file focus with identifier focus
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-files 'src/auth.py' \
  --mentioned-idents 'authenticate,login'
```

## 🚀 **Real-World Workflow**

### **Scenario: Adding a New Feature**

```bash
# Step 1: Understand the codebase structure
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 8192 \
  --mentioned-files 'main.py,commands.py'

# Step 2: Discover existing patterns
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-idents 'cmd_,def cmd_'

# Step 3: Focus on specific area
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 4096 \
  --mentioned-files 'commands.py' \
  --mentioned-idents 'existing_command1,existing_command2'
```

## 🎯 **Common Mistakes to Avoid**

### **1. Assuming Identifiers Exist**

```bash
# ❌ Bad: Assuming functions exist
--mentioned-idents 'process_payment,validate_credit_card'

# ✅ Good: Discover first, then use
--mentioned-idents 'get_user,authenticate'  # Only if they exist
```

### **2. Using Generic Terms**

```bash
# ❌ Bad: Too generic
--mentioned-idents 'user,data,file'

# ✅ Good: Specific existing identifiers
--mentioned-idents 'UserModel,process_data,save_file'
```

### **3. Not Discovering First**

```bash
# ❌ Bad: Jumping straight to specific identifiers
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'specific_function'

# ✅ Good: Discover first
docker run --rm -v $PWD:/project repomap-tool /project \
  --map-tokens 8192 \
  --verbose
# Then use discovered identifiers
```

## 🎉 **Key Takeaways**

1. **Identifiers must exist** in the codebase to be effective
2. **Discover first** using broad searches and verbose output
3. **Use progressive refinement** from broad to specific
4. **Combine strategies** (files + identifiers) for better results
5. **Verify existence** before using specific identifiers

The RepoMap system is powerful, but it can only work with what actually exists in your codebase! 🎯
