#!/usr/bin/env python3
"""
LLM Optimization Demo

This script demonstrates the LLM optimization features of the RepoMap Tool,
showing how code analysis can be optimized for LLM consumption.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from repomap_tool.llm import (
    CriticalLineExtractor,
    HierarchicalFormatter,
    TokenOptimizer,
    SignatureEnhancer,
    ContextSelector,
    OutputTemplates,
)
from repomap_tool.llm.context_selector import SelectionStrategy


def demo_critical_line_extraction():
    """Demonstrate critical line extraction."""
    print("🔍 Demo: Critical Line Extraction")
    print("=" * 50)

    # Sample Python function
    sample_code = '''
def authenticate_user(username, password):
    """Authenticate a user with username and password."""
    user = User.find_by_username(username)
    if not user:
        return AuthResult(success=False, reason="User not found")
    
    if not user.verify_password(password):
        user.increment_failed_attempts()
        return AuthResult(success=False, reason="Invalid password")
    
    user.reset_failed_attempts()
    session = user.create_session()
    return AuthResult(success=True, user=user, session=session)
'''

    extractor = CriticalLineExtractor()
    critical_lines = extractor.extract_critical_lines(sample_code, "python")

    print("Sample Code:")
    print(sample_code)
    print("\nCritical Lines Extracted:")
    for line in critical_lines:
        print(f"  Line {line.line_number}: {line.content}")
        print(f"    Importance: {line.importance:.2f}, Type: {line.pattern_type}")

    print(
        f"\nImplementation Essence: {extractor.get_implementation_essence(sample_code, 'python')}"
    )
    print()


def demo_signature_enhancement():
    """Demonstrate signature enhancement."""
    print("🔧 Demo: Signature Enhancement")
    print("=" * 50)

    # Sample function with minimal type information
    sample_code = '''
def process_payment(amount, card, user):
    """Process a payment with the given amount and card."""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    if not card.is_valid():
        return PaymentResult(success=False, error="Invalid card")
    
    result = payment_gateway.charge(amount, card.token)
    if result.success:
        user.add_payment_history(result)
        return PaymentResult(success=True, transaction_id=result.id)
    else:
        return PaymentResult(success=False, error=result.error)
'''

    enhancer = SignatureEnhancer()
    enhanced = enhancer.enhance_function_signature(sample_code, "python")

    print("Original Code:")
    print(sample_code)
    print("\nEnhanced Signature:")
    print(f"  Original: {enhanced.original_signature}")
    print(f"  Enhanced: {enhanced.enhanced_signature}")
    print(f"  Parameter Types: {enhanced.parameter_types}")
    print(f"  Return Type: {enhanced.return_type}")
    print(f"  Usage Examples: {enhanced.usage_examples}")
    print(f"  Error Cases: {enhanced.error_cases}")
    print(f"  Complexity Score: {enhanced.complexity_score:.2f}")
    print()


def demo_hierarchical_formatting():
    """Demonstrate hierarchical formatting."""
    print("🌳 Demo: Hierarchical Formatting")
    print("=" * 50)

    # Sample symbol data
    sample_symbols = [
        {
            "name": "authenticate_user",
            "file_path": "src/auth/service.py",
            "line_number": 15,
            "symbol_type": "function",
            "signature": "def authenticate_user(username: str, password: str) -> AuthResult",
            "critical_lines": [
                'if not user: return AuthResult(success=False, reason="User not found")',
                'if not user.verify_password(password): return AuthResult(success=False, reason="Invalid password")',
                "return AuthResult(success=True, user=user, session=session)",
            ],
            "dependencies": [
                "User.find_by_username",
                "user.verify_password",
                "user.create_session",
            ],
            "centrality_score": 0.95,
            "impact_risk": 0.8,
        },
        {
            "name": "User",
            "file_path": "src/auth/models.py",
            "line_number": 42,
            "symbol_type": "class",
            "signature": "class User(BaseModel)",
            "critical_lines": [
                "def verify_password(self, password: str) -> bool:",
                "return check_password_hash(self.password_hash, password)",
            ],
            "dependencies": ["BaseModel", "check_password_hash"],
            "centrality_score": 0.87,
            "impact_risk": 0.6,
        },
    ]

    formatter = HierarchicalFormatter()
    formatted = formatter.format_symbol_hierarchy(sample_symbols)

    print("Sample Symbols:")
    for symbol in sample_symbols:
        print(f"  - {symbol['name']} ({symbol['symbol_type']})")

    print("\nHierarchically Formatted Output:")
    print(formatted)
    print()


def demo_token_optimization():
    """Demonstrate token optimization."""
    print("📊 Demo: Token Optimization")
    print("=" * 50)

    # Sample content that might be over token budget
    sample_content = """
