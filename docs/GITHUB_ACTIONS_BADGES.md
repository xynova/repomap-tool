# GitHub Actions Status Badges

Add these badges to your README.md to show the status of your GitHub Actions workflows:

## CI Status Badge
```markdown
![CI](https://github.com/{username}/repomap-tool/workflows/CI/badge.svg)
```

## Docker Build Status Badge
```markdown
![Docker Build](https://github.com/{username}/repomap-tool/workflows/Docker%20Build/badge.svg)
```

## Release Status Badge
```markdown
![Release](https://github.com/{username}/repomap-tool/workflows/Release/badge.svg)
```

## Nightly Build Status Badge
```markdown
![Nightly Build](https://github.com/{username}/repomap-tool/workflows/Nightly%20Build/badge.svg)
```

## All Badges Together
```markdown
[![CI](https://github.com/{username}/repomap-tool/workflows/CI/badge.svg)](https://github.com/{username}/repomap-tool/actions?query=workflow%3ACI)
[![Docker Build](https://github.com/{username}/repomap-tool/workflows/Docker%20Build/badge.svg)](https://github.com/{username}/repomap-tool/actions?query=workflow%3A%22Docker+Build%22)
[![Release](https://github.com/{username}/repomap-tool/workflows/Release/badge.svg)](https://github.com/{username}/repomap-tool/actions?query=workflow%3ARelease)
[![Nightly Build](https://github.com/{username}/repomap-tool/workflows/Nightly%20Build/badge.svg)](https://github.com/{username}/repomap-tool/actions?query=workflow%3A%22Nightly+Build%22)
```

## Usage Instructions

1. Replace `{username}` with your actual GitHub username
2. Replace `repomap-tool` with your actual repository name if different
3. Copy the desired badge(s) to your README.md file
4. The badges will automatically update based on workflow status

## Badge Colors

- **Green**: All checks passed
- **Yellow**: Some checks failed but workflow completed
- **Red**: Workflow failed
- **Gray**: Workflow is running or pending

## Customization

You can customize the badge appearance by adding query parameters:

```markdown
![CI](https://github.com/{username}/repomap-tool/workflows/CI/badge.svg?branch=main)
![CI](https://github.com/{username}/repomap-tool/workflows/CI/badge.svg?event=pull_request)
```

## Alternative Badge Services

If you prefer different badge styles, you can also use:

### Shields.io
```markdown
![CI](https://img.shields.io/github/actions/workflow/status/{username}/repomap-tool/ci.yml?branch=main)
```

### GitHub Workflow Status API
```markdown
![CI](https://img.shields.io/github/workflow/status/{username}/repomap-tool/CI?branch=main)
```
