# Google Pollen Integration - Test Suite

This document describes the test suite for the Google Pollen Home Assistant custom component.

## Setup

The test suite uses `pytest-homeassistant-custom-component` which provides testing utilities specifically designed for Home Assistant custom components.

### Install Dependencies

```bash
pip install pytest pytest-homeassistant-custom-component
```

Or install from the project:

```bash
pip install -e ".[test]"
```

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test File

```bash
pytest tests/test_config_flow.py
pytest tests/test_coordinator.py
pytest tests/test_sensor.py
pytest tests/test_google_pollen_api.py
```

### Run Specific Test

```bash
pytest tests/test_config_flow.py::test_form
```

### Run with Verbose Output

```bash
pytest tests/ -v
```

### Run with Coverage

```bash
pytest tests/ --cov=custom_components.google_pollen --cov-report=html
```

## Test Structure

```
tests/
├── __init__.py                    # Test package marker
├── conftest.py                    # Shared fixtures and configuration
├── test_config_flow.py           # Config flow tests
├── test_coordinator.py           # Data coordinator tests
├── test_google_pollen_api.py     # API client tests
├── test_init.py                  # Integration setup/unload tests
└── test_sensor.py                # Sensor platform tests
```

## Test Coverage

### API Client Tests (`test_google_pollen_api.py`)
- ✅ Successful API calls
- ✅ API calls with referrer header
- ✅ HTTP error handling
- ✅ Timeout handling
- ✅ Defensive parsing with missing data
- ✅ Defensive parsing with minimal data

### Config Flow Tests (`test_config_flow.py`)
- ✅ Initial config flow form
- ✅ Config flow with optional referrer
- ✅ Connection error handling
- ✅ Unknown error handling
- ✅ Duplicate API key detection
- ✅ Duplicate location detection

### Coordinator Tests (`test_coordinator.py`)
- ✅ Successful data updates
- ✅ Failed data updates
- ⚠️ Interval-based updates (needs refinement)

### Integration Tests (`test_init.py`)
- ⚠️ Config entry setup
- ✅ Setup with no subentries
- ⚠️ Config entry unload
- ⚠️ Options update

### Sensor Tests (`test_sensor.py`)
- ⚠️ Sensor platform setup
- ⚠️ Missing data handling
- ⚠️ Sensor attributes

## Known Issues

Some tests are currently failing due to mock configuration challenges with subentries. The main issues are:

1. **Mock Patching**: Some tests need the GooglePollenApi to be patched at the correct import location
2. **Subentry Mocking**: MockConfigEntry subentry handling needs proper setup

### Workaround for Failed Tests

The failing tests are primarily integration tests that test the full setup flow. The unit tests (API, config flow basics, coordinator) are passing successfully.

To focus on passing tests:

```bash
pytest tests/test_google_pollen_api.py tests/test_config_flow.py -v
```

## Fixtures

### Common Fixtures (conftest.py)

- `auto_enable_custom_integrations`: Automatically enables custom integration loading for all tests
- `mock_google_pollen_api`: Mocked GooglePollenApi client with sample data
- `mock_config_entry_data`: Sample config entry data with API key and referrer
- `mock_subentry_data`: Sample subentry data with latitude/longitude
- `create_mock_entry_with_subentry()`: Helper function to create config entries with subentries

## Writing New Tests

### Test a New Sensor

```python
async def test_my_new_sensor(
    hass: HomeAssistant,
    mock_google_pollen_api,
    mock_config_entry_data,
    mock_subentry_data,
) -> None:
    """Test my new sensor."""
    from tests.conftest import create_mock_entry_with_subentry

    config_entry, _ = create_mock_entry_with_subentry(
        hass, mock_config_entry_data, mock_subentry_data
    )

    with patch(
        "custom_components.google_pollen.GooglePollenApi",
        return_value=mock_google_pollen_api,
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    # Your test assertions here
    state = hass.states.get("sensor.test_location_my_sensor")
    assert state is not None
```

### Test Error Handling

```python
async def test_api_error_handling(mock_session):
    """Test API error handling."""
    api = GooglePollenApi(mock_session, "test_key")

    mock_session.get.side_effect = aiohttp.ClientError("Connection failed")

    with pytest.raises(GooglePollenApiError):
        await api.async_get_current_conditions(37.7749, -122.4194)
```

##Configuration

Test configuration is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
norecursedirs = [".git", "testing_config"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

## Best Practices

1. **Use Fixtures**: Leverage the shared fixtures in `conftest.py` to avoid duplication
2. **Mock External Calls**: Always mock API calls and external dependencies
3. **Test Edge Cases**: Include tests for error conditions, missing data, and edge cases
4. **Keep Tests Independent**: Each test should be able to run independently
5. **Use Descriptive Names**: Test names should clearly describe what they test
6. **Follow HA Patterns**: Follow Home Assistant's testing patterns from their core tests

## Continuous Integration

To set up CI/CD for these tests, create a GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-homeassistant-custom-component
      - name: Run tests
        run: pytest tests/ -v
```

## Troubleshooting

### Tests Can't Find Custom Component

Make sure `pytest_plugins = "pytest_homeassistant_custom_component"` is in your `conftest.py` and the `auto_enable_custom_integrations` fixture is present.

### AsyncIO Errors

Ensure `asyncio_mode = "auto"` is set in `pyproject.toml` under `[tool.pytest.ini_options]`.

### Import Errors

Make sure you're running tests from the project root directory and the `custom_components` directory is in the correct location.
