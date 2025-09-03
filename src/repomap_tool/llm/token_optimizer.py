"""
Token optimizer for LLM output efficiency.

This module optimizes repomap output to maximize information density
within token budget constraints for different LLM models.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CompressionLevel(Enum):
    """Compression levels for token optimization."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class BudgetAllocation:
    """Token budget allocation for different content types."""
    critical_lines: float = 0.4      # 40% for critical implementation
    signatures: float = 0.3          # 30% for function signatures
    structure: float = 0.2           # 20% for hierarchical structure
    context: float = 0.1             # 10% for context information
    
    def to_token_counts(self, total_tokens: int) -> Dict[str, int]:
        """Convert percentages to actual token counts."""
        return {
            'critical_lines': int(total_tokens * self.critical_lines),
            'signatures': int(total_tokens * self.signatures),
            'structure': int(total_tokens * self.structure),
            'context': int(total_tokens * self.context)
        }


class TokenEstimator:
    """Estimates token count for different LLM models."""
    
    def __init__(self):
        # Rough token estimation (words + punctuation)
        # In production, would use tiktoken for accurate counting
        self.words_per_token = 0.75  # Average words per token
        self.punctuation_multiplier = 1.1  # Punctuation increases token count
    
    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Estimate token count for given text and model.
        
        Args:
            text: Text to count tokens for
            model: LLM model name
            
        Returns:
            Estimated token count
        """
        # Simple estimation based on word count
        words = len(text.split())
        punctuation = len(re.findall(r'[^\w\s]', text))
        
        # Base token count
        base_tokens = int(words / self.words_per_token)
        
        # Adjust for punctuation
        punctuation_tokens = int(punctuation * self.punctuation_multiplier)
        
        total_tokens = base_tokens + punctuation_tokens
        
        # Model-specific adjustments
        if "gpt-4" in model.lower():
            # GPT-4 is more efficient with structured text
            total_tokens = int(total_tokens * 0.9)
        elif "claude" in model.lower():
            # Claude is good with hierarchical text
            total_tokens = int(total_tokens * 0.95)
        elif "gemini" in model.lower():
            # Gemini is similar to GPT-4
            total_tokens = int(total_tokens * 0.9)
        
        return max(1, total_tokens)
    
    def estimate_content_size(self, content: Dict[str, Any]) -> int:
        """Estimate total token count for content structure.
        
        Args:
            content: Content dictionary with various sections
            
        Returns:
            Estimated total token count
        """
        total_tokens = 0
        
        # Estimate tokens for each section
        if 'symbols' in content:
            for symbol in content['symbols']:
                symbol_tokens = self.count_tokens(str(symbol))
                total_tokens += symbol_tokens
        
        if 'structure' in content:
            structure_tokens = self.count_tokens(str(content['structure']))
            total_tokens += structure_tokens
        
        if 'context' in content:
            context_tokens = self.count_tokens(str(content['context']))
            total_tokens += context_tokens
        
        return total_tokens


class TokenOptimizer:
    """Optimizes output for maximum information per token."""
    
    def __init__(self, compression_level: CompressionLevel = CompressionLevel.MEDIUM):
        self.compression_level = compression_level
        self.token_estimator = TokenEstimator()
        self.compression_strategies = self._load_compression_strategies()
    
    def optimize_for_token_budget(
        self, 
        content: str, 
        max_tokens: int,
        model: str = "gpt-4"
    ) -> str:
        """Optimize content to fit within token budget.
        
        Args:
            content: Raw content to optimize
            max_tokens: Maximum allowed tokens
            model: Target LLM model
            
        Returns:
            Token-optimized content
        """
        current_tokens = self.token_estimator.count_tokens(content, model)
        
        if current_tokens <= max_tokens:
            logger.info(f"Content already within budget: {current_tokens}/{max_tokens}")
            return content
        
        logger.info(f"Optimizing content: {current_tokens} -> {max_tokens} tokens")
        
        # Apply progressive compression strategies
        strategies = self._get_compression_strategies()
        optimized_content = content
        
        for strategy_name, strategy_func in strategies:
            try:
                optimized_content = strategy_func(optimized_content, max_tokens)
                current_tokens = self.token_estimator.count_tokens(optimized_content, model)
                
                logger.debug(f"Applied {strategy_name}: {current_tokens} tokens")
                
                if current_tokens <= max_tokens:
                    logger.info(f"Budget achieved with {strategy_name}")
                    break
                    
            except Exception as e:
                logger.warning(f"Strategy {strategy_name} failed: {e}")
                continue
        
        # Final validation
        final_tokens = self.token_estimator.count_tokens(optimized_content, model)
        if final_tokens > max_tokens:
            logger.warning(f"Could not meet budget, using emergency truncation")
            optimized_content = self._emergency_truncation(optimized_content, max_tokens, model)
        
        return optimized_content
    
    def compress_without_losing_meaning(self, content: str) -> str:
        """Compress content while preserving important information.
        
        Args:
            content: Content to compress
            
        Returns:
            Compressed content
        """
        compressed = content
        
        # Apply safe compression strategies
        compressed = self._remove_extra_whitespace(compressed)
        compressed = self._abbreviate_common_patterns(compressed)
        compressed = self._compress_variable_names(compressed)
        
        # Validate compression didn't break anything important
        if self._validate_compression(content, compressed):
            return compressed
        else:
            logger.warning("Compression validation failed, using original")
            return content
    
    def prioritize_content_by_importance(
        self, 
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Prioritize content sections by importance.
        
        Args:
            sections: List of content sections with importance scores
            
        Returns:
            Prioritized list of sections
        """
        # Sort by importance score (higher is more important)
        prioritized = sorted(sections, key=lambda x: x.get('importance', 0.0), reverse=True)
        
        # Group by importance level
        high_importance = [s for s in prioritized if s.get('importance', 0.0) > 0.8]
        medium_importance = [s for s in prioritized if 0.5 <= s.get('importance', 0.0) <= 0.8]
        low_importance = [s for s in prioritized if s.get('importance', 0.0) < 0.5]
        
        # Return in priority order
        return high_importance + medium_importance + low_importance
    
    def allocate_token_budget(
        self, 
        content: Dict[str, Any], 
        max_tokens: int
    ) -> BudgetAllocation:
        """Allocate token budget based on content characteristics.
        
        Args:
            content: Content to analyze
            max_tokens: Total available tokens
            
        Returns:
            Budget allocation strategy
        """
        # Analyze content complexity
        total_symbols = len(content.get('symbols', []))
        high_centrality_symbols = [
            s for s in content.get('symbols', []) 
            if s.get('centrality_score', 0.0) > 0.8
        ]
        
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
        
        return allocation
    
    def _load_compression_strategies(self) -> Dict[str, Any]:
        """Load compression strategies based on compression level."""
        base_strategies = {
            'abbreviations': {
                'function': 'fn',
                'parameter': 'param',
                'returns': 'ret',
                'class': 'cls',
                'method': 'meth',
                'variable': 'var',
            },
            'symbol_compression': {
                'remove_common_prefixes': True,
                'abbreviate_types': True,
                'compress_whitespace': True,
            }
        }
        
        if self.compression_level == CompressionLevel.HIGH:
            base_strategies['symbol_compression']['aggressive_compression'] = True
            base_strategies['symbol_compression']['remove_optional_words'] = True
        
        return base_strategies
    
    def _get_compression_strategies(self) -> List[Tuple[str, callable]]:
        """Get ordered list of compression strategies to apply."""
        strategies = [
            ("whitespace_compression", self._remove_extra_whitespace),
            ("pattern_abbreviation", self._abbreviate_common_patterns),
            ("variable_compression", self._compress_variable_names),
            ("repetitive_content_compression", self._summarize_repetitive_patterns),
            ("context_reduction", self._reduce_context_information),
        ]
        
        if self.compression_level == CompressionLevel.HIGH:
            strategies.extend([
                ("aggressive_compression", self._apply_aggressive_compression),
            ])
        
        return strategies
    
    def _remove_extra_whitespace(self, content: str) -> str:
        """Remove unnecessary whitespace."""
        # Remove multiple blank lines
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Remove trailing whitespace
        content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
        
        # Compress multiple spaces to single space
        content = re.sub(r'[ \t]+', ' ', content)
        
        return content
    
    def _abbreviate_common_patterns(self, content: str) -> str:
        """Abbreviate common patterns to save tokens."""
        abbreviations = self.compression_strategies['abbreviations']
        
        for full, abbrev in abbreviations.items():
            # Replace whole words only
            pattern = r'\b' + re.escape(full) + r'\b'
            content = re.sub(pattern, abbrev, content, flags=re.IGNORECASE)
        
        return content
    
    def _compress_variable_names(self, content: str) -> str:
        """Compress variable names where safe."""
        # This is a conservative approach - only compress very long names
        # In production, would need more sophisticated analysis
        
        # Compress common long variable names
        long_name_mappings = {
            'authentication_result': 'auth_result',
            'user_credentials': 'creds',
            'validation_response': 'val_resp',
            'configuration_settings': 'config',
        }
        
        for long_name, short_name in long_name_mappings.items():
            pattern = r'\b' + re.escape(long_name) + r'\b'
            content = re.sub(pattern, short_name, content)
        
        return content
    
    def _summarize_repetitive_patterns(self, content: str) -> str:
        """Summarize repetitive content patterns."""
        lines = content.split('\n')
        summarized_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for repetitive patterns
            if i + 2 < len(lines):
                next_line = lines[i + 1]
                next_next_line = lines[i + 2]
                
                if (line.strip() == next_line.strip() == next_next_line.strip() and 
                    line.strip() and not line.strip().startswith('#')):
                    # Found repetition, summarize
                    summarized_lines.append(line)
                    summarized_lines.append(f"    ... repeated {len(lines) - i} times")
                    break
            
            summarized_lines.append(line)
            i += 1
        
        return '\n'.join(summarized_lines)
    
    def _reduce_context_information(self, content: str) -> str:
        """Reduce context information to save tokens."""
        lines = content.split('\n')
        reduced_lines = []
        
        for line in lines:
            # Skip verbose context lines
            if any(skip_pattern in line.lower() for skip_pattern in [
                'context:', 'background:', 'note:', 'info:', 'details:'
            ]):
                continue
            
            # Keep essential lines
            if any(keep_pattern in line.lower() for keep_pattern in [
                'critical:', 'important:', 'key:', 'main:', 'core:'
            ]):
                reduced_lines.append(line)
                continue
            
            # Keep structural lines
            if line.strip().startswith(('├──', '└──', '│')):
                reduced_lines.append(line)
                continue
            
            # Keep function/class definitions
            if re.search(r'\b(def|class|function)\b', line):
                reduced_lines.append(line)
                continue
            
            # Skip other lines to save tokens
            continue
        
        return '\n'.join(reduced_lines)
    
    def _apply_aggressive_compression(self, content: str) -> str:
        """Apply aggressive compression strategies."""
        # Only use for high compression level
        if self.compression_level != CompressionLevel.HIGH:
            return content
        
        # Aggressive abbreviation
        aggressive_abbrevs = {
            'implementation': 'impl',
            'configuration': 'config',
            'authentication': 'auth',
            'authorization': 'authz',
            'validation': 'val',
            'initialization': 'init',
        }
        
        for full, abbrev in aggressive_abbrevs.items():
            pattern = r'\b' + re.escape(full) + r'\b'
            content = re.sub(pattern, abbrev, content, flags=re.IGNORECASE)
        
        return content
    
    def _emergency_truncation(self, content: str, max_tokens: int, model: str) -> str:
        """Emergency truncation when other strategies fail."""
        lines = content.split('\n')
        truncated_lines = []
        current_tokens = 0
        
        for line in lines:
            line_tokens = self.token_estimator.count_tokens(line, model)
            
            if current_tokens + line_tokens <= max_tokens - 20:  # Leave buffer for truncation message
                truncated_lines.append(line)
                current_tokens += line_tokens
            else:
                break
        
        # Add truncation message
        truncated_lines.append("")
        truncated_lines.append(f"... truncated at {max_tokens} tokens")
        
        return '\n'.join(truncated_lines)
    
    def _validate_compression(self, original: str, compressed: str) -> bool:
        """Validate that compression didn't lose essential information."""
        # Basic validation - check that key structural elements are preserved
        
        # Must preserve function/class definitions
        original_defs = re.findall(r'\b(def|class|function)\b', original)
        compressed_defs = re.findall(r'\b(def|class|function)\b', compressed)
        
        if len(compressed_defs) < len(original_defs) * 0.8:  # Allow 20% loss
            return False
        
        # Must preserve critical markers
        original_critical = re.findall(r'critical:', original, re.IGNORECASE)
        compressed_critical = re.findall(r'critical:', compressed, re.IGNORECASE)
        
        if len(compressed_critical) < len(original_critical) * 0.9:  # Allow 10% loss
            return False
        
        return True
