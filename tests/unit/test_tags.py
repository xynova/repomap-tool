#!/usr/bin/env python3

from aider.repomap import RepoMap
from aider.io import InputOutput
from aider.models import Model, DEFAULT_MODEL_NAME

# Initialize RepoMap
rm = RepoMap(root='.', main_model=Model(DEFAULT_MODEL_NAME), io=InputOutput())

# Get tags from core.py
tags = rm.get_tags('src/repomap_tool/core.py', 'src/repomap_tool/core.py')

print(f'Found {len(tags)} tags in core.py')

# Check available kinds
kinds = set(tag.kind for tag in tags)
print(f'Available tag kinds: {sorted(kinds)}')

# Look for DockerRepoMap specifically
docker_tags = [tag for tag in tags if 'DockerRepoMap' in tag.name]
print(f'Found {len(docker_tags)} tags containing "DockerRepoMap":')
for tag in docker_tags:
    print(f'  {tag.name} (kind: {tag.kind}, line: {tag.line})')

# Look for class definitions
class_tags = [tag for tag in tags if tag.kind == 'def' and 'class' in tag.name.lower()]
print(f'\nFound {len(class_tags)} class definitions:')
for tag in class_tags[:10]:
    print(f'  {tag.name} (line: {tag.line})')

# Look for all 'def' kind tags
def_tags = [tag for tag in tags if tag.kind == 'def']
print(f'\nFound {len(def_tags)} definition tags:')
for tag in def_tags[:10]:
    print(f'  {tag.name} (line: {tag.line})')
