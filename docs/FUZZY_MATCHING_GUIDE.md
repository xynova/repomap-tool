# RepoMap-Tool - Fuzzy Matching Feature

## 🎯 **Overview**

The RepoMap-Tool tool now includes intelligent fuzzy matching capabilities that enable discovery of related identifiers in codebases. This feature makes it much easier to find relevant code when you don't know the exact function or class names.

## 🚀 **Key Features**

- **Multiple Matching Strategies**: Prefix, substring, Levenshtein distance, and word-based matching
- **Configurable Thresholds**: Adjust similarity requirements (0-100%)
- **Intelligent Discovery**: Find related functions and classes automatically
- **Performance Optimized**: Caching and efficient algorithms
- **Seamless Integration**: Works with existing RepoMap functionality

## 📖 **Usage**

### **Basic Fuzzy Matching**

```bash
# Find authentication-related functions
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'auth' \
  --fuzzy-match
```

### **Advanced Configuration**

```bash
# Custom threshold and strategies
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'process' \
  --fuzzy-match \
  --fuzzy-threshold 80 \
  --fuzzy-strategies 'prefix,substring,levenshtein'
```

### **Command Line Options**

| Option | Description | Default |
|--------|-------------|---------|
| `--fuzzy-match` | Enable fuzzy matching | `false` |
| `--fuzzy-threshold` | Similarity threshold (0-100) | `70` |
| `--fuzzy-strategies` | Comma-separated list of strategies | `prefix,substring,levenshtein` |

## 🔍 **Matching Strategies**

### **1. Prefix Matching**
Matches identifiers that start with the query.

**Example**: `auth` → `authenticate_user`, `auth_utils`, `authorization`

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'auth' \
  --fuzzy-match \
  --fuzzy-strategies 'prefix'
```

### **2. Substring Matching**
Matches identifiers containing the query.

**Example**: `process` → `process_data`, `data_processor`, `preprocessing`

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'process' \
  --fuzzy-match \
  --fuzzy-strategies 'substring'
```

### **3. Levenshtein Distance**
Matches based on edit distance using multiple algorithms.

**Example**: `authentication` → `authenticate_user`, `user_authentication`

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'authentication' \
  --fuzzy-match \
  --fuzzy-strategies 'levenshtein'
```

### **4. Word-Based Matching**
Matches based on word overlap in identifiers.

**Example**: `user auth` → `user_authentication`, `authenticate_user`

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'user auth' \
  --fuzzy-match \
  --fuzzy-strategies 'word'
```

## 🎛️ **Threshold Configuration**

### **High Threshold (80-100%)**
Only very close matches.

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'validate' \
  --fuzzy-match \
  --fuzzy-threshold 90
```

### **Medium Threshold (60-80%)**
Balanced precision and recall.

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'process' \
  --fuzzy-match \
  --fuzzy-threshold 70
```

### **Low Threshold (30-60%)**
Discovery mode for exploration.

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'test' \
  --fuzzy-match \
  --fuzzy-threshold 50
```

## 🔧 **Real-World Examples**

### **Example 1: Authentication Discovery**

```bash
# Find all authentication-related functions
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'auth' \
  --fuzzy-match \
  --map-tokens 4096
```

**Results**: Finds `authenticate_user`, `user_authentication`, `auth_utils`, `OAuthCallbackHandler`, etc.

### **Example 2: Data Processing Functions**

```bash
# Find data processing functions
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'process' \
  --fuzzy-match \
  --map-tokens 4096
```

**Results**: Finds `process_data`, `data_processor`, `process_changes`, `process_markdown`, etc.

### **Example 3: Validation Functions**

```bash
# Find validation functions with high precision
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'validate' \
  --fuzzy-match \
  --fuzzy-threshold 80 \
  --map-tokens 2048
```

**Results**: Finds `validate_environment`, `validate_variables`, `_validate_color_settings`, etc.

### **Example 4: Test Discovery**

```bash
# Find test-related functions for exploration
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'test' \
  --fuzzy-match \
  --fuzzy-threshold 50 \
  --map-tokens 2048
```

**Results**: Finds many test functions for comprehensive testing overview.

## 🎯 **Use Cases**

### **1. Code Exploration**
When exploring a new codebase, use fuzzy matching to discover related functions.

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'api' \
  --fuzzy-match \
  --fuzzy-threshold 60
```

### **2. Refactoring**
Find all related functions before refactoring.

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'database' \
  --fuzzy-match \
  --map-tokens 8192
```

### **3. Feature Development**
Discover existing patterns when implementing new features.

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'config' \
  --fuzzy-match \
  --map-tokens 4096
```

### **4. LLM Integration**
Provide LLMs with intelligent context discovery.

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'user,profile,settings' \
  --fuzzy-match \
  --map-tokens 4096
```

## 🔄 **Integration with Existing Features**

### **Combined with Mentioned Files**

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'auth' \
  --mentioned-files 'aider/repomap.py,aider/coders/base_coder.py' \
  --fuzzy-match \
  --map-tokens 4096
```

### **Dynamic Context Generation**

```bash
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'process' \
  --chat-files 'current_file.py' \
  --fuzzy-match \
  --map-tokens 4096
```

## 📊 **Performance**

### **Speed**
- Fuzzy matching adds < 1 second to processing time
- Caching reduces repeated computation
- Efficient algorithms for large codebases

### **Memory Usage**
- Minimal memory overhead
- Intelligent caching strategies
- Scalable to large projects

### **Accuracy**
- Configurable precision vs. recall trade-offs
- Multiple algorithms for different use cases
- Intelligent scoring system

## 🛠️ **Technical Details**

### **Scoring Algorithm**
1. **Exact Match**: 100% score
2. **Prefix Match**: 70-95% score (based on length)
3. **Substring Match**: 60-85% score (based on position)
4. **Levenshtein**: Multiple algorithms combined
5. **Word Match**: Based on word overlap ratio

### **Caching**
- Results cached by query + threshold + strategies
- Automatic cache invalidation
- Memory-efficient storage

### **Identifier Extraction**
- Function and class names from Python files
- Regex-based extraction for performance
- Extensible to other languages

## 🚀 **Future Enhancements**

### **Planned Features**
- Support for more programming languages
- Semantic similarity using embeddings
- Advanced caching strategies
- Integration with IDE plugins

### **API Enhancements**
- REST API support for fuzzy matching
- Batch processing capabilities
- Real-time matching suggestions

## 📝 **Examples Script**

Run the comprehensive examples script:

```bash
./fuzzy_matching_examples.sh
```

This script demonstrates all major features and use cases.

## 🎯 **Best Practices**

### **1. Start with Discovery**
Use low thresholds (50-60%) for initial exploration.

### **2. Refine with Precision**
Use high thresholds (80-90%) for specific tasks.

### **3. Combine Strategies**
Use multiple strategies for comprehensive results.

### **4. Monitor Performance**
Adjust token budgets based on project size.

### **5. Cache Results**
Reuse results for repeated queries.

## 🔗 **Related Documentation**

- [Main README](README.md)
- [CLI Usage](README-CLI.md)
- [API Documentation](README-API.md)
- [Dynamic Context](README-DYNAMIC.md)

---

**Fuzzy matching makes RepoMap-Tool more intelligent and user-friendly! 🎯**
