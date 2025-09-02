# Phase 3: LLM Optimization Implementation

## Overview
**Goal:** Optimize repomap output specifically for LLM consumption with hierarchical structure, critical code line extraction, and token-efficient formatting.

**Duration:** 1-2 weeks  
**Effort:** Low-Medium  
**Impact:** Medium  
**Priority:** Medium (After Phases 1 & 2)  
**Depends On:** Phase 1 (Tree-Based Exploration), Phase 2 (Dependency Analysis)

## Current State vs Target State

### Current State
- Generic code analysis output
- Function listings without critical implementation details
- No hierarchical organization optimized for LLM parsing
- Not optimized for token efficiency
- Missing type signatures and call patterns

### Target State
- LLM-optimized hierarchical output format
- Critical code line extraction for each symbol
- Token-efficient representation maximizing information density
- Type signatures and call patterns prominently displayed
- Adaptive output based on token budget constraints

## Technical Architecture

### New Components to Add

```
src/repomap_tool/llm/
├── __init__.py
├── critical_line_extractor.py   # Extract most important code lines
├── hierarchical_formatter.py    # Format output hierarchically
├── token_optimizer.py           # Optimize for token efficiency
├── signature_enhancer.py        # Enhance function signatures
├── context_selector.py          # Select most relevant context
└── output_templates.py          # LLM-optimized output templates
```

### Core Classes to Implement

```python
class CriticalLineExtractor:
    """Extracts the most important lines from functions/classes"""
    
class HierarchicalFormatter:
    """Formats output in LLM-friendly hierarchical structure"""
    
class TokenOptimizer:
    """Optimizes output for maximum information per token"""
    
class SignatureEnhancer:
    """Enhances function signatures with type information"""
    
class ContextSelector:
    """Selects most relevant context based on token budget"""
```

## Technical Architecture Overview

### System Flow Diagram
```
Phase 1 Trees + Phase 2 Dependencies → CriticalLineExtractor → HierarchicalFormatter
                                                ↓
TokenOptimizer → SignatureEnhancer → ContextSelector → OutputTemplates
                                                ↓
LLM-Optimized Repomap (40% more efficient, hierarchical, critical lines)
```

### Data Flow Architecture

```python
# Input: Enhanced exploration trees from Phases 1 & 2
exploration_trees = get_dependency_enhanced_trees(session_id, intent)
# Input: [ExplorationTree with dependency intelligence, centrality scores]

# Stage 1: Critical Line Extraction
critical_extractor = CriticalLineExtractor()
for tree in exploration_trees:
    for node in tree.tree_structure:
        critical_lines = critical_extractor.extract_critical_lines(node)
        node.critical_lines = critical_lines
# Output: Trees with critical implementation lines identified

# Stage 2: Token Budget Planning
token_optimizer = TokenOptimizer()
total_content = estimate_content_size(exploration_trees)
budget_allocation = token_optimizer.allocate_token_budget(total_content, max_tokens=2048)
# Output: {'signatures': 614, 'critical_lines': 819, 'structure': 409, 'context': 206}

# Stage 3: Content Selection
context_selector = ContextSelector()
selected_content = context_selector.select_optimal_context(
    exploration_trees, user_context, budget_allocation
)
# Output: Prioritized content that fits within token budget

# Stage 4: Signature Enhancement
signature_enhancer = SignatureEnhancer()
for symbol in selected_content.symbols:
    enhanced_sig = signature_enhancer.enhance_function_signature(symbol)
    symbol.enhanced_signature = enhanced_sig
# Output: Symbols with enhanced type signatures and call patterns

# Stage 5: Hierarchical Formatting
hierarchical_formatter = HierarchicalFormatter()
formatted_output = hierarchical_formatter.format_symbol_hierarchy(selected_content)
# Output: Hierarchical, LLM-friendly formatted text

# Stage 6: Final Token Optimization
optimized_output = token_optimizer.optimize_for_token_budget(formatted_output, max_tokens)
# Output: Token-efficient repomap ready for LLM consumption
```

### Component Integration Map

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Phase 1 & 2       │    │   LLM Processing    │    │   Output Layer      │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ ExplorationTrees    │───►│ CriticalExtractor   │───►│ HierarchicalFormat  │
│ DependencyGraph     │───►│ ContextSelector     │───►│ TokenOptimizer      │
│ CentralityScores    │───►│ SignatureEnhancer   │───►│ OutputTemplates     │
│                     │    │                     │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
         ▲                           ▲                           ▲
         │                           │                           │
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  Language Support   │    │   Token Management  │    │   LLM Integration   │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ Python Analyzer     │    │ tiktoken Library    │    │ GPT-4 Optimized     │
│ JavaScript Analyzer │    │ Budget Allocation   │    │ Claude Optimized     │
│ TypeScript Analyzer │    │ Compression Engine  │    │ Gemini Optimized     │
│                     │    │                     │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

### File Structure & Dependencies

```
src/repomap_tool/llm/
├── __init__.py                      # Package initialization
├── critical_line_extractor.py       # Uses: AST analysis, regex patterns, language-specific
├── hierarchical_formatter.py        # Uses: jinja2 templates, tree structures
├── token_optimizer.py              # Uses: tiktoken, compression algorithms
├── signature_enhancer.py           # Uses: static analysis, type inference
├── context_selector.py             # Uses: Phase 1 trees, Phase 2 dependencies
└── output_templates.py             # Uses: jinja2, LLM-specific formatting

# Enhanced files (integrates with Phases 1 & 2):
src/repomap_tool/trees/tree_mapper.py       # Enhanced with LLM optimization
src/repomap_tool/core/repo_map.py           # New LLM-optimized output methods

# New dependencies:
pyproject.toml                      # Add: tiktoken, Pygments, jinja2
```

