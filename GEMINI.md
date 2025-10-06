# GEMINI.md

## Project Overview

This project is a Python command-line tool called `repomap-tool` that helps AI assistants understand codebases. It uses fuzzy matching and semantic analysis to find relevant code, analyze dependencies, and assess the impact of changes. The tool is built with `click` for the CLI, `pydantic` for data validation, and `dependency-injector` for dependency injection.

## Building and Running

The project uses a `Makefile` to automate common tasks.

### Installation

To install the dependencies, run:

```bash
make install
```

### Running Tests

To run the test suite, use:

```bash
make test
```

### Linting and Formatting

To check for code quality and format the code, run:

```bash
make lint
make format
```

### Building the Project

To build the project package, run:

```bash
make build
```

### Docker

The project can also be built and run using Docker:

```bash
make docker-build
```

## Development Conventions

*   **CLI:** The command-line interface is built using the `click` library. The main entry point is `src/repomap_tool/cli/main.py`.
*   **Commands:** The CLI is organized into command groups: `system`, `index`, `explore`, and `inspect`.
*   **Dependency Injection:** The project uses the `dependency-injector` library to manage dependencies.
*   **Configuration:** The project uses `pydantic` for configuration management.
*   **Testing:** Tests are located in the `tests/` directory and are run using `pytest`.
*   **Code Style:** The project uses `black` for code formatting and `flake8` for linting.

## Key Commands

The `repomap-tool` provides the following main commands:

*   `repomap-tool system config`: Generate a configuration file.
*   `repomap-tool system version`: Show version information.
*   `repomap-tool index create`: Create a project analysis and repository map.
*   `repomap-tool inspect find <query>`: Find identifiers in the project.
*   `repomap-tool inspect cycles`: Check for circular dependencies.
*   `repomap-tool inspect centrality`: Analyze the centrality of files.
*   `repomap-tool inspect impact --files <file1> ...`: Assess the impact of changes to files.
*   `repomap-tool explore start <intent>`: Start an interactive exploration session.
