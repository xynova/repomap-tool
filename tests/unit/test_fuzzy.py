#!/usr/bin/env python3

from src.repomap_tool.core import DockerRepoMap
from src.repomap_tool.models import RepoMapConfig
from pathlib import Path

# Initialize the tool
config = RepoMapConfig(project_root='.', verbose=True)
dm = DockerRepoMap(config)

# Get identifiers
project_files = dm._get_project_files()
all_tags = []
for file_path in project_files:
    rel_fname = str(Path(file_path).relative_to(config.project_root))
    try:
        tags = dm.repo_map.get_tags(file_path, rel_fname)
        if tags:
            all_tags.extend(tags)
    except Exception as e:
        print(f"Failed to get tags for {rel_fname}: {e}")

identifiers = set()
for tag in all_tags:
    if hasattr(tag, 'name') and tag.name:
        identifiers.add(tag.name)

print(f'Testing fuzzy search with {len(identifiers)} identifiers')

# Test fuzzy matcher directly
if dm.fuzzy_matcher:
    print('Testing fuzzy matcher...')
    matches = dm.fuzzy_matcher.match_identifiers('DockerRepoMap', identifiers)
    print(f'Found {len(matches)} matches for "DockerRepoMap":')
    for identifier, score in matches[:5]:
        print(f'  {identifier}: {score}%')
    
    matches = dm.fuzzy_matcher.match_identifiers('parse_gitignore', identifiers)
    print(f'Found {len(matches)} matches for "parse_gitignore":')
    for identifier, score in matches[:5]:
        print(f'  {identifier}: {score}%')
else:
    print('Fuzzy matcher not available')