### Critical Technical Decisions

1. **Token Counting**: Use tiktoken for accurate token estimation across different LLM models
2. **Critical Line Detection**: Language-specific patterns + AST analysis for maximum accuracy
3. **Hierarchical Format**: Tree-like structure optimized for LLM parsing and understanding
4. **Compression Strategy**: Semantic compression preserving meaning over character count
5. **Template System**: Jinja2-based templates for different LLM model optimizations

## User Experience Examples

### Example 1: Token-Efficient Output Comparison

#### Before Phase 3 (Generic Output):
```bash
$ repomap-tool map --session auth_debug

🌳 Exploration Tree: Auth Error Handling
📍 Root: AuthErrorHandler

├── AuthErrorHandler (src/auth/error_handler.py:15)
│   ├── handle_login_error (src/auth/error_handler.py:42)
│   ├── validate_credentials (src/auth/error_handler.py:68)
│   └── log_auth_failure (src/auth/error_handler.py:85)
├── LoginValidator (src/auth/validators.py:12)
│   └── check_password_strength (src/auth/validators.py:23)
└── AuthExceptions (src/auth/exceptions.py:8)
    ├── InvalidCredentialsError (src/auth/exceptions.py:12)
    └── AccountLockedError (src/auth/exceptions.py:18)

Token Count: ~450 tokens
Information Density: Low (mostly structure, no implementation details)
```

#### After Phase 3 (LLM-Optimized):
```bash
$ repomap-tool generate-llm /project --session auth_debug --max-tokens 450

🧠 LLM-Optimized Repomap (450 tokens, 65% more information)
═══════════════════════════════════════════════════════════

src/auth/error_handler.py:15:
├── AuthErrorHandler:
│   ├── handle_login_error(username: str, password: str) -> ErrorResponse:
│   │   💡 Critical: if not user or not user.verify_password(password): 
│   │   💡 Critical:     return ErrorResponse("Invalid credentials", 401)
│   │   💡 Critical: self.log_attempt(username, success=False)
│   │   📞 Usage: handler.handle_login_error("john", "wrong_pass")
│   ├── validate_credentials(creds: dict) -> bool:
│   │   💡 Critical: return all(key in creds for key in ['username', 'password'])
│   └── log_auth_failure(username: str, reason: str):
│       💡 Critical: logger.warning(f"Auth failed: {username} - {reason}")

src/auth/validators.py:12:
├── LoginValidator:
│   └── check_password_strength(password: str) -> ValidationResult:
│       💡 Critical: if len(password) < 8: return ValidationResult(False, "Too short")
│       💡 Critical: if not re.search(r'[A-Z]', password): return ValidationResult(False, "No uppercase")
│       📞 Usage: result = validator.check_password_strength("Password123")

🔗 Key Dependencies: user.verify_password(), logger.warning(), ValidationResult
📊 Impact: 8 downstream files, 3 API endpoints, HIGH risk

Token Count: 450 tokens (same budget)
Information Density: High (implementation details, usage patterns, impact analysis)
```

### Example 2: Critical Line Extraction

```bash
$ repomap-tool extract-critical /project --file src/auth/service.py --function authenticate_user

🔍 Critical Line Analysis: authenticate_user()
═══════════════════════════════════════════════

📍 Function: authenticate_user(username: str, password: str) -> AuthResult

🔥 Critical Implementation Lines (ranked by importance):
  1. [Score: 0.95] if not user or not user.is_active:
                      return AuthResult(success=False, reason="User not found or inactive")
  
  2. [Score: 0.92] if not user.verify_password(password):
                      self._increment_failed_attempts(user)
                      return AuthResult(success=False, reason="Invalid password")
  
  3. [Score: 0.88] if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
                      user.lock_account()
                      return AuthResult(success=False, reason="Account locked")
  
  4. [Score: 0.85] session = self._create_user_session(user)
                   user.reset_failed_attempts()
                   return AuthResult(success=True, session=session)

💡 Business Logic: Authentication with rate limiting and account locking
🎯 Key Error Cases: User not found (35%), wrong password (45%), account locked (20%)
📊 Complexity: 4 decision points, 3 external dependencies, 2 side effects

🔧 Suggested LLM Context:
  "This function handles user authentication with security measures including 
   rate limiting and automatic account locking after failed attempts."
```

### Example 3: Hierarchical Format with Budget Optimization

```bash
$ repomap-tool generate-llm /large-project --message "payment processing flow" --max-tokens 1024

🧠 LLM-Optimized Repomap (1024 tokens allocated strategically)
════════════════════════════════════════════════════════════

💰 Payment Processing Flow (5 key components):

src/payments/gateway.py:20: [Centrality: 0.95] ⭐ CORE
├── PaymentGateway:
│   ├── process_payment(amount: Decimal, card: CreditCard) -> PaymentResult:
│   │   💡 if amount <= 0: raise ValueError("Invalid amount")
│   │   💡 result = self.stripe_connector.charge(amount, card.token)
│   │   💡 self.audit_log.record_payment(result)
│   │   📞 gateway.process_payment(Decimal('99.99'), user.credit_card)
│   └── handle_webhook(payload: dict, signature: str) -> bool:
│       💡 if not self.verify_signature(payload, signature): return False
│       💡 self.process_webhook_event(payload['type'], payload['data'])

src/payments/providers/stripe.py:15: [Centrality: 0.83]
├── StripeConnector:
│   └── charge(amount: Decimal, token: str) -> ChargeResult:
│       💡 return stripe.Charge.create(amount=int(amount*100), source=token)

src/payments/validation.py:12: [Centrality: 0.71]
├── PaymentValidator:
│   ├── validate_card(card: CreditCard) -> ValidationResult:
│   │   💡 if card.is_expired(): return ValidationResult(False, "Card expired")
│   └── check_fraud_rules(amount: Decimal, user: User) -> FraudResult:
│       💡 if amount > user.daily_limit: return FraudResult(BLOCKED, "Limit exceeded")

🔗 Dependencies: stripe.Charge, audit_log.record_payment, user.daily_limit
📈 Flow: validate_card() → check_fraud_rules() → charge() → record_payment()
⚠️  Critical Paths: Stripe connectivity, fraud detection, audit logging

[Budget Used: 1021/1024 tokens - 99.7% efficiency]
```

