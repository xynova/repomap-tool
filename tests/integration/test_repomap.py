#!/usr/bin/env python3

from aider.repomap import RepoMap
import os

class SimpleIO:
    def read_text(self, fname):
        print(f"Reading file: {fname}")
        if os.path.exists(fname):
            with open(fname, 'r') as f:
                content = f.read()
            print(f"File content length: {len(content)}")
            return content
        else:
            print(f"File does not exist: {fname}")
            return 'def test(): pass'
    
    def tool_warning(self, msg):
        print(f"Warning: {msg}")

class SimpleModel:
    def token_count(self, text):
        return len(text.split())

try:
    rm = RepoMap(root='.', io=SimpleIO(), main_model=SimpleModel())
    print('RepoMap created successfully')
    
    # Test with a file that definitely exists and has functions
    test_file = 'src/repomap_tool/core.py'
    print(f"\nTesting with file: {test_file}")
    
    # Test the method that's failing
    result = rm.get_ranked_tags_map([test_file], max_map_tokens=1024)
    print('Type:', type(result))
    print('Keys:', list(result.keys()) if isinstance(result, dict) else 'Not a dict')
    print('Sample:', str(result)[:500] if result else 'Empty')
    
    # Let's also try getting tags directly
    print("\nTrying get_tags directly:")
    tags = list(rm.get_tags(test_file, test_file))
    print(f"Tags found: {len(tags)}")
    for tag in tags[:10]:  # Show first 10 tags
        print(f"  {tag}")
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
