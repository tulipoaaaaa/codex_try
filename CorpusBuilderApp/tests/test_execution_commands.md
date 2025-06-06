# Run all tests with coverage
pytest --cov=app --cov=shared_tools --cov-report=html --cov-report=term

# Run security-critical tests only
pytest -m security -v

# Run integration tests
pytest -m integration -v

# Run performance tests
pytest -m performance -v

# Run UI tests (requires display)
pytest -m ui -v

# Generate detailed coverage report
pytest --cov=app --cov=shared_tools --cov-report=html --cov-fail-under=80
