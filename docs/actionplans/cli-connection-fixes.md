# CLI Connection Fixes Action Plan

## Overview
This action plan addresses the 10 disconnected CLI options and 49 unused configuration fields identified in the CLI connection analysis. The goal is to ensure all CLI options are properly connected to their underlying configuration and functionality.

## Current Issues Summary

### Disconnected CLI Options (10)
1. `--config` - Configuration file option
2. `--fuzzy/--no-fuzzy` - Fuzzy matching toggle  
3. `--semantic/--no-semantic` - Semantic matching toggle
4. `--output` - Output format (multiple commands)
5. `--no-progress` - Progress bar toggle
6. `--no-monitoring` - Monitoring toggle

### Unused Configuration Fields (49)
Many configuration fields exist but aren't exposed through CLI options, including:
- `cache_size`, `log_level`, `identifier`, `cache_status`
- `file_types`, `request_id`, `fuzzy_match`, `output_format`
- `search_time_ms`, `use_tfidf`, `query`, `errors`
- And many more...

## Action Plan

### Phase 1: Fix Critical Disconnections (Priority: High)

#### 1.1 Fix `--config` Option
**Issue**: CLI accepts `--config` but doesn't properly map to configuration fields
**Files to modify**: `src/repomap_tool/cli.py`, `src/repomap_tool/models.py`

**Actions**:
- [ ] Update `load_config_file()` function to properly validate config structure
- [ ] Add config validation against `RepoMapConfig` model
- [ ] Ensure config file values override CLI defaults correctly
- [ ] Add error handling for invalid config files

**Code changes needed**:
```python
# In cli.py, update load_config_file function
def load_config_file(config_path: str) -> RepoMapConfig:
    """Load and validate configuration from file."""
    try:
        with open(config_path, "r") as f:
            config_dict = json.load(f)
        
        # Validate against RepoMapConfig model
        config = RepoMapConfig(**config_dict)
        return config
    except ValidationError as e:
        raise ValueError(f"Invalid configuration file: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load configuration file: {e}")
```

#### 1.2 Fix `--fuzzy/--no-fuzzy` and `--semantic/--no-semantic` Options
**Issue**: These options don't properly update the configuration objects
**Files to modify**: `src/repomap_tool/cli.py`

**Actions**:
- [ ] Update `create_default_config()` to properly set fuzzy/semantic enabled flags
- [ ] Ensure these options override config file settings
- [ ] Add validation to prevent conflicting settings

**Code changes needed**:
```python
# In cli.py, update create_default_config function
def create_default_config(
    project_path: str,
    fuzzy: bool,
    semantic: bool,
    # ... other params
) -> RepoMapConfig:
    """Create default configuration with proper fuzzy/semantic settings."""
    
    # Create fuzzy match config with proper enabled state
    fuzzy_config = FuzzyMatchConfig(
        enabled=fuzzy,  # This was missing proper connection
        threshold=int(threshold * 100),
        strategies=["prefix", "substring", "levenshtein"],
    )

    # Create semantic match config with proper enabled state
    semantic_config = SemanticMatchConfig(
        enabled=semantic,  # This was missing proper connection
        threshold=threshold,
        use_tfidf=True
    )
    
    # ... rest of function
```

#### 1.3 Fix `--output` Option
**Issue**: Output format option doesn't properly map to configuration
**Files to modify**: `src/repomap_tool/cli.py`, `src/repomap_tool/models.py`

**Actions**:
- [ ] Ensure `--output` properly sets `output_format` in config
- [ ] Add validation for output format choices
- [ ] Update display functions to respect output format

### Phase 2: Fix Performance Options (Priority: Medium)

#### 2.1 Fix `--no-progress` and `--no-monitoring` Options
**Issue**: These options don't properly update performance configuration
**Files to modify**: `src/repomap_tool/cli.py`

**Actions**:
- [ ] Update `create_default_config()` to properly set performance flags
- [ ] Ensure these options override config file settings
- [ ] Add validation for performance settings

**Code changes needed**:
```python
# In cli.py, update create_default_config function
def create_default_config(
    # ... other params
    no_progress: bool = False,
    no_monitoring: bool = False,
    # ... other params
) -> RepoMapConfig:
    """Create default configuration with proper performance settings."""
    
    # Create performance config with proper flags
    performance_config = PerformanceConfig(
        max_workers=max_workers,
        parallel_threshold=parallel_threshold,
        enable_progress=not no_progress,  # Properly invert the flag
        enable_monitoring=not no_monitoring,  # Properly invert the flag
        allow_fallback=allow_fallback,
    )
    
    # ... rest of function
```

