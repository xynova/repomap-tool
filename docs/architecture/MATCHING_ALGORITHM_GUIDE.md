# Docker RepoMap - Matching Algorithm Guide

## 🎯 **Is RepoMap Matching Exact?**

**No, it's not just exact matching!** The RepoMap system uses a sophisticated, multi-layered matching algorithm that goes far beyond simple exact string matching.

## 🔍 **How the Matching Actually Works**

### **1. Multi-Layer Matching Strategy**

The RepoMap system uses **multiple types of matching** simultaneously:

#### **A. Function/Class Definition Matching**
```python
# Finds where functions/classes are DEFINED
if tag.kind == "def":
    defines[tag.name].add(rel_fname)
```
- **Exact match** for function/class names
- **Tree-sitter parsing** for accurate identification
- **Cross-file discovery** of definitions

#### **B. Reference Matching**
```python
# Finds where functions/classes are USED
elif tag.kind == "ref":
    references[tag.name].append(rel_fname)
```
- **Exact match** for function/class references
- **Usage pattern discovery**
- **Dependency mapping**

#### **C. Path Component Matching**
```python
# Checks if file path contains the identifier
path_obj = Path(rel_fname)
path_components = set(path_obj.parts)
basename_with_ext = path_obj.name
basename_without_ext, _ = os.path.splitext(basename_with_ext)
components_to_check = path_components.union({basename_with_ext, basename_without_ext})

matched_idents = components_to_check.intersection(mentioned_idents)
```
- **File path matching** (e.g., `auth.py` matches `auth`)
- **Directory name matching** (e.g., `models/` matches `model`)
- **Case-insensitive matching**

#### **D. Filename Stem Matching**
```python
# Matches identifiers to filename stems
base = path.stem.lower()  # Use stem instead of with_suffix("").name
if len(base) >= 5:
    all_fnames[base].add(fname)
```
- **Filename stem matching** (e.g., `user_model.py` matches `user_model`)
- **Extension removal** for better matching
- **Minimum length filtering** (5+ characters)

### **2. Intelligent Weighting System**

The system doesn't just match - it **weights and prioritizes** matches:

#### **A. Mentioned Identifier Boosting**
```python
if ident in mentioned_idents:
    mul *= 10  # 10x importance boost
```
- **10x multiplier** for explicitly mentioned identifiers
- **Significant priority boost** for user-specified functions

#### **B. Naming Convention Recognition**
```python
is_snake = ("_" in ident) and any(c.isalpha() for c in ident)
is_kebab = ("-" in ident) and any(c.isalpha() for c in ident)
is_camel = any(c.isupper() for c in ident) and any(c.islower() for c in ident)

if (is_snake or is_kebab or is_camel) and len(ident) >= 8:
    mul *= 10  # 10x boost for well-named identifiers
```
- **Snake_case recognition** (`user_authentication`)
- **Kebab-case recognition** (`user-authentication`)
- **CamelCase recognition** (`userAuthentication`)
- **Length-based filtering** (8+ characters)

#### **C. Visibility and Scope Weighting**
```python
if ident.startswith("_"):
    mul *= 0.1  # Reduce importance of private functions

if len(defines[ident]) > 5:
    mul *= 0.1  # Reduce importance of overused functions
```
- **Private function de-prioritization** (starts with `_`)
- **Overuse penalty** (functions defined in >5 files)

### **3. PageRank-Based Ranking**

The system uses **PageRank algorithm** to determine file importance:

```python
ranked = nx.pagerank(G, weight="weight", **pers_args)
```

#### **A. Graph Construction**
- **Nodes**: Files in the codebase
- **Edges**: Function/class relationships
- **Weights**: Based on matching and usage patterns

#### **B. Relationship Types**
- **Definition-to-Reference**: Where functions are defined vs. used
- **Cross-File Dependencies**: How files relate to each other
- **Usage Frequency**: How often functions are referenced

### **4. Personalization and Context**

#### **A. Chat File Prioritization**
```python
if referencer in chat_rel_fnames:
    use_mul *= 50  # 50x boost for files in current chat
```
- **50x multiplier** for files currently in chat
- **Context-aware prioritization**

