# CodeRefactorAI

An AI-powered code analysis and refactoring tool built with Streamlit that helps developers improve code quality, maintainability, and performance.

## Features

- 📊 **Code Quality Analysis**: Comprehensive analysis of code metrics including maintainability, complexity, and code smells
- 📈 **Interactive Visualizations**: Beautiful charts and graphs to visualize code metrics
- 🔍 **Multi-Language Support**: Supports Python, Java, JavaScript, and more
- 🤖 **AI-Powered Refactoring**: Smart suggestions for code improvements
- 📁 **Project-Wide Analysis**: Analyze entire projects or single files
- 🔄 **GitHub Integration**: Direct analysis from GitHub repositories

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

1. **Upload Code**: Choose from three options:
   - Single file upload
   - Project archive (ZIP)
   - GitHub repository URL

2. **Analyze**: View comprehensive metrics including:
   - Maintainability Index
   - Cyclomatic Complexity
   - Cognitive Complexity
   - Code Coverage
   - Size Metrics
   - Code Quality Issues

3. **Visualize**: Explore interactive charts:
   - Quality Metrics Radar
   - Code Size Analysis
   - Code Composition
   - Issues Overview

4. **Refactor**: Get AI-powered suggestions for code improvements

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

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