### Phase 3: Add Missing CLI Options (Priority: Medium)

#### 3.1 Add Configuration Management Options
**Files to modify**: `src/repomap_tool/cli.py`

**Actions**:
- [ ] Add `--cache-size` option for cache management
- [ ] Add `--log-level` option for logging control
- [ ] Add `--refresh-cache` option for cache invalidation
- [ ] Add `--cache-dir` option for custom cache location

**New CLI options to add**:
```python
@click.option(
    "--cache-size",
    type=int,
    default=1000,
    help="Maximum cache entries (100-10000)"
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Logging level"
)
@click.option(
    "--refresh-cache",
    is_flag=True,
    help="Refresh cache before analysis"
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    help="Custom cache directory"
)
```

#### 3.2 Add Advanced Configuration Options
**Actions**:
- [ ] Add `--map-tokens` option for token limits
- [ ] Add `--max-memory-mb` option for memory limits
- [ ] Add `--cache-ttl` option for cache expiration
- [ ] Add `--strategies` option for fuzzy matching strategies

### Phase 4: Improve Configuration Validation (Priority: Low)

#### 4.1 Add Configuration Validation
**Files to modify**: `src/repomap_tool/models.py`

**Actions**:
- [ ] Add cross-field validation (e.g., fuzzy/semantic can't both be disabled)
- [ ] Add range validation for numeric fields
- [ ] Add dependency validation (e.g., cache options require cache enabled)

#### 4.2 Add Configuration Documentation
**Actions**:
- [ ] Add comprehensive docstrings to all configuration models
- [ ] Create configuration examples
- [ ] Add validation error messages

### Phase 5: Testing and Validation (Priority: High)

#### 5.1 Add CLI Connection Tests
**Files to create**: `tests/unit/test_cli_connections.py`

**Actions**:
- [ ] Test that all CLI options properly update configuration
- [ ] Test configuration file loading with CLI overrides
- [ ] Test validation of CLI options
- [ ] Test error handling for invalid options

**Test structure**:
```python
def test_fuzzy_option_connection():
    """Test that --fuzzy properly enables fuzzy matching."""
    # Test implementation

def test_config_file_override():
    """Test that CLI options override config file settings."""
    # Test implementation

def test_invalid_config_file():
    """Test error handling for invalid config files."""
    # Test implementation
```

#### 5.2 Add Integration Tests
**Actions**:
- [ ] Test full CLI workflow with various option combinations
- [ ] Test configuration persistence
- [ ] Test performance impact of different options

## Implementation Timeline

### Week 1: Phase 1 (Critical Fixes)
- Fix `--config` option connection
- Fix `--fuzzy/--no-fuzzy` and `--semantic/--no-semantic` options
- Fix `--output` option connection

### Week 2: Phase 2 (Performance Options)
- Fix `--no-progress` and `--no-monitoring` options
- Add basic configuration management options

### Week 3: Phase 3 (Missing Options)
- Add advanced configuration options
- Add cache management options

### Week 4: Phase 4 & 5 (Validation & Testing)
- Add configuration validation
- Create comprehensive test suite
- Documentation updates

## Success Criteria

1. **Zero Disconnected Options**: All CLI options properly connected to configuration
2. **Full Test Coverage**: All CLI options have corresponding tests
3. **Configuration Validation**: All configuration combinations are validated
4. **Documentation**: Complete documentation of all CLI options
5. **Backward Compatibility**: Existing CLI usage continues to work

## Risk Mitigation

1. **Incremental Changes**: Implement fixes one at a time to avoid breaking changes
2. **Comprehensive Testing**: Test each change thoroughly before proceeding
3. **Backward Compatibility**: Ensure existing CLI usage continues to work
4. **Documentation**: Update documentation as changes are made

## Monitoring and Validation

1. **Run CLI Analysis**: After each phase, run the CLI connection analyzer
2. **Test Coverage**: Ensure test coverage increases with each phase
3. **Integration Testing**: Test full workflows after each phase
4. **Performance Testing**: Ensure changes don't impact performance

## Next Steps

1. **Review Action Plan**: Get stakeholder approval for the plan
2. **Set Up Development Environment**: Ensure all tools and tests are ready
3. **Begin Phase 1**: Start with critical fixes
4. **Regular Reviews**: Weekly reviews of progress and any issues

---

*This action plan addresses the immediate issues while setting up a foundation for better CLI management going forward.*
