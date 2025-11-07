#!/usr/bin/env python3
"""
Find Python files under a directory that contain NUL bytes.
Usage:
    python sample.py [path]
If no path is given, it scans the current directory (.)
Exit codes:
    0 - no files with NUL bytes
    1 - some files contain NUL bytes
    2 - invalid path / error
"""
from pathlib import Path
import sys

def find_files_with_nul(root: Path):
    if not root.exists():
        print(f"ERROR: path not found: {root}")
        return None
    found = []
    for p in root.rglob("*.py"):
        try:
            data = p.read_bytes()
        except Exception as e:
            print(f"ERROR reading {p}: {e}")
            continue
        if b"\x00" in data:
            found.append(p)
    return found


def main(argv):
    # 👇 If no argument, use current directory
    target = Path(argv[1]) if len(argv) > 1 else Path(".")
    target = target.resolve()
    print(f"🔍 Scanning: {target}")
    
    result = find_files_with_nul(target)
    if result is None:
        return 2
    if not result:
        print("✅ No Python files with NUL bytes found.")
        return 0
    for p in result:
        print(f"❌ {p}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
