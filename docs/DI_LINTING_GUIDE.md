# 🔍 **DI Linting Guide - RepoMap-Tool**

This guide explains how to use the custom Dependency Injection (DI) linting system to maintain code quality and prevent DI anti-patterns.

## 🎯 **Overview**

The DI linter is a custom tool that automatically detects dependency injection violations in the RepoMap-Tool codebase. It helps maintain the excellent DI architecture by catching common anti-patterns before they reach production.

## 🚨 **DI Violations Detected**

### **DI001: Direct Console() Instantiation**
```python
# ❌ BAD: Direct instantiation
console = Console()

# ✅ GOOD: Use DI system
console = get_console(ctx)
```

### **DI002: Direct Matcher Instantiation**
```python
# ❌ BAD: Direct instantiation
matcher = FuzzyMatcher(threshold=70)

# ✅ GOOD: Use service factory
service_factory = get_service_factory()
repomap_service = service_factory.create_repomap_service(config)
matcher = repomap_service.fuzzy_matcher
```

### **DI003: Fallback Instantiation**
```python
# ❌ BAD: Fallback pattern
self.console = console or Console()

# ✅ GOOD: Strict validation
if console is None:
    raise ValueError("Console must be injected - no fallback allowed")
self.console = console
```

### **DI004: Fallback Assignment Pattern**
```python
# ❌ BAD: Fallback assignment
self.service = service or Service()

# ✅ GOOD: Strict validation
if service is None:
    raise ValueError("Service must be injected - no fallback allowed")
self.service = service
```

## 🛠️ **Usage**

### **Command Line Usage**
```bash
# Check specific files
python scripts/di_linter.py src/repomap_tool/cli/utils/console.py

# Check directories
python scripts/di_linter.py src/ tests/

# Check with JSON output
python scripts/di_linter.py src/ --format=json
```

### **Makefile Integration**
```bash
# Run all linting (includes DI linter)
make lint

# Run only DI linter
python scripts/di_linter.py src/ tests/
```

### **Pre-commit Hook**
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run di-linter --all-files
```

## 🔧 **Configuration**

### **Excluding Files**
The DI linter automatically excludes:
- `__pycache__` directories
- `.git` directories
- Test files (when appropriate)

### **Custom Exclusions**
```bash
# Exclude specific directories
python scripts/di_linter.py src/ --exclude vendor third_party
```

### **Output Formats**
- **Text** (default): Human-readable output
- **JSON**: Machine-readable output for CI/CD

## 🏗️ **Integration Options**

### **1. Makefile Integration** ✅
Already integrated in the main `make lint` command.

### **2. Pre-commit Hooks** ✅
Configured in `.pre-commit-config.yaml`.

### **3. GitHub Actions** ✅
Configured in `.github/workflows/di-lint.yml`.

### **4. VS Code/Cursor** ✅
Configured in `.vscode/settings.json`.

### **5. Custom Flake8 Plugin** (Advanced)
For more sophisticated integration, you can create a custom flake8 plugin.

## 📊 **CI/CD Integration**

### **GitHub Actions**
The DI linter runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

### **Local Development**
```bash
# Run before committing
make lint

# Or run DI linter specifically
python scripts/di_linter.py src/ tests/
```

## 🎯 **Best Practices**

### **For Developers**
1. **Run DI linter before committing**
2. **Fix violations immediately**
3. **Use service factory for CLI commands**
4. **Validate all dependencies in constructors**
5. **Never use fallback instantiation**

### **For Code Reviews**
1. **Check that DI linter passes**
2. **Verify no direct service instantiation**
3. **Ensure proper dependency validation**
4. **Confirm service factory usage in CLI**

### **For CI/CD**
1. **Run DI linter in all environments**
2. **Fail builds on DI violations**
3. **Include DI linter in quality gates**
4. **Monitor DI compliance metrics**

## 🔍 **Troubleshooting**

### **Common Issues**

#### **False Positives**
If the linter reports a false positive:
1. Check if the code is in a factory class (allowed)
2. Verify the code is in a test file (may be allowed)
3. Consider if the pattern is actually a violation

#### **Missing Violations**
If the linter misses a violation:
1. Check the AST parsing logic
2. Verify the violation pattern is covered
3. Consider adding new detection rules

#### **Performance Issues**
If the linter is slow:
1. Exclude unnecessary directories
2. Use file-specific checks
3. Consider caching results

### **Debug Mode**
```bash
# Run with verbose output
python scripts/di_linter.py src/ --verbose
```

## 🚀 **Advanced Usage**

### **Custom Rules**
You can extend the DI linter by:
1. Adding new violation patterns in `DILinter` class
2. Implementing custom AST visitors
3. Adding configuration options

### **IDE Integration**
For better IDE integration:
1. Install the Python extension
2. Configure the linter in VS Code settings
3. Enable format-on-save

### **Team Standards**
To enforce DI standards across the team:
1. Add DI linter to pre-commit hooks
2. Include in CI/CD pipeline
3. Set up code review requirements

## 📈 **Metrics and Monitoring**

### **Compliance Tracking**
- Track DI violation counts over time
- Monitor compliance by module/team
- Set up alerts for violations

### **Quality Gates**
- Require 0 DI violations for production
- Set thresholds for different environments
- Include in quality dashboards

## 🎉 **Benefits**

### **Code Quality**
- Prevents DI anti-patterns
- Maintains architectural consistency
- Improves testability

### **Developer Experience**
- Catches issues early
- Provides clear error messages
- Integrates with existing tools

### **Maintainability**
- Enforces best practices
- Reduces technical debt
- Improves code reviews

## 🔗 **Related Documentation**

- [Python Coding Standards](.cursor/rules/rules-for-python-coding.mdc)
- [DI Architecture Guide](docs/architecture/)
- [Testing Strategy](docs/TESTING_STRATEGY.md)
- [CLI Guide](docs/CLI_GUIDE.md)

---

**Remember**: The DI linter is a tool to help maintain the excellent DI architecture. Use it consistently and fix violations promptly to keep the codebase clean and maintainable.
