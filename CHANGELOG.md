# Changelog

All notable changes to the HSBC Insurance Underwriting Automation Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CI/CD workflow for automated structure validation (`.github/workflows/structure-validation.yml`)
- Environment-specific configuration files (`.env.dev`, `.env.staging`, `.env.prod`)
- Integration test placeholders (`test/integration/test_orchestration.py`)
- End-to-end test placeholders (`test/e2e/test_document_processing_workflow.py`)
- Documentation guides:
  - Environment configuration guide (`docs/guides/environment_configuration.md`)
  - Testing strategy guide (`docs/guides/testing_strategy.md`)

### Changed
- Updated `pyproject.toml` with hatchling build configuration
- Corrected import-linter layering to place orchestration at application layer
- All development dependencies installed via UV (pytest, mypy, import-linter, ruff)

### Fixed
- Import-linter contracts now passing (2/2 contracts kept)
- UV sync build errors resolved with correct package configuration

### Validation Status (2025-12-15)
- ✅ Structure validation: All FR requirements passing
- ✅ Import-linter: 2/2 contracts kept (layering + component isolation)
- ✅ Pytest: 10/10 placeholder tests passing
- ✅ UV sync: 47 packages resolved successfully

---

## [0.1.0] - 2025-12-15

### Added
- Initial project structure implementation
- Basic project scaffolding for POC phase

[Unreleased]: https://github.com/hsbc/iwpb-uw/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/hsbc/iwpb-uw/releases/tag/v0.1.0
