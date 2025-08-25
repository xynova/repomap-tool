# Docker RepoMap Tool

A Docker container that provides aider's RepoMap functionality as a standalone tool. This tool analyzes your codebase and generates a concise map of the most important classes, functions, and their relationships.

## Features

- **Code Analysis**: Uses tree-sitter to parse and analyze source code
- **Smart Caching**: Caches parsed tags for faster subsequent runs
- **Graph-based Ranking**: Uses PageRank algorithm to prioritize important code
- **Multi-language Support**: Works with Python, JavaScript, TypeScript, Java, C++, Go, Rust, PHP, Ruby, Swift, Kotlin, Scala, and more
- **Configurable**: Adjust token budget, cache behavior, and output options

## Quick Start

### 1. Build the Docker Image

```bash
# Make scripts executable
chmod +x build.sh run.sh

# Build the image
./build.sh
```

### 2. Basic Usage

```bash
# Generate repo map for a project
docker run -v /path/to/your/project:/project repomap-tool /project

# With custom token budget
docker run -v /path/to/your/project:/project repomap-tool /project --map-tokens 2048

# With verbose output
docker run -v /path/to/your/project:/project repomap-tool /project --verbose
```

### 3. Using the Run Script

```bash
# Basic usage
./run.sh /path/to/your/project

# With custom token budget
./run.sh /path/to/your/project 2048

# With verbose output
./run.sh /path/to/your/project 2048 true
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--map-tokens N` | Token budget for repo map | 1024 |
| `--output FILE` | Output file path | repo_map.txt |
| `--clear-cache` | Clear cache before generating | false |
| `--force-refresh` | Force refresh of repo map | false |
| `--cache-stats` | Show cache statistics | false |
| `--verbose` | Verbose output | false |
| `--extensions` | File extensions to include | auto-detected |

## Examples

### Show Cache Statistics

```bash
docker run -v /path/to/your/project:/project repomap-tool /project --cache-stats
```

### Clear Cache and Regenerate

```bash
docker run -v /path/to/your/project:/project repomap-tool /project --clear-cache --force-refresh
```

### Custom Output File

```bash
docker run -v /path/to/your/project:/project repomap-tool /project --output /project/custom_map.txt
```

### Verbose Output

```bash
docker run -v /path/to/your/project:/project repomap-tool /project --verbose
```

## Docker Compose Usage

### 1. Create Project Directory

```bash
mkdir -p projects/my-project
# Copy your project files to projects/my-project/
```

### 2. Run with Docker Compose

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### 3. Customize Command

Edit `docker-compose.yml` to change the command:

```yaml
command: ["/projects/my-project", "--map-tokens", "4096", "--verbose", "--output", "/projects/my-project/repo_map.txt"]
```

## Output

The tool generates a `repo_map.txt` file containing:

- File paths and their most important symbols
- Function and class definitions with signatures
- Relationships between different parts of the codebase
- Prioritized content based on importance and relevance

Example output:
```
src/main.py:
  main: def main():
  process_data: def process_data(input_data):
  DataProcessor: class DataProcessor:

src/utils.py:
  helper_function: def helper_function():
  format_output: def format_output(data):
```

## Cache Management

The tool uses a sophisticated caching system:

- **Tags Cache**: SQLite-based cache for parsed code tags
- **Map Cache**: In-memory cache for generated repo maps
- **Tree Cache**: Cache for rendered code contexts

Cache location: `.aider.tags.cache.v4/` in your project directory

### Cache Operations

```bash
# Show cache statistics
docker run -v /path/to/your/project:/project repomap-tool /project --cache-stats

# Clear cache
docker run -v /path/to/your/project:/project repomap-tool /project --clear-cache
```

## Supported Languages

- Python (.py)
- JavaScript (.js)
- TypeScript (.ts)
- Java (.java)
- C++ (.cpp, .c)
- Go (.go)
- Rust (.rs)
- PHP (.php)
- Ruby (.rb)
- Swift (.swift)
- Kotlin (.kt)
- Scala (.scala)

## Performance Tips

1. **First Run**: Initial run may be slow as it parses all files
2. **Subsequent Runs**: Much faster due to caching
3. **Large Projects**: Increase `--map-tokens` for better coverage
4. **Cache Management**: Use `--clear-cache` if you encounter issues

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure Docker has access to your project directory
2. **Cache Errors**: Use `--clear-cache` to reset the cache
3. **Large Projects**: Increase token budget with `--map-tokens`
4. **No Output**: Check if your project contains supported file types

### Debug Mode

```bash
# Run with verbose output for debugging
docker run -v /path/to/your/project:/project repomap-tool /project --verbose
```

## Development

### Building from Source

```bash
# Clone the repository
git clone <repository-url>
cd docker-repomap

# Build the image
./build.sh

# Test with a sample project
./run.sh /path/to/test/project
```

### Customizing

- Modify `external_repomap.py` to change behavior
- Update `requirements.txt` to add dependencies
- Edit `Dockerfile` to customize the container

## License

This tool uses aider's RepoMap functionality. Please refer to aider's license for usage terms.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request
