# Semantic Matching Implementation Guide for Docker RepoMap

## 🎯 **Overview**

This guide explores how to implement semantic matching capabilities in docker-repomap without requiring external LLMs. We'll use local techniques like embeddings, word vectors, and semantic similarity algorithms.

## 🚀 **Local Semantic Matching Approaches**

### **Approach 1: Pre-trained Word Embeddings**

#### **Using spaCy or Gensim**
```python
import spacy
from gensim.models import KeyedVectors
import numpy as np

class SemanticMatcher:
    def __init__(self, embedding_model='en_core_web_sm'):
        # Load pre-trained word vectors
        self.nlp = spacy.load(embedding_model)
        
    def get_identifier_embedding(self, identifier):
        """Get embedding for an identifier"""
        # Split identifier into words (camelCase, snake_case, etc.)
        words = self.split_identifier(identifier)
        
        # Get embeddings for each word
        word_embeddings = []
        for word in words:
            doc = self.nlp(word.lower())
            if doc.vector.any():  # Check if vector exists
                word_embeddings.append(doc.vector)
        
        # Average the word embeddings
        if word_embeddings:
            return np.mean(word_embeddings, axis=0)
        return None
    
    def semantic_similarity(self, query, identifier):
        """Calculate semantic similarity between query and identifier"""
        query_embedding = self.get_identifier_embedding(query)
        identifier_embedding = self.get_identifier_embedding(identifier)
        
        if query_embedding is not None and identifier_embedding is not None:
            # Cosine similarity
            similarity = np.dot(query_embedding, identifier_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(identifier_embedding)
            )
            return similarity
        return 0.0
```

#### **Implementation with FastText**
```python
import fasttext
import numpy as np

class FastTextSemanticMatcher:
    def __init__(self, model_path=None):
        # Use pre-trained FastText model or train custom one
        if model_path:
            self.model = fasttext.load_model(model_path)
        else:
            # Use default FastText model
            self.model = fasttext.load_model('cc.en.300.bin')
    
    def get_identifier_vector(self, identifier):
        """Get FastText vector for identifier"""
        words = self.split_identifier(identifier)
        vectors = []
        
        for word in words:
            vector = self.model.get_word_vector(word.lower())
            vectors.append(vector)
        
        if vectors:
            return np.mean(vectors, axis=0)
        return None
    
    def semantic_similarity(self, query, identifier):
        """Calculate semantic similarity using FastText"""
        query_vector = self.get_identifier_vector(query)
        identifier_vector = self.get_identifier_vector(identifier)
        
        if query_vector is not None and identifier_vector is not None:
            similarity = np.dot(query_vector, identifier_vector) / (
                np.linalg.norm(query_vector) * np.linalg.norm(identifier_vector)
            )
            return similarity
        return 0.0
```

### **Approach 2: Domain-Specific Semantic Dictionaries**

#### **Programming Language Semantic Mappings**
```python
class DomainSemanticMatcher:
    def __init__(self):
        # Define semantic mappings for programming concepts
        self.semantic_mappings = {
            'authentication': [
                'auth', 'login', 'signin', 'authenticate', 'verify', 'validate',
                'password', 'credential', 'token', 'session', 'user', 'identity'
            ],
            'data_processing': [
                'process', 'transform', 'convert', 'parse', 'format', 'serialize',
                'deserialize', 'encode', 'decode', 'filter', 'sort', 'aggregate'
            ],
            'configuration': [
                'config', 'setting', 'option', 'parameter', 'env', 'environment',
                'preference', 'property', 'attribute', 'flag', 'switch'
            ],
            'api_development': [
                'api', 'endpoint', 'route', 'handler', 'controller', 'service',
                'request', 'response', 'method', 'action', 'operation'
            ],
            'database': [
                'db', 'database', 'query', 'select', 'insert', 'update', 'delete',
                'table', 'record', 'row', 'column', 'field', 'schema'
            ],
            'testing': [
                'test', 'spec', 'mock', 'stub', 'fixture', 'assert', 'verify',
                'check', 'validate', 'expect', 'should', 'describe'
            ]
        }
        
        # Create reverse mapping for quick lookup
        self.reverse_mappings = {}
        for category, terms in self.semantic_mappings.items():
            for term in terms:
                self.reverse_mappings[term] = category
    
    def get_semantic_category(self, identifier):
        """Get semantic category for an identifier"""
        words = self.split_identifier(identifier)
        
        for word in words:
            if word.lower() in self.reverse_mappings:
                return self.reverse_mappings[word.lower()]
        
        return None
    
    def semantic_similarity(self, query, identifier):
        """Calculate semantic similarity based on categories"""
        query_category = self.get_semantic_category(query)
        identifier_category = self.get_semantic_category(identifier)
        
        if query_category and identifier_category:
            if query_category == identifier_category:
                return 0.9  # High similarity for same category
            else:
                return 0.3  # Lower similarity for different categories
        
        return 0.0
```

