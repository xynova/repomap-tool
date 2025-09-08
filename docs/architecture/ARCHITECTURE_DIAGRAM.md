# RepoMap-Tool: Technical Architecture

## 🔧 **System Components Overview**

```mermaid
graph TB
    subgraph "User Interface Layer"
        A[User Command] --> B[Docker Container]
        B --> C[CLI Interface]
    end
    
    subgraph "Core Processing Layer"
        C --> D[External RepoMap]
        D --> E[RepoMap Core]
        E --> F[Code Parser]
        F --> G[Tree-sitter]
    end
    
    subgraph "Analysis Layer"
        G --> H[Identifier Extraction]
        H --> I[Code Analysis]
        I --> J[Pattern Recognition]
    end
    
    subgraph "Matching Engine Layer"
        J --> K[Fuzzy Matcher]
        J --> L[Semantic Matcher]
        J --> M[Hybrid Matcher]
    end
    
    subgraph "Output Layer"
        K --> N[Results Aggregator]
        L --> N
        M --> N
        N --> O[Formatted Output]
    end
    
    style A fill:#e3f2fd
    style B fill:#f3e5f5
    style E fill:#e8f5e8
    style K fill:#fff3e0
    style L fill:#fff3e0
    style M fill:#fff3e0
    style O fill:#fce4ec
```

## 🔄 **Detailed Data Flow**

```mermaid
sequenceDiagram
    participant User
    participant Docker
    participant RepoMap
    participant Parser
    participant Matchers
    participant Cache
    participant Output

    User->>Docker: docker run repomap-tool
    Docker->>RepoMap: Initialize with parameters
    
    RepoMap->>Cache: Check for existing analysis
    alt Cache Hit
        Cache->>RepoMap: Return cached results
    else Cache Miss
        RepoMap->>Parser: Parse codebase
        Parser->>RepoMap: Return identifiers
        
        RepoMap->>Matchers: Process query
        
        par Fuzzy Matching
            Matchers->>Matchers: Apply string similarity
            Matchers->>RepoMap: Return fuzzy results
        and Semantic Matching
            Matchers->>Matchers: TF-IDF analysis
            Matchers->>Matchers: Vector similarity
            Matchers->>RepoMap: Return semantic results
        and Hybrid Matching
            Matchers->>Matchers: Combine approaches
            Matchers->>RepoMap: Return hybrid results
        end
        
        RepoMap->>Cache: Store results
    end
    
    RepoMap->>Output: Aggregate all results
    Output->>Docker: Format output
    Docker->>User: Display results
```

## 🧠 **Matching Algorithm Details**

### **Fuzzy Matching Process**

```mermaid
graph LR
    A[Query: "auth"] --> B[String Normalization]
    B --> C[Multiple Strategies]
    
    C --> D[Prefix Match]
    C --> E[Substring Match]
    C --> F[Levenshtein]
    C --> G[Word Overlap]
    
    D --> H[Score Calculation]
    E --> H
    F --> H
    G --> H
    
    H --> I[Threshold Filter]
    I --> J[Ranked Results]
    
    style A fill:#e3f2fd
    style C fill:#fff3e0
    style J fill:#e8f5e8
```

### **Semantic Matching Process**

```mermaid
graph TB
    A[Codebase] --> B[Identifier Collection]
    B --> C[Word Extraction]
    C --> D[TF-IDF Calculation]
    
    D --> E[Term Frequency]
    D --> F[Inverse Document Frequency]
    
    E --> G[Vector Creation]
    F --> G
    
    G --> H[Query Vectorization]
    H --> I[Cosine Similarity]
    I --> J[Similarity Scores]
    J --> K[Threshold Filtering]
    K --> L[Semantic Results]
    
    style A fill:#e8f5e8
    style D fill:#fff3e0
    style I fill:#f3e5f5
    style L fill:#e1f5fe
```

### **Hybrid Matching Process**

```mermaid
graph LR
    A[Query] --> B[Hybrid Matcher]
    
    B --> C[Fuzzy Analysis]
    B --> D[Semantic Analysis]
    
    C --> E[String Scores]
    D --> F[Semantic Scores]
    
    E --> G[Score Combination]
    F --> G
    
    G --> H[Weighted Ranking]
    H --> I[Final Results]
    
    style A fill:#e3f2fd
    style B fill:#fff3e0
    style G fill:#f3e5f5
    style I fill:#e8f5e8
```

## 🏗️ **Component Architecture**

### **Core Components**

```mermaid
graph TB
    subgraph "DockerRepoMap Class"
        A[__init__] --> B[Initialize Matchers]
        B --> C[Setup RepoMap]
        C --> D[Configure Cache]
    end
    
    subgraph "FuzzyMatcher Class"
        E[__init__] --> F[Set Threshold]
        F --> G[Configure Strategies]
        G --> H[match_identifiers]
    end
    
    subgraph "AdaptiveSemanticMatcher Class"
        I[__init__] --> J[Setup TF-IDF]
        J --> K[learn_from_identifiers]
        K --> L[find_semantic_matches]
    end
    
    subgraph "HybridMatcher Class"
        M[__init__] --> N[Initialize Both]
        N --> O[combine_results]
        O --> P[weighted_ranking]
    end
    
    style A fill:#e3f2fd
    style E fill:#fff3e0
    style I fill:#fff3e0
    style M fill:#fff3e0
```

### **Data Structures**

```mermaid
graph LR
    A[Identifier Set] --> B[Word Dictionary]
    B --> C[TF-IDF Vectors]
    C --> D[Similarity Matrix]
    
    E[Query String] --> F[Processed Query]
    F --> G[Query Vector]
    G --> H[Match Results]
    
    style A fill:#e8f5e8
    style C fill:#fff3e0
    style H fill:#fce4ec
```

## ⚡ **Performance Characteristics**

### **Time Complexity**

| Operation | Fuzzy | Semantic | Hybrid |
|-----------|-------|----------|--------|
| **Initialization** | O(1) | O(n) | O(n) |
| **Single Query** | O(n) | O(n) | O(n) |
| **Batch Queries** | O(n×m) | O(n×m) | O(n×m) |
| **Cache Lookup** | O(1) | O(1) | O(1) |

*Where n = number of identifiers, m = number of queries*

### **Memory Usage**

```mermaid
graph LR
    A[Codebase Size] --> B[Identifier Count]
    B --> C[Memory Usage]
    
    C --> D[Fuzzy: Low]
    C --> E[Semantic: Medium]
    C --> F[Hybrid: Medium]
    
    style A fill:#e8f5e8
    style C fill:#fff3e0
    style D fill:#e1f5fe
    style E fill:#f3e5f5
    style F fill:#fce4ec
```

## 🔧 **Configuration Architecture**

### **Parameter Flow**

```mermaid
graph TB
    A[CLI Arguments] --> B[Argument Parser]
    B --> C[Configuration Object]
    C --> D[DockerRepoMap]
    
    D --> E[FuzzyMatcher Config]
    D --> F[SemanticMatcher Config]
    D --> G[HybridMatcher Config]
    
    E --> H[Threshold Settings]
    F --> I[TF-IDF Settings]
    G --> J[Weight Settings]
    
    style A fill:#e3f2fd
    style C fill:#fff3e0
    style H fill:#e8f5e8
    style I fill:#f3e5f5
    style J fill:#fce4ec
```

### **Default Configuration**

```yaml
# Fuzzy Matching Defaults
fuzzy_match: false
fuzzy_threshold: 70
fuzzy_strategies: ["prefix", "substring", "levenshtein"]

# Semantic Matching Defaults
adaptive_semantic: false
semantic_threshold: 0.1

# Hybrid Matching Defaults
hybrid_match: false
weight_fuzzy: 0.6
weight_semantic: 0.4

# General Settings
verbose: true
cache_results: true
```

## 🔄 **Integration Points**

### **With Aider Core**

```mermaid
graph TB
    A[Aider Core] --> B[RepoMap Module]
    B --> C[External RepoMap]
    C --> D[Docker Container]
    
    D --> E[Fuzzy Matcher]
    D --> F[Semantic Matcher]
    D --> G[Hybrid Matcher]
    
    E --> H[Results]
    F --> H
    G --> H
    
    H --> I[Code Analysis]
    I --> J[AI Suggestions]
    
    style A fill:#e3f2fd
    style D fill:#fff3e0
    style J fill:#e8f5e8
```

### **With Development Tools**

```mermaid
graph LR
    A[IDE/Editor] --> B[Plugin/Extension]
    B --> C[RepoMap-Tool API]
    C --> D[Analysis Engine]
    D --> E[Results Display]
    
    style A fill:#e3f2fd
    style C fill:#fff3e0
    style E fill:#e8f5e8
```

## 🚀 **Deployment Architecture**

### **Docker Container Structure**

```mermaid
graph TB
    subgraph "Docker Container"
        A[Entry Point] --> B[Python Runtime]
        B --> C[Application Code]
        C --> D[Dependencies]
        
        D --> E[Tree-sitter]
        D --> F[Fuzzy Matching]
        D --> G[TF-IDF Libraries]
    end
    
    subgraph "Host System"
        H[Project Directory] --> I[Volume Mount]
        I --> A
    end
    
    style A fill:#e3f2fd
    style C fill:#fff3e0
    style H fill:#e8f5e8
```

### **File Organization**

```
docker-repomap/
├── Dockerfile                 # Container definition
├── external_repomap.py       # Main application
├── fuzzy_matcher.py          # Fuzzy matching logic
├── adaptive_semantic_matcher.py  # Semantic matching logic
├── hybrid_matcher.py         # Hybrid matching logic
├── requirements.txt          # Python dependencies
├── build.sh                  # Build script
├── run.sh                    # Run script
└── README.md                 # Documentation
```

## 🔍 **Error Handling & Recovery**

```mermaid
graph TB
    A[User Input] --> B[Validation]
    B --> C{Valid?}
    
    C -->|Yes| D[Process]
    C -->|No| E[Error Message]
    
    D --> F[Analysis]
    F --> G{Success?}
    
    G -->|Yes| H[Results]
    G -->|No| I[Fallback Strategy]
    
    I --> J[Partial Results]
    J --> K[Warning Message]
    
    style A fill:#e3f2fd
    style E fill:#ffebee
    style H fill:#e8f5e8
    style K fill:#fff3e0
```

---

*This architecture provides a robust, scalable foundation for intelligent code analysis and discovery.*