🧠 LLM-Optimized Repomap: Payment Processing System
============================================================
📊 Summary: 25 files, 150 symbols

📁 src/auth/
    ├── service.py (8 symbols) [Centrality: 0.95]
        ├── authenticate_user(username: str, password: str) -> AuthResult
        │   💡 Critical: if not user: return AuthResult(success=False, reason="User not found")
        │   💡 Critical: if not user.verify_password(password): return AuthResult(success=False, reason="Invalid password")
        │   💡 Critical: return AuthResult(success=True, user=user, session=session)
        │   📞 Usage: result = authenticate_user("john", "secret123")
        │   🔗 Dependencies: User.find_by_username, user.verify_password, user.create_session
        └── validate_token(token: str) -> bool
            💡 Critical: return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            🔗 Dependencies: jwt.decode, SECRET_KEY

📁 src/payments/
    ├── gateway.py (12 symbols) [Centrality: 0.88]
        ├── process_payment(amount: Decimal, card: CreditCard) -> PaymentResult
        │   💡 Critical: if amount <= 0: raise ValueError("Amount must be positive")
        │   💡 Critical: result = stripe.Charge.create(amount=int(amount*100), source=card.token)
        │   💡 Critical: return PaymentResult(success=True, transaction_id=result.id)
        │   📞 Usage: result = gateway.process_payment(Decimal('99.99'), user.credit_card)
        │   🔗 Dependencies: stripe.Charge, PaymentResult, user.credit_card
        └── handle_webhook(payload: dict, signature: str) -> bool
            💡 Critical: if not verify_signature(payload, signature): return False
            🔗 Dependencies: verify_signature, process_webhook_event

📁 src/models/
    ├── user.py (15 symbols) [Centrality: 0.82]
        ├── User(BaseModel)
        │   ├── __init__(username: str, email: str)
        │   ├── verify_password(password: str) -> bool
        │   │   💡 Critical: return check_password_hash(self.password_hash, password)
        │   └── create_session() -> Session
        │       💡 Critical: return Session.create(user_id=self.id)
        │   🔗 Dependencies: BaseModel, check_password_hash, Session
        └── Session(BaseModel)
            ├── __init__(user_id: int, expires_at: datetime)
            └── is_expired() -> bool
                💡 Critical: return datetime.utcnow() > self.expires_at
                🔗 Dependencies: datetime.utcnow

📁 src/utils/
    ├── crypto.py (8 symbols) [Centrality: 0.75]
        ├── hash_password(password: str) -> str
        │   💡 Critical: return generate_password_hash(password, method='sha256')
        │   🔗 Dependencies: generate_password_hash
        └── verify_signature(payload: bytes, signature: str) -> bool
            💡 Critical: expected = hmac.new(SECRET_KEY.encode(), payload, hashlib.sha256).hexdigest()
            💡 Critical: return hmac.compare_digest(expected, signature)
            🔗 Dependencies: hmac.new, hashlib.sha256, hmac.compare_digest