### **Approach 3: TF-IDF with Semantic Clustering**

#### **Using scikit-learn for TF-IDF**
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class TFIDFSemanticMatcher:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            analyzer='word',
            ngram_range=(1, 2),  # Unigrams and bigrams
            max_features=1000
        )
        self.identifier_vectors = None
        self.identifiers = []
    
    def prepare_identifiers(self, all_identifiers):
        """Prepare TF-IDF vectors for all identifiers"""
        self.identifiers = list(all_identifiers)
        
        # Convert identifiers to readable text
        identifier_texts = []
        for identifier in self.identifiers:
            text = self.identifier_to_text(identifier)
            identifier_texts.append(text)
        
        # Create TF-IDF vectors
        self.identifier_vectors = self.vectorizer.fit_transform(identifier_texts)
    
    def identifier_to_text(self, identifier):
        """Convert identifier to readable text"""
        # Split camelCase, snake_case, etc.
        words = self.split_identifier(identifier)
        
        # Add common programming terms
        programming_terms = {
            'api': 'application programming interface',
            'db': 'database',
            'config': 'configuration',
            'auth': 'authentication',
            'util': 'utility',
            'helper': 'helper function',
            'manager': 'manager class',
            'handler': 'event handler',
            'processor': 'data processor',
            'validator': 'data validator'
        }
        
        expanded_words = []
        for word in words:
            if word.lower() in programming_terms:
                expanded_words.append(programming_terms[word.lower()])
            else:
                expanded_words.append(word)
        
        return ' '.join(expanded_words)
    
    def semantic_similarity(self, query, identifier):
        """Calculate semantic similarity using TF-IDF"""
        if self.identifier_vectors is None:
            return 0.0
        
        # Convert query to text
        query_text = self.identifier_to_text(query)
        
        # Transform query to TF-IDF vector
        query_vector = self.vectorizer.transform([query_text])
        
        # Find identifier index
        try:
            identifier_index = self.identifiers.index(identifier)
            identifier_vector = self.identifier_vectors[identifier_index]
            
            # Calculate cosine similarity
            similarity = cosine_similarity(query_vector, identifier_vector)[0][0]
            return similarity
        except ValueError:
            return 0.0
```

### **Approach 4: Hybrid Semantic Matching**

#### **Combining Multiple Approaches**
```python
class HybridSemanticMatcher:
    def __init__(self):
        self.word_embedding_matcher = SemanticMatcher()
        self.domain_matcher = DomainSemanticMatcher()
        self.tfidf_matcher = TFIDFSemanticMatcher()
        
        # Weights for different approaches
        self.weights = {
            'word_embedding': 0.4,
            'domain': 0.3,
            'tfidf': 0.3
        }
    
    def semantic_similarity(self, query, identifier):
        """Calculate weighted semantic similarity"""
        # Get similarities from different approaches
        word_embedding_sim = self.word_embedding_matcher.semantic_similarity(query, identifier)
        domain_sim = self.domain_matcher.semantic_similarity(query, identifier)
        tfidf_sim = self.tfidf_matcher.semantic_similarity(query, identifier)
        
        # Weighted combination
        weighted_similarity = (
            self.weights['word_embedding'] * word_embedding_sim +
            self.weights['domain'] * domain_sim +
            self.weights['tfidf'] * tfidf_sim
        )
        
        return weighted_similarity
