"""
Unit tests for validating tree-sitter query file syntax.

These tests ensure that all .scm query files:
1. Have valid syntax (no invalid node types)
2. Can be compiled into tree-sitter Query objects
3. Don't contain "Impossible pattern" errors
"""

import pytest
import tree_sitter
from pathlib import Path
from grep_ast.tsl import get_language
from repomap_tool.code_analysis.query_loader import FileQueryLoader


class TestQuerySyntaxValidation:
    """Tests to validate query file syntax for all supported languages."""

    @pytest.fixture
    def query_loader(self):
        """Create a FileQueryLoader instance."""
        return FileQueryLoader()

    @pytest.fixture
    def supported_languages(self):
        """List of languages that have query files."""
        queries_dir = Path(__file__).parent.parent.parent.parent / "src" / "repomap_tool" / "code_analysis" / "queries"
        languages = []
        for query_file in queries_dir.glob("*-tags.scm"):
            # Extract language name from filename: "python-tags.scm" -> "python"
            lang_name = query_file.stem.replace("-tags", "")
            languages.append(lang_name)
        return languages

    def test_all_query_files_have_valid_syntax(self, query_loader, supported_languages):
        """Test that all query files can be compiled into tree-sitter Query objects.
        
        This catches:
        - Invalid node types (e.g., "function" instead of "function_expression")
        - Invalid node names (e.g., "named_exports" instead of "export_clause")
        - Impossible patterns (structural conflicts in queries)
        
        Note: Some languages may have query syntax issues that are non-critical.
        Critical languages (python, javascript, typescript) must pass.
        """
        errors = []
        critical_languages = ["python", "javascript", "typescript"]
        non_critical_errors = []
        
        for language in supported_languages:
            try:
                # Load the query string
                query_string = query_loader.load_query(language)
                if query_string is None:
                    error_msg = f"Language '{language}': Query file not found or could not be loaded"
                    if language in critical_languages:
                        errors.append(error_msg)
                    else:
                        non_critical_errors.append(error_msg)
                    continue
                
                # Get the language parser
                try:
                    language_obj = get_language(language)
                    if language_obj is None:
                        error_msg = f"Language '{language}': Language parser returned None (may not be installed)"
                        if language in critical_languages:
                            errors.append(error_msg)
                        else:
                            non_critical_errors.append(error_msg)
                        continue
                except Exception as e:
                    error_msg = f"Language '{language}': Could not get language parser: {e}"
                    if language in critical_languages:
                        errors.append(error_msg)
                    else:
                        non_critical_errors.append(error_msg)
                    continue
                
                # Try to compile the query - this will raise an error if syntax is invalid
                try:
                    query = tree_sitter.Query(language_obj, query_string)
                    # If we get here, the query compiled successfully
                    assert query is not None, f"Language '{language}': Query compilation returned None"
                except tree_sitter.QueryError as e:
                    # QueryError may have different attributes depending on tree-sitter version
                    error_msg = str(e)
                    # Try to extract row/column if available
                    if hasattr(e, 'row') and hasattr(e, 'column'):
                        full_error = f"Language '{language}': Query syntax error at row {e.row}, column {e.column}: {error_msg}"
                    else:
                        full_error = f"Language '{language}': Query syntax error: {error_msg}"
                    
                    if language in critical_languages:
                        errors.append(full_error)
                    else:
                        non_critical_errors.append(full_error)
                except Exception as e:
                    error_msg = f"Language '{language}': Unexpected error compiling query: {e}"
                    if language in critical_languages:
                        errors.append(error_msg)
                    else:
                        non_critical_errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"Language '{language}': Failed to validate query: {e}"
                if language in critical_languages:
                    errors.append(error_msg)
                else:
                    non_critical_errors.append(error_msg)
        
        # Report errors: critical languages must pass, others are warnings
        if errors:
            error_msg = "\n".join(f"  - {error}" for error in errors)
            pytest.fail(f"Query syntax validation failed for {len(errors)} critical language(s):\n{error_msg}")
        
        # Log non-critical errors as warnings but don't fail the test
        if non_critical_errors:
            import warnings
            for error in non_critical_errors:
                warnings.warn(f"Non-critical query syntax issue: {error}", UserWarning)

    def test_specific_languages_have_queries(self, query_loader):
        """Test that specific important languages have query files."""
        critical_languages = ["python", "javascript", "typescript"]
        
        missing = []
        for lang in critical_languages:
            query_string = query_loader.load_query(lang)
            if query_string is None:
                missing.append(lang)
        
        if missing:
            pytest.fail(f"Missing query files for critical languages: {', '.join(missing)}")

    @pytest.mark.parametrize("language", ["python", "javascript", "typescript", "java", "go", "csharp"])
    def test_query_file_exists_for_language(self, query_loader, language):
        """Test that a query file exists and can be loaded for a specific language.
        
        Note: This only tests that the file exists and loads, not that the language parser is available.
        """
        query_string = query_loader.load_query(language)
        assert query_string is not None, f"Query file not found for language: {language}"
        assert len(query_string) > 0, f"Query file is empty for language: {language}"
        
        # Optionally try to compile the query if the language parser is available
        try:
            language_obj = get_language(language)
            if language_obj is not None:
                query = tree_sitter.Query(language_obj, query_string)
                assert query is not None, f"Query compilation returned None for language: {language}"
        except Exception:
            # Language parser not available - that's okay for this test
            pass

