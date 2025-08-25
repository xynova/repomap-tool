# LLM Agent Two-Pass Strategy Guide for Docker RepoMap

## 🎯 **Overview**

This guide explains how LLM agents (like Roocode) can use docker-repomap's fuzzy matching capabilities to implement a **two-pass execution strategy** for understanding codebases. This approach combines broad discovery with precise analysis.

## 🚀 **Two-Pass Execution Strategy**

### **Pass 1: Fuzzy Discovery (Broad Exploration)**
Use fuzzy matching to discover related functions, classes, and patterns in the codebase.

### **Pass 2: Exact Analysis (Precise Understanding)**
Use the discovered identifiers to generate detailed, focused repo maps for specific analysis.

## 📋 **Step-by-Step Implementation**

### **Step 1: Initial Codebase Exploration**

**Goal**: Get a broad understanding of the codebase structure and discover relevant patterns.

```bash
# Pass 1: Fuzzy discovery with low threshold for broad exploration
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'api,config,model,service,util,helper,manager,handler,processor,validator' \
  --fuzzy-match \
  --fuzzy-threshold 50 \
  --fuzzy-strategies 'prefix,substring,word' \
  --map-tokens 8192 \
  --verbose
```

**What this discovers**:
- API-related functions: `api_handler`, `api_service`, `api_config`
- Configuration functions: `config_manager`, `config_validator`, `load_config`
- Model-related functions: `model_processor`, `data_model`, `model_validator`
- Service functions: `service_handler`, `service_manager`, `service_util`
- Utility functions: `util_helper`, `helper_functions`, `utility_manager`

### **Step 2: Analyze Discovery Results**

**Goal**: Extract meaningful identifiers from the fuzzy discovery results.

```bash
# Extract discovered identifiers from the fuzzy matching output
# Look for patterns like:
# - authenticate_user, user_authentication, auth_utils
# - process_data, data_processor, process_changes
# - validate_input, input_validator, validate_config
```

### **Step 3: Targeted Exact Analysis**

**Goal**: Generate precise repo maps using discovered identifiers.

```bash
# Pass 2: Exact analysis using discovered identifiers
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'authenticate_user,user_authentication,auth_utils,process_data,data_processor,validate_input,input_validator' \
  --map-tokens 4096 \
  --verbose
```

## 🔍 **LLM Agent Decision Framework**

### **When to Use Two-Pass Strategy**

#### **Scenario 1: New Codebase Exploration**
```python
# LLM Agent Logic
if codebase_is_new:
    # Pass 1: Broad discovery
    fuzzy_identifiers = [
        'api', 'config', 'model', 'service', 'util', 
        'helper', 'manager', 'handler', 'processor', 'validator'
    ]
    
    # Pass 2: Focused analysis
    discovered_identifiers = extract_from_fuzzy_results(fuzzy_results)
    exact_analysis(discovered_identifiers)
```

#### **Scenario 2: Feature Development**
```python
# LLM Agent Logic
if developing_feature('user_authentication'):
    # Pass 1: Discover authentication patterns
    fuzzy_identifiers = ['auth', 'login', 'user', 'session', 'token']
    
    # Pass 2: Analyze specific auth functions
    discovered_identifiers = extract_auth_functions(fuzzy_results)
    exact_analysis(discovered_identifiers)
```

#### **Scenario 3: Refactoring Preparation**
```python
# LLM Agent Logic
if refactoring_module('data_processing'):
    # Pass 1: Discover all processing functions
    fuzzy_identifiers = ['process', 'data', 'transform', 'convert', 'parse']
    
    # Pass 2: Analyze specific processing functions
    discovered_identifiers = extract_processing_functions(fuzzy_results)
    exact_analysis(discovered_identifiers)
```

## 🎯 **LLM Agent Implementation Patterns**

### **Pattern 1: Progressive Discovery**

