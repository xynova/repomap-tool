# Testing Strategy Guide

## Overview

This guide explains the testing approach used in the repomap-tool project to ensure reliability and quality. Understanding the testing strategy helps developers contribute effectively and users trust the tool's functionality.

## Testing Philosophy

### **Quality First**
- All new functionality must have comprehensive tests
- Tests are written before or alongside code implementation
- No feature is considered complete without proper test coverage

### **Reliability Over Speed**
- Tests must actually pass, not just appear to pass
- Edge cases and error conditions are thoroughly tested
- Integration tests ensure components work together correctly

## Testing Layers

### 1. **Unit Tests** - Component Isolation
Unit tests verify individual components work correctly in isolation:

```bash
# Run all unit tests
make test-unit

# Run specific test file
python -m pytest tests/unit/test_dependencies.py -v

# Run tests with coverage
python -m pytest tests/unit/ --cov=src/repomap_tool --cov-report=term-missing
```

**What Unit Tests Cover:**
- Individual class methods and functions
- Data model validation
- Configuration handling
- Error conditions and edge cases
- Input validation and sanitization

### 2. **CLI Tests** - Command Reliability
CLI tests ensure all commands work correctly in all scenarios:

```bash
# Run CLI-specific tests
python -m pytest tests/unit/test_cli_dependencies.py -v

# Test CLI command help
python -m repomap_tool.cli analyze-dependencies --help
```

**CLI Testing Features:**
- **Command Existence**: Verify all commands are available
- **Help Documentation**: Ensure help text is accurate and complete
- **Option Validation**: Test all command-line options
- **Output Formats**: Verify JSON, table, and text output
- **Error Handling**: Test error conditions and user feedback
- **Configuration Integration**: Ensure CLI uses configuration correctly

### 3. **Integration Tests** - Component Interaction
Integration tests verify that components work together correctly:

```bash
# Run integration tests
python -m pytest tests/integration/ -v

# Test end-to-end workflows
python examples/dependency_analysis_demo.py
```

**Integration Testing Covers:**
- Component initialization and setup
- Data flow between components
- Configuration loading and validation
- Error propagation across components
- Performance characteristics

## CLI Testing Strategy

### **Why CLI Testing is Critical**

The CLI is the primary interface users interact with. CLI tests ensure:

1. **Commands Always Work**: Users can rely on the tool
2. **Options Are Valid**: All command-line options function correctly
3. **Output Is Correct**: Results are accurate and well-formatted
4. **Errors Are Helpful**: Users get clear feedback when things go wrong
5. **Configuration Works**: CLI properly uses configuration settings

### **CLI Testing Approach**

#### **Mock-Based Testing**
```python
# Test CLI without actual file system operations
with patch('repomap_tool.cli.DockerRepoMap') as mock_repo_map:
    mock_instance = Mock()
    mock_instance.build_dependency_graph.return_value = mock_graph
    mock_repo_map.return_value = mock_instance
    
    result = cli_runner.invoke(cli, ["analyze-dependencies", temp_project])
    assert result.exit_code == 0
```

#### **Real CLI Execution**
```python
# Test actual CLI command execution
result = cli_runner.invoke(cli, ["analyze-dependencies", "--help"])
assert result.exit_code == 0
assert "Analyze project dependencies" in result.output
```

#### **Output Validation**
```python
# Verify JSON output is valid
output_data = json.loads(result.output)
assert "total_nodes" in output_data
assert isinstance(output_data["total_nodes"], int)
```

### **CLI Test Categories**

#### **1. Command Existence Tests**
- Verify all commands are registered
- Check help text is available
- Ensure command descriptions are clear

#### **2. Option Validation Tests**
- Test all command-line options
- Verify option types and constraints
- Check option help text

#### **3. Output Format Tests**
- Test JSON output validity
- Verify table formatting
- Check text output readability

#### **4. Error Handling Tests**
- Test invalid inputs
- Verify error messages are helpful
- Check exit codes are correct

#### **5. Configuration Integration Tests**
- Verify CLI uses configuration correctly
- Test configuration overrides
- Check default values

## Running Tests

### **Complete Test Suite**
```bash
# Run all tests with coverage
make test-unit

# Run specific test categories
python -m pytest tests/unit/ -k "cli" -v
python -m pytest tests/unit/ -k "dependencies" -v
```

### **Test Coverage Requirements**
- **New Code**: Must have >80% test coverage
- **Modified Code**: Must maintain or improve existing coverage
- **CLI Commands**: Must have 100% test coverage
- **Integration Points**: Must be tested with real scenarios

### **Continuous Integration**
Tests are automatically run:
- On every pull request
- Before merging to main branch
- On scheduled intervals
- When dependencies are updated

## Writing Tests

### **Test Structure**
```python
class TestFeatureName:
    """Test description for the feature."""
    
    @pytest.fixture
    def setup_data(self):
        """Setup test data."""
        return test_data
    
    def test_basic_functionality(self, setup_data):
        """Test basic functionality works."""
        result = function_under_test(setup_data)
        assert result == expected_value
    
    def test_edge_case(self, setup_data):
        """Test edge case handling."""
        result = function_under_test(edge_case_data)
        assert result is not None
    
    def test_error_condition(self, setup_data):
        """Test error handling."""
        with pytest.raises(ExpectedError):
            function_under_test(invalid_data)
```

### **Test Best Practices**
1. **Descriptive Names**: Test names should clearly describe what they test
2. **Single Responsibility**: Each test should test one specific thing
3. **Setup and Teardown**: Use fixtures for common setup
4. **Assertions**: Make assertions specific and meaningful
5. **Edge Cases**: Test boundary conditions and error scenarios
6. **Documentation**: Document complex test logic

## Debugging Tests

### **Common Test Issues**

#### **Test Isolation Problems**
```bash
# Run tests in isolation
python -m pytest tests/unit/test_specific.py -v --tb=short

# Debug specific test
python -m pytest tests/unit/test_specific.py::test_function -v -s
```

#### **Mock Issues**
```python
# Verify mocks were called correctly
mock_function.assert_called_once_with(expected_args)
mock_function.assert_called_with(expected_args)
```

#### **CLI Test Problems**
```python
# Check CLI exit codes
assert result.exit_code == 0  # Success
assert result.exit_code == 1  # Error
assert result.exit_code == 2  # Usage error

# Check CLI output
assert "expected text" in result.output
assert result.output.strip() == "expected output"
```

### **Test Debugging Commands**
```bash
# Run with verbose output
python -m pytest -v -s

# Run with maximum verbosity
python -m pytest -vvv -s

# Stop on first failure
python -m pytest -x

# Run only failing tests
python -m pytest --lf
```

## Test Maintenance

### **Keeping Tests Current**
- Update tests when functionality changes
- Remove tests for removed features
- Add tests for new edge cases
- Maintain test data and fixtures

### **Test Quality Metrics**
- **Coverage**: Percentage of code covered by tests
- **Reliability**: Tests consistently pass
- **Maintainability**: Tests are easy to understand and modify
- **Performance**: Tests run in reasonable time

### **Continuous Improvement**
- Review test failures for patterns
- Identify gaps in test coverage
- Refactor tests for better maintainability
- Add tests for discovered bugs

## Conclusion

The testing strategy ensures that the repomap-tool is reliable and trustworthy. By following these testing practices:

- **Developers** can confidently make changes
- **Users** can rely on the tool's functionality
- **Maintainers** can quickly identify and fix issues
- **Quality** is maintained as the project evolves

Remember: **Good tests are the foundation of good software**. Invest time in writing comprehensive, reliable tests, and the entire project will benefit.
