#!/usr/bin/env python3
"""Setup script for repomap-tool."""

from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name="repomap-tool",
        version="0.1.0",
        description="Portable code analysis tool using aider libraries",
        author="Your Name",
        author_email="your.email@example.com",
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        install_requires=[
            "aider-chat",
            "networkx>=3.0",
            "diskcache>=5.6.0",
            "grep-ast>=0.1.0",
            "pygments>=2.15.0",
            "tqdm>=4.65.0",
            "tree-sitter==0.24.0",
            "packaging>=21.0",
            "click>=8.0",
            "colorama>=0.4.4",
            "rich>=13.0.0",
            "numpy>=1.21.0",
            "scipy>=1.7.0",
            "fuzzywuzzy>=0.18.0",
            "python-Levenshtein>=0.21.0",
        ],
        extras_require={
            "dev": [
                "pytest>=7.0.0",
                "pytest-cov>=4.0.0",
                "black>=22.0.0",
                "flake8>=5.0.0",
                "mypy>=1.0.0",
            ],
        },
        entry_points={
            "console_scripts": [
                "repomap-tool=repomap_tool.cli:cli",
            ],
        },
        python_requires=">=3.8",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
        ],
    )