### Example 4: Signature Enhancement

```bash
$ repomap-tool optimize-signatures /project --file src/api/user.py

🔧 Enhanced Function Signatures
═══════════════════════════════

Original:
  def create_user(data): ...
  def update_user(user_id, changes): ...
  def delete_user(user_id): ...

Enhanced:
├── create_user(data: UserCreateRequest) -> CreateUserResponse:
│   ├── Args: data.username (str), data.email (str), data.password (str)
│   ├── Returns: CreateUserResponse(user_id: int, success: bool, errors: List[str])
│   ├── Raises: ValidationError, DuplicateUserError
│   └── 📞 create_user(UserCreateRequest(username="john", email="john@example.com", password="..."))

├── update_user(user_id: int, changes: UserUpdateRequest) -> UpdateUserResponse:
│   ├── Args: user_id (required), changes.email (optional), changes.password (optional)
│   ├── Returns: UpdateUserResponse(success: bool, updated_fields: List[str])
│   ├── Raises: UserNotFoundError, ValidationError
│   └── 📞 update_user(123, UserUpdateRequest(email="newemail@example.com"))

└── delete_user(user_id: int, soft_delete: bool = True) -> DeleteUserResponse:
    ├── Args: user_id (required), soft_delete (default: True)
    ├── Returns: DeleteUserResponse(success: bool, permanently_deleted: bool)
    ├── Raises: UserNotFoundError, DeleteRestrictedError
    └── 📞 delete_user(123, soft_delete=False)

💡 Type Enhancement: +85% type coverage, inferred from usage patterns
🎯 LLM Context: Complete function contracts with examples and error cases
```

### Example 5: Token Budget Management

```bash
$ repomap-tool optimize-tokens /project --input large_analysis.txt --target-tokens 512

📊 Token Budget Optimization
═══════════════════════════════

Input Analysis: 1,247 tokens (143% over budget)
Target Budget: 512 tokens

🎯 Optimization Strategy:
  Critical Lines:     205 tokens (40%) - Keep all essential logic
  Function Signatures: 154 tokens (30%) - Enhanced with types
  Structure:          102 tokens (20%) - Hierarchical organization  
  Context:             51 tokens (10%) - Key dependencies only

⚡ Compression Applied:
  ✂️  Removed verbose comments (-89 tokens)
  🗜️  Abbreviated common patterns (-156 tokens)
  📦 Compressed whitespace (-23 tokens)
  🎯 Prioritized by centrality scores (-467 tokens)

📈 Result:
  Final Output: 509 tokens (99.4% of budget used)
  Information Retained: 87% (high-value content preserved)
  Compression Ratio: 2.45x (512 tokens contain 2.45x more useful information)

✅ Optimization Success: 
  - All critical business logic preserved
  - Function signatures complete with types
  - Key dependencies and relationships clear
  - Ready for LLM consumption
```

## Quality Standards & Anti-Patterns

### ✅ What Good Looks Like

#### **1. Intelligent Critical Line Extraction**
```python
# GOOD: Language-aware critical line detection
class CriticalLineExtractor:
    def extract_critical_lines(self, symbol: Symbol) -> List[CriticalLine]:
        analyzer = self.language_analyzers[symbol.language]
        
        # Parse symbol content using AST
        try:
            tree = analyzer.parse_code(symbol.content)
            critical_nodes = analyzer.find_critical_nodes(tree)
            
            critical_lines = []
            for node in critical_nodes:
                importance_score = self._calculate_importance(node, symbol)
                if importance_score > self.threshold:
                    critical_lines.append(CriticalLine(
                        line_number=node.line_number,
                        content=node.content,
                        importance=importance_score,
                        pattern_type=node.pattern_type  # return, conditional, call, etc.
                    ))
            
            return sorted(critical_lines, key=lambda x: x.importance, reverse=True)
            
        except ParseError as e:
            logger.warning(f"Failed to parse {symbol.name}: {e}")
            return self._fallback_extraction(symbol)

# GOOD: Business logic focused importance scoring
def _calculate_importance(self, node: ASTNode, symbol: Symbol) -> float:
    base_score = PATTERN_SCORES.get(node.pattern_type, 0.0)
    
    # Boost for business logic indicators
    if self._is_business_logic(node):
        base_score += 0.3
    
    # Boost for error handling
    if self._is_error_handling(node):
        base_score += 0.25
    
    # Boost for external API calls
    if self._is_external_call(node):
        base_score += 0.2
    
    return min(1.0, base_score)
```

