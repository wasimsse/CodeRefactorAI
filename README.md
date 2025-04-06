# RefactoringAI

A powerful AI-powered code refactoring and analysis tool that helps developers improve code quality, detect code smells, and suggest refactoring opportunities.

## Features

### Code Analysis
- Basic code metrics (lines of code, complexity, etc.)
- Advanced complexity analysis
  - Cyclomatic complexity
  - Cognitive complexity
  - Halstead metrics
- Code smell detection
  - Bloaters
  - Object-oriented abusers
  - Change preventers
  - Dispensables
  - Couplers
- Technical debt estimation
- Refactoring suggestions

### Advanced Analysis
- Detailed complexity metrics visualization
- Code smell categorization and severity assessment
- Impact-based refactoring opportunities
- Technical debt cost estimation
- Project-wide analysis capabilities

### Supported Languages
- Python
- Java
- C++
- C#
- JavaScript/TypeScript
- Go
- Ruby
- Rust

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/refactoringai.git
cd refactoringai
```

2. Create a virtual environment:
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

2. Access the web interface at `http://localhost:8501`

3. Upload your code files or connect to a GitHub repository

4. Use the various tabs to:
   - Upload and manage files
   - View basic code analysis
   - Access advanced analysis features
   - Get refactoring suggestions

## Advanced Analysis Features

### Complexity Metrics
- View detailed complexity metrics for each file
- Compare different complexity measures
- Identify highly complex code sections

### Code Smells
- Categorized code smell detection
- Severity assessment
- Detailed descriptions and suggestions
- Visual representation of smell distribution

### Refactoring Opportunities
- Impact-based refactoring suggestions
- Prioritized recommendations
- Detailed refactoring steps
- Cost-benefit analysis

### Technical Debt
- Hour-based technical debt estimation
- Cost estimation
- Distribution analysis
- Project-wide debt assessment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

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