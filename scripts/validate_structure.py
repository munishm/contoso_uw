#!/usr/bin/env python3
"""
Validate directory structure against requirements.

Checks that the monorepo structure meets all requirements from the specification.
"""

import sys
import json
from pathlib import Path
from typing import List, Tuple


# Required directories (FR-001 through FR-007)
REQUIRED_DIRS = [
    "src",
    "src/interfaces",
    "src/shared",
    "src/shared/utils",
    "src/shared/models",
    "src/shared/schemas",
    "src/shared/config",
    "test",
    "test/unit",
    "test/integration",
    "test/e2e",
    "docs",
    "docs/architecture",
    "docs/adr",
    "docs/guides",
    "build",
    "dist",
]

# Required files
REQUIRED_FILES = [
    "README.md",
    ".gitignore",
    ".env.example",
    "pyproject.toml",
    ".import-linter.ini",
]


def check_directory_exists(dir_path: Path, base_path: Path) -> bool:
    """Check if directory exists."""
    full_path = base_path / dir_path
    return full_path.exists() and full_path.is_dir()


def check_file_exists(file_path: Path, base_path: Path) -> bool:
    """Check if file exists."""
    full_path = base_path / file_path
    return full_path.exists() and full_path.is_file()


def validate_structure(base_path: Path = None) -> Tuple[bool, List[str]]:
    """
    Validate directory structure.
    
    Args:
        base_path: Repository root path (defaults to current directory)
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    if base_path is None:
        base_path = Path.cwd()
    
    errors = []
    
    # Check required directories
    for dir_path in REQUIRED_DIRS:
        if not check_directory_exists(Path(dir_path), base_path):
            errors.append(f"Missing required directory: {dir_path}")
    
    # Check required files
    for file_path in REQUIRED_FILES:
        if not check_file_exists(Path(file_path), base_path):
            errors.append(f"Missing required file: {file_path}")
    
    # Check that .env files are gitignored (FR-012)
    gitignore_path = base_path / ".gitignore"
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()
        if ".env" not in gitignore_content:
            errors.append(".env files must be in .gitignore")
        if ".env.example" in gitignore_content and "!.env.example" not in gitignore_content:
            errors.append(".env.example should NOT be in .gitignore")
    
    # Check components have pyproject.toml (FR-013)
    src_path = base_path / "src"
    if src_path.exists():
        for item in src_path.iterdir():
            if item.is_dir() and item.name not in ["interfaces", "shared", "orchestration", "__pycache__"]:
                pyproject = item / "pyproject.toml"
                if not pyproject.exists():
                    errors.append(f"Component {item.name} missing pyproject.toml")
    
    return (len(errors) == 0, errors)


def main():
    """Main validation entry point."""
    print("🔍 Validating directory structure...")
    print()
    
    is_valid, errors = validate_structure()
    
    if is_valid:
        print("✅ All structure validations passed!")
        return 0
    else:
        print("❌ Structure validation failed:")
        print()
        for error in errors:
            print(f"  - {error}")
        print()
        print(f"Total errors: {len(errors)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