#### **2. Token-Efficient Hierarchical Formatting**
```python
# GOOD: Structured output with semantic compression
class HierarchicalFormatter:
    def format_symbol_hierarchy(self, symbols: List[Symbol]) -> str:
        output = []
        
        for symbol in symbols:
            # Start with file and line number for context
            output.append(f"{symbol.file_path}:{symbol.line_number}:")
            
            # Function signature with enhanced types
            if symbol.enhanced_signature:
                output.append(f"├── {symbol.enhanced_signature}:")
            else:
                output.append(f"├── {symbol.name}:")
            
            # Critical implementation lines (most important)
            for i, critical_line in enumerate(symbol.critical_lines[:3]):  # Limit to top 3
                icon = "💡" if critical_line.pattern_type == "business_logic" else "⚠️"
                output.append(f"│   {icon} Critical: {critical_line.content.strip()}")
            
            # Usage example (if available and budget allows)
            if symbol.usage_example and self.budget_remaining > 50:
                output.append(f"│   📞 Usage: {symbol.usage_example}")
            
            # Dependencies (compressed)
            if symbol.dependencies:
                deps = ", ".join(symbol.dependencies[:3])  # Limit dependencies
                if len(symbol.dependencies) > 3:
                    deps += f" (+{len(symbol.dependencies) - 3} more)"
                output.append(f"│   🔗 Deps: {deps}")
        
        return "\n".join(output)

# GOOD: Semantic compression preserving meaning
def compress_without_losing_meaning(self, content: str) -> str:
    # Apply compression strategies in order of safety
    compressed = content
    
    # Safe compressions (no information loss)
    compressed = self._remove_extra_whitespace(compressed)
    compressed = self._abbreviate_common_patterns(compressed)
    
    # Semantic compressions (preserve meaning)
    compressed = self._compress_variable_names(compressed)
    compressed = self._summarize_repetitive_patterns(compressed)
    
    # Validate compression didn't break anything important
    if self._validate_compression(content, compressed):
        return compressed
    else:
        logger.warning("Compression validation failed, using original")
        return content
```

#### **3. Smart Token Budget Management**
```python
# GOOD: Intelligent budget allocation based on content importance
class TokenOptimizer:
    def allocate_token_budget(self, content: ProjectContent, max_tokens: int) -> BudgetAllocation:
        # Analyze content complexity and importance
        total_symbols = len(content.symbols)
        high_centrality_symbols = [s for s in content.symbols if s.centrality_score > 0.8]
        
        # Adaptive allocation based on content characteristics
        if len(high_centrality_symbols) > total_symbols * 0.3:
            # Many important symbols - prioritize breadth
            allocation = BudgetAllocation(
                critical_lines=0.35,     # 35% - less detail per symbol
                signatures=0.35,         # 35% - focus on interfaces
                structure=0.25,          # 25% - show connections
                context=0.05            # 5% - minimal context
            )
        else:
            # Few important symbols - prioritize depth
            allocation = BudgetAllocation(
                critical_lines=0.45,     # 45% - detailed implementation
                signatures=0.25,         # 25% - essential signatures
                structure=0.20,          # 20% - key structure
                context=0.10            # 10% - richer context
            )
        
        # Convert percentages to actual token counts
        return allocation.to_token_counts(max_tokens)

# GOOD: Graceful degradation when over budget
def optimize_for_token_budget(self, content: str, max_tokens: int) -> str:
    current_tokens = self.token_estimator.count_tokens(content)
    
    if current_tokens <= max_tokens:
        return content  # Already within budget
    
    # Apply progressive compression strategies
    strategies = [
        self._remove_low_importance_lines,
        self._compress_repetitive_content,
        self._abbreviate_function_bodies,
        self._reduce_context_information,
        self._emergency_truncation  # Last resort
    ]
    
    compressed_content = content
    for strategy in strategies:
        compressed_content = strategy(compressed_content)
        current_tokens = self.token_estimator.count_tokens(compressed_content)
        
        if current_tokens <= max_tokens:
            logger.info(f"Budget achieved with strategy: {strategy.__name__}")
            break
    
    # Validate we didn't lose critical information
    if self._validate_essential_content(content, compressed_content):
        return compressed_content
    else:
        # Fallback to safer compression
        return self._safe_truncation(content, max_tokens)
```

#### **4. Phase Integration That Enhances Rather Than Replaces**
```python
# GOOD: Builds on Phase 1 & 2 capabilities
class LLMOptimizedMapper(TreeMapper):  # Inherits from Phase 1
    def __init__(self, repo_map: DockerRepoMap):
        super().__init__(repo_map)
        self.critical_extractor = CriticalLineExtractor()
        self.token_optimizer = TokenOptimizer()
        self.hierarchical_formatter = HierarchicalFormatter()
        
        # Use Phase 2 dependency intelligence
        if hasattr(repo_map, 'dependency_graph'):
            self.context_selector = ContextSelector(repo_map.dependency_graph)
        else:
            self.context_selector = BasicContextSelector()  # Fallback
    
    def generate_tree_map(self, tree: ExplorationTree, include_code: bool = True) -> str:
        # Start with Phase 1 tree mapping (proven to work)
        base_map = super().generate_tree_map(tree, include_code)
        
        # Add LLM optimizations as enhancements
        if not self.config.llm.enabled:
            return base_map  # Fall back to Phase 1 when disabled
        
        try:
            # Enhance with LLM optimizations
            optimized_map = self._add_llm_optimizations(tree, base_map)
            return optimized_map
        except Exception as e:
            logger.error(f"LLM optimization failed: {e}")
            return base_map  # Always fall back to working Phase 1
```

### ❌ What NOT Good Looks Like (Anti-Patterns)

#### **1. Naive Line Extraction (AVOID)**
```python
# BAD: Pattern matching without understanding
def extract_critical_lines_WRONG(self, code: str):
    critical_lines = []
    
    # Simplistic pattern matching - misses context!
    for line in code.split('\n'):
        if 'return' in line or 'if' in line:
            critical_lines.append(line)  # No importance scoring!
    
    return critical_lines[:5]  # Arbitrary limit!

# BAD: Language-agnostic approach
def get_important_code_WRONG(self, symbol):
    # Same logic for all languages - terrible!
    return [line for line in symbol.code.split('\n') 
            if any(keyword in line for keyword in ['return', 'if', 'else'])]
# WHY BAD: No language awareness, no AST parsing, no business logic understanding
```

