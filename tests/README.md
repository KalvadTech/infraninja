# Testing the InfraNinja Project

This directory contains comprehensive tests for the InfraNinja project. The tests are organized by module, with each module having its own subdirectory that mirrors the main project structure.

## Test Structure

```text
tests/
├── __init__.py
├── common/           # Tests for common security modules
│   ├── test_acl.py
│   ├── test_ssh_hardening.py
│   ├── test_kernel_hardening.py
│   └── ...
├── inventory/        # Tests for inventory management
│   ├── test_coolify.py
│   ├── test_jinn.py
│   └── ...
└── utils/           # Tests for utility modules
    ├── test_motd.py
    ├── test_pubkeys.py
    └── ...
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Tests for Specific Modules

```bash
# Test inventory modules
pytest tests/inventory/

# Test security modules
pytest tests/common/

# Test utility modules
pytest tests/utils/
```

### Run Specific Test Files

```bash
# Test Jinn inventory integration
pytest tests/inventory/test_jinn.py

# Test Coolify integration
pytest tests/inventory/test_coolify.py

# Test SSH hardening
pytest tests/common/test_ssh_hardening.py
```

### Run Tests with Coverage

```bash
# Generate coverage report
pytest --cov=infraninja tests/

# Generate HTML coverage report
pytest --cov=infraninja --cov-report=html tests/
```

### Run Tests with Verbose Output

```bash
pytest -v tests/
```

## Testing Approach

This project demonstrates modern Python testing practices using two complementary approaches:

### 1. unittest Style (Traditional)

**Example**: `test_coolify.py`

- Uses Python's built-in `unittest.TestCase` framework
- Mock patching with `unittest.mock.patch`
- Explicit setup and teardown methods
- Detailed test class organization

```python
class TestCoolify(unittest.TestCase):
    def setUp(self):
        self.api_key = "test-api-key"
        
    @patch('requests.get')
    def test_api_request(self, mock_get):
        mock_get.return_value.json.return_value = {"servers": []}
        # Test implementation
```

### 2. pytest Style (Modern)

**Example**: `test_jinn_pytest.py`

- Uses pytest framework with fixtures
- Monkeypatching for mocking
- Parameterized tests
- More concise and readable syntax

```python
@pytest.fixture
def api_key():
    return "test-api-key"

def test_api_request(monkeypatch, api_key):
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: mock_response)
    # Test implementation
```

Both approaches are valid and demonstrate different testing philosophies. Choose the one that best fits your team's preferences and existing codebase.

## Testing API Integration

The project includes comprehensive tests for API integration, particularly for modules that make external HTTP requests:

### Testing HTTP Requests

When testing functions that make API calls (like `fetch_ssh_config`), we follow these principles:

1. **Mock External Dependencies**: Never make actual HTTP requests during tests
2. **Test Success and Error Cases**: Include HTTP errors, timeouts, and connection errors
3. **Verify Parameter Handling**: Ensure parameters are correctly passed and processed
4. **Test URL Handling**: Verify URLs with/without trailing slashes work correctly

### Example: Testing Jinn API Integration

```python
@patch('infraninja.inventory.jinn.requests.get')
def test_load_servers_success(self, mock_get):
    # Mock successful API response
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"servers": [...]}
    
    jinn = Jinn(api_key="test-key")
    assert len(jinn.servers) == expected_count

@patch('infraninja.inventory.jinn.requests.get')
def test_load_servers_api_error(self, mock_get):
    # Mock API error response
    mock_get.side_effect = requests.RequestException("API Error")
    
    with pytest.raises(JinnAPIError):
        Jinn(api_key="test-key")
```

### Testing Security Modules

Security module tests focus on:

- **Configuration Validation**: Ensure security configurations are correctly applied
- **OS Compatibility**: Test modules work across different operating systems
- **Error Handling**: Verify graceful handling of system errors
- **Side Effects**: Confirm no unintended system modifications

```python
def test_ssh_hardening(self, mock_pyinfra_operations):
    ssh_hardening()
    
    # Verify SSH configuration changes
    mock_pyinfra_operations.files.replace.assert_called_with(
        name="Configure SSH: PasswordAuthentication",
        path="/etc/ssh/sshd_config",
        # ... other parameters
    )
```

## Test Fixtures and Utilities

### Shared Fixtures

Common test fixtures are defined in `conftest.py` files and can be used across multiple test files:

```python
# conftest.py
@pytest.fixture
def mock_ssh_key_path(tmp_path):
    key_file = tmp_path / "test_key"
    key_file.write_text("mock-ssh-key-content")
    return key_file

@pytest.fixture
def sample_server_data():
    return {
        "servers": [
            {"name": "server1", "ip": "1.1.1.1"},
            {"name": "server2", "ip": "2.2.2.2"}
        ]
    }
```

### Mock Helpers

Utility functions for common mocking scenarios:

```python
def mock_api_response(data, status_code=200):
    """Helper to create mock API responses"""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = data
    return mock_response
```

## Continuous Integration

The test suite is designed to run in CI/CD environments:

### GitHub Actions

```yaml
- name: Run tests
  run: |
    pip install pytest pytest-cov
    pytest --cov=infraninja tests/
```

### Local Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests with file watching
pytest-watch tests/

# Run specific test categories
pytest -m "not integration" tests/  # Skip integration tests
pytest -m "security" tests/         # Run only security tests
```

## Test Categories

Tests are organized into categories using pytest markers:

- `@pytest.mark.unit`: Unit tests for individual functions
- `@pytest.mark.integration`: Integration tests for API interactions
- `@pytest.mark.security`: Security-focused tests
- `@pytest.mark.slow`: Tests that take longer to run

Run specific categories:

```bash
pytest -m unit tests/           # Fast unit tests
pytest -m integration tests/   # API integration tests
pytest -m "not slow" tests/    # Skip slow tests
```

## Best Practices

1. **Test Independence**: Each test should be independent and not rely on state from other tests
2. **Descriptive Names**: Use descriptive test names that explain what you're testing
3. **AAA Pattern**: Follow the Arrange, Act, Assert pattern for clear test structure
4. **Mock External Dependencies**: Mock external APIs, file systems, and network calls
5. **Test Both Paths**: Test both successful operations and error conditions
6. **Use Fixtures**: Leverage pytest fixtures for common test data and setup
7. **Keep Tests Fast**: Mock expensive operations to keep tests running quickly
8. **Document Complex Logic**: Add comments for complex test scenarios or edge cases

## Writing New Tests

When adding new functionality to InfraNinja:

1. **Create Test File**: Follow the naming convention `test_<module_name>.py`
2. **Mirror Structure**: Place tests in the same directory structure as the source code
3. **Cover Edge Cases**: Test error conditions, invalid inputs, and boundary conditions
4. **Mock Dependencies**: Mock external services, APIs, and system calls
5. **Test Documentation**: Ensure examples in documentation are tested
6. **Update Coverage**: Aim for high test coverage but focus on meaningful tests

Example test structure for a new module:

```python
# tests/security/test_new_module.py
import pytest
from unittest.mock import patch, Mock

from infraninja.security.new_module import new_function

class TestNewModule:
    def test_new_function_success(self):
        # Test successful operation
        result = new_function("valid_input")
        assert result == expected_output
    
    def test_new_function_invalid_input(self):
        # Test error handling
        with pytest.raises(ValueError):
            new_function("invalid_input")
    
    @patch('infraninja.security.new_module.external_dependency')
    def test_new_function_with_mock(self, mock_dependency):
        # Test with mocked external dependency
        mock_dependency.return_value = "mocked_result"
        result = new_function("input")
        assert "mocked_result" in result
```
