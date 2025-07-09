# Contributing to GreyBrain Bank

Thank you for your interest in contributing to GreyBrain Bank! We welcome contributions from the community and are excited to see what you'll bring to our AI model aggregation platform.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Git
- Basic understanding of FastAPI and JavaScript

### Development Setup

1. **Fork the repository**
   ```bash
   git fork https://github.com/satishskid/greybrain-bank.git
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/greybrain-bank.git
   cd greybrain-bank
   ```

3. **Set up the development environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Start the development server**
   ```bash
   python app.py
   ```

## 🎯 How to Contribute

### Reporting Bugs
- Use the GitHub issue tracker
- Include detailed steps to reproduce
- Provide system information (OS, Python version, etc.)
- Include error messages and logs

### Suggesting Features
- Open an issue with the "enhancement" label
- Describe the feature and its benefits
- Provide use cases and examples
- Consider implementation complexity

### Code Contributions

#### Areas We Need Help With
- **AI Model Integrations**: Adding new AI providers and models
- **Academic Tools**: Expanding academic writing AI integrations
- **Frontend Improvements**: UI/UX enhancements
- **Performance Optimization**: Backend and frontend performance
- **Documentation**: API docs, tutorials, and guides
- **Testing**: Unit tests, integration tests, and end-to-end tests

#### Development Guidelines

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Follow coding standards**
   - Python: Follow PEP 8
   - JavaScript: Use consistent formatting
   - Add docstrings and comments
   - Write meaningful commit messages

3. **Test your changes**
   - Run existing tests
   - Add new tests for new features
   - Test the admin dashboard
   - Verify API endpoints work correctly

4. **Update documentation**
   - Update README.md if needed
   - Add API documentation for new endpoints
   - Update configuration examples

5. **Submit a pull request**
   - Provide a clear description
   - Reference related issues
   - Include screenshots for UI changes
   - Ensure CI passes

## 🔧 Development Guidelines

### Code Style
- **Python**: Follow PEP 8, use type hints
- **JavaScript**: Use modern ES6+ features
- **HTML/CSS**: Semantic markup, responsive design

### Commit Messages
Use conventional commit format:
```
type(scope): description

feat(models): add support for new AI provider
fix(api): resolve content generation timeout
docs(readme): update installation instructions
```

### Testing
- Write unit tests for new functions
- Test API endpoints with different inputs
- Verify frontend functionality across browsers
- Test admin dashboard features

## 🎓 Adding New AI Models

### Academic Writing AI
To add a new academic writing AI tool:

1. **Update model discovery**
   ```python
   # In model_discovery.py
   def get_academic_writing_models(self):
       academic_models = [
           # Add your new model here
           {"name": "new-academic-tool", "provider": "provider-name", 
            "type": "academic_writing", "source": "academic"},
       ]
   ```

2. **Add to content categories**
   ```python
   # In app.py CONTENT_CATEGORY_CONFIGS
   "quality_models": {
       1: ["new-academic-tool", ...],
       2: ["new-academic-tool", ...],
       3: ["new-academic-tool", ...]
   }
   ```

3. **Test the integration**
   - Verify model appears in discovery
   - Test health checks
   - Test content generation

### Enterprise AI Models
For enterprise AI models:

1. **Add to enterprise models list**
2. **Implement API integration**
3. **Add authentication handling**
4. **Update admin dashboard**

## 🐛 Bug Reports

### Before Reporting
- Check existing issues
- Try the latest version
- Reproduce the bug consistently

### Bug Report Template
```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g. macOS, Windows, Linux]
- Python version: [e.g. 3.9]
- Browser: [e.g. Chrome, Firefox]

**Additional context**
Any other context about the problem.
```

## 🚀 Feature Requests

### Feature Request Template
```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Any other context or screenshots about the feature request.
```

## 📝 Documentation

### Areas Needing Documentation
- API endpoint examples
- Configuration guides
- Deployment tutorials
- Academic AI integration guides
- Troubleshooting guides

### Documentation Style
- Use clear, concise language
- Include code examples
- Add screenshots for UI features
- Provide step-by-step instructions

## 🎉 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and community support
- **Email**: support@greybrain.ai for direct contact

## 📄 License

By contributing to GreyBrain Bank, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to GreyBrain Bank!**

*Made with ❤️ by the GreyBrain.ai community*
