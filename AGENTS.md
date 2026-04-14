# Claude Code instructions

This repository contains a Home Assistant custom integration that fetches pollen data from the Google Pollen API and exposes it as sensors.

## Project structure

```
custom_components/google_pollen/  # Integration source
tests/                            # pytest test suite
pyproject.toml                    # Project config, linting, type checking
.ruff.toml                        # Ruff linter config (if present)
```

## Python requirements

- **Compatibility**: Python 3.13+
- **Language features**: Use the newest features when possible:
  - Pattern matching
  - Type hints
  - f-strings (preferred over `%` or `.format()`)
  - Dataclasses
  - Walrus operator

### Strict typing
- Add type hints to all functions, methods, and variables
- Use the custom config entry type alias pattern:
  ```python
  type GooglePollenConfigEntry = ConfigEntry["GooglePollenRuntimeData"]
  ```

## Code quality

- **Formatter/linter**: Ruff (`python -m ruff check --fix && python -m ruff format`)
- **Type checking**: MyPy (`mypy custom_components/google_pollen`)
- **Testing**: pytest

Prefer fixing the underlying issue over adding `# type: ignore` or `# noqa` suppressions.

## Development commands

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests
pytest tests/

# Run specific test
pytest tests/test_config_flow.py -v

# Lint and format
python -m ruff check --fix custom_components/
python -m ruff format custom_components/

# Type check
mypy custom_components/google_pollen
```

## Async programming

All external I/O must be async (aiohttp, coordinator updates). No blocking calls.

- Use `asyncio.sleep()` not `time.sleep()`
- Avoid awaiting in loops — use `asyncio.gather()` instead
- Never block the event loop with sync HTTP calls or file I/O

## Error handling

Keep try blocks minimal — only wrap the call that can throw, then process data outside:

```python
# Good
try:
    data = await self.api.fetch(...)
except GooglePollenApiError as err:
    raise UpdateFailed(f"API error: {err}") from err

result = data.pollen_index * 100  # Process outside try

# Bad
try:
    data = await self.api.fetch(...)
    result = data.pollen_index * 100  # Don't process inside try
except GooglePollenApiError as err:
    raise UpdateFailed(...)
```

Catch specific exceptions. Avoid bare `except Exception:` outside of config flows and background tasks.

## Logging

- No periods at end of log messages
- No integration name/domain in messages (added automatically)
- No sensitive data (API keys, tokens)
- Use lazy formatting: `_LOGGER.debug("Fetched data for %s", location)`
- Use `debug` level for non-user-facing messages

## Writing style

- American English, sentence case (capitalize only the first word and proper nouns)
- Second-person ("you" and "your") for user-facing strings
- Use backticks for file paths, variable names, and field entries in messages
- Write for non-native English speakers — keep it clear and simple
