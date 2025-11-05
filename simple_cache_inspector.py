import json
from pathlib import Path
from repomap_tool.core.tag_cache import TreeSitterTagCache

def inspect_cache(cache_path: str = "~/.repomap-tool/cache/tags.db") -> None:
    cache_file = Path(cache_path).expanduser()
    if not cache_file.exists():
        print(f"Cache file not found at: {cache_file}")
        return

    print(f"Inspecting cache file: {cache_file}")
    tag_cache = TreeSitterTagCache(cache_path=str(cache_file))
    stats = tag_cache.get_cache_stats()

    print("\n--- Cache Statistics ---")
    for key, value in stats.items():
        print(f"{key}: {value}")

    # Optionally, dump contents
    # print("\n--- Cache Contents (first 5 entries) ---")
    # try:
    #     conn = sqlite3.connect(cache_file)
    #     cursor = conn.cursor()
    #     cursor.execute("SELECT file_path, tags_json, timestamp FROM tags LIMIT 5")
    #     for row in cursor.fetchall():
    #         file_path, tags_json, timestamp = row
    #         tags_data = json.loads(tags_json)
    #         print(f"File: {file_path}, Tags: {len(tags_data)}, Timestamp: {timestamp}")
    # except Exception as e:
    #     print(f"Error reading cache contents: {e}")
    # finally:
    #     conn.close()

if __name__ == "__main__":
    inspect_cache() 