```python
def progressive_discovery_strategy(codebase_path, feature_domain):
    """
    Progressive discovery: Start broad, then narrow down
    """
    # Phase 1: Domain-specific fuzzy search
    domain_keywords = get_domain_keywords(feature_domain)
    
    fuzzy_results = run_fuzzy_discovery(
        codebase_path=codebase_path,
        identifiers=domain_keywords,
        threshold=50,
        strategies=['prefix', 'substring', 'word']
    )
    
    # Phase 2: Extract and categorize discovered functions
    discovered_functions = categorize_discovered_functions(fuzzy_results)
    
    # Phase 3: Exact analysis of categorized functions
    for category, functions in discovered_functions.items():
        exact_results = run_exact_analysis(
            codebase_path=codebase_path,
            identifiers=functions,
            map_tokens=4096
        )
        analyze_category(category, exact_results)
```

### **Pattern 2: Hierarchical Analysis**

```python
def hierarchical_analysis_strategy(codebase_path):
    """
    Hierarchical analysis: Start with high-level concepts, then drill down
    """
    # Level 1: High-level architectural components
    architectural_components = ['api', 'service', 'model', 'config', 'util']
    
    level1_results = run_fuzzy_discovery(
        codebase_path=codebase_path,
        identifiers=architectural_components,
        threshold=60
    )
    
    # Level 2: Specific patterns within each component
    for component, functions in level1_results.items():
        specific_patterns = get_component_patterns(component)
        
        level2_results = run_fuzzy_discovery(
            codebase_path=codebase_path,
            identifiers=specific_patterns,
            threshold=70
        )
        
        # Level 3: Exact analysis of specific functions
        exact_analysis = run_exact_analysis(
            codebase_path=codebase_path,
            identifiers=level2_results,
            map_tokens=2048
        )
```

### **Pattern 3: Context-Aware Discovery**

```python
def context_aware_discovery_strategy(codebase_path, current_context):
    """
    Context-aware discovery: Adapt discovery based on current conversation
    """
    # Extract context from current conversation
    mentioned_files = extract_mentioned_files(current_context)
    mentioned_terms = extract_mentioned_terms(current_context)
    
    # Pass 1: Context-aware fuzzy discovery
    fuzzy_results = run_fuzzy_discovery(
        codebase_path=codebase_path,
        identifiers=mentioned_terms,
        mentioned_files=mentioned_files,
        threshold=60
    )
    
    # Pass 2: Focused exact analysis
    discovered_identifiers = extract_relevant_identifiers(fuzzy_results, current_context)
    
    exact_results = run_exact_analysis(
        codebase_path=codebase_path,
        identifiers=discovered_identifiers,
        mentioned_files=mentioned_files,
        map_tokens=4096
    )
```

## 🔧 **Practical Examples**

### **Example 1: Understanding Authentication System**

```bash
# Pass 1: Discover authentication patterns
echo "=== Pass 1: Authentication Discovery ==="
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'auth,login,user,session,token,password,credential' \
  --fuzzy-match \
  --fuzzy-threshold 50 \
  --map-tokens 4096

# Extract discovered functions from output:
# - authenticate_user, user_authentication, auth_utils
# - login_handler, session_manager, token_validator
# - password_hasher, credential_checker

# Pass 2: Exact analysis of auth functions
echo "=== Pass 2: Exact Auth Analysis ==="
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'authenticate_user,user_authentication,auth_utils,login_handler,session_manager,token_validator,password_hasher,credential_checker' \
  --map-tokens 4096
```

### **Example 2: Data Processing Pipeline Analysis**

```bash
# Pass 1: Discover data processing patterns
echo "=== Pass 1: Data Processing Discovery ==="
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'process,data,transform,convert,parse,validate,filter,sort' \
  --fuzzy-match \
  --fuzzy-threshold 50 \
  --map-tokens 4096

# Extract discovered functions from output:
# - process_data, data_processor, process_changes
# - transform_input, convert_format, parse_config
# - validate_data, filter_results, sort_items

# Pass 2: Exact analysis of processing functions
echo "=== Pass 2: Exact Processing Analysis ==="
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'process_data,data_processor,process_changes,transform_input,convert_format,parse_config,validate_data,filter_results,sort_items' \
  --map-tokens 4096
```