#### **2. Token-Wasting Output (AVOID)**
```python
# BAD: Verbose output with no compression
def format_output_WRONG(self, symbols):
    output = []
    output.append("=" * 50)  # Wasting tokens on decoration!
    output.append("DETAILED CODE ANALYSIS REPORT")
    output.append("=" * 50)
    
    for symbol in symbols:
        output.append(f"Function Name: {symbol.name}")  # Verbose labels!
        output.append(f"File Location: {symbol.file_path}")
        output.append(f"Line Number: {symbol.line_number}")
        output.append("Full Implementation:")
        output.append(symbol.full_code)  # Including all code regardless of importance!
        output.append("-" * 30)  # More decoration waste!
    
    return "\n".join(output)

# BAD: No token counting or budget management
def optimize_WRONG(self, content, max_tokens):
    return content[:max_tokens * 4]  # Naive character truncation!
# WHY BAD: Wastes tokens on formatting, includes irrelevant code, no budget awareness
```

#### **3. Over-Compression Losing Meaning (AVOID)**
```python
# BAD: Aggressive compression that destroys meaning
def compress_WRONG(self, code):
    # Remove all "unnecessary" words
    compressed = code.replace('function', 'fn')
    compressed = compressed.replace('return', 'ret')
    compressed = compressed.replace('if', '?')
    compressed = compressed.replace('else', ':')
    compressed = compressed.replace(' ', '')  # Remove ALL spaces!
    
    return compressed

# BAD: No validation of compressed output
def optimize_aggressive_WRONG(self, content, target_tokens):
    while self.count_tokens(content) > target_tokens:
        content = content[:-10]  # Keep removing chunks until it fits!
    return content
# WHY BAD: Makes code unreadable, loses essential information, no semantic preservation
```

#### **4. Poor Phase Integration (AVOID)**
```python
# BAD: Replaces Phase 1 & 2 instead of enhancing
class BadLLMMapper:
    def generate_map(self, project_path, intent):
        # Ignores all Phase 1 tree exploration work!
        # Ignores all Phase 2 dependency analysis!
        
        symbols = self.get_all_symbols(project_path)  # Back to basic analysis!
        critical_lines = self.extract_lines(symbols)
        return self.format_for_llm(critical_lines)

# BAD: No fallback when LLM optimization fails  
class BadIntegration:
    def generate_optimized_map(self, tree):
        # Assumes LLM optimization always works - no error handling!
        critical_lines = self.critical_extractor.extract(tree)  # Can fail!
        formatted = self.formatter.format(critical_lines)       # Can fail!
        optimized = self.optimizer.optimize(formatted)          # Can fail!
        return optimized
# WHY BAD: Doesn't leverage previous phase investments, no error recovery
```

### 🚨 Shortcut Prevention Checklist

#### **Before Claiming "Done" - Verify:**

1. **Critical Line Extraction Quality**
   - [ ] Uses AST parsing, not simple regex matching
   - [ ] Language-specific patterns for Python, JavaScript, TypeScript, Java
   - [ ] Business logic identification (not just syntax patterns)
   - [ ] Importance scoring based on code semantics, not keyword frequency

2. **Token Efficiency Standards**
   - [ ] Achieves 40%+ information density improvement over generic output
   - [ ] Uses accurate token counting (tiktoken) for different LLM models
   - [ ] Implements graceful degradation when over budget
   - [ ] Preserves essential information during compression

3. **Hierarchical Format Quality**
   - [ ] Tree-like structure that LLMs can parse easily
   - [ ] Function signatures enhanced with inferred types
   - [ ] Critical implementation lines clearly marked
   - [ ] Dependencies and relationships clearly shown

4. **Phase Integration Integrity**
   - [ ] Enhances Phase 1 tree mapping, doesn't replace it
   - [ ] Uses Phase 2 dependency intelligence for context selection
   - [ ] Falls back gracefully when LLM optimization fails
   - [ ] Preserves all existing functionality when LLM features disabled

5. **Performance and Reliability**
   - [ ] Output generation < 5 seconds for 1000 symbols
   - [ ] Memory usage < 200MB during optimization
   - [ ] Handles malformed code without crashing
   - [ ] Comprehensive error handling and logging

### 🎯 Acceptance Tests (Must Pass)

