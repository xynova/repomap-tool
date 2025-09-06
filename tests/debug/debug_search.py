#!/usr/bin/env python3

from src.repomap_tool.core import RepoMapService
from src.repomap_tool.models import RepoMapConfig
from pathlib import Path

# Initialize the tool
config = RepoMapConfig(project_root=".", verbose=True)
dm = RepoMapService(config)

# Get project files
project_files = dm._get_project_files()
print(f"Found {len(project_files)} project files")

# Get tags from all files
all_tags = []
for file_path in project_files:
    rel_fname = str(Path(file_path).relative_to(config.project_root))
    try:
        tags = dm.repo_map.get_tags(file_path, rel_fname)
        if tags:
            all_tags.extend(tags)
    except Exception as e:
        print(f"Failed to get tags for {rel_fname}: {e}")

print("Found {} total tags".format(len(all_tags)))

# Extract identifiers
identifiers = set()
for tag in all_tags:
    if hasattr(tag, "name") and tag.name:
        identifiers.add(tag.name)

print("Extracted {} unique identifiers".format(len(identifiers)))

# Check if specific identifiers exist
test_identifiers = ["RepoMapService", "parse_gitignore", "should_ignore_file"]
for identifier in test_identifiers:
    if identifier in identifiers:
        print(f"✅ Found: {identifier}")
    else:
        print(f"❌ Not found: {identifier}")

# Show some sample identifiers
print("\nSample identifiers:")
sample_identifiers = list(identifiers)[:20]
for identifier in sample_identifiers:
    print(f"  {identifier}")