#### **B. Mentioned File Prioritization**
```python
if rel_fname in mentioned_fnames:
    current_pers = max(current_pers, personalize)
```
- **Personalization boost** for explicitly mentioned files
- **User intent recognition**

## 🚀 **Real-World Examples**

### **Example 1: Function Matching**

```bash
--mentioned-idents 'authenticate_user'
```

**What gets matched:**
- ✅ `def authenticate_user()` - **Definition match**
- ✅ `authenticate_user()` - **Reference match**
- ✅ `auth.py` - **Path component match**
- ✅ `user_authentication.py` - **Filename stem match**
- ✅ `authentication_utils.py` - **Path component match**

### **Example 2: Class Matching**

```bash
--mentioned-idents 'UserModel'
```

**What gets matched:**
- ✅ `class UserModel:` - **Definition match**
- ✅ `UserModel.create()` - **Reference match**
- ✅ `models/user_model.py` - **Path component match**
- ✅ `user_model.py` - **Filename stem match**
- ✅ `models/` - **Directory name match**

### **Example 3: Pattern Matching**

```bash
--mentioned-idents 'process_data'
```

**What gets matched:**
- ✅ `def process_data()` - **Definition match**
- ✅ `process_data()` - **Reference match**
- ✅ `data_processor.py` - **Filename stem match**
- ✅ `processors/` - **Directory name match**
- ✅ `data_processing.py` - **Filename stem match**

## 🎯 **Advanced Matching Features**

### **1. Cross-Language Support**
- **Python**: `def`, `class`, imports, references
- **JavaScript**: `function`, `class`, imports, references
- **TypeScript**: `function`, `class`, interfaces, references
- **Java**: `public class`, `public static`, references
- **Go**: `func`, `type`, references
- **And more...**

### **2. Import and Dependency Tracking**
```python
# Tracks import relationships
references[ident].append(rel_fname)
```
- **Import statement matching**
- **Cross-module dependencies**
- **Library usage patterns**

### **3. Context-Aware Filtering**
```python
# Filters out irrelevant matches
if len(ident) < 5:
    continue  # Skip short identifiers
```
- **Minimum length filtering**
- **Relevance scoring**
- **Noise reduction**

## 🔧 **Matching Algorithm Summary**

| Matching Type | What It Matches | Example |
|---------------|----------------|---------|
| **Definition** | Function/class definitions | `def authenticate_user()` |
| **Reference** | Function/class usage | `authenticate_user()` |
| **Path Component** | File/directory names | `auth.py`, `models/` |
| **Filename Stem** | File names without extension | `user_model.py` → `user_model` |
| **Import** | Import statements | `from auth import authenticate_user` |
| **Naming Convention** | Snake_case, CamelCase, etc. | `user_authentication`, `userAuthentication` |

## 🎉 **Key Benefits**

### **1. Intelligent Discovery**
- **Finds related code** even with different naming patterns
- **Cross-file relationship mapping**
- **Dependency chain discovery**

### **2. Context-Aware Prioritization**
- **User intent recognition**
- **Current work context**
- **Relevance scoring**

### **3. Robust Matching**
- **Multiple matching strategies**
- **Fallback mechanisms**
- **Noise filtering**

### **4. Performance Optimization**
- **Caching for speed**
- **Incremental updates**
- **Efficient graph algorithms**

## 🚀 **Best Practices**

### **1. Use Specific Identifiers**
```bash
# Good: Specific function names
--mentioned-idents 'authenticate_user,process_payment'

# Less effective: Generic terms
--mentioned-idents 'user,data'
```

### **2. Leverage Naming Conventions**
```bash
# The system recognizes these patterns:
--mentioned-idents 'user_authentication'  # snake_case
--mentioned-idents 'userAuthentication'   # camelCase
--mentioned-idents 'user-authentication'  # kebab-case
```

### **3. Combine with File Focus**
```bash
# Combine identifier matching with file matching
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-files 'src/auth.py' \
  --mentioned-idents 'authenticate,login'
```

The RepoMap matching system is **far more sophisticated than exact matching** - it's an intelligent, multi-layered algorithm that understands code structure, relationships, and context! 🎯
