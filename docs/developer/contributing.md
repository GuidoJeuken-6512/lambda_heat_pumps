# Contributing

Thank you for your interest in contributing to the Lambda Heat Pumps integration!

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Home Assistant development environment
- Git

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/lambda_wp_hacs.git
   ```
3. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements_test.txt
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 style guide
- Use type hints
- Write docstrings for all functions and classes
- Keep functions focused and small

### Testing

Write tests for new features:

```python
async def test_new_feature():
    # Test implementation
    assert result == expected
```

Run tests:

```bash
pytest tests/
```

### Documentation

- Update documentation for new features
- Add examples where appropriate
- Keep documentation in sync with code

## Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make your changes and commit:
   ```bash
   git commit -m "Add new feature"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/my-feature
   ```

4. Create a Pull Request on GitHub

### PR Requirements

- Code follows style guidelines
- Tests pass
- Documentation is updated
- Changes are backward compatible (or migration is provided)

## Reporting Issues

When reporting issues, please include:

- Home Assistant version
- Integration version
- Error messages
- Steps to reproduce
- Relevant logs

## Related Documentation

- [Architecture](architecture.md)
- [Entity Creation](entity-creation.md)