```

## 🔧 **Integration with Docker RepoMap**

### **Enhanced Fuzzy Matcher with Semantic Matching**
```python
class EnhancedFuzzyMatcher:
    def __init__(self, threshold=70, strategies=None, enable_semantic=True):
        self.threshold = threshold
        self.strategies = strategies or ['prefix', 'substring', 'levenshtein']
        self.enable_semantic = enable_semantic
        
        if enable_semantic:
            self.semantic_matcher = HybridSemanticMatcher()
    
    def match_identifiers(self, query, all_identifiers):
        """Enhanced matching with semantic capabilities"""
        matches = []
        
        # Traditional fuzzy matching
        fuzzy_matches = self._traditional_fuzzy_matching(query, all_identifiers)
        
        # Semantic matching (if enabled)
        if self.enable_semantic:
            semantic_matches = self._semantic_matching(query, all_identifiers)
            
            # Combine and deduplicate results
            all_matches = fuzzy_matches + semantic_matches
            matches = self._deduplicate_and_rank(all_matches)
        else:
            matches = fuzzy_matches
        
        return matches
    
    def _semantic_matching(self, query, all_identifiers):
        """Perform semantic matching"""
        semantic_matches = []
        
        for identifier in all_identifiers:
            semantic_score = self.semantic_matcher.semantic_similarity(query, identifier)
            
            if semantic_score >= self.threshold / 100.0:  # Convert threshold to 0-1 scale
                semantic_matches.append((identifier, int(semantic_score * 100)))
        
        return semantic_matches
    
    def _deduplicate_and_rank(self, all_matches):
        """Deduplicate and rank matches"""
        # Group by identifier
        identifier_scores = {}
        
        for identifier, score in all_matches:
            if identifier in identifier_scores:
                # Take the highest score
                identifier_scores[identifier] = max(identifier_scores[identifier], score)
            else:
                identifier_scores[identifier] = score
        
        # Convert back to list and sort
        matches = [(ident, score) for ident, score in identifier_scores.items()]
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
```

## 📦 **Dependencies and Installation**

### **Requirements for Semantic Matching**
```txt
# Add to requirements.txt
spacy>=3.0.0
gensim>=4.0.0
scikit-learn>=1.0.0
numpy>=1.21.0
fasttext>=0.9.0
```

### **Dockerfile Updates**
```dockerfile
# Install spaCy models
RUN python -m spacy download en_core_web_sm
RUN python -m spacy download en_core_web_md

# Install FastText (optional)
RUN pip install fasttext
```

## 🎯 **Usage Examples**

### **Basic Semantic Matching**
```bash
# Enable semantic matching
docker run --rm -v $PWD:/project repomap-tool /project \
  --mentioned-idents 'user authentication' \
  --fuzzy-match \
  --semantic-match \
  --map-tokens 4096
```

### **Semantic Discovery Examples**
```python
# Example: Find authentication-related functions semantically
semantic_matcher = HybridSemanticMatcher()

# These should all find similar functions
queries = [
    'user login',
    'authentication system', 
    'password verification',
    'session management',
    'identity validation'
]

for query in queries:
    matches = semantic_matcher.find_semantic_matches(query, all_identifiers)
    print(f"Query: {query}")
    for identifier, score in matches[:5]:
        print(f"  - {identifier} (semantic score: {score})")
```

## 🚀 **Performance Considerations**

### **Caching Semantic Results**
```python
class CachedSemanticMatcher:
    def __init__(self):
        self.semantic_cache = {}
        self.embedding_cache = {}
    
    def get_cached_embedding(self, identifier):
        """Get cached embedding or compute new one"""
        if identifier in self.embedding_cache:
            return self.embedding_cache[identifier]
        
        embedding = self.compute_embedding(identifier)
        self.embedding_cache[identifier] = embedding
        return embedding
    
    def get_cached_similarity(self, query, identifier):
        """Get cached similarity or compute new one"""
        cache_key = f"{query}_{identifier}"
        
        if cache_key in self.semantic_cache:
            return self.semantic_cache[cache_key]
        
        similarity = self.compute_similarity(query, identifier)
        self.semantic_cache[cache_key] = similarity
        return similarity
```

### **Lazy Loading**
```python
class LazySemanticMatcher:
    def __init__(self):
        self._semantic_matcher = None
        self._initialized = False
    
    @property
    def semantic_matcher(self):
        """Lazy load semantic matcher"""
        if not self._initialized:
            self._semantic_matcher = HybridSemanticMatcher()
            self._initialized = True
        return self._semantic_matcher
```

## 🎉 **Benefits of Local Semantic Matching**

### **Advantages**
- ✅ **No external dependencies** - works offline
- ✅ **Fast performance** - no API calls
- ✅ **Privacy** - no data sent to external services
- ✅ **Customizable** - can be tuned for specific domains
- ✅ **Cost-effective** - no usage fees

### **Use Cases**
- **Code exploration** - find semantically related functions
- **Refactoring** - discover similar functionality across codebase
- **Documentation** - group related functions by semantic meaning
- **Code review** - identify similar patterns and implementations

## 🎯 **Implementation Roadmap**

### **Phase 1: Basic Semantic Matching**
- Implement domain-specific semantic dictionaries
- Add TF-IDF based similarity
- Integrate with existing fuzzy matching

### **Phase 2: Advanced Semantic Matching**
- Add pre-trained word embeddings
- Implement hybrid matching approach
- Add caching and performance optimizations

### **Phase 3: Domain-Specific Tuning**
- Create programming language specific semantic mappings
- Add framework-specific patterns (Django, React, etc.)
- Implement custom training for specific codebases

This approach provides powerful semantic matching capabilities without requiring external LLMs! 🎯
