#!/usr/bin/env python3

from src.repomap_tool.cli import create_search_config
from src.repomap_tool.core import DockerRepoMap

# Test the search config
config = create_search_config('.', 'fuzzy', True)
print(f'Fuzzy enabled: {config.fuzzy_match.enabled}')
print(f'Semantic enabled: {config.semantic_match.enabled}')

# Initialize RepoMap with this config
dm = DockerRepoMap(config)
print(f'Fuzzy matcher available: {dm.fuzzy_matcher is not None}')

if dm.fuzzy_matcher:
    print('Testing fuzzy matcher...')
    # Test with some identifiers
    test_identifiers = {'DockerRepoMap', 'parse_gitignore', 'should_ignore_file'}
    matches = dm.fuzzy_matcher.match_identifiers('DockerRepoMap', test_identifiers)
    print(f'Found {len(matches)} matches for "DockerRepoMap":')
    for identifier, score in matches:
        print(f'  {identifier}: {score}%')
else:
    print('Fuzzy matcher not available')
