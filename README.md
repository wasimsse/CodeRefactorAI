# RefactoringAI 🔄

A powerful AI-powered code analysis and refactoring tool built with Streamlit.

## Features 🌟

- **Code Quality Analysis**: Comprehensive analysis of code complexity, maintainability, and best practices
- **Multi-Format Support**: Analyze single files, project archives, or GitHub repositories
- **Interactive Visualizations**: Visual representation of code metrics and quality indicators
- **Smart Recommendations**: AI-powered suggestions for code improvements
- **Project-Level Insights**: Aggregate analysis of entire codebases

## Installation 🛠️

1. Clone the repository:
```bash
git clone https://github.com/yourusername/RefactoringAI.git
cd RefactoringAI
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

## Usage 🚀

1. Start the application:
```bash
streamlit run app.py
```

2. Open your browser and navigate to:
- Local: http://localhost:8501
- Network: http://192.168.0.19:8501

3. Choose your analysis method:
- Upload a single Python file
- Upload a project archive (ZIP)
- Analyze a GitHub repository

## Project Structure 📁

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