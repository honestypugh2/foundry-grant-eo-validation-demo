# Contributing to Grant Compliance Automation Demo

Thank you for your interest in contributing to this solution accelerator! This document provides guidelines for contributions.

## Code of Conduct

This project follows the Microsoft Open Source Code of Conduct. By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion:
1. Check if the issue already exists in the Issues section
2. If not, create a new issue with:
   - Clear, descriptive title
   - Detailed description of the issue or suggestion
   - Steps to reproduce (for bugs)
   - Expected vs. actual behavior
   - Environment details (OS, Python version, etc.)

### Submitting Changes

1. **Fork the Repository**
   ```bash
   git fork https://github.com/your-org/foundry-grant-eo-validation-demo
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
   - Follow the code style guidelines (see below)
   - Add or update tests as needed
   - Update documentation

4. **Test Your Changes**
   ```bash
   pytest tests/
   ```

5. **Commit Your Changes**
   ```bash
   git commit -m "Add: Brief description of changes"
   ```

6. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure all tests pass

## Development Setup

### Prerequisites
- Python 3.10 or higher
- Azure subscription (for testing with real services)
- Git

### Local Setup
```bash
# Clone your fork
git clone https://github.com/your-username/foundry-grant-eo-validation-demo
cd foundry-grant-eo-validation-demo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install agent-framework-azure-ai --pre

# Install dev dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your Azure credentials
```

## Code Style Guidelines

### Python
- Follow PEP 8 style guide
- Use Black for code formatting: `black .`
- Use type hints where appropriate
- Maximum line length: 100 characters
- Docstrings for all public functions and classes

### Example:
```python
def analyze_compliance(
    proposal_text: str,
    executive_orders: List[str]
) -> ComplianceResult:
    """
    Analyze a grant proposal for compliance.
    
    Args:
        proposal_text: The full text of the grant proposal
        executive_orders: List of relevant executive order IDs
    
    Returns:
        ComplianceResult containing analysis and recommendations
    """
    # Implementation
    pass
```

### Streamlit
- Keep components modular and reusable
- Use st.cache_data or st.cache_resource appropriately
- Provide helpful error messages
- Include user-friendly documentation

### Documentation
- Update README.md for new features
- Add docstrings to all functions
- Include inline comments for complex logic
- Update API documentation

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agents --cov=app

# Run specific test file
pytest tests/test_agents.py
```

### Writing Tests
- Write unit tests for new functions
- Include integration tests for workflows
- Mock external Azure services in tests
- Aim for >80% code coverage

Example:
```python
def test_compliance_analysis():
    """Test compliance agent analysis."""
    agent = ComplianceAgent(config)
    result = agent.analyze_proposal(sample_proposal)
    
    assert result.status in ["Compliant", "Non-Compliant", "Requires Review"]
    assert 0 <= result.confidence_score <= 100
    assert len(result.findings) > 0
```

## Project Structure

```
foundry-grant-eo-validation-demo/
├── agents/           # AI agent implementations
├── app/              # Streamlit application
├── config/           # Configuration files
├── knowledge_base/   # Sample documents
├── tests/            # Test suite
└── docs/             # Documentation
```

## Areas We'd Love Help With

- 🐛 Bug fixes
- 📝 Documentation improvements
- ✨ New features (check Issues for ideas)
- 🧪 Additional test coverage
- 🎨 UI/UX enhancements
- 🌐 Internationalization
- ♿ Accessibility improvements
- 📊 Additional sample data

## Specific Contribution Ideas

### Easy (Good First Issues)
- Add more sample grant proposals
- Improve error messages
- Add unit tests
- Fix documentation typos
- Enhance code comments

### Medium
- Add new executive order documents
- Improve UI components
- Add data visualization features
- Implement export functionality
- Add email notification templates

### Advanced
- Integrate with SharePoint
- Implement Azure Function Apps
- Add real-time collaboration features
- Enhance AI agent capabilities
- Build evaluation framework

## Review Process

1. **Automated Checks**: GitHub Actions will run tests and linters
2. **Code Review**: Maintainers will review your changes
3. **Feedback**: You may be asked to make changes
4. **Merge**: Once approved, your PR will be merged

## Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes
- Project documentation

## Questions?

- Open an issue for questions
- Join discussions in the Discussions tab
- Contact maintainers at [email protected]

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to improving grant compliance automation!
