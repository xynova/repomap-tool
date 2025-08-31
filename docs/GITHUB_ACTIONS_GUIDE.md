# GitHub Actions Guide

This document provides a comprehensive overview of the GitHub Actions workflows implemented for the repomap-tool project.

## Overview

The project includes four main GitHub Actions workflows:

1. **CI Workflow** (`ci.yml`) - Continuous Integration for code quality
2. **Docker Build Workflow** (`docker-build.yml`) - Docker image building and testing
3. **Release Workflow** (`release.yml`) - Automated releases and container publishing
4. **Nightly Build Workflow** (`nightly.yml`) - Scheduled comprehensive testing

## Workflow Details

### 1. CI Workflow (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Jobs:**

#### Test Job
- **Purpose:** Run unit tests across multiple Python versions
- **Python Versions:** 3.11
- **Features:**
  - Caches pip dependencies for faster builds
  - Runs pytest with coverage reporting
  - Uploads coverage to Codecov
  - Generates HTML coverage reports

#### Lint Job
- **Purpose:** Code quality checks
- **Tools:**
  - `flake8` for code style and complexity checks
  - `black` for code formatting verification
- **Configuration:** Uses project-specific settings from `pyproject.toml`

#### Type Check Job
- **Purpose:** Static type checking
- **Tool:** `mypy` with strict configuration
- **Configuration:** Uses settings from `pyproject.toml`

#### Integration Test Job
- **Purpose:** End-to-end testing
- **Dependencies:** Runs after test, lint, and type-check jobs
- **Executes:** Integration test scripts from `tests/integration/`

#### Security Job
- **Purpose:** Security vulnerability scanning
- **Tools:**
  - `bandit` for Python security analysis
  - `safety` for dependency vulnerability checking
- **Output:** Generates security reports as artifacts

### 2. Docker Build Workflow (`docker-build.yml`)

**Triggers:**
- Push/PR to `main` or `develop` branches
- Only when changes are made to:
  - `docker/` directory
  - `src/` directory
  - `pyproject.toml`
  - `setup.py`

**Jobs:**

#### Docker Build Job
- **Purpose:** Build and test Docker images
- **Features:**
  - Multi-platform builds (linux/amd64, linux/arm64)
  - Docker layer caching for faster builds
  - Uses Docker Buildx for advanced features
- **Testing:** Basic functionality test after build

#### Docker Integration Test Job
- **Purpose:** Comprehensive Docker testing
- **Dependencies:** Runs after successful Docker build
- **Tests:**
  - Basic CLI functionality
  - Sample project analysis
  - Volume mounting and workspace operations

### 3. Release Workflow (`release.yml`)

**Triggers:**
- Release publication events

**Jobs:**

#### Build and Push Job
- **Purpose:** Build and publish Docker images to GitHub Container Registry
- **Features:**
  - Automatic tagging based on release version
  - Multi-platform builds
  - Pushes to `ghcr.io` registry
- **Permissions:** Requires `packages: write` permission

#### Test Release Job
- **Purpose:** Validate released images
- **Dependencies:** Runs after successful build and push
- **Tests:**
  - Pulls and tests the latest release image
  - Sample project analysis with released image

### 4. Nightly Build Workflow (`nightly.yml`)

**Triggers:**
- Daily at 2 AM UTC (cron schedule)
- Manual dispatch (workflow_dispatch)

**Jobs:**

#### Nightly Test Job
- **Purpose:** Comprehensive testing on schedule
- **Python Versions:** 3.11
- **Features:**
  - Extended test duration reporting
  - Coverage artifact generation
  - Linting and type checking

#### Nightly Docker Job
- **Purpose:** Docker image testing
- **Dependencies:** Runs after successful nightly tests
- **Tests:**
  - Complex project structure analysis
  - Volume mounting scenarios

#### Nightly API Test Job
- **Purpose:** API functionality validation
- **Tests:**
  - API module imports
  - Client example functionality

#### Nightly Report Job
- **Purpose:** Generate comprehensive nightly reports
- **Dependencies:** Runs after all other jobs (even if they fail)
- **Output:** Markdown report with all job results

## Usage Instructions

### For Developers

1. **Local Development:**
   ```bash
   # Run the same checks locally
   make ci
   
   # Run specific checks
   make test
   make lint
   make mypy
   make check
   ```

2. **Before Pushing:**
   - Ensure all tests pass locally
   - Run `make format` to format code
   - Check that Docker builds successfully

3. **Creating Releases:**
   - Create a new release on GitHub
   - Tag it with a semantic version (e.g., `v1.0.0`)
   - The release workflow will automatically build and publish Docker images

### For Maintainers

1. **Monitoring Workflows:**
   - Check GitHub Actions tab for workflow status
   - Review nightly reports for trends
   - Monitor security scan results

2. **Manual Triggers:**
   - Use "workflow_dispatch" for nightly builds
   - Re-run failed jobs as needed

3. **Docker Image Management:**
   - Images are published to `ghcr.io/[username]/repomap-tool`
   - Tags include version numbers and branch names
   - Latest tag points to the most recent release

## Configuration

### Required Secrets

The workflows use the following secrets (automatically provided by GitHub):

- `GITHUB_TOKEN` - For repository access and package publishing

### Optional Configuration

1. **Codecov Integration:**
   - Add `CODECOV_TOKEN` secret for enhanced coverage reporting
   - Configure Codecov settings in repository

2. **Custom Registries:**
   - Modify `REGISTRY` environment variable in release workflow
   - Add appropriate login credentials

3. **Notification Settings:**
   - Configure webhooks for Slack/Teams notifications
   - Set up email notifications for failed builds

## Troubleshooting

### Common Issues

1. **Docker Build Failures:**
   - Check Dockerfile syntax
   - Verify all dependencies are available
   - Ensure proper file permissions

2. **Test Failures:**
   - Run tests locally to reproduce
   - Check for environment-specific issues
   - Verify test dependencies are installed

3. **Cache Issues:**
   - Clear GitHub Actions cache if needed
   - Check cache key configuration
   - Verify cache paths are correct

### Performance Optimization

1. **Faster Builds:**
   - Optimize Docker layer caching
   - Use dependency caching effectively
   - Parallelize independent jobs

2. **Resource Usage:**
   - Monitor workflow execution times
   - Optimize test execution
   - Use appropriate runner types

## Best Practices

1. **Code Quality:**
   - Keep workflows focused and modular
   - Use meaningful job and step names
   - Add proper error handling

2. **Security:**
   - Use minimal required permissions
   - Scan for vulnerabilities regularly
   - Keep dependencies updated

3. **Maintenance:**
   - Review and update workflows regularly
   - Monitor workflow performance
   - Document changes and improvements

## Support

For issues with GitHub Actions workflows:

1. Check the GitHub Actions logs for detailed error messages
2. Review this documentation for configuration guidance
3. Test workflows locally using `act` (GitHub Actions local runner)
4. Create issues in the repository for workflow-specific problems
