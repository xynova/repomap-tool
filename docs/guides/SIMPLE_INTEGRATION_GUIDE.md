# Docker RepoMap Integration: Simple Guide

## 🎯 **What Does This Tool Do?**

Think of Docker RepoMap as a **smart code detective** that helps you find related pieces of code in your project. It's like having a super-powered search that understands not just exact matches, but also similar concepts and patterns.

## 🔍 **The Three Detective Methods**

### 1. **The Fuzzy Detective** 🔍
*"Find things that look similar"*

```
You search for: "auth"
Fuzzy Detective finds:
✅ authentication (starts with "auth")
✅ auth_token (contains "auth") 
✅ authorize (similar spelling)
✅ user_auth (has "auth" in it)
```

**How it works:**
- Looks for exact matches first
- Then finds things that start with your search term
- Then finds things that contain your search term
- Finally finds things that are spelled similarly

### 2. **The Semantic Detective** 🧠
*"Find things that mean similar things"*

```
You search for: "user validation"
Semantic Detective finds:
✅ authenticate_user (does user validation)
✅ validate_credentials (similar concept)
✅ check_user_permissions (related to user validation)
✅ verify_user_input (validates user data)
```

**How it works:**
- Learns from your actual codebase
- Understands that "validate" and "check" mean similar things
- Groups related concepts together
- Finds patterns you might not notice

### 3. **The Hybrid Detective** 🚀
*"Use both methods for best results"*

```
You search for: "data processing"
Hybrid Detective finds:
✅ process_data (exact match)
✅ data_processor (fuzzy match)
✅ transform_dataset (semantic match)
✅ batch_processing (conceptually related)
```

**How it works:**
- Combines fuzzy and semantic approaches
- Gives you the best of both worlds
- More comprehensive results
- Smarter ranking of results

## 🏗️ **How It All Works Together**

```
┌─────────────────┐
│   Your Code     │
│   (Project)     │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Docker Tool    │
│  (Container)    │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Code Scanner   │
│  (Tree-sitter)  │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Smart Matchers │
│  ┌─────────────┐│
│  │   Fuzzy     ││
│  │  Semantic   ││
│  │   Hybrid    ││
│  └─────────────┘│
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Results Report │
│  (Ranked List)  │
└─────────────────┘
```

## 🎮 **Real-World Example**

Let's say you're working on a web application and want to find all the code related to user authentication:

### **Step 1: Run the Tool**
```bash
docker run -v /path/to/your/app:/project repomap-tool /project \
    --mentioned-idents "auth,login,user" \
    --fuzzy-match \
    --adaptive-semantic
```

### **Step 2: Get Results**
```
🔍 Found 15 related identifiers:

Fuzzy Matches:
- authentication.py (score: 95)
- auth_middleware.py (score: 90)
- login_handler.py (score: 85)

Semantic Matches:
- user_verification.py (score: 0.8)
- credential_checker.py (score: 0.7)
- session_manager.py (score: 0.6)

Hybrid Matches:
- auth_service.py (combined score: 92)
- login_validator.py (combined score: 88)
```

### **Step 3: Use the Results**
Now you know exactly which files to look at for authentication-related code!

## ⚙️ **Configuration Made Simple**

### **Basic Setup**
```bash
# Just fuzzy matching (fastest)
--fuzzy-match --fuzzy-threshold 70

# Just semantic matching (smartest)
--adaptive-semantic --semantic-threshold 0.2

# Both together (best results)
--fuzzy-match --adaptive-semantic
```

### **Thresholds Explained**
- **Fuzzy Threshold (0-100)**: How similar strings need to be
  - 90 = Very strict (almost exact matches)
  - 70 = Medium (good balance)
  - 50 = Very loose (lots of results)

- **Semantic Threshold (0.0-1.0)**: How similar concepts need to be
  - 0.8 = Very strict (very similar concepts)
  - 0.3 = Medium (good balance)
  - 0.1 = Very loose (related concepts)

## 🚀 **Quick Start Examples**

### **Find API-related code:**
```bash
docker run -v /path/to/project:/project repomap-tool /project \
    --mentioned-idents "api,endpoint,route" \
    --fuzzy-match \
    --fuzzy-threshold 60
```

### **Find database-related code:**
```bash
docker run -v /path/to/project:/project repomap-tool /project \
    --mentioned-idents "database,query,model" \
    --adaptive-semantic \
    --semantic-threshold 0.2
```

### **Find everything related to "user management":**
```bash
docker run -v /path/to/project:/project repomap-tool /project \
    --mentioned-idents "user,profile,account" \
    --fuzzy-match \
    --fuzzy-threshold 70 \
    --adaptive-semantic \
    --semantic-threshold 0.15
```

## 🎯 **When to Use Each Method**

| Use Case | Best Method | Why |
|----------|-------------|-----|
| **Exact names** | Fuzzy | You know the exact function/class name |
| **Similar concepts** | Semantic | You want related functionality |
| **Unknown codebase** | Hybrid | Best coverage for exploration |
| **Fast search** | Fuzzy | Quickest results |
| **Deep analysis** | Semantic | Most intelligent matches |

## 🔧 **Integration with Your Workflow**

### **With Aider (AI Pair Programming)**
```
1. You ask Aider: "Find all authentication code"
2. Aider uses Docker RepoMap to scan your codebase
3. Aider gets intelligent results about auth-related code
4. Aider can suggest improvements or help you understand the code
```

### **With Your IDE**
```
1. You're working on a new feature
2. You run Docker RepoMap to find related code
3. You understand the existing patterns
4. You write better, more consistent code
```

## 🎉 **Benefits You Get**

✅ **Save Time**: Find related code instantly instead of manually searching

✅ **Discover Patterns**: See how your codebase is organized

✅ **Avoid Duplication**: Find existing code before writing new code

✅ **Better Understanding**: See relationships between different parts of your code

✅ **Consistent Code**: Learn from existing naming patterns

✅ **Smart Suggestions**: Get intelligent recommendations for your code

## 🚨 **Common Gotchas**

❌ **Too strict thresholds**: You might miss relevant code
✅ **Solution**: Start with medium thresholds (70 for fuzzy, 0.2 for semantic)

❌ **Too broad searches**: You might get too many results
✅ **Solution**: Use more specific search terms

❌ **Not using both methods**: You might miss some relevant code
✅ **Solution**: Try hybrid matching for best results

## 🔮 **Pro Tips**

1. **Start broad, then narrow**: Use loose thresholds first, then tighten them
2. **Use multiple terms**: Search for "auth,login,user" instead of just "auth"
3. **Try different combinations**: Experiment with fuzzy vs semantic vs hybrid
4. **Save good searches**: Keep track of search terms that work well for your project
5. **Use with Aider**: Combine with AI pair programming for maximum benefit

---

*This tool makes understanding and navigating complex codebases much easier by combining multiple intelligent search strategies!*