"""

    optimizer = TokenOptimizer()

    # Estimate current tokens
    current_tokens = optimizer.token_estimator.count_tokens(sample_content)
    target_tokens = 800  # Target budget

    print(f"Current Content Length: {len(sample_content)} characters")
    print(f"Estimated Current Tokens: {current_tokens}")
    print(f"Target Token Budget: {target_tokens}")
    print(
        f"Token Budget Status: {'✅ Within Budget' if current_tokens <= target_tokens else '❌ Over Budget'}"
    )

    if current_tokens > target_tokens:
        print(f"\nOptimizing content to fit within {target_tokens} tokens...")
        optimized = optimizer.optimize_for_token_budget(sample_content, target_tokens)
        optimized_tokens = optimizer.token_estimator.count_tokens(optimized)

        print(f"\nOptimized Content Length: {len(optimized)} characters")
        print(f"Optimized Token Count: {optimized_tokens}")
        print(f"Compression Ratio: {len(sample_content) / len(optimized):.2f}x")
        print(
            f"Token Reduction: {((current_tokens - optimized_tokens) / current_tokens * 100):.1f}%"
        )

        print("\nOptimized Content Preview:")
        print(optimized[:500] + "..." if len(optimized) > 500 else optimized)

    print()


def demo_context_selection():
    """Demonstrate context selection."""
    print("🎯 Demo: Context Selection")
    print("=" * 50)

    # Sample symbols with different characteristics
    sample_symbols = [
        {
            "name": "authenticate_user",
            "centrality_score": 0.95,
            "impact_risk": 0.9,
            "complexity_score": 0.8,
            "file_path": "src/auth/service.py",
            "line_number": 15,
        },
        {
            "name": "process_payment",
            "centrality_score": 0.88,
            "impact_risk": 0.85,
            "complexity_score": 0.7,
            "file_path": "src/payments/gateway.py",
            "line_number": 25,
        },
        {
            "name": "User",
            "centrality_score": 0.82,
            "impact_risk": 0.6,
            "complexity_score": 0.5,
            "file_path": "src/models/user.py",
            "line_number": 42,
        },
        {
            "name": "hash_password",
            "centrality_score": 0.75,
            "impact_risk": 0.4,
            "complexity_score": 0.3,
            "file_path": "src/utils/crypto.py",
            "line_number": 18,
        },
        {
            "name": "validate_token",
            "centrality_score": 0.68,
            "impact_risk": 0.5,
            "complexity_score": 0.4,
            "file_path": "src/auth/service.py",
            "line_number": 45,
        },
    ]

    selector = ContextSelector()

    # Test different strategies
    strategies = ["breadth_first", "depth_first", "hybrid", "centrality_based"]

    for strategy_name in strategies:
        print(f"\nStrategy: {strategy_name.upper()}")
        print("-" * 30)

        if strategy_name == "breadth_first":
            strategy = SelectionStrategy.BREADTH_FIRST
        elif strategy_name == "depth_first":
            strategy = SelectionStrategy.DEPTH_FIRST
        elif strategy_name == "hybrid":
            strategy = SelectionStrategy.HYBRID
        else:
            strategy = SelectionStrategy.CENTRALITY_BASED

        selection = selector.select_optimal_context(
            sample_symbols, token_budget=600, strategy=strategy
        )

        print(f"Selected Symbols: {len(selection.selected_symbols)}")
        print(f"Total Tokens: {selection.total_tokens}")
        print(f"Coverage: {selection.coverage_percentage:.1f}%")
        print(f"Priority Breakdown: {selection.priority_breakdown}")

        print("Selected Symbols:")
        for symbol in selection.selected_symbols:
            print(
                f"  - {symbol['name']} (Centrality: {symbol['centrality_score']:.2f})"
            )

    print()


def main():
    """Run all demos."""
    print("🚀 RepoMap Tool - LLM Optimization Demo")
    print("=" * 60)
    print()

    try:
        demo_critical_line_extraction()
        demo_signature_enhancement()
        demo_hierarchical_formatting()
        demo_token_optimization()
        demo_context_selection()

        print("✅ All demos completed successfully!")
        print("\n🎉 The LLM optimization components are working correctly!")
        print("These components provide:")
        print("  - Intelligent critical line extraction")
        print("  - Enhanced function signatures with type inference")
        print("  - Hierarchical output formatting")
        print("  - Token budget optimization")
        print("  - Smart context selection")
        print("  - Model-specific output templates")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
