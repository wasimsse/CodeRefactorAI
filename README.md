# CodeRefactorAI

A powerful code analysis and refactoring tool built with Streamlit that helps developers improve code quality, maintainability, and complexity.

## Features

- **Code Analysis**: Analyze code files to identify complexity, maintainability issues, and code smells
- **Refactoring Suggestions**: Get AI-powered suggestions for improving your code
- **Metrics Visualization**: View detailed metrics about your codebase
- **Project-wide Analysis**: Analyze entire projects to get comprehensive insights
- **Binary File Handling**: Properly handles binary files during analysis

## Recent Improvements

### Binary File Handling
- Added detection of binary files based on file extensions and MIME types
- Implemented skipping of binary files during analysis to prevent errors
- Added proper error handling for unsupported encodings

### Code Analysis Enhancements
- Improved AST parsing for better code metrics
- Enhanced complexity and maintainability scoring algorithms
- Added detection of code smells and refactoring opportunities
- Implemented detailed metrics for classes, methods, functions, and imports

### UI Improvements
- Fixed indentation issues throughout the codebase
- Improved error handling and user feedback
- Enhanced visualization of analysis results

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/CodeRefactorAI.git
cd CodeRefactorAI
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Upload code files or select a project directory
2. View analysis results in the dashboard
3. Explore refactoring suggestions
4. Apply suggested improvements to your code

## Project Structure

```
CodeRefactorAI/
├── app.py                 # Main Streamlit application
├── code_analyzer.py       # Code analysis logic
├── file_manager.py        # File handling utilities
├── project_analyzer.py    # Project-level analysis
├── visualization_manager.py # Data visualization components
├── dataset_analyzer.py    # Dataset analysis utilities
├── config.py             # Configuration settings
├── requirements.txt      # Project dependencies
└── README.md            # Project documentation
```

## Requirements 📋

- Python 3.8+
- Streamlit
- Plotly
- PyArrow
- Python-Magic
- GitPython
- Additional dependencies listed in requirements.txt

## Features in Detail 🔍

### Code Analysis
- Cyclomatic complexity measurement
- Maintainability index calculation
- Code smell detection
- Documentation coverage analysis

### Visualization
- Interactive metrics dashboard
- Code composition charts
- Quality score visualizations
- Issue tracking and categorization

### Project Management
- Multi-file analysis support
- Directory structure visualization
- Aggregate metrics calculation
- Trend analysis

## Contributing 🤝

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments 🙏

- Built with [Streamlit](https://streamlit.io/)
- Powered by various open-source Python libraries
- Inspired by the need for better code quality tools 