```python
# Test 1: Critical Line Extraction Accuracy
def test_critical_line_extraction():
    extractor = CriticalLineExtractor()
    
    # Test function with known critical lines
    python_function = """
    def authenticate_user(username, password):
        user = User.find_by_username(username)
        if not user:
            return AuthResult(success=False, reason="User not found")
        if not user.verify_password(password):
            user.increment_failed_attempts()
            return AuthResult(success=False, reason="Invalid password")
        user.reset_failed_attempts()
        return AuthResult(success=True, user=user)
    """
    
    symbol = Symbol(name="authenticate_user", content=python_function, language="python")
    critical_lines = extractor.extract_critical_lines(symbol)
    
    # Must identify the most important lines
    assert len(critical_lines) >= 3
    assert any("return AuthResult" in line.content for line in critical_lines)
    assert any("if not user" in line.content for line in critical_lines)
    
    # Must rank importance correctly
    assert critical_lines[0].importance > critical_lines[1].importance

# Test 2: Token Efficiency Improvement
def test_token_efficiency():
    # Generic output (baseline)
    generic_output = generate_generic_repomap(test_symbols)
    generic_tokens = token_counter.count_tokens(generic_output)
    
    # LLM-optimized output
    optimizer = TokenOptimizer()
    optimized_output = optimizer.optimize_for_token_budget(generic_output, generic_tokens)
    
    # Should contain more information in same token budget
    information_density_generic = calculate_information_density(generic_output)
    information_density_optimized = calculate_information_density(optimized_output)
    
    improvement = information_density_optimized / information_density_generic
    assert improvement >= 1.4  # 40% improvement requirement

# Test 3: Hierarchical Format Parsability
def test_hierarchical_format():
    formatter = HierarchicalFormatter()
    
    formatted_output = formatter.format_symbol_hierarchy(test_symbols)
    
    # Should be parsable by LLM (structured format)
    lines = formatted_output.split('\n')
    
    # Must have hierarchical structure
    assert any(line.startswith('├──') for line in lines)
    assert any(line.startswith('│') for line in lines)
    
    # Must include enhanced signatures
    assert any('(' in line and ')' in line and ':' in line for line in lines)
    
    # Must include critical line markers
    assert any('💡' in line or '⚠️' in line for line in lines)

# Test 4: Phase Integration
def test_phase_integration():
    # Should work with Phase 1 trees
    tree_mapper = TreeMapper(repo_map)
    llm_mapper = LLMOptimizedMapper(repo_map)
    
    exploration_tree = create_test_tree()
    
    # Phase 1 output should work
    phase1_output = tree_mapper.generate_tree_map(exploration_tree)
    assert len(phase1_output) > 0
    
    # LLM optimization should enhance, not replace
    llm_output = llm_mapper.generate_tree_map(exploration_tree)
    assert len(llm_output) > 0
    
    # Should fall back gracefully
    with mock.patch.object(llm_mapper, '_add_llm_optimizations', side_effect=Exception):
        fallback_output = llm_mapper.generate_tree_map(exploration_tree)
        assert fallback_output == phase1_output  # Falls back to Phase 1

# Test 5: Performance Requirements
def test_performance_requirements():
    large_symbol_set = generate_test_symbols(1000)  # 1000 symbols
    
    start_time = time.time()
    
    # Critical line extraction
    extractor = CriticalLineExtractor()
    for symbol in large_symbol_set:
        critical_lines = extractor.extract_critical_lines(symbol)
    
    extraction_time = time.time() - start_time
    assert extraction_time < 5.0  # 5 second limit
    
    # Token optimization
    start_time = time.time()
    optimizer = TokenOptimizer()
    large_content = "\n".join(symbol.content for symbol in large_symbol_set)
    optimized = optimizer.optimize_for_token_budget(large_content, 2048)
    optimization_time = time.time() - start_time
    
    assert optimization_time < 3.0  # 3 second limit for optimization
```

### 🚫 Automatic Failure Conditions

**Implementation FAILS if:**
- Uses simple regex instead of AST parsing for critical line extraction
- Doesn't achieve 40% information density improvement over generic output
- Token optimization breaks code semantics or removes essential information
- Doesn't integrate with Phase 1 tree exploration (replaces instead of enhances)
- No fallback when LLM optimization fails
- Doesn't meet performance requirements (> 5s for 1000 symbols)
- Output format is not hierarchical or LLM-parsable
- No accurate token counting for different LLM models
- Silent failures during optimization process

## Implementation Plan

### Week 1: Core LLM Optimization Infrastructure

#### Day 1-2: Critical Line Extraction
**Files to Create:**
- `src/repomap_tool/llm/__init__.py`
- `src/repomap_tool/llm/critical_line_extractor.py`

**Key Features:**
```python
class CriticalLineExtractor:
    def __init__(self):
        self.importance_patterns = self._load_importance_patterns()
        self.language_analyzers = {
            'python': PythonCriticalAnalyzer(),
            'javascript': JavaScriptCriticalAnalyzer(),
            'typescript': TypeScriptCriticalAnalyzer(),
            # ... more languages
        }
    
    def extract_critical_lines(self, symbol: Symbol) -> List[CriticalLine]:
        """Extract most important lines from a function/class"""
        
    def rank_line_importance(self, lines: List[str], symbol_type: str) -> List[float]:
        """Rank lines by importance for LLM understanding"""
        
    def get_implementation_essence(self, symbol: Symbol) -> str:
        """Get the essence of what this symbol does"""
```

**Importance Patterns:**
```python
IMPORTANCE_PATTERNS = {
    'python': {
        'function': {
            'high_importance': [
                r'return\s+.*',           # Return statements
                r'if\s+.*:',              # Conditional logic
                r'raise\s+.*',            # Error handling
                r'yield\s+.*',            # Generator logic
                r'.*\..*\(.*\)',          # Method calls
            ],
            'medium_importance': [
                r'for\s+.*:',             # Loops
                r'while\s+.*:',           # Loops
                r'try:',                  # Error handling
                r'except.*:',             # Error handling
            ],
            'context_lines': [
                r'""".*"""',              # Docstrings
                r'#.*',                   # Comments
            ]
        },
        'class': {
            'high_importance': [
                r'def __init__',          # Constructor
                r'def __.*__',            # Magic methods
                r'@property',             # Properties
                r'@.*',                   # Decorators
            ]
        }
    }
    # ... other languages
}
```

#### Day 3: Hierarchical Formatting
**Files to Create:**
- `src/repomap_tool/llm/hierarchical_formatter.py`

**Key Features:**
```python
class HierarchicalFormatter:
    def __init__(self):
        self.indentation_level = 0
        self.max_depth = 4
    
    def format_file_hierarchy(self, file_analysis: FileAnalysis) -> str:
        """Format file analysis in hierarchical structure"""
        
    def format_symbol_hierarchy(self, symbols: List[Symbol]) -> str:
        """Format symbols with proper hierarchy"""
        
    def create_llm_structure(self, project_analysis: ProjectAnalysis) -> str:
        """Create overall LLM-optimized structure"""
```