### **Example 3: API Development Context**

```bash
# Pass 1: Discover API-related patterns
echo "=== Pass 1: API Discovery ==="
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'api,endpoint,route,handler,controller,request,response' \
  --fuzzy-match \
  --fuzzy-threshold 50 \
  --map-tokens 4096

# Extract discovered functions from output:
# - api_handler, endpoint_controller, route_manager
# - request_validator, response_formatter, api_service

# Pass 2: Exact analysis of API functions
echo "=== Pass 2: Exact API Analysis ==="
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'api_handler,endpoint_controller,route_manager,request_validator,response_formatter,api_service' \
  --map-tokens 4096
```

## 🎯 **LLM Agent Best Practices**

### **1. Adaptive Threshold Strategy**
```python
def adaptive_threshold_strategy(codebase_size, discovery_goal):
    """
    Adapt threshold based on codebase size and discovery goal
    """
    if codebase_size == 'small':
        return 70  # Higher threshold for small codebases
    elif discovery_goal == 'exploration':
        return 50  # Lower threshold for broad exploration
    elif discovery_goal == 'precision':
        return 80  # Higher threshold for precise discovery
    else:
        return 60  # Default threshold
```

### **2. Intelligent Identifier Selection**
```python
def intelligent_identifier_selection(context, domain):
    """
    Select identifiers based on context and domain
    """
    base_identifiers = {
        'authentication': ['auth', 'login', 'user', 'session', 'token'],
        'data_processing': ['process', 'data', 'transform', 'convert', 'parse'],
        'api_development': ['api', 'endpoint', 'route', 'handler', 'controller'],
        'configuration': ['config', 'setting', 'option', 'parameter', 'env'],
        'testing': ['test', 'spec', 'mock', 'stub', 'fixture']
    }
    
    return base_identifiers.get(domain, ['util', 'helper', 'manager', 'service'])
```

### **3. Result Analysis and Refinement**
```python
def analyze_and_refine_results(fuzzy_results, context):
    """
    Analyze fuzzy results and refine for exact analysis
    """
    # Extract high-confidence matches
    high_confidence_matches = [
        identifier for identifier, score in fuzzy_results 
        if score >= 80
    ]
    
    # Group by functional similarity
    grouped_identifiers = group_by_functional_similarity(high_confidence_matches)
    
    # Select most relevant for exact analysis
    relevant_identifiers = select_most_relevant(grouped_identifiers, context)
    
    return relevant_identifiers
```

## 📊 **Performance Optimization**

### **1. Caching Strategy**
```python
def cached_two_pass_strategy(codebase_path, domain):
    """
    Use caching to optimize repeated discoveries
    """
    cache_key = f"{codebase_path}_{domain}"
    
    if cache_exists(cache_key):
        return load_from_cache(cache_key)
    
    # Perform two-pass discovery
    results = perform_two_pass_discovery(codebase_path, domain)
    
    # Cache results
    save_to_cache(cache_key, results)
    
    return results
```

### **2. Parallel Processing**
```python
def parallel_discovery_strategy(codebase_path, domains):
    """
    Perform parallel discovery across multiple domains
    """
    with ThreadPoolExecutor(max_workers=len(domains)) as executor:
        future_to_domain = {
            executor.submit(single_domain_discovery, codebase_path, domain): domain 
            for domain in domains
        }
        
        results = {}
        for future in future_to_domain:
            domain = future_to_domain[future]
            results[domain] = future.result()
    
    return results
```

## 🎉 **Conclusion**

The two-pass execution strategy enables LLM agents to:

1. **Discover broadly** using fuzzy matching to understand codebase patterns
2. **Analyze precisely** using exact identifiers for detailed understanding
3. **Adapt intelligently** based on context and discovery goals
4. **Optimize performance** through caching and parallel processing

This approach transforms docker-repomap into a powerful tool for LLM agents to understand and work with codebases effectively! 🎯
