# Adaptive Semantic Matching Integration

## 🎯 **Overview**

The `docker-repomap` tool now includes **Adaptive Semantic Matching** - a much more flexible approach than rigid dictionary-based matching. This feature learns from your actual codebase patterns and adapts to any terminology or naming conventions.

## 🚀 **Key Features**

### **1. Codebase Learning**
- **No predefined categories** - learns from your actual identifiers
- **Adapts to any domain** - works with `widget`, `gadget`, `doohickey`, or any terminology
- **Discovers patterns** - finds semantic relationships automatically

### **2. TF-IDF Based Similarity**
- **Word importance scoring** - common words get lower weight, distinctive words get higher weight
- **Context-aware matching** - understands the semantic context of your codebase
- **Cosine similarity** - provides meaningful similarity scores

### **3. Automatic Clustering**
- **Groups related functionality** - discovers which identifiers are semantically related
- **Pattern recognition** - identifies naming patterns and conventions
- **Relationship discovery** - finds connections you might not have noticed

## 🔧 **Usage**

### **Basic Adaptive Semantic Matching**
```bash
docker run --rm -v $PWD:/project repomap-tool /project \
    --mentioned-idents "process,valid,create" \
    --adaptive-semantic \
    --semantic-threshold 0.1
```

### **Domain-Specific Terms**
```bash
docker run --rm -v $PWD:/project repomap-tool /project \
    --mentioned-idents "widget,gadget,doohickey" \
    --adaptive-semantic \
    --semantic-threshold 0.1
```

### **Combined Fuzzy + Adaptive Semantic**
```bash
docker run --rm -v $PWD:/project repomap-tool /project \
    --mentioned-idents "auth,data,file" \
    --fuzzy-match \
    --fuzzy-threshold 60 \
    --adaptive-semantic \
    --semantic-threshold 0.1
```

### **Complex Queries**
```bash
docker run --rm -v $PWD:/project repomap-tool /project \
    --mentioned-idents "connection pool,rate limit,audit trail" \
    --adaptive-semantic \
    --semantic-threshold 0.2
```

## 📊 **Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--adaptive-semantic` | flag | false | Enable adaptive semantic matching |
| `--semantic-threshold` | float | 0.1 | Similarity threshold (0.0-1.0) |

## 🎯 **Why This Approach is Better**

### **vs Rigid Dictionaries**
- ❌ **Rigid**: Fixed categories that may not match your codebase
- ❌ **Limited**: Misses domain-specific terminology
- ❌ **Static**: Doesn't adapt to different codebases
- ❌ **Manual**: Requires maintenance and updates

- ✅ **Adaptive**: Learns from your actual codebase
- ✅ **Flexible**: Handles any terminology
- ✅ **Dynamic**: Adapts to naming patterns
- ✅ **Automatic**: Discovers relationships automatically

### **vs Simple Fuzzy Matching**
- ❌ **Fuzzy**: Only matches string similarity
- ❌ **Context-blind**: Doesn't understand semantic meaning
- ❌ **Limited scope**: Misses conceptual relationships

- ✅ **Semantic**: Understands functional relationships
- ✅ **Context-aware**: Considers codebase patterns
- ✅ **Comprehensive**: Finds both exact and conceptual matches

## 🔍 **Example Results**

### **Query: "process"**
```
Semantic matches for 'process':
  - data_processor (score: 0.707)
  - doohickey_processor (score: 0.707)
  - batch_processor (score: 0.707)
  - stream_processor (score: 0.707)
```

### **Query: "widget"**
```
Semantic matches for 'widget':
  - widget_factory (score: 0.707)
  - widget_builder (score: 0.707)
  - widget_validator (score: 0.707)
```

### **Query: "connection pool"**
```
Semantic matches for 'connection pool':
  - connection_pool (score: 1.000)
  - database_connection_pool (score: 0.752)
  - db_connection (score: 0.404)
```

## 🧪 **Testing**

Run the integrated test suite:
```bash
./test_integrated_adaptive.sh
```

This will test:
1. Basic adaptive semantic matching
2. Domain-specific terms
3. Combined fuzzy + adaptive semantic
4. Complex queries
5. Low threshold scenarios

## 🎉 **Benefits**

### **For LLM Agents**
- **Better context discovery** - finds semantically related code
- **Reduced manual specification** - learns from codebase patterns
- **Improved accuracy** - understands functional relationships
- **Domain adaptation** - works with any terminology

### **For Developers**
- **Faster code exploration** - discovers related functionality
- **Better refactoring support** - finds similar patterns
- **Improved documentation** - groups related functions
- **Reduced cognitive load** - automatic relationship discovery

## 🔮 **Future Enhancements**

1. **Semantic Clustering Visualization** - show related code groups
2. **Query Suggestions** - suggest related terms based on codebase
3. **Pattern Recognition** - identify common architectural patterns
4. **Performance Optimization** - caching and lazy loading
5. **Custom Training** - learn from specific codebase patterns

This adaptive approach makes `docker-repomap` much more intelligent and flexible for real-world codebases! 🎯
