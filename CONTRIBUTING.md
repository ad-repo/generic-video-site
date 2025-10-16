# Contributing to Generic Video Site

Thank you for your interest in contributing to Generic Video Site! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git
- Basic knowledge of FastAPI and web development

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/generic-video-site.git
   cd generic-video-site
   ```

2. **Set Up Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set Up Data Directory**
   ```bash
   mkdir -p data
   # Add your test video files to the data directory
   ```

4. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

## 📝 Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions small and focused

### Testing

- Write tests for all new features
- Maintain test coverage above 80%
- Use descriptive test names
- Test both success and failure cases

### Documentation

- Update README.md for new features
- Add docstrings to new functions
- Update API documentation if applicable

## 🔄 Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write your code
- Add tests
- Update documentation

### 3. Test Your Changes

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Test Docker build
docker build -t generic-video-site .
```

### 4. Commit Changes

```bash
git add .
git commit -m "Add feature: brief description"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── test_main.py      # Main application tests
├── test_docker.py    # Docker and infrastructure tests
└── test_integration.py # Integration tests
```

### Writing Tests

```python
def test_feature_name():
    """Test description."""
    # Arrange
    setup_test_data()
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result == expected_value
```

### Test Categories

- **Unit Tests**: Test individual functions
- **Integration Tests**: Test API endpoints
- **Docker Tests**: Test containerization
- **Security Tests**: Test security aspects

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to Reproduce**: Detailed steps to reproduce the bug
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Python version, Docker version
6. **Logs**: Relevant error messages or logs

## 💡 Feature Requests

When requesting features, please include:

1. **Use Case**: Why is this feature needed?
2. **Description**: Detailed description of the feature
3. **Acceptance Criteria**: How will we know it's complete?
4. **Mockups**: Visual representations if applicable

## 🔍 Code Review Process

### For Contributors

1. **Self-Review**: Review your own code before submitting
2. **Test Coverage**: Ensure adequate test coverage
3. **Documentation**: Update relevant documentation
4. **Performance**: Consider performance implications

### For Reviewers

1. **Functionality**: Does the code work as intended?
2. **Testing**: Are there adequate tests?
3. **Security**: Are there any security concerns?
4. **Performance**: Any performance issues?
5. **Documentation**: Is documentation updated?

## 📋 Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Docker build successful

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

## 🏷️ Release Process

1. **Version Bumping**: Update version numbers
2. **Changelog**: Update CHANGELOG.md
3. **Tagging**: Create git tags for releases
4. **Docker**: Build and push Docker images
5. **Documentation**: Update documentation

## 🤝 Community Guidelines

### Be Respectful

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully

### Be Constructive

- Focus on what is best for the community
- Show empathy towards other community members
- Help others learn and grow

### Be Professional

- Keep discussions focused on the project
- Avoid personal attacks or harassment
- Follow the code of conduct

## 📞 Getting Help

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Documentation**: Check the README and code comments
- **Community**: Join our community discussions

## 🎯 Areas for Contribution

### High Priority

- Performance improvements
- Security enhancements
- Mobile responsiveness
- Accessibility improvements

### Medium Priority

- Additional video formats
- Advanced search functionality
- User authentication
- Analytics dashboard

### Low Priority

- UI/UX improvements
- Additional themes
- Plugin system
- API extensions

## 📄 License

By contributing to Generic Video Site, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to Generic Video Site! 🎉
