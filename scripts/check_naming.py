#!/usr/bin/env python3
"""
Check that all directories follow snake_case naming convention.

Validates FR-008: All directory names MUST follow snake_case naming convention.
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple


SNAKE_CASE_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')

# Directories to exclude from naming validation
EXCLUDED_DIRS = {
    '.git',
    '.github',
    '.specify',
    '.vscode',
    '.idea',
    '__pycache__',
    'node_modules',
    '.pytest_cache',
    '.mypy_cache',
    '.tox',
    '.azure',
}


def is_snake_case(name: str) -> bool:
    """Check if name follows snake_case convention."""
    return bool(SNAKE_CASE_PATTERN.match(name))


def check_naming(base_path: Path = None) -> Tuple[bool, List[str]]:
    """
    Check directory naming conventions.
    
    Args:
        base_path: Repository root path (defaults to current directory)
        
    Returns:
        Tuple of (is_valid, list_of_violations)
    """
    if base_path is None:
        base_path = Path.cwd()
    
    violations = []
    
    # Walk directory tree
    for item in base_path.rglob("*"):
        if not item.is_dir():
            continue
        
        # Skip hidden and excluded directories
        if item.name.startswith('.') or item.name in EXCLUDED_DIRS:
            continue
        
        # Check naming convention
        if not is_snake_case(item.name):
            rel_path = item.relative_to(base_path)
            violations.append(f"{rel_path}: '{item.name}' is not snake_case")
    
    return (len(violations) == 0, violations)


def main():
    """Main naming check entry point."""
    print("🔍 Checking directory naming conventions (snake_case)...")
    print()
    
    is_valid, violations = check_naming()
    
    if is_valid:
        print("✅ All directories follow snake_case convention!")
        return 0
    else:
        print("❌ Naming convention violations found:")
        print()
        for violation in violations:
            print(f"  - {violation}")
        print()
        print(f"Total violations: {len(violations)}")
        print()
        print("Fix: Rename directories to use snake_case (lowercase with underscores)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
