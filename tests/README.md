# Testing the Infraninja Project

This directory contains tests for the Infraninja project. The tests are organized by module, with each module having its own subdirectory.

## Running Tests

To run all tests:

```bash
pytest
```

To run tests for a specific module:

```bash
pytest tests/inventory/
```

To run a specific test file:

```bash
pytest tests/inventory/test_jinn.py
```

## Testing Approach

This project provides examples of two testing styles:

1. **unittest style** (`test_jinn.py`) - Using Python's built-in unittest framework with mock patching
2. **pytest style** (`test_jinn_pytest.py`) - Using pytest fixtures and monkeypatching

Both approaches are valid, but pytest offers a more modern and concise syntax that many developers prefer.

## Testing Functions That Make API Calls

The `fetch_ssh_config` function demonstrates how to test code that makes external API calls:

1. **Mock the requests library** - We don't want actual HTTP requests during tests
2. **Test both success and error cases** - Including HTTP errors, timeouts, and connection errors
3. **Verify parameter handling** - Ensuring parameters like `bastionless` are correctly passed
4. **Check URL handling** - Testing that URLs with/without trailing slashes work correctly

## Test Fixtures

Shared test fixtures are defined in `conftest.py` and can be used by any test. This promotes DRY (Don't Repeat Yourself) principles in your test code.

## Best Practices

1. Each test should be independent and not rely on the state from other tests
2. Use descriptive test names that explain what you're testing
3. Follow the AAA pattern: Arrange, Act, Assert
4. Mock external dependencies to isolate your code
5. Test both happy paths and error conditions