**Output Structure:**
```
src/auth.py:
├── imports: [os, hashlib, datetime]
├── authenticate_user(username: str, password: str) -> bool:
│   ├── line 15: if not user.verify_password(password): return False
│   ├── line 18: session = user.create_session()
│   └── returns: bool (authentication success/failure)
├── User(BaseModel):
│   ├── __init__(username: str, email: str)
│   ├── verify_password(password: str) -> bool:
│   │   └── line 45: return check_password_hash(self.password_hash, password)
│   └── create_session() -> Session:
│       └── line 52: return Session.create(user_id=self.id)
└── dependencies: [models.user, utils.crypto, database.session]
```

#### Day 4: Token Optimization
**Files to Create:**
- `src/repomap_tool/llm/token_optimizer.py`

**Key Features:**
```python
class TokenOptimizer:
    def __init__(self):
        self.token_estimator = TokenEstimator()
        self.compression_strategies = self._load_compression_strategies()
    
    def optimize_for_token_budget(
        self, 
        content: str, 
        max_tokens: int
    ) -> str:
        """Optimize content to fit within token budget"""
        
    def compress_without_losing_meaning(self, content: str) -> str:
        """Compress content while preserving important information"""
        
    def prioritize_content_by_importance(
        self, 
        sections: List[ContentSection]
    ) -> List[ContentSection]:
        """Prioritize content sections by importance"""
```

**Token Optimization Strategies:**
```python
COMPRESSION_STRATEGIES = {
    'abbreviations': {
        'function': 'fn',
        'parameter': 'param',
        'returns': 'ret',
        'class': 'cls',
    },
    'symbol_compression': {
        'remove_common_prefixes': True,
        'abbreviate_types': True,
        'compress_whitespace': True,
    },
    'content_prioritization': {
        'critical_lines': 0.4,      # 40% of budget
        'signatures': 0.3,          # 30% of budget
        'structure': 0.2,           # 20% of budget
        'context': 0.1,             # 10% of budget
    }
}
```

#### Day 5: Signature Enhancement
**Files to Create:**
- `src/repomap_tool/llm/signature_enhancer.py`

**Key Features:**
```python
class SignatureEnhancer:
    def __init__(self):
        self.type_inference = TypeInferenceEngine()
        self.signature_patterns = self._load_signature_patterns()
    
    def enhance_function_signature(self, symbol: Symbol) -> EnhancedSignature:
        """Enhance function signature with type information"""
        
    def infer_missing_types(self, symbol: Symbol) -> Dict[str, str]:
        """Infer types for parameters/returns when not explicitly typed"""
        
    def add_call_patterns(self, symbol: Symbol) -> List[str]:
        """Add common call patterns for this function"""
```

### Week 2: Integration and Advanced Features

#### Day 6-7: Context Selection and Integration
**Files to Create:**
- `src/repomap_tool/llm/context_selector.py`
- `src/repomap_tool/llm/output_templates.py`

**Context Selection:**
```python
class ContextSelector:
    def __init__(self, dependency_graph, context_manager):
        self.dependency_graph = dependency_graph
        self.context_manager = context_manager
    
    def select_optimal_context(
        self, 
        all_symbols: List[Symbol], 
        user_context: ConversationContext,
        token_budget: int
    ) -> List[Symbol]:
        """Select optimal symbols to include given token budget"""
        
    def balance_breadth_vs_depth(
        self, 
        symbols: List[Symbol], 
        budget: int
    ) -> List[Symbol]:
        """Balance showing many files vs detailed information"""
```

**Output Templates:**
```python
class OutputTemplates:
    def __init__(self):
        self.templates = {
            'function_template': self._load_function_template(),
            'class_template': self._load_class_template(),
            'file_template': self._load_file_template(),
            'project_template': self._load_project_template(),
        }
    
    def apply_template(self, symbol: Symbol, template_type: str) -> str:
        """Apply LLM-optimized template to symbol"""
```

#### Day 8-9: Integration with Existing Components
**Files to Modify:**
- `src/repomap_tool/context/context_aware_mapper.py`
- `src/repomap_tool/core/repo_map.py`

**Enhanced Context-Aware Mapper:**
```python
class LLMOptimizedMapper(ContextAwareMapper):
    def __init__(self, repo_map: DockerRepoMap):
        super().__init__(repo_map)
        self.critical_extractor = CriticalLineExtractor()
        self.hierarchical_formatter = HierarchicalFormatter()
        self.token_optimizer = TokenOptimizer()
        self.context_selector = ContextSelector(
            self.repo_map.dependency_graph,
            self.context_manager
        )
    
    def generate_llm_optimized_map(
        self, 
        message: str, 
        current_files: List[str] = None,
        max_tokens: int = 1024
    ) -> str:
        """Generate LLM-optimized repomap"""
        
        # 1. Get context-aware and dependency-ranked symbols
        symbols = self.get_prioritized_symbols(message, current_files)
        
        # 2. Select optimal context within token budget
        selected_symbols = self.context_selector.select_optimal_context(
            symbols, self.context_manager.current_context, max_tokens
        )
        
        # 3. Extract critical lines for each symbol
        for symbol in selected_symbols:
            symbol.critical_lines = self.critical_extractor.extract_critical_lines(symbol)
        
        # 4. Format hierarchically
        formatted_content = self.hierarchical_formatter.format_symbol_hierarchy(
            selected_symbols
        )
        
        # 5. Optimize for token budget
        optimized_content = self.token_optimizer.optimize_for_token_budget(
            formatted_content, max_tokens
        )
        
        return optimized_content
```

