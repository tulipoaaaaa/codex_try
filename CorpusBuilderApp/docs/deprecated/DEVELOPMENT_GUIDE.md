# File: docs/DEVELOPMENT_GUIDE.md

# CryptoFinance Corpus Builder - Development Guide

## Project Structure


## Development Workflow

CorpusBuilderApp/
├── app/ # Main application code
│ ├── main.py # Application entry point
│ ├── ui/ # User interface components
│ │ ├── tabs/ # Main application tabs
│ │ ├── widgets/ # Reusable UI widgets
│ │ └── dialogs/ # Dialog windows
│ └── resources/ # Application resources
├── shared_tools/ # Shared functionality
│ ├── collectors/ # Data collectors
│ ├── processors/ # Document processors
│ ├── ui_wrappers/ # UI wrapper classes
│ └── config/ # Configuration management
├── tests/ # Test suite
├── docs/ # Documentation
└── requirements.txt # Dependencies

text


### Setting Up Development Environment

1. **Virtual Environment Setup**
Activate the project virtual environment
G:\venv\ai_trading_dev_1\Scripts\activate
Install dependencies
pip install -r requirements.txt

2. **IDE Configuration**
- Configure your IDE to use the virtual environment
- Set up PyQt6 paths for code completion
- Enable code formatting with Black

### Adding New Processors

To add a new processor to the system:

1. **Create the Processor Class**
shared_tools/processors/my_processor.py
class MyProcessor:
def init(self, project_config):
self.config = project_config

   def process(self, input_data, **kwargs):
       # Implement processing logic
       return results


2. **Create the UI Wrapper**
shared_tools/ui_wrappers/processors/my_processor_wrapper.py
from shared_tools.ui_wrappers.base_wrapper import BaseWrapper, ProcessorWrapperMixin

class MyProcessorWrapper(BaseWrapper, ProcessorWrapperMixin):
def init(self, project_config):
super().init(project_config)
self.processor = MyProcessor(project_config)


3. **Add to Factory Function**
Update the `create_processor_wrapper` function in `wrapper_factory.py`.

4. **Write Tests**
Create unit tests in `tests/unit/test_my_processor.py`.

### Adding New UI Components

1. **Widget Development**
- Inherit from appropriate PyQt6 base class
- Implement proper signal/slot connections
- Follow the existing naming conventions

2. **Integration**
- Add to appropriate tab or dialog
- Connect signals to application logic
- Update main window if necessary

### Testing Guidelines

1. **Unit Tests**
- Test individual components in isolation
- Mock external dependencies
- Focus on business logic

2. **Integration Tests**
- Test component interactions
- Use temporary directories for file operations
- Test actual data processing workflows

3. **UI Tests**
- Use pytest-qt for PyQt6 testing
- Test user interactions
- Verify signal emissions

### Code Quality Standards

1. **Code Formatting**
Format code with Black
black app/ shared_tools/ tests/

Check with flake8
flake8 app/ shared_tools/ tests/


2. **Type Hints**
- Use type hints for function parameters and return values
- Import from `typing` module for complex types

3. **Documentation**
- Write clear docstrings for all public methods
- Include usage examples where appropriate
- Update documentation when adding features

### Debugging Tips

1. **PyQt6 Debugging**
- Use `QApplication.processEvents()` for responsive UI during long operations
- Enable Qt debugging with environment variables
- Use `QTimer.singleShot()` for delayed operations

2. **Logging**
- Use the project's logging configuration
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Include context information in log messages

### Performance Considerations

1. **Threading**
- Use QThread for long-running operations
- Never access UI elements from worker threads
- Use signals to communicate between threads

2. **Memory Management**
- Properly delete large objects when done
- Use context managers for file operations
- Monitor memory usage during development

## Contributing

1. **Branch Naming**
- `feature/description` for new features
- `bugfix/description` for bug fixes
- `refactor/description` for refactoring

2. **Commit Messages**
- Use clear, descriptive commit messages
- Include ticket numbers if applicable
- Keep commits focused and atomic

3. **Pull Requests**
- Include tests for new functionality
- Update documentation as needed
- Ensure all tests pass before submitting

