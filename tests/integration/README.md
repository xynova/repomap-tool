# Self-Integration Tests for repomap-tool

This directory contains comprehensive integration tests that test the repomap-tool against itself. These tests verify that all major functionality works correctly by using the actual repomap-tool codebase as the test subject.

## Overview

The self-integration tests cover:

1. **Default Analysis** - Finding classes, functions, and other identifiers in the codebase
2. **Fuzzy Search** - Testing fuzzy matching functionality independently
3. **Semantic Search** - Testing semantic matching functionality independently
4. **Hybrid Search** - Testing the combination of fuzzy and semantic search
5. **Specific Identifier Search** - Testing search for known identifiers
6. **Context Inclusion** - Verifying that search results include proper context
7. **Result Ranking** - Ensuring results are properly ranked by relevance
8. **Error Handling** - Testing graceful handling of edge cases
9. **Performance Benchmarking** - Measuring performance of different search modes

## Test Files

- `test_self_integration.py` - Main test suite with comprehensive tests
- `test_config.py` - Configuration and test data definitions
- `run_self_integration_tests.sh` - Shell script to run the tests
- `README.md` - This documentation file

## Running the Tests

### Quick Start

```bash
# Make the script executable (if not already)
chmod +x tests/integration/run_self_integration_tests.sh

# Run the tests
./tests/integration/run_self_integration_tests.sh
```

### Using Make (Recommended)

```bash
# Run all tests (including self-integration tests)
make test

# Run only self-integration tests
make test-self-integration

# Run all integration tests
make test-integration

# Run comprehensive checks (tests + lint + mypy + format)
make ci
```

### Manual Execution

```bash
# Set up Python path
export PYTHONPATH="src:$PYTHONPATH"

# Run with pytest
python3 -m pytest tests/integration/test_self_integration.py -v

# Run with coverage
coverage run -m pytest tests/integration/test_self_integration.py -v
coverage report --show-missing
```

### Individual Test Methods

You can run specific test methods:

```bash
# Run only default analysis test
python3 -m pytest tests/integration/test_self_integration.py::TestSelfIntegration::test_default_analysis_finds_classes_and_functions -v

# Run only fuzzy search test
python3 -m pytest tests/integration/test_self_integration.py::TestSelfIntegration::test_fuzzy_search_independently -v

# Run only semantic search test
python3 -m pytest tests/integration/test_self_integration.py::TestSelfIntegration::test_semantic_search_independently -v

# Run only hybrid search test
python3 -m pytest tests/integration/test_self_integration.py::TestSelfIntegration::test_hybrid_search_combination -v
```

## Test Configuration

The tests use configuration defined in `test_config.py`:

- **Expected Files**: Core Python files that should be found
- **Expected Classes**: Key classes that should be identified
- **Expected Functions**: Key functions that should be identified
- **Test Queries**: Various search terms to test different functionality
- **Performance Thresholds**: Maximum acceptable execution times
- **Validation Rules**: Minimum requirements for test success

## What the Tests Verify

### 1. Default Analysis Test
- ✅ Finds Python files in the project
- ✅ Extracts identifiers (classes, functions, variables)
- ✅ Identifies expected core classes like `DockerRepoMap`, `RepoMapConfig`
- ✅ Identifies expected functions like `analyze_project`, `search_identifiers`

### 2. Fuzzy Search Test
- ✅ Performs fuzzy matching with configurable threshold (70%)
- ✅ Uses multiple strategies (prefix, substring, levenshtein)
- ✅ Returns results with proper scoring
- ✅ Handles various query types (RepoMap, matcher, config, etc.)

### 3. Semantic Search Test
- ✅ Performs semantic matching with TF-IDF
- ✅ Uses configurable threshold (0.1)
- ✅ Finds conceptually related code
- ✅ Handles natural language queries

### 4. Hybrid Search Test
- ✅ Combines fuzzy and semantic search results
- ✅ Properly ranks and deduplicates results
- ✅ Returns results from both matchers
- ✅ Maintains proper scoring for each match type

### 5. Specific Identifier Search
- ✅ Finds specific known identifiers in the codebase
- ✅ Verifies search accuracy for core components
- ✅ Tests search for main classes and functions

### 6. Context and Ranking Tests
- ✅ Includes code context in search results
- ✅ Ranks results by relevance score
- ✅ Maintains proper result ordering

### 7. Error Handling Test
- ✅ Handles empty queries gracefully
- ✅ Handles very short queries
- ✅ Handles special characters
- ✅ Maintains system stability

### 8. Performance Benchmark Test
- ✅ Measures execution time for each search mode
- ✅ Ensures performance within acceptable limits
- ✅ Compares performance between modes

## Expected Results

When all tests pass, you should see output like:

```
✅ All self-integration tests passed!

Test Summary:
  • Default analysis (classes, functions, etc.)
  • Fuzzy search (independent)
  • Semantic search (independent)
  • Hybrid search (fuzzy + semantic combination)
  • Specific identifier search
  • Context inclusion
  • Result ranking
  • Error handling
  • Performance benchmarking
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure `PYTHONPATH` includes the `src` directory
2. **Missing Dependencies**: Install required packages: `pydantic`, `click`, `rich`, `pytest`
3. **Permission Errors**: Make sure the test script is executable
4. **Timeout Errors**: Increase timeout values in `test_config.py` if needed

### Debug Mode

Run tests with debug output:

```bash
python3 -m pytest tests/integration/test_self_integration.py -v -s --tb=long
```

### Verbose Output

Enable verbose output for detailed test information:

```bash
python3 -m pytest tests/integration/test_self_integration.py -vvv
```

## Performance Expectations

The tests include performance benchmarks with these thresholds:

- **Fuzzy Search**: < 10 seconds for 5 queries
- **Semantic Search**: < 10 seconds for 5 queries  
- **Hybrid Search**: < 15 seconds for 5 queries

## Contributing

When adding new functionality to repomap-tool:

1. Update `test_config.py` with new expected identifiers
2. Add new test methods to `test_self_integration.py`
3. Update this README with new test descriptions
4. Ensure all tests pass before merging

## Test Coverage

These integration tests complement the unit tests by:

- Testing the complete system end-to-end
- Using real code as test data
- Verifying integration between components
- Testing performance under realistic conditions
- Ensuring backward compatibility

The tests should be run regularly to catch regressions and verify that new features work correctly with the existing codebase.