#### Day 10: Advanced LLM Features
**Files to Create:**
- `src/repomap_tool/llm/semantic_grouping.py`
- `src/repomap_tool/llm/call_pattern_analyzer.py`

**Semantic Grouping:**
```python
class SemanticGrouping:
    def __init__(self):
        self.grouping_strategies = self._load_grouping_strategies()
    
    def group_related_symbols(self, symbols: List[Symbol]) -> List[SymbolGroup]:
        """Group semantically related symbols together"""
        
    def create_logical_sections(self, symbols: List[Symbol]) -> List[Section]:
        """Create logical sections (auth, data, ui, etc.)"""
```

**Call Pattern Analysis:**
```python
class CallPatternAnalyzer:
    def __init__(self, call_graph):
        self.call_graph = call_graph
    
    def analyze_usage_patterns(self, symbol: Symbol) -> UsagePattern:
        """Analyze how this symbol is typically used"""
        
    def generate_usage_examples(self, symbol: Symbol) -> List[str]:
        """Generate typical usage examples for LLM"""
```

### Advanced Features and Testing

#### Day 11-12: Output Quality Optimization
**Focus Areas:**
- Readability optimization for LLMs
- Information density maximization
- Error handling for malformed code
- Performance optimization

#### Day 13-14: Testing and Validation
**Testing Strategy:**
- LLM consumption tests (feed output to actual LLMs)
- Token counting accuracy tests
- Information preservation tests
- Performance benchmarks

## Integration with CLI and API

### Enhanced CLI Commands
```bash
# LLM-optimized output
repomap-tool generate-llm /path/to/project --message "fix auth bug" --max-tokens 2048
repomap-tool optimize-tokens /path/to/project --input analysis.txt --target-tokens 1024
repomap-tool extract-critical /path/to/project --file auth.py --function authenticate_user
```

### Enhanced API Endpoints
```python
POST /repo-map/llm-optimized
{
    "project_path": "/path/to/project",
    "message": "I need to fix authentication",
    "max_tokens": 2048,
    "optimization_level": "high"
}

POST /llm/extract-critical
{
    "file_path": "src/auth.py",
    "symbol_name": "authenticate_user"
}
```

## Configuration Changes

### New LLM Config
```python
class LLMConfig(BaseModel):
    enabled: bool = True
    max_tokens_default: int = 1024
    extract_critical_lines: bool = True
    hierarchical_format: bool = True
    optimize_for_tokens: bool = True
    include_type_signatures: bool = True
    include_call_patterns: bool = True
    compression_level: str = "medium"  # low, medium, high
    output_style: str = "hierarchical"  # flat, hierarchical, semantic

class RepoMapConfig(BaseModel):
    # ... existing fields ...
    llm: LLMConfig = LLMConfig()
```

## Output Format Examples

### Before (Current)
```
src/auth.py:
  authenticate_user: def authenticate_user(username, password)
  User: class User:
    __init__: def __init__(self, username, email)
    verify_password: def verify_password(self, password)
```

### After (LLM-Optimized)
```
src/auth.py:15:
├── authenticate_user(username: str, password: str) -> bool:
│   ├── Critical: if not user.verify_password(password): return False
│   ├── Critical: session = user.create_session()
│   └── Usage: success = authenticate_user("john", "secret123")
├── User(BaseModel):42:
│   ├── __init__(username: str, email: str)
│   ├── verify_password(password: str) -> bool:
│   │   └── Critical: return check_password_hash(self.password_hash, password)
│   └── create_session() -> Session:
│       └── Critical: return Session.create(user_id=self.id)
└── Dependencies: models.user, utils.crypto, database.session
```

## Success Metrics

### Quality Metrics
- [ ] LLMs can understand code structure 95%+ accurately from optimized output
- [ ] Token efficiency improves by 40%+ (more information per token)
- [ ] Critical line extraction identifies most important lines 90%+ accurately
- [ ] Hierarchical format reduces LLM parsing errors by 50%+

### Performance Metrics
- [ ] Output generation time < 5 seconds for 1000 symbols
- [ ] Memory usage < 200MB for optimization processing
- [ ] Token counting accuracy within 5% of actual LLM tokenization

### User Experience Metrics
- [ ] LLM-generated code based on optimized repomaps has fewer errors
- [ ] Developers report better LLM suggestions when using optimized output
- [ ] Reduced need for follow-up questions to LLMs

## Risk Mitigation

### Technical Risks
- **Over-optimization:** Losing important information while compressing
- **Format Complexity:** Making output too complex for some LLMs
- **Performance Impact:** Optimization taking too long

### Mitigation Strategies
- Configurable optimization levels
- A/B testing with different LLMs
- Performance monitoring and optimization
- Fallback to simpler formats when needed

## Dependencies

### New Dependencies
```toml
# Add to pyproject.toml
tiktoken = "^0.5"        # Token counting for different LLM models
Pygments = "^2.15"       # Code syntax highlighting/parsing
jinja2 = "^3.1"          # Template engine for output formatting
```

## Definition of Done

### Phase 3 Complete When:
- [ ] Critical line extraction works accurately for major languages
- [ ] Hierarchical formatting is LLM-friendly and readable
- [ ] Token optimization achieves 40%+ efficiency improvement
- [ ] Signature enhancement adds valuable type information
- [ ] Context selection balances breadth vs depth optimally
- [ ] Integration with Phases 1 & 2 works seamlessly
- [ ] Output templates are optimized for major LLM models
- [ ] Performance meets targets (< 5s for optimization)
- [ ] CLI and API provide full LLM optimization features
- [ ] Test coverage > 90%
- [ ] Documentation includes LLM integration examples
- [ ] A/B testing shows improved LLM performance with optimized output

This phase will make the repomap output significantly more effective for LLM consumption, maximizing the value of context within token constraints.

