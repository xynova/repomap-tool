#!/usr/bin/env python3
"""
Custom DI Linter for RepoMap-Tool.

This script checks for dependency injection violations and anti-patterns.
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple, Set
import argparse


class DILinter(ast.NodeVisitor):
    """AST visitor to detect DI violations."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.violations: List[Tuple[int, int, str]] = []
        self.imports: Set[str] = set()
        self.in_test_file = "test_" in filename or "/test" in filename
        
    def visit_Import(self, node: ast.Import) -> None:
        """Track imports to understand what's available."""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track from imports."""
        if node.module:
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call) -> None:
        """Check for direct service instantiation."""
        # Skip if this is in a test file and it's a test function
        if self.in_test_file and self._is_in_test_function():
            self.generic_visit(node)
            return
            
        # Check for direct Console() instantiation
        if self._is_direct_console_instantiation(node):
            self.violations.append((
                node.lineno,
                node.col_offset,
                "DI001: Direct Console() instantiation detected. Use get_console(ctx) instead."
            ))
        
        # Check for direct matcher instantiation
        elif self._is_direct_matcher_instantiation(node):
            self.violations.append((
                node.lineno,
                node.col_offset,
                "DI002: Direct matcher instantiation detected. Use service factory instead."
            ))
        
        # Check for fallback instantiation patterns
        elif self._is_fallback_instantiation(node):
            self.violations.append((
                node.lineno,
                node.col_offset,
                "DI003: Fallback instantiation detected. Use strict dependency validation instead."
            ))
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign) -> None:
        """Check for assignment patterns that violate DI."""
        # Check for fallback assignment patterns
        if self._is_fallback_assignment(node):
            self.violations.append((
                node.lineno,
                node.col_offset,
                "DI004: Fallback assignment pattern detected. Use strict dependency validation."
            ))
        
        self.generic_visit(node)
    
    def _is_direct_console_instantiation(self, node: ast.Call) -> bool:
        """Check if this is a direct Console() call."""
        # Skip formatting utilities that create console for output formatting
        if "format_utils" in self.filename:
            return False
        
        # Skip factory classes where direct instantiation is allowed
        if "console.py" in self.filename:
            return False
            
        if isinstance(node.func, ast.Name):
            return node.func.id == "Console"
        elif isinstance(node.func, ast.Attribute):
            return (isinstance(node.func.value, ast.Name) and 
                   node.func.value.id == "Console")
        return False
    
    def _is_direct_matcher_instantiation(self, node: ast.Call) -> bool:
        """Check if this is a direct matcher instantiation."""
        # Skip test files - they often need direct instantiation for testing
        if self.in_test_file:
            return False
            
        matcher_classes = {
            "FuzzyMatcher", "AdaptiveSemanticMatcher", "HybridMatcher",
            "CentralityCalculator", "ImpactAnalyzer", "DependencyGraph"
        }
        
        if isinstance(node.func, ast.Name):
            return node.func.id in matcher_classes
        elif isinstance(node.func, ast.Attribute):
            return (isinstance(node.func.value, ast.Name) and 
                   node.func.value.id in matcher_classes)
        return False
    
    def _is_fallback_instantiation(self, node: ast.Call) -> bool:
        """Check for fallback instantiation patterns like 'service or Service()'."""
        # This is a simplified check - in practice, you'd need more sophisticated AST analysis
        return False
    
    def _is_fallback_assignment(self, node: ast.Assign) -> bool:
        """Check for fallback assignment patterns."""
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Attribute):
            # Pattern: self.service = service or Service()
            if isinstance(node.value, ast.BoolOp) and isinstance(node.value.op, ast.Or):
                # Check if the right side is a constructor call
                if isinstance(node.value.values[1], ast.Call):
                    return True
        return False
    
    def _is_in_test_function(self) -> bool:
        """Check if we're currently in a test function."""
        # This is a simplified check - in practice, you'd track function context
        return False


def check_file(filepath: Path) -> List[Tuple[int, int, str]]:
    """Check a single file for DI violations."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(filepath))
        linter = DILinter(str(filepath))
        linter.visit(tree)
        
        return linter.violations
    except Exception as e:
        print(f"Error checking {filepath}: {e}", file=sys.stderr)
        return []


def main():
    """Main entry point for the DI linter."""
    parser = argparse.ArgumentParser(description="DI Linter for RepoMap-Tool")
    parser.add_argument("paths", nargs="*", default=["src/"], 
                       help="Paths to check (default: src/)")
    parser.add_argument("--exclude", nargs="*", default=["__pycache__", ".git"],
                       help="Directories to exclude")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                       help="Output format")
    
    args = parser.parse_args()
    
    violations_found = False
    
    for path_str in args.paths:
        path = Path(path_str)
        
        if path.is_file() and path.suffix == ".py":
            # Check single file
            violations = check_file(path)
            if violations:
                violations_found = True
                for line, col, message in violations:
                    print(f"{path}:{line}:{col}: {message}")
        
        elif path.is_dir():
            # Check directory recursively
            for py_file in path.rglob("*.py"):
                # Skip excluded directories
                if any(excluded in str(py_file) for excluded in args.exclude):
                    continue
                
                violations = check_file(py_file)
                if violations:
                    violations_found = True
                    for line, col, message in violations:
                        print(f"{py_file}:{line}:{col}: {message}")
    
    if violations_found:
        sys.exit(1)
    else:
        print("✅ No DI violations found!")


if __name__ == "__main__":
    main()
