# Contributing to Zeek-YARA Integration Platform

Thank you for your interest in contributing to this educational security platform! Contributions from all skill levels are welcome and appreciated.

## Ways to Contribute

### 1. Documentation & Educational Content
- **Tutorial Development**: Create new step-by-step learning modules
- **Documentation Improvements**: Fix typos, clarify instructions, add examples
- **Translations**: Help make content accessible in other languages
- **Case Studies**: Share real-world security scenarios and analysis

### 2. Code Contributions
- **Bug Fixes**: Identify and resolve platform issues
- **Feature Enhancements**: Improve existing functionality
- **New Features**: Add capabilities that enhance learning experience
- **Performance Optimizations**: Improve system efficiency

### 3. Testing & Quality Assurance
- **Test Coverage**: Write unit, integration, and performance tests
- **Cross-Platform Testing**: Verify functionality across different operating systems
- **Educational Testing**: Validate tutorial effectiveness and accuracy
- **Bug Reporting**: Document issues with reproduction steps

### 4. Community Support
- **Issue Triage**: Help organize and prioritize GitHub issues
- **User Support**: Assist users in discussions and troubleshooting
- **Code Reviews**: Review pull requests from other contributors
- **Community Guidelines**: Help maintain a welcoming environment

## Getting Started

### Prerequisites
- Python 3.12.5 or higher
- Basic understanding of network security concepts
- Familiarity with Git and GitHub workflows

### Development Setup

1. **Fork and Clone**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/zeek-yara-integration.git
   cd zeek-yara-integration
   ```

2. **Set up Development Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r config/test-requirements.txt
   ```

3. **Verify Installation**:
   ```bash
   ./TOOLS/cli/zyi status
   ./TOOLS/cli/zyi demo run --tutorial basic-detection
   ```

4. **Run Tests**:
   ```bash
   python -m pytest TESTING/
   ```

### Making Changes

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**: Follow existing code patterns and conventions

3. **Test Your Changes**:
   ```bash
   # Run relevant tests
   python -m pytest TESTING/unit/
   python -m pytest TESTING/integration/
   
   # Verify educational content if applicable
   cd EDUCATION && python start_tutorial_server.py
   ```

4. **Commit Changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

## Code Standards

### Python Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep line length under 100 characters

### Code Formatting
We use automated code formatting tools to ensure consistency across the codebase:

**Black for Code Formatting:**
```bash
# Format all Python files
black .

# Check formatting without making changes
black --check --diff .
```

**isort for Import Sorting:**
```bash
# Sort imports in all Python files
isort .

# Check import sorting without making changes
isort --check-only --diff .
```

**Running Both Tools:**
```bash
# Format code and sort imports
black . && isort .
```

All code must pass Black and isort checks before being merged. The CI pipeline will automatically verify formatting compliance.

### Pre-commit Hooks (Recommended)
To automatically run formatting checks before each commit, set up pre-commit hooks:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install

# Run on all files (optional)
pre-commit run --all-files
```

Once installed, Black, isort, and other quality checks will run automatically before each commit.

### Documentation Standards
- Use clear, beginner-friendly language
- Include code examples where relevant
- Provide step-by-step instructions
- Test all examples before submitting

### Educational Content Guidelines
- **Accessibility**: Content should be understandable by beginners
- **Practical Focus**: Include hands-on exercises and real examples
- **Safety First**: Ensure all examples use safe, non-malicious content
- **Progressive Learning**: Build concepts incrementally

## Pull Request Process

### Before Submitting
1. Ensure all tests pass
2. Update documentation as needed
3. Add tests for new functionality
4. Verify educational content works as expected

### Pull Request Template
```markdown
## Description
Brief description of changes made

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that changes existing functionality)
- [ ] Documentation update
- [ ] Educational content addition/improvement

## Testing
- [ ] Tests pass locally
- [ ] Educational content tested (if applicable)
- [ ] Cross-platform compatibility verified (if applicable)

## Additional Notes
Any additional information about the changes
```

### Review Process
1. **Automated Checks**: CI/CD pipeline runs tests and quality checks
2. **Code Review**: Maintainers review code for quality and educational value
3. **Educational Review**: Educational content is tested for clarity and accuracy
4. **Final Testing**: Changes are tested in various environments

## Educational Content Contribution

### Tutorial Development
When creating new tutorials, ensure they:
- Have clear learning objectives
- Include hands-on exercises
- Use safe, educational examples (like EICAR test files)
- Provide verification steps
- Follow the existing tutorial structure

### Example Tutorial Structure
```python
TutorialStep(
    id="unique_step_id",
    title="Step Title",
    content="Educational content with examples",
    action="action_to_execute",
    duration_estimate="5 minutes",
    prerequisites=["previous_step"],
    learning_objectives=[
        "What learners will understand",
        "Skills they will develop"
    ]
)
```

## Issue Reporting

### Bug Reports
When reporting bugs, please include:
- **Environment**: OS, Python version, installation method
- **Steps to Reproduce**: Detailed steps that trigger the issue
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Logs/Screenshots**: Relevant error messages or screenshots

### Feature Requests
For new features, describe:
- **Use Case**: Why this feature would be valuable
- **Educational Impact**: How it enhances learning
- **Implementation Ideas**: Suggestions for implementation
- **Examples**: Similar features in other tools

## Community Guidelines

### Code of Conduct
- **Respectful Communication**: Treat all contributors with respect
- **Inclusive Environment**: Welcome people of all backgrounds and skill levels
- **Constructive Feedback**: Provide helpful, specific feedback
- **Educational Focus**: Keep discussions focused on learning and security education

### Getting Help
- **Discussions**: Use GitHub Discussions for questions and collaboration
- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Documentation**: Check existing documentation first
- **Community**: Engage with other contributors and learners

## Recognition

### Contributors
All contributors are recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Community showcases for educational content

### Maintainer Path
Active contributors may be invited to become maintainers, with responsibilities including:
- Code review and merge authority
- Community management
- Technical decision making
- Educational content oversight

## Resources

### Development Resources
- [Python Security Best Practices](https://docs.python.org/3/library/security.html)
- [Educational Technology Guidelines](EDUCATION/README.md)
- [Testing Framework Documentation](TESTING/README.md)

### Security Resources
- [Zeek Documentation](https://docs.zeek.org/)
- [YARA Documentation](https://yara.readthedocs.io/)
- [Suricata Documentation](https://suricata.readthedocs.io/)

### Community Resources
- [GitHub Discussions](https://github.com/quanticsoul4772/zeek-yara-integration/discussions)
- [Issue Templates](https://github.com/quanticsoul4772/zeek-yara-integration/issues/new/choose)
- [Project Roadmap](PROJECT_PLAN.md)

Thank you for helping make network security education more accessible and effective!