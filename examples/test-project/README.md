# Test Project for RepoMap Tool

This is a simple test project to demonstrate RepoMap Tool's capabilities.

## Files

- `test.py` - Contains a simple test function
- `auth.py` - Contains authentication-related functions with different naming conventions

## Test Commands

Try these commands to see RepoMap Tool in action:

```bash
# Search for authentication-related code
docker run -v $(pwd)/.repomap:/app/cache -v $(pwd)/examples/test-project:/workspace repomap-tool repomap-tool search /workspace "auth" --threshold 0.1

# Find specific function names
docker run -v $(pwd)/.repomap:/app/cache -v $(pwd)/examples/test-project:/workspace repomap-tool repomap-tool search /workspace "authenticate_user" --threshold 0.1

# Test fuzzy matching with different naming conventions
docker run -v $(pwd)/.repomap:/app/cache -v $(pwd)/examples/test-project:/workspace repomap-tool repomap-tool search /workspace "user_auth" --threshold 0.1

# Test fuzzy matching specifically
docker run -v $(pwd)/.repomap:/app/cache -v $(pwd)/examples/test-project:/workspace repomap-tool repomap-tool search /workspace "authentication" --match-type fuzzy --threshold 0.1
```

## Expected Results

- Searching for "auth" should find authentication-related functions
- Searching for "authenticate_user" should find the exact function
- Searching for "user_auth" should find both `user_auth` and `UserAuth` (fuzzy matching)
- Searching for "authentication" should find `authenticate_user` (fuzzy matching)

