import streamlit as st

# Set page config at the very beginning
st.set_page_config(
    page_title="RefactoringAI",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

import asyncio
from typing import Dict, Optional
import os
from pathlib import Path
import time
import git

from config import Config
from logger import Logger
from file_manager import FileManager
from code_analyzer import CodeAnalyzer
from ai_models import AIModelManager
from ui_components import UIComponents
from visualization import VisualizationManager

class RefactoringAI:
    def __init__(self):
        """Initialize the RefactoringAI application."""
        self.config = Config()
        self.logger = Logger(self.config)
        self.file_manager = FileManager(self.config)
        self.code_analyzer = CodeAnalyzer(self.config)
        self.ai_manager = AIModelManager()
        self.ui = UIComponents()
        self.visualization = VisualizationManager()
        
        # Initialize session state
        if 'uploaded_files' not in st.session_state:
            st.session_state.uploaded_files = []
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = {}
        if 'selected_file' not in st.session_state:
            st.session_state.selected_file = None
        if 'refactoring_history' not in st.session_state:
            st.session_state.refactoring_history = []

    def run(self):
        """Run the Streamlit application."""
        # Custom CSS for better styling
        st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stButton>button {
            width: 100%;
            margin-top: 1rem;
        }
        .upload-section {
            padding: 2rem;
            border-radius: 0.5rem;
            background-color: #f8f9fa;
            margin-bottom: 2rem;
        }
        .metrics-card {
            padding: 1.5rem;
            border-radius: 0.5rem;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        h1, h2, h3 {
            color: #1f77b4;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Application header with logo and title
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image("https://raw.githubusercontent.com/your-repo/assets/main/logo.png", width=100)  # Replace with your logo
        with col2:
            st.title("RefactoringAI - Code Analysis & Refactoring")
            st.markdown("*Intelligent code analysis and refactoring assistant powered by AI*")
        
        # Create tabs with icons
        tab1, tab2, tab3 = st.tabs([
            "📤 Upload & Analyze",
            "📁 File Explorer",
            "🔄 Refactor with AI"
        ])
        
        with tab1:
            self._handle_upload_tab()
        
        with tab2:
            self._handle_explorer_tab()
            
        with tab3:
            self._handle_refactoring_tab()

    def _handle_upload_tab(self):
        """Handle file upload and analysis."""
        st.header("Upload Your Code")
        
        # Upload method selection
        upload_method = st.radio(
            "Choose upload method:",
            ["Single File", "ZIP Archive", "GitHub Repository"],
            horizontal=True
        )
        
        st.markdown("---")
        
        if upload_method == "Single File":
            self._handle_single_file_upload()
        elif upload_method == "ZIP Archive":
            self._handle_zip_upload()
        else:
            self._handle_github_upload()

    def _handle_single_file_upload(self):
        """Handle single file upload."""
        st.subheader("Upload Single File")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['py', 'java', 'cpp', 'js', 'jsx', 'ts', 'tsx', 'cs'],
            help="Upload a single code file for analysis"
        )
        
        if uploaded_file:
            try:
                with st.spinner("Processing file..."):
                    file_path = self.file_manager._handle_single_file_upload(uploaded_file)
                    st.session_state.uploaded_files = [file_path]
                    
                    # Analyze file
                    results = self.code_analyzer.analyze_file(file_path)
                    st.session_state.analysis_results[file_path] = results
                    
                    # Display results
                    self._display_analysis_results(results)
                    
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

    def _handle_zip_upload(self):
        """Handle ZIP archive upload."""
        st.subheader("Upload ZIP Archive")
        
        uploaded_file = st.file_uploader(
            "Choose a ZIP file",
            type=['zip'],
            help="Upload a ZIP archive containing your code files"
        )
        
        if uploaded_file:
            try:
                with st.spinner("Processing ZIP archive..."):
                    files = self.file_manager._handle_zip_upload(uploaded_file)
                    st.session_state.uploaded_files = files
                    
                    # Analyze files
                    progress_bar = st.progress(0)
                    for i, file in enumerate(files):
                        results = self.code_analyzer.analyze_file(file)
                        st.session_state.analysis_results[file] = results
                        progress = (i + 1) / len(files)
                        progress_bar.progress(progress)
                    
                    # Display combined results
                    combined_results = self._combine_analysis_results(
                        st.session_state.analysis_results
                    )
                    self.visualization.display_analysis_dashboard(combined_results)
                    
            except Exception as e:
                st.error(f"Error processing ZIP file: {str(e)}")

    def _handle_github_upload(self):
        """Handle GitHub repository upload."""
        st.subheader("Import from GitHub")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            repo_url = st.text_input(
                "GitHub Repository URL",
                placeholder="https://github.com/username/repository"
            )
        with col2:
            branch = st.text_input("Branch (optional)", value="main")
        
        if st.button("Import Repository"):
            if repo_url:
                try:
                    with st.spinner("Cloning repository..."):
                        # Clone repository
                        repo_name = repo_url.split('/')[-1].replace('.git', '')
                        repo_path = Path(self.config.UPLOAD_DIR) / repo_name
                        
                        if repo_path.exists():
                            st.warning("Repository already exists. Updating...")
                            repo = git.Repo(repo_path)
                            repo.remotes.origin.pull()
                        else:
                            git.Repo.clone_from(repo_url, repo_path, branch=branch)
                        
                        # Get all code files
                        files = []
                        for ext in ['.py', '.java', '.cpp', '.js', '.jsx', '.ts', '.tsx', '.cs']:
                            files.extend(list(repo_path.rglob(f"*{ext}")))
                        
                        st.session_state.uploaded_files = [str(f) for f in files]
                        
                        # Analyze files
                        progress_bar = st.progress(0)
                        for i, file in enumerate(files):
                            results = self.code_analyzer.analyze_file(str(file))
                            st.session_state.analysis_results[str(file)] = results
                            progress = (i + 1) / len(files)
                            progress_bar.progress(progress)
                        
                        # Display results
                        combined_results = self._combine_analysis_results(
                            st.session_state.analysis_results
                        )
                        self.visualization.display_analysis_dashboard(combined_results)
                        
                except Exception as e:
                    st.error(f"Error importing repository: {str(e)}")
            else:
                st.warning("Please enter a GitHub repository URL")

    def _handle_explorer_tab(self):
        """Handle file exploration and content display."""
        st.header("File Explorer")
        
        if not st.session_state.uploaded_files:
            st.info("Please upload files in the Upload & Analyze tab first.")
            return
            
        # File selection with tree view
        st.sidebar.subheader("Files")
        selected_file = st.sidebar.selectbox(
            "Select a file to view",
            st.session_state.uploaded_files,
            format_func=lambda x: Path(x).name
        )
        
        if selected_file:
            st.session_state.selected_file = selected_file
            
            try:
                content = self.file_manager.read_file(selected_file)
                
                # Display file info
                file_info_col1, file_info_col2 = st.columns(2)
                with file_info_col1:
                    st.markdown(f"**File:** `{Path(selected_file).name}`")
                    st.markdown(f"**Type:** `{Path(selected_file).suffix[1:].upper()}`")
                
                with file_info_col2:
                    st.markdown(f"**Size:** `{os.path.getsize(selected_file) / 1024:.1f} KB`")
                    st.markdown(f"**Last Modified:** `{time.ctime(os.path.getmtime(selected_file))}`")
                
                # Display code and analysis
                code_col, analysis_col = st.columns([2, 1])
                
                with code_col:
                    st.code(content, language=self._get_language(selected_file))
                    
                with analysis_col:
                    if selected_file in st.session_state.analysis_results:
                        results = st.session_state.analysis_results[selected_file]
                        st.subheader("File Analysis")
                        
                        # Display metrics using gauge charts
                        metrics = {
                            'Complexity': results.get('complexity', 0),
                            'Maintainability': results.get('maintainability', 0),
                            'Code Quality': 100 - results.get('code_smells', 0),
                            'Performance': results.get('performance', 0)
                        }
                        
                        for metric, value in metrics.items():
                            st.plotly_chart(
                                self.visualization.create_metrics_gauge(value, metric),
                                use_container_width=True
                            )
                        
                        # Display code issues if any
                        if 'issues' in results and results['issues']:
                            st.subheader("Issues Found")
                            for issue in results['issues']:
                                st.warning(issue)
                        
            except Exception as e:
                st.error(f"Error displaying file: {str(e)}")

    def _handle_refactoring_tab(self):
        """Handle code refactoring with AI models."""
        st.header("AI-Powered Refactoring")
        
        if not st.session_state.selected_file:
            st.info("Please select a file in the File Explorer tab first.")
            return
            
        # Refactoring options
        st.subheader("Refactoring Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Code Improvements")
            options = {
                'improve_structure': st.checkbox("Improve Code Structure", value=True),
                'add_documentation': st.checkbox("Add Documentation", value=True),
                'error_handling': st.checkbox("Improve Error Handling", value=True),
                'solid_principles': st.checkbox("Apply SOLID Principles", value=True)
            }
            
        with col2:
            st.markdown("#### Model Settings")
            model = st.selectbox(
                "AI Model",
                ["GPT-4", "GPT-3.5", "Claude", "PaLM"],
                index=0
            )
            temperature = st.slider(
                "Creativity Level",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Higher values make the output more creative but less focused"
            )
        
        if st.button("Start Refactoring", type="primary"):
            try:
                with st.spinner("Analyzing and refactoring code..."):
                    # Simulate refactoring process
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.1)
                        progress_bar.progress(i + 1)
                    
                    # Add to history
                    history_entry = {
                        'timestamp': time.time(),
                        'file': st.session_state.selected_file,
                        'model': model,
                        'options': options
                    }
                    st.session_state.refactoring_history.append(history_entry)
                    
                    st.success("Refactoring completed successfully!")
                    
                    # Display refactoring history
                    if st.session_state.refactoring_history:
                        st.subheader("Refactoring History")
                        for entry in reversed(st.session_state.refactoring_history[-5:]):
                            with st.expander(
                                f"Refactoring at {time.ctime(entry['timestamp'])}",
                                expanded=False
                            ):
                                st.markdown(f"**File:** `{Path(entry['file']).name}`")
                                st.markdown(f"**Model:** {entry['model']}")
                                st.markdown("**Options:**")
                                for opt, val in entry['options'].items():
                                    if val:
                                        st.markdown(f"- {opt.replace('_', ' ').title()}")
                    
            except Exception as e:
                st.error(f"Error during refactoring: {str(e)}")

    def _combine_analysis_results(self, results: dict) -> dict:
        """Combine analysis results from multiple files."""
        combined = {
            'complexity': 0,
            'maintainability': 0,
            'code_smells': 0,
            'performance': 0,
            'test_coverage': 0,
            'issues': [],
            'history': []
        }
        
        if not results:
            return combined
            
        # Calculate averages
        num_files = len(results)
        for file_results in results.values():
            combined['complexity'] += file_results.get('complexity', 0)
            combined['maintainability'] += file_results.get('maintainability', 0)
            combined['code_smells'] += file_results.get('code_smells', 0)
            combined['performance'] += file_results.get('performance', 0)
            combined['test_coverage'] += file_results.get('test_coverage', 0)
            
            if 'issues' in file_results:
                combined['issues'].extend(file_results['issues'])
                
            if 'history' in file_results:
                combined['history'].extend(file_results['history'])
        
        # Calculate averages
        for key in ['complexity', 'maintainability', 'code_smells', 'performance', 'test_coverage']:
            combined[key] /= num_files
            
        return combined

    def _get_language(self, filename: str) -> str:
        """Get programming language based on file extension."""
        ext = os.path.splitext(filename)[1].lower()
        language_map = {
            '.py': 'python',
            '.java': 'java',
            '.cpp': 'cpp',
            '.hpp': 'cpp',
            '.h': 'cpp',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.cs': 'csharp'
        }
        return language_map.get(ext, 'text')

    def _display_analysis_results(self, results: dict):
        """Display analysis results in a professional format."""
        st.subheader("Analysis Results")
        
        # Create metrics cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            with st.container():
                st.markdown('<div class="metrics-card">', unsafe_allow_html=True)
                st.metric("Complexity Score", f"{results.get('complexity', 0):.1f}")
                st.markdown("</div>", unsafe_allow_html=True)
                
        with col2:
            with st.container():
                st.markdown('<div class="metrics-card">', unsafe_allow_html=True)
                st.metric("Maintainability", f"{results.get('maintainability', 0):.1f}")
                st.markdown("</div>", unsafe_allow_html=True)
                
        with col3:
            with st.container():
                st.markdown('<div class="metrics-card">', unsafe_allow_html=True)
                st.metric("Code Quality", f"{100 - results.get('code_smells', 0):.1f}")
                st.markdown("</div>", unsafe_allow_html=True)
                
        with col4:
            with st.container():
                st.markdown('<div class="metrics-card">', unsafe_allow_html=True)
                st.metric("Performance", f"{results.get('performance', 0):.1f}")
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Display detailed metrics
        st.markdown("### Detailed Metrics")
        col1, col2 = st.columns(2)
        
        with col1:
            if 'functions' in results:
                st.info(f"Number of Functions: {results['functions']}")
            if 'classes' in results:
                st.info(f"Number of Classes: {results['classes']}")
            if 'imports' in results:
                st.info(f"Number of Imports: {len(results['imports'])}")
                
        with col2:
            if 'total_lines' in results:
                st.info(f"Total Lines: {results['total_lines']}")
            if 'non_empty_lines' in results:
                st.info(f"Non-empty Lines: {results['non_empty_lines']}")
            if 'average_line_length' in results:
                st.info(f"Average Line Length: {results['average_line_length']:.1f}")

def main():
    """Main entry point."""
    app = RefactoringAI()
    app.run()

if __name__ == "__main__":
    main() 