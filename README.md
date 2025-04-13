# CodeRefactorAI

A Streamlit-based application for intelligent code refactoring using AI. This tool helps developers improve their code quality through automated refactoring suggestions.

## Features

- Interactive code editor with syntax highlighting
- Multiple refactoring options:
  - Improve readability
  - Reduce complexity
  - Enhance maintainability
  - Optimize performance
- File management:
  - Single file upload
  - ZIP archive support
  - GitHub repository import
- Code analysis and metrics
- Refactoring history tracking
- Backup creation before refactoring

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/CodeRefactorAI.git
cd CodeRefactorAI
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Upload your code files using one of the available methods:
   - Single file upload
   - ZIP archive
   - GitHub repository URL

4. Select a file to refactor and choose your refactoring options

5. Generate and apply refactoring suggestions

## Project Structure

```
CodeRefactorAI/
├── app.py                 # Main Streamlit application
├── refactoring_tab.py     # Refactoring interface
├── refactoring_engine.py  # Core refactoring logic
├── code_analyzer.py       # Code analysis tools
├── file_manager.py        # File handling utilities
└── requirements.txt       # Project dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Project Structure

```
RefactoringAI/
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