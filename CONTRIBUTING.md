# Contributing

Thank you for helping improve API Test Platform.

## Before you start

1. Read the [README](README.md) and [Code of Conduct](CODE_OF_CONDUCT.md).
2. Search existing issues and pull requests to avoid duplicate work.
3. Open an issue before starting a large feature or an API-breaking change.

## Development workflow

1. Fork the repository and create a focused branch.
2. Set up the backend with `uv sync` and the UI with `pnpm install` in `ui/`.
3. Add or update tests for behavioural changes.
4. Run the relevant checks before opening a pull request:

   ```bash
   uv run python -m pytest
   cd ui && pnpm format:check && pnpm build
   ```

5. Describe the problem, approach, verification evidence, and any migration or security implications in the pull request.

## Pull request expectations

- Keep each pull request small and focused.
- Preserve backwards compatibility unless the issue explicitly approves a breaking change.
- Do not include secrets, customer data, or generated test artifacts.
- Update documentation for user-visible behaviour or configuration changes.
- Be respectful and constructive in review discussions.

## Licensing

By contributing, you agree that your contributions are licensed under the [Apache License 2.0](LICENSE).
