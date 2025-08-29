#!/usr/bin/env python3

from src.repomap_tool.core import DockerRepoMap
from src.repomap_tool.models import RepoMapConfig
from pathlib import Path

# Initialize the tool
config = RepoMapConfig(project_root='.', verbose=True)
dm = DockerRepoMap(config)

# Get project files
project_files = dm._get_project_files()
print(f'Found {len(project_files)} project files')

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

print(f'Found {len(all_tags)} total tags')

# Extract identifiers
identifiers = set()
for tag in all_tags:
    if hasattr(tag, 'name') and tag.name:
        identifiers.add(tag.name)

print(f'Extracted {len(identifiers)} unique identifiers')

# Check if specific identifiers exist
test_identifiers = ['DockerRepoMap', 'parse_gitignore', 'should_ignore_file']
for identifier in test_identifiers:
    if identifier in identifiers:
        print(f'✅ Found: {identifier}')
    else:
        print(f'❌ Not found: {identifier}')

# Show some sample identifiers
print(f'\nSample identifiers:')
sample_identifiers = list(identifiers)[:20]
for identifier in sample_identifiers:
    print(f'  {identifier}')
