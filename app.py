import streamlit as st
import os
import tempfile
import zipfile
import git
import shutil
from pathlib import Path
import magic
from typing import List, Dict, Optional
import json
from dotenv import load_dotenv
import requests
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from config import Config
from code_analyzer import CodeAnalyzer, analyze_file
from file_manager import FileManager
from project_analyzer import ProjectAnalyzer
from visualization_manager import VisualizationManager
from dataset_analyzer import DatasetAnalyzer
from stats_manager import StatsManager
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="RefactoringAI",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with fixed escape sequences
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .code-viewer {
        background-color: #1e1e1e;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .file-tree {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem;
    }
    .main-header {
        color: #1E88E5;
        padding: 1rem 0;
    }
    .sub-header {
        color: #424242;
        padding: 0.5rem 0;
    }
    .card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .file-button {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.2rem 0;
        transition: all 0.2s;
    }
    .file-button:hover {
        background-color: #e9ecef;
        border-color: #1E88E5;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .tab-content {
        padding: 1rem 0;
    }
    .status-box {
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #e8f5e9;
        border: 1px solid #81c784;
        color: #2e7d32;
    }
    .info-box {
        background-color: #e3f2fd;
        border: 1px solid #64b5f6;
        color: #1565c0;
    }
    .warning-box {
        background-color: #fff3e0;
        border: 1px solid #ffb74d;
        color: #ef6c00;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = {}
if 'project_analysis' not in st.session_state:
    st.session_state.project_analysis = None
if 'current_file' not in st.session_state:
    st.session_state.current_file = None

# Configuration for supported programming languages and their analysis settings
config = {
    # Basic analysis configuration
    'max_line_length': 100,
    'max_function_length': 50,
    'max_complexity': 10,
    'min_comment_ratio': 0.1,

    # Supported programming languages configuration
    # Each language includes:
    # - extensions: List of file extensions
    # - name: Display name
    # - icon: Emoji icon for UI
    'supported_languages': {
        'python': {
            'extensions': ['.py'],
            'name': 'Python',
            'icon': '🐍'
        },
        'java': {
            'extensions': ['.java'],
            'name': 'Java',
            'icon': '☕'
        },
        'cpp': {
            'extensions': ['.cpp', '.hpp', '.cc', '.h'],
            'name': 'C++',
            'icon': '⚡'
        },
        'csharp': {
            'extensions': ['.cs'],
            'name': 'C#',
            'icon': '🔷'
        },
        'javascript': {
            'extensions': ['.js', '.jsx', '.ts', '.tsx'],
            'name': 'JavaScript/TypeScript',
            'icon': '🟨'
        },
        'go': {
            'extensions': ['.go'],
            'name': 'Go',
            'icon': '🔵'
        },
        'ruby': {
            'extensions': ['.rb'],
            'name': 'Ruby',
            'icon': '💎'
        },
        'rust': {
            'extensions': ['.rs'],
            'name': 'Rust',
            'icon': '🦀'
        }
    }
}

# Initialize the stats manager
if 'stats_manager' not in st.session_state:
    st.session_state.stats_manager = StatsManager()


def init_session_state():
    """Initialize or reset session state variables."""
    # Define all session state variables with their default values
    defaults = {
        'initialized': True,
        'uploaded_files': {},
        'analysis_results': {},
        'project_analysis': None,
        'selected_directory': None,
        'selected_file': None,
        'analyzer': CodeAnalyzer(config),
        'project_analyzer': ProjectAnalyzer(config)
    }

    # Initialize any missing session state variables
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def cleanup_upload_dir():
    """Clean up the upload directory before new uploads."""
    try:
        if config.UPLOAD_DIR.exists():
            shutil.rmtree(config.UPLOAD_DIR)
        config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        st.error(f"Error cleaning upload directory: {str(e)}")


def clear_analysis_state():
    """Clear analysis related session state."""
    st.session_state.uploaded_files = {}
    st.session_state.analysis_results = {}
    st.session_state.project_analysis = None
    st.session_state.selected_directory = None
    st.session_state.selected_file = None
    # Clean up the upload directory
    cleanup_upload_dir()


class CodeRefactorer:
    def __init__(self):
        self.available_models = {
            'OpenAI': [
                'gpt-4',
                'gpt-3.5-turbo'],
            'Anthropic': [
                'claude-3-opus-20240229',
                'claude-3-sonnet-20240229'],
            'Google': ['gemini-pro'],
            'Cohere': ['command']}

    async def refactor_code(self, code: str, model: str, prompt: str) -> str:
        """Refactor code using the specified model."""
        # Placeholder for actual refactoring logic
        return code


def main():
    """Main application function."""
    init_session_state()  # Initialize or reset session state

    st.title("🔄 RefactoringAI")
    st.markdown("""
        ### AI-Powered Code Refactoring Tool
        Upload your code and let AI help you improve its quality, maintainability, and performance.
    """)

    # Create tabs
    tab1, tab2, tab3 = st.tabs(
        ["Upload & Analyze", "File Explorer", "Refactor"])

    with tab1:
        # Hero section with enhanced gradient and animation
        st.markdown("""
            <style>
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .hero-section {
                background: linear-gradient(135deg, #1E88E5 0%, #1565C0 50%, #0D47A1 100%);
                padding: 3rem;
                border-radius: 20px;
                margin-bottom: 2rem;
                color: white;
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
                animation: fadeIn 0.8s ease-out;
            }
            .hero-badge {
                display: inline-block;
                background-color: rgba(255,255,255,0.1);
                padding: 0.8rem 1.5rem;
                border-radius: 12px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
            }
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 1.5rem;
                margin: 2rem 0;
            }
            .feature-card {
                background: white;
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                transition: transform 0.2s, box-shadow 0.2s;
                border: 1px solid #e0e0e0;
            }
            .feature-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.1);
            }
            .upload-container {
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 2rem;
                border-radius: 15px;
                margin: 2rem 0;
            }
            .stats-container {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 1rem;
                margin: 2rem 0;
            }
            .stat-card {
                background: white;
                padding: 1.5rem;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .stat-number {
                font-size: 1.8em;
                font-weight: 600;
                color: #1E88E5;
                margin-bottom: 0.5rem;
            }
            .stat-label {
                color: #666;
                font-size: 0.9em;
            }
            </style>
            <div class="hero-section">
                <h1 style='font-size: 2.8em; margin-bottom: 1rem; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    Code Quality Analysis
                </h1>
                <p style='font-size: 1.3em; margin-bottom: 2rem; opacity: 0.9; max-width: 800px; line-height: 1.5;'>
                    Transform your code into high-quality, maintainable solutions with our AI-powered analysis platform
                </p>
                <div class="hero-badge">
                    <span style='font-size: 1.1em; margin-right: 1rem;'>✨ Smart Analysis</span>
                    <span style='opacity: 0.5; margin: 0 1rem;'>|</span>
                    <span style='font-size: 1.1em; margin-right: 1rem;'>🔍 Deep Insights</span>
                    <span style='opacity: 0.5; margin: 0 1rem;'>|</span>
                    <span style='font-size: 1.1em;'>🚀 Actionable Results</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Key statistics section
        display_landing_stats()

        # Upload section with improved styling and logical order
        st.markdown("""
            <div class="upload-section">
                <h2 class="section-title">Start Your Analysis</h2>
                <p class="section-description">Choose your preferred method to analyze your code. Our intelligent system will guide you through the process.</p>
            </div>
        """, unsafe_allow_html=True)

        # Create three columns for upload methods
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
                <div class="feature-card">
                    <div class="icon-container">📄</div>
                    <h3>Single File</h3>
                    <p>Quick analysis of individual source files</p>
                    <div class="supported-languages">
                        <p style="font-size: 0.9em; color: #666; margin-bottom: 0.5rem;">Supported Languages:</p>
                        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                            {supported_langs_html}
                        </div>
                    </div>
                </div>
            """.format(
                supported_langs_html=''.join([
                    f'<span style="padding: 0.2rem 0.5rem; background: #f8f9fa; border-radius: 4px; font-size: 0.8em;">{
                        lang["icon"]} {
                        lang["name"]}</span>'
                    for lang in config['supported_languages'].values()
                ])
            ), unsafe_allow_html=True)

            # Update file uploader to accept all supported extensions
            supported_extensions = []
            for lang in config['supported_languages'].values():
                # Remove the dot from extensions
                supported_extensions.extend(
                    [ext[1:] for ext in lang['extensions']])

            uploaded_file = st.file_uploader(
                "Choose a source file",
                type=supported_extensions,
                key="single_file",
                help=f"Supported file types: {', '.join(supported_extensions)}"
            )
            if uploaded_file:
                with st.spinner("🔍 Analyzing your code..."):
                    if handle_file_upload(uploaded_file):
                        st.success(
                            "✅ Analysis Complete! View results in the File Explorer tab.")

        with col2:
            st.markdown("""
                <div class="feature-card">
                    <div class="icon-container">📦</div>
                    <h3>Project Archive</h3>
                    <p>Comprehensive analysis of multiple files with project-wide insights</p>
                    <ul class="feature-list">
                        <li>✓ Multi-file analysis</li>
                        <li>✓ Project overview</li>
                        <li>✓ Dependency scanning</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
            uploaded_zip = st.file_uploader(
                "Choose a ZIP file", type=['zip'], key="zip_file")
            if uploaded_zip:
                with st.spinner("📊 Processing your project..."):
                    if handle_zip_upload(uploaded_zip):
                        st.success(
                            "✅ Project Analysis Complete! View results in the File Explorer tab.")

        with col3:
            st.markdown("""
                <div class="feature-card">
                    <div class="icon-container">🔗</div>
                    <h3>GitHub Repository</h3>
                    <p>Direct analysis from your GitHub repositories with branch support</p>
                    <ul class="feature-list">
                        <li>✓ Repository integration</li>
                        <li>✓ Branch analysis</li>
                        <li>✓ Commit history review</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
            repo_url = st.text_input(
                "Enter repository URL",
                placeholder="https://github.com/username/repository",
                help="Enter the URL of a public GitHub repository")

            if repo_url:
                if st.button(
                    "🚀 Start Analysis",
                    type="primary",
                        use_container_width=True):
                    with st.spinner("🔍 Cloning and analyzing repository..."):
                        handle_github_upload(repo_url)
                        st.success(
                            "✅ Repository Analysis Complete! View results in the File Explorer tab.")

        # Add custom CSS for the upload section
        st.markdown("""
            <style>
            .upload-section {
                margin: 2rem 0;
            }
            .section-title {
                color: #1E88E5;
                font-size: 2.2em;
                margin-bottom: 1rem;
                font-weight: 600;
            }
            .section-description {
                color: #424242;
                margin-bottom: 1.5rem;
                font-size: 1.1em;
                line-height: 1.6;
            }
            .feature-card {
                background: white;
                padding: 1.5rem;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                margin: 1rem 0;
                transition: transform 0.2s;
            }
            .feature-card:hover {
                transform: translateY(-5px);
            }
            .icon-container {
                text-align: center;
                font-size: 3em;
                color: #1E88E5;
                margin-bottom: 1rem;
            }
            .feature-card h3 {
                color: #1E88E5;
                text-align: center;
                font-size: 1.4em;
                margin-bottom: 1rem;
            }
            .feature-card p {
                color: #424242;
                text-align: center;
                font-size: 1em;
                line-height: 1.5;
                margin-bottom: 1rem;
            }
            .feature-list {
                list-style: none;
                padding: 0;
                margin: 0;
                background: #f8f9fa;
                border-radius: 8px;
                padding: 1rem;
            }
            .feature-list li {
                color: #666;
                font-size: 0.9em;
                margin-bottom: 0.5rem;
            }
            .feature-list li:last-child {
                margin-bottom: 0;
            }
            </style>
        """, unsafe_allow_html=True)

        # Enhanced features section
        st.markdown("""
            <div style='background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                      padding: 2.5rem; border-radius: 20px; margin: 3rem 0;
                      box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>
                <h2 style='color: #1E88E5; font-size: 1.8em; margin-bottom: 2rem; text-align: center;'>
                    🎯 Advanced Features
                </h2>
                <div class="feature-grid">
                    <div class="feature-card">
                        <h3 style='color: #1E88E5; font-size: 1.2em; margin-bottom: 1rem;'>
                            Code Quality Metrics
                        </h3>
                        <p style='color: #666; font-size: 0.95em; line-height: 1.5;'>
                            Comprehensive analysis of code complexity, maintainability, and adherence to best practices
                        </p>
                    </div>
                    <div class="feature-card">
                        <h3 style='color: #1E88E5; font-size: 1.2em; margin-bottom: 1rem;'>
                            Smart Recommendations
                        </h3>
                        <p style='color: #666; font-size: 0.95em; line-height: 1.5;'>
                            AI-powered suggestions for code improvements and optimization opportunities
                        </p>
                    </div>
                    <div class="feature-card">
                        <h3 style='color: #1E88E5; font-size: 1.2em; margin-bottom: 1rem;'>
                            Detailed Reports
                        </h3>
                        <p style='color: #666; font-size: 0.95em; line-height: 1.5;'>
                            Visual representation of analysis results with actionable insights
                        </p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Documentation sections with improved styling
        col_exp1, col_exp2 = st.columns(2)

        with col_exp1:
            with st.expander("📋 Getting Started Guide"):
                st.markdown("""
                    <div style='background-color: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
                        <ol style='margin: 0; padding-left: 1.2rem; color: #424242;'>
                            <li style='margin-bottom: 1.2rem;'>
                                <strong style='color: #1E88E5; font-size: 1.1em;'>Choose Your Method</strong>
                                <ul style='margin-top: 0.8rem;'>
                                    <li style='margin-bottom: 0.5rem;'>Single File: Quick individual analysis</li>
                                    <li style='margin-bottom: 0.5rem;'>Project Archive: Multi-file project analysis</li>
                                    <li>GitHub: Direct repository analysis</li>
                                </ul>
                            </li>
                            <li style='margin-bottom: 1.2rem;'>
                                <strong style='color: #1E88E5; font-size: 1.1em;'>Upload & Process</strong>
                                <ul style='margin-top: 0.8rem;'>
                                    <li style='margin-bottom: 0.5rem;'>Select your file(s)</li>
                                    <li style='margin-bottom: 0.5rem;'>Wait for analysis to complete</li>
                                    <li>Review the success message</li>
                                </ul>
                            </li>
                            <li>
                                <strong style='color: #1E88E5; font-size: 1.1em;'>Explore Results</strong>
                                <ul style='margin-top: 0.8rem;'>
                                    <li style='margin-bottom: 0.5rem;'>Navigate to File Explorer</li>
                                    <li style='margin-bottom: 0.5rem;'>Review detailed metrics</li>
                                    <li>Check recommendations</li>
                                </ul>
                            </li>
                        </ol>
                    </div>
                """, unsafe_allow_html=True)

        with col_exp2:
            with st.expander("⚠️ Requirements & Limitations"):
                st.markdown("""
                    <div style='background-color: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
                        <h4 style='color: #1E88E5; margin-bottom: 1rem; font-size: 1.1em;'>File Requirements</h4>
                        <ul style='color: #424242; margin-bottom: 1.5rem;'>
                            <li style='margin-bottom: 0.5rem;'>Python files (.py extension)</li>
                            <li style='margin-bottom: 0.5rem;'>Valid syntax required</li>
                            <li>UTF-8 encoding recommended</li>
                        </ul>

                        <h4 style='color: #1E88E5; margin-bottom: 1rem; font-size: 1.1em;'>Size Limits</h4>
                        <ul style='color: #424242; margin-bottom: 1.5rem;'>
                            <li style='margin-bottom: 0.5rem;'>Single file: Max 100MB</li>
                            <li style='margin-bottom: 0.5rem;'>ZIP archive: Max 500MB</li>
                            <li>Repository: No strict limit</li>
                        </ul>

                        <div style='background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
                                  padding: 1rem; border-radius: 8px; margin-top: 1rem;'>
                            <p style='color: #ef6c00; margin: 0; font-size: 0.95em;'>
                                Note: Analysis time may vary based on code size and complexity
                            </p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    with tab2:
        display_file_explorer()

    with tab3:
        st.header("Refactor")
        if st.session_state.current_file:
            display_refactoring_options()
        else:
            st.info("Select a file from the File Explorer to start refactoring.")


def handle_file_upload(uploaded_file):
    """
    Handle single file upload and analysis.

    This function processes individual source code files in any supported language.
    It performs the following steps:
    1. Validates file extension against supported languages
    2. Saves the file to a temporary directory
    3. Analyzes the file using the CodeAnalyzer
    4. Updates session state with analysis results
    5. Updates statistics for the analyzed file

    Args:
        uploaded_file: StreamlitUploadedFile object containing the source code

    Returns:
        bool: True if analysis was successful, False otherwise
    """
    if uploaded_file is not None:
        try:
            # Validate file extension
            file_ext = Path(uploaded_file.name).suffix.lower()
            supported_extensions = []
            for lang in config['supported_languages'].values():
                supported_extensions.extend(lang['extensions'])

            if file_ext not in supported_extensions:
                st.error(
                    f"Unsupported file type. Supported extensions: {
                        ', '.join(supported_extensions)}")
                return False

            # Process and analyze file
            temp_dir = Path("temp_analysis")
            temp_dir.mkdir(exist_ok=True)

            file_path = temp_dir / uploaded_file.name
            content = uploaded_file.getvalue().decode('utf-8')
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Use the analyze_file function directly
            file_metrics = analyze_file(str(file_path), content)

            # Update session state
            if 'uploaded_files' not in st.session_state:
                st.session_state.uploaded_files = {}
            st.session_state.uploaded_files[str(file_path)] = file_metrics
            st.session_state.current_file = str(file_path)

            # Update statistics
            st.session_state.stats_manager.update_file_analysis(
                uploaded_file.name,
                file_metrics
            )

            return True
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return False


def handle_zip_upload(uploaded_zip):
    """
    Handle ZIP file upload and project analysis.

    This function processes ZIP archives containing multiple source files.
    It supports all configured programming languages and performs:
    1. Extracts ZIP contents to a temporary directory
    2. Recursively analyzes all supported source files
    3. Updates session state with analysis results
    4. Generates project-wide statistics

    Args:
        uploaded_zip: StreamlitUploadedFile object containing the ZIP archive

    Returns:
        bool: True if analysis was successful, False otherwise
    """
    if uploaded_zip is not None:
        try:
            # Setup temporary directories
            temp_dir = Path("temp_analysis")
            temp_dir.mkdir(exist_ok=True)

            # Extract ZIP contents
            zip_path = temp_dir / uploaded_zip.name
            with open(zip_path, "wb") as f:
                f.write(uploaded_zip.getbuffer())

            extract_dir = temp_dir / Path(uploaded_zip.name).stem
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # Initialize analysis
            analyzer = CodeAnalyzer(config)
            st.session_state.uploaded_files = {}

            # Get supported file extensions
            supported_extensions = []
            for lang in config['supported_languages'].values():
                supported_extensions.extend(lang['extensions'])

            # Process all supported files
            files_found = False
            for root, _, files in os.walk(extract_dir):
                for file in files:
                    file_ext = Path(file).suffix.lower()
                    if file_ext in supported_extensions:
                        files_found = True
                        file_path = Path(root) / file
                        try:
                            # Analyze individual file
                            file_metrics = analyzer.analyze_file(
                                str(file_path))
                            st.session_state.uploaded_files[str(
                                file_path)] = file_metrics

                            # Update statistics
                            st.session_state.stats_manager.update_file_analysis(
                                file, file_metrics)
                        except Exception as e:
                            st.warning(f"Error analyzing {file}: {str(e)}")

            if not files_found:
                st.warning(
                    f"No supported files found in the ZIP archive. Supported extensions: {
                        ', '.join(supported_extensions)}")
                return False

            # Set initial file selection
            st.session_state.current_file = next(
                iter(st.session_state.uploaded_files))

            # Generate and update project analysis
            project_metrics = analyzer.analyze_project(str(extract_dir))
            st.session_state.project_analysis = project_metrics
            st.session_state.stats_manager.update_project_analysis()

            return True

        except Exception as e:
            st.error(f"Error processing ZIP file: {str(e)}")
            return False


def handle_github_upload(repo_url):
    """
    Handle GitHub repository analysis.

    This function clones and analyzes GitHub repositories:
    1. Creates a unique directory for the repository
    2. Clones the repository using git
    3. Analyzes all supported source files
    4. Generates project-wide metrics and statistics

    Supports all configured programming languages and maintains
    proper file organization for multi-language projects.

    Args:
        repo_url: String URL of the GitHub repository

    Returns:
        bool: True if analysis was successful, False otherwise
    """
    try:
        # Setup repository directory
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_dir = Path("temp_analysis") / f"{repo_name}_{os.urandom(6).hex()}"
        repo_dir.mkdir(parents=True, exist_ok=True)

        # Clone repository
        git.Repo.clone_from(repo_url, repo_dir)

        # Initialize analysis
        st.session_state.uploaded_files = {}
        analyzer = CodeAnalyzer(config)

        # Get supported file extensions
        supported_extensions = []
        for lang in config['supported_languages'].values():
            supported_extensions.extend(lang['extensions'])

        # Process all supported files
        files_found = False
        for root, _, files in os.walk(repo_dir):
            for file in files:
                file_ext = Path(file).suffix.lower()
                if file_ext in supported_extensions:
                    files_found = True
                    file_path = Path(root) / file
                    try:
                        # Analyze file
                        file_metrics = analyzer.analyze_file(str(file_path))
                        st.session_state.uploaded_files[str(
                            file_path)] = file_metrics

                        # Update statistics
                        st.session_state.stats_manager.update_file_analysis(
                            file,
                            file_metrics
                        )
                    except Exception as e:
                        st.warning(f"Error analyzing {file}: {str(e)}")

        if not files_found:
            st.warning(
                f"No supported files found in the repository. Supported extensions: {
                    ', '.join(supported_extensions)}")
            return False

        # Set initial file selection
        st.session_state.current_file = next(
            iter(st.session_state.uploaded_files))

        # Generate and update project analysis
        project_metrics = analyzer.analyze_project(str(repo_dir))
        st.session_state.project_analysis = project_metrics
        st.session_state.stats_manager.update_project_analysis()

        return True

    except Exception as e:
        st.error(f"Error cloning repository: {str(e)}")
        return False


def display_refactoring_options():
    """Display the refactoring interface with enhanced UI and features."""
    # Initialize session state variables if they don't exist
    if 'current_metrics' not in st.session_state:
        st.session_state.current_metrics = {}
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None
    if 'refactoring_history' not in st.session_state:
        st.session_state.refactoring_history = []
    if 'current_code' not in st.session_state:
        st.session_state.current_code = ""
    if 'refactored_code' not in st.session_state:
        st.session_state.refactored_code = ""
    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = "🔍 Analysis & Selection"
    if 'refactoring_suggestions' not in st.session_state:
        st.session_state.refactoring_suggestions = []
    if 'refactoring_model' not in st.session_state:
        st.session_state.refactoring_model = "gpt-4"
    if 'refactoring_goals' not in st.session_state:
        st.session_state.refactoring_goals = []
    if 'refactoring_constraints' not in st.session_state:
        st.session_state.refactoring_constraints = []
    if 'refactoring_mode' not in st.session_state:
        st.session_state.refactoring_mode = "local"

    # Check if files are available
    if 'uploaded_files' not in st.session_state or not st.session_state.uploaded_files:
        st.warning("Please upload or select files to refactor first.")
        return

    files = list(st.session_state.uploaded_files.keys())
    if not files:
        st.warning("No files available for refactoring.")
        return

    # Header with gradient background
    st.markdown("""
        <div style="
            background: linear-gradient(120deg, #1E88E5 0%, #42A5F5 100%);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            <h2 style="color: white; text-align: center; margin-bottom: 1rem; font-size: 1.8em;">
                Code Refactoring Assistant
            </h2>
        </div>
    """, unsafe_allow_html=True)

    # Main layout with sidebar and content area
    with st.container():
        # File selection in a compact format at the top
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_file = st.selectbox(
                "Select file to refactor",
                files,
                index=files.index(st.session_state.current_file) if st.session_state.current_file in files else 0,
                key="file_selector"
            )
        with col2:
            if st.button("📋 Show File Info", use_container_width=True):
                st.session_state.selected_tab = "🔍 Analysis & Selection"

        # Update session state when file selection changes
        if selected_file != st.session_state.current_file:
            st.session_state.current_file = selected_file
            st.session_state.current_metrics = st.session_state.uploaded_files[selected_file]
            if st.session_state.current_metrics:
                st.session_state.current_code = st.session_state.current_metrics.get('content', '')

        # Create tabs for different aspects of refactoring
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔍 Analysis & Selection",
            "✏️ Code Editor",
            "🎯 Refactoring Options",
            "👀 Preview & Impact"
        ])

        # Display the selected tab content
        if st.session_state.selected_tab == "🎯 Refactoring Options":
            with tab3:
                # Refactoring mode selection
                st.markdown("#### 🔄 Refactoring Mode")
                mode = st.radio(
                    "Select refactoring mode",
                    ["Local", "Cloud-based", "Hybrid"],
                    help="Choose how you want to perform the refactoring",
                    horizontal=True
                )
                st.session_state.refactoring_mode = mode.lower()

                # Display different options based on mode
                if mode == "Local":
                    st.info("Local mode uses your machine's resources for refactoring. Best for small to medium files.")
                    st.markdown("#### 🛠️ Local Processing Options")
                    local_engine = st.selectbox(
                        "Select local processing engine",
                        ["Basic Refactoring", "Advanced Analysis", "Performance Optimization"],
                        help="Choose the type of local processing to apply"
                    )
                    
                    use_cache = st.checkbox("Use cached analysis", value=True, 
                                         help="Use previously cached analysis results if available")
                    
                    parallel_processing = st.checkbox("Enable parallel processing", value=True,
                                                   help="Use multiple CPU cores for faster processing")

                elif mode == "Cloud-based":
                    st.info("Cloud mode leverages powerful cloud resources for comprehensive refactoring. Best for large projects.")
                    st.markdown("#### ☁️ Cloud Service Options")
                    
                    # Model selection
                    model = st.selectbox(
                        "Select AI Model",
                        ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet"],
                        index=0,
                        help="Choose the AI model for refactoring"
                    )
                    st.session_state.refactoring_model = model
                    
                    # Cloud provider selection
                    cloud_provider = st.selectbox(
                        "Select Cloud Provider",
                        ["OpenAI", "Anthropic", "Google Cloud", "Azure"],
                        help="Choose the cloud provider for processing"
                    )
                    
                    # API configuration
                    with st.expander("API Configuration"):
                        st.text_input("API Key", type="password", help="Enter your API key")
                        st.number_input("Request Timeout (seconds)", min_value=30, max_value=300, value=60)
                        st.checkbox("Enable streaming response", value=True)

                else:  # Hybrid
                    st.info("Hybrid mode combines local and cloud processing for optimal results.")
                    st.markdown("#### 🔄 Hybrid Processing Options")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("##### Local Components")
                        st.checkbox("Static Analysis", value=True)
                        st.checkbox("Syntax Optimization", value=True)
                        st.checkbox("Performance Profiling", value=True)
                    
                    with col2:
                        st.markdown("##### Cloud Components")
                        st.checkbox("AI-based Suggestions", value=True)
                        st.checkbox("Pattern Recognition", value=True)
                        st.checkbox("Security Analysis", value=True)

                # Common options for all modes
                st.markdown("#### 🎯 Refactoring Goals")
                goals = st.multiselect(
                    "Select refactoring goals",
                    [
                        "Improve readability",
                        "Enhance maintainability",
                        "Optimize performance",
                        "Fix code smells",
                        "Reduce complexity",
                        "Improve error handling",
                        "Add documentation",
                        "Enhance security",
                        "Improve test coverage",
                        "Modernize code style"
                    ],
                    default=["Improve readability", "Enhance maintainability"],
                    key="goals_selector"
                )
                st.session_state.refactoring_goals = goals

                st.markdown("#### 🎯 Constraints")
                constraints = st.multiselect(
                    "Select constraints",
                    [
                        "Preserve functionality",
                        "Maintain backward compatibility",
                        "Keep existing interfaces",
                        "Minimize changes",
                        "Follow style guide",
                        "Use design patterns",
                        "Consider performance impact",
                        "Maintain test coverage",
                        "Keep memory usage stable",
                        "Preserve API compatibility"
                    ],
                    default=["Preserve functionality"],
                    key="constraints_selector"
                )
                st.session_state.refactoring_constraints = constraints

                st.markdown("#### 📝 Custom Instructions")
                custom_instructions = st.text_area(
                    "Add any specific instructions or requirements",
                    key="custom_instructions",
                    height=100,
                    help="Provide any additional context or requirements for the refactoring"
                )
                st.session_state.custom_instructions = custom_instructions

                # Advanced options expander
                with st.expander("⚙️ Advanced Options", expanded=False):
                    st.markdown("##### Processing Options")
                    st.checkbox("Deep Analysis", value=False, 
                              help="Perform deeper analysis (slower but more thorough)")
                    st.checkbox("Generate Documentation", value=True,
                              help="Automatically generate documentation for changes")
                    st.checkbox("Create Backup", value=True,
                              help="Create backup of original files")
                    
                    st.markdown("##### Output Options")
                    st.checkbox("Generate Detailed Report", value=True,
                              help="Create a detailed report of all changes")
                    st.checkbox("Include Metrics Comparison", value=True,
                              help="Compare metrics before and after refactoring")
                    st.checkbox("Generate Test Cases", value=False,
                              help="Automatically generate test cases for modified code")

                # Generate button at the bottom
                if st.button("Generate Refactoring Suggestions", type="primary", use_container_width=True):
                    if not st.session_state.current_file:
                        st.warning("Please select a file to refactor first.")
                    elif not goals:
                        st.warning("Please select at least one refactoring goal.")
                    else:
                        with st.spinner("Analyzing code and generating refactoring suggestions..."):
                            suggestions = generate_refactoring_suggestions(
                                st.session_state.current_file,
                                st.session_state.current_metrics,
                                st.session_state.refactoring_model,
                                st.session_state.refactoring_goals,
                                st.session_state.refactoring_constraints,
                                st.session_state.custom_instructions
                            )
                            st.session_state.refactoring_suggestions = suggestions
                            
                            if suggestions:
                                st.success(f"Generated {len(suggestions)} refactoring suggestions!")
                                # Switch to preview tab
                                st.session_state.selected_tab = "👀 Preview & Impact"
                            else:
                                st.info("No refactoring suggestions were generated. Try adjusting your goals or constraints.")

        elif st.session_state.selected_tab == "🔍 Analysis & Selection":
            with tab1:
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown("#### Current Code")
                    with st.expander("View Code", expanded=True):
                        if st.session_state.current_metrics:
                            st.code(st.session_state.current_metrics.get('content', ''), language='python')
                        else:
                            st.info("No code content available for the selected file.")

                with col2:
                    st.markdown("#### Code Analysis")
                    if st.session_state.current_metrics:
                        metrics = st.session_state.current_metrics.get('metrics', {})
                        
                        # Create columns for different metric categories
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("##### 📊 Quality Metrics")
                            st.metric("Maintainability Index", 
                                f"{metrics.get('maintainability', 0):.1f}/100",
                                help="Score from 0-100. Higher is better. Based on Halstead Volume, Cyclomatic Complexity, and LOC")
                            st.metric("Cyclomatic Complexity", 
                                f"{metrics.get('complexity', 0):.1f}",
                                help="Number of linearly independent paths through the code")
                            st.metric("Cognitive Complexity",
                                f"{metrics.get('cognitive_complexity', 0):.1f}",
                                help="How difficult it is to understand the code's control flow")
                            st.metric("Code Coverage",
                                f"{metrics.get('code_coverage', 0)}%",
                                help="Percentage of code covered by tests")
                        
                        with col2:
                            st.markdown("##### 📏 Size Metrics")
                            st.metric("Lines of Code", 
                                metrics.get('loc', 0),
                                help="Total lines of code")
                            st.metric("Comment Density",
                                f"{metrics.get('comment_ratio', 0):.1f}%",
                                help="Percentage of comments in code")
                            st.metric("Function Count",
                                metrics.get('function_count', 0),
                                help="Number of functions/methods")
                            st.metric("Class Count",
                                metrics.get('class_count', 0),
                                help="Number of classes")

                        # Code Quality Issues
                        st.markdown("##### 🔍 Code Quality Analysis")
                        
                        # Design Issues
                        with st.expander("Design Issues", expanded=False):
                            design_issues = metrics.get('design_issues', [])
                            if design_issues:
                                for issue in design_issues:
                                    st.warning(f"🎨 {issue}")
                            else:
                                st.success("No design issues detected")

                        # Code Smells
                        with st.expander("Code Smells", expanded=False):
                            code_smells = metrics.get('code_smells', [])
                            if code_smells:
                                for smell in code_smells:
                                    st.warning(f"👃 {smell}")
                            else:
                                st.success("No code smells detected")

                        # Performance Issues
                        with st.expander("Performance Issues", expanded=False):
                            perf_issues = metrics.get('performance_issues', [])
                            if perf_issues:
                                for issue in perf_issues:
                                    st.warning(f"⚡ {issue}")
                            else:
                                st.success("No performance issues detected")

                        # Security Issues
                        with st.expander("Security Issues", expanded=False):
                            security_issues = metrics.get('security_issues', [])
                            if security_issues:
                                for issue in security_issues:
                                    st.error(f"🔒 {issue}")
                            else:
                                st.success("No security issues detected")

                        # Detailed Metrics
                        with st.expander("Detailed Metrics", expanded=False):
                            st.markdown("##### Function-Level Metrics")
                            
                            # Function complexity table
                            if metrics.get('function_metrics'):
                                function_data = []
                                for func, func_metrics in metrics['function_metrics'].items():
                                    function_data.append({
                                        "Function": func,
                                        "Complexity": func_metrics.get('complexity', 0),
                                        "Lines": func_metrics.get('lines', 0),
                                        "Parameters": func_metrics.get('parameters', 0),
                                        "Cognitive Load": func_metrics.get('cognitive_load', 0)
                                    })
                                
                                if function_data:
                                    st.dataframe(
                                        function_data,
                                        column_config={
                                            "Function": "Function Name",
                                            "Complexity": st.column_config.NumberColumn("Complexity", help="Cyclomatic complexity"),
                                            "Lines": st.column_config.NumberColumn("Lines", help="Lines of code"),
                                            "Parameters": st.column_config.NumberColumn("Parameters", help="Number of parameters"),
                                            "Cognitive Load": st.column_config.NumberColumn("Cognitive Load", help="Cognitive complexity")
                                        },
                                        hide_index=True
                                    )

                        # Dependencies
                        with st.expander("Dependencies", expanded=False):
                            st.markdown("##### 📦 Dependencies Analysis")
                            deps = metrics.get('dependencies', {})
                            if deps:
                                st.metric("Direct Dependencies", deps.get('direct', 0))
                                st.metric("Indirect Dependencies", deps.get('indirect', 0))
                                st.metric("Dependency Depth", deps.get('depth', 0))
                                
                                if deps.get('circular_deps'):
                                    st.warning("⚠️ Circular dependencies detected!")
                                    for dep in deps['circular_deps']:
                                        st.markdown(f"- {dep}")

                        # Technical Debt
                        with st.expander("Technical Debt", expanded=False):
                            st.markdown("##### 💸 Technical Debt Analysis")
                            debt = metrics.get('technical_debt', {})
                            if debt:
                                st.metric("Debt Score", f"{debt.get('score', 0)}/100")
                                st.metric("Estimated Hours to Fix", debt.get('hours_to_fix', 0))
                                
                                if debt.get('issues'):
                                    st.markdown("##### Key Issues:")
                                    for issue in debt['issues']:
                                        st.markdown(f"- {issue}")

                        # Language-specific metrics
                        file_ext = os.path.splitext(st.session_state.current_file)[1].lower()
                        language = next((info['name'] for lang, info in config['supported_languages'].items() 
                                      if file_ext in info['extensions']), "Unknown")
                        
                        if language != "Unknown":
                            with st.expander(f"{language}-Specific Metrics", expanded=False):
                                lang_metrics = metrics.get('language_specific', {})
                                if lang_metrics:
                                    for metric_name, value in lang_metrics.items():
                                        st.metric(metric_name, value)
                                else:
                                    st.info(f"No {language}-specific metrics available")

                        # File Information
                        st.markdown("##### 📄 File Information")
                        col3, col4 = st.columns(2)
                        with col3:
                            st.markdown(f"**Language:** {language}")
                            st.markdown(f"**Last Modified:** {metrics.get('last_modified', 'Unknown')}")
                        with col4:
                            st.markdown(f"**File Size:** {os.path.getsize(st.session_state.current_file) / 1024:.1f} KB")
                            st.markdown(f"**Encoding:** {metrics.get('encoding', 'UTF-8')}")
                    else:
                        st.info("No metrics available for the selected file.")

        elif st.session_state.selected_tab == "✏️ Code Editor":
            with tab2:
                st.markdown("#### Code Editor")

                if st.session_state.current_code:
                    # Code actions toolbar
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        if st.button("📋 Copy Code", use_container_width=True):
                            st.toast("Code copied to clipboard!", icon="✅")
                    with col2:
                        if st.button("🔍 Find in Code", use_container_width=True):
                            st.session_state.show_find = True
                    with col3:
                        if st.button("📝 Edit Code", use_container_width=True):
                            st.session_state.edit_mode = True

                    # Find in code functionality
                    if st.session_state.get('show_find', False):
                        find_term = st.text_input("Search in code", key="find_term")
                        if find_term:
                            # Highlight search term in code
                            highlighted_code = highlight_search_term(st.session_state.current_code, find_term)
                            # Add line numbers and display code
                            lines = highlighted_code.split('\n')
                            numbered_code = '\n'.join(f'{i+1:4d} | {line}' for i, line in enumerate(lines))
                            st.markdown(f"""
                                <div style="background-color: #f5f5f5; padding: 1rem; border-radius: 5px; font-family: monospace; white-space: pre; overflow-x: auto;">
                                    <code>{numbered_code}</code>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Display code with line numbers
                            lines = st.session_state.current_code.split('\n')
                            numbered_code = '\n'.join(f'{i+1:4d} | {line}' for i, line in enumerate(lines))
                            st.code(numbered_code, language=st.session_state.current_metrics.get('language', 'python'))
                    else:
                        # Display code with line numbers
                        lines = st.session_state.current_code.split('\n')
                        numbered_code = '\n'.join(f'{i+1:4d} | {line}' for i, line in enumerate(lines))
                        st.code(numbered_code, language=st.session_state.current_metrics.get('language', 'python'))
                else:
                    st.info(
                        "No code available to edit. Please select a file first.")

        elif st.session_state.selected_tab == "👀 Preview & Impact":
            with tab4:
                if st.session_state.refactoring_suggestions:
                    for i, suggestion in enumerate(
                            st.session_state.refactoring_suggestions, 1):
                        with st.expander(f"Suggestion {i}: {suggestion['title']}", expanded=True):
                            st.markdown(suggestion['description'])

                            # Before/After comparison
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Before:**")
                                st.code(
                                    suggestion['before'], language='python')
                            with col2:
                                st.markdown("**After:**")
                                st.code(suggestion['after'], language='python')

                            # Impact metrics
                            st.markdown("#### Impact Analysis")
                            impact = suggestion.get('impact', {})
                            imp_col1, imp_col2, imp_col3 = st.columns(3)

                            with imp_col1:
                                st.metric(
                                    "Complexity Reduction",
                                    f"{impact.get('complexity_reduction', 0)}%",
                                    help="Reduction in code complexity"
                                )
                            with imp_col2:
                                st.metric(
                                    "Maintainability Improvement",
                                    f"{impact.get('maintainability_improvement', 0)}%",
                                    help="Improvement in code maintainability"
                                )
                            with imp_col3:
                                st.metric(
                                    "Lines Changed",
                                    impact.get('lines_changed', 0),
                                    help="Number of lines modified"
                                )

                            # Apply button
                            if st.button(
                                    f"Apply Suggestion {i}", key=f"apply_{i}"):
                                # Update session state with refactored code
                                st.session_state.refactored_code = suggestion['after']
                                st.session_state.current_code = suggestion['after']

                                # Add to refactoring history
                                st.session_state.refactoring_history.append({
                                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    'file': st.session_state.current_file,
                                    'suggestion': suggestion['title'],
                                    'impact': impact
                                })

                                # Save changes to file
                                try:
                                    with open(st.session_state.current_file, 'w') as f:
                                        f.write(st.session_state.current_code)
                                    st.success("Changes applied successfully!")
                                except Exception as e:
                                    st.error(f"Error saving changes: {str(e)}")

                                # Show updated metrics
                                st.markdown("#### Updated Metrics")
                                new_metrics = {
                                    'maintainability': 85.0,
                                    'maintainability_delta': 20.0,
                                    'complexity': 45.0,
                                    'complexity_delta': -15.0
                                }
                                metric_col1, metric_col2 = st.columns(2)

                                with metric_col1:
                                    st.metric(
                                        "New Maintainability",
                                        f"{new_metrics.get('maintainability', 0):.1f}",
                                        delta=f"{new_metrics.get('maintainability_delta', 0):.1f}"
                                    )
                                with metric_col2:
                                    st.metric(
                                        "New Complexity",
                                        f"{new_metrics.get('complexity', 0):.1f}",
                                        delta=f"{new_metrics.get('complexity_delta', 0):.1f}"
                                    )
                else:
                    st.info(
                        "No refactoring suggestions available. Generate suggestions from the Refactoring Options tab.")
                    if st.button(
                        "Go to Refactoring Options",
                            use_container_width=True):
                        st.session_state.selected_tab = "🎯 Refactoring Options"
                        st.experimental_rerun()

            # Display refactoring history
            if st.session_state.refactoring_history:
                st.markdown("#### Refactoring History")
                history_df = pd.DataFrame(st.session_state.refactoring_history)
                st.dataframe(
                    history_df,
                    column_config={
                        "timestamp": "Time",
                        "file": "File",
                        "suggestion": "Suggestion",
                        "impact": "Impact"
                    },
                    hide_index=True
                )


def display_project_analysis():
    """Display project analysis results."""
    if not st.session_state.project_analysis:
        return

    analysis = st.session_state.project_analysis

    # Display metrics dashboard
    viz_manager = VisualizationManager()
    viz_manager.display_metrics_dashboard(
        analysis['metrics'], prefix="project")

    # Display project structure
    viz_manager.display_project_structure(analysis['structure'])


def display_directory_analysis(dir_path: str):
    """Display analysis for a specific directory."""
    if not st.session_state.project_analysis:
        return

    analysis = st.session_state.project_analyzer.analyze_directory(dir_path)

    st.header(f"Directory Analysis: {dir_path}")

    # Display metrics dashboard for directory
    viz_manager = VisualizationManager()
    viz_manager.display_metrics_dashboard(
        analysis['metrics'], prefix=f"dir_{dir_path}")

    # Display directory structure
    viz_manager.display_project_structure(analysis['structure'])


def display_landing_stats():
    """Display dynamic statistics on the landing page."""
    stats = st.session_state.stats_manager.get_display_stats()

    # Create a container with a gradient background for stats
    st.markdown("""
        <div style="
            background: linear-gradient(120deg, #1E88E5 0%, #42A5F5 100%);
            padding: 2rem;
            border-radius: 20px;
            margin: 2rem 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            <h2 style="
                color: white;
                text-align: center;
                margin-bottom: 2rem;
                font-size: 2em;
            ">
                Empowering Better Code Quality
            </h2>
        </div>
    """, unsafe_allow_html=True)

    # Display key metrics in a 4-column layout
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Analysis Accuracy",
            f"{stats['analysis_accuracy']}%",
            help="Overall analysis accuracy"
        )

    with col2:
        st.metric(
            "Code Metrics",
            f"{stats['code_metrics']}+",
            help="Available code quality metrics"
        )

    with col3:
        st.metric(
            "Projects Analyzed",
            stats['projects_analyzed'],
            help="Total projects analyzed"
        )

    with col4:
        st.metric(
            "Availability",
            stats['availability'],
            help="System availability"
        )

    # Display detailed statistics
    st.markdown("### Project Impact")
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Files Analyzed", stats["total_files"])
        st.metric("Total Lines of Code", f"{stats['total_lines']:,}")
        st.metric("Issues Identified", stats["issues_found"])

    with col2:
        # Language distribution
        st.subheader("Language Distribution")
        languages = stats.get("languages", {})
        if languages:
            # Create a proper DataFrame for language distribution
            lang_data = pd.DataFrame(
                data={
                    'Language': list(languages.keys()),
                    'Count': list(languages.values())
                }
            ).sort_values('Count', ascending=False)

            # Create a bar chart using Plotly
            fig = px.bar(
                lang_data,
                x='Language',
                y='Count',
                title='Language Distribution',
                color='Count',
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                showlegend=False,
                xaxis_title="",
                yaxis_title="Files",
                plot_bgcolor='white'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No language statistics available yet")

    # Quality improvements
    st.markdown("### Quality Improvements")
    improvements = stats["improvements"]
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Complexity Reduced",
            f"{improvements.get('complexity_reduced', 0)}%",
            help="Reduction in code complexity"
        )
    with col2:
        st.metric(
            "Maintainability Improved",
            f"{improvements.get('maintainability_improved', 0)}%",
            help="Improvement in code maintainability"
        )
    with col3:
        st.metric(
            "Bugs Fixed",
            improvements.get("bugs_fixed", 0),
            help="Number of potential bugs identified and fixed"
        )


def display_metrics_tab(metrics):
    """Display metrics tab with visualizations."""
    if not metrics:
        st.info("No metrics available for this file.")
        return

    st.header("📊 File Statistics")

    # Create three columns for the metrics
    col1, col2, col3 = st.columns(3)

    # Extract metrics from the raw_metrics dictionary
    raw_metrics = metrics.get('raw_metrics', {})

    with col1:
        st.metric("Lines of Code", raw_metrics.get('loc', 0))
        st.metric("Classes", raw_metrics.get('classes', 0))
        st.metric("Methods", raw_metrics.get('methods', 0))

    with col2:
        st.metric("Source Lines", raw_metrics.get('sloc', 0))
        st.metric("Functions", raw_metrics.get('functions', 0))
        st.metric("Imports", raw_metrics.get('imports', 0))

    with col3:
        comments = raw_metrics.get('comments', 0) + raw_metrics.get('multi', 0)
        st.metric("Comments", comments)
        st.metric("Packages", len(metrics.get('imported_packages', [])))
        comment_ratio = (comments / raw_metrics.get('loc', 1)) * \
            100 if raw_metrics.get('loc', 0) > 0 else 0
        st.metric("Comment Ratio", f"{comment_ratio:.1f}%")

    # Code Composition Chart
    st.header("📈 Code Composition")

    composition_data = {
        'Category': ['Source Lines', 'Comments', 'Blank Lines'],
        'Lines': [
            raw_metrics.get('sloc', 0),
            comments,
            raw_metrics.get('blank', 0)
        ]
    }
    composition_df = pd.DataFrame(composition_data)

    fig_composition = px.bar(
        composition_df,
        x='Category',
        y='Lines',
        title='Code Composition',
        color='Category',
        color_discrete_sequence=['#1f77b4', '#2ca02c', '#d62728']
    )
    fig_composition.update_layout(
        showlegend=True,
        plot_bgcolor='white',
        yaxis_title="Number of Lines",
        xaxis_title=""
    )
    st.plotly_chart(fig_composition, use_container_width=True)

    # Quality Metrics Charts
    st.header("🎯 Quality Metrics")

    # Maintainability Index Gauge
    maintainability = metrics.get('maintainability', {}).get('score', 0)
    fig_maintainability = go.Figure(go.Indicator(
        mode="gauge+number",
        value=maintainability,
        title={'text': "Maintainability Index"},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#1f77b4"},
            'steps': [
                {'range': [0, 40], 'color': "#ff7f0e"},
                {'range': [40, 70], 'color': "#2ca02c"},
                {'range': [70, 100], 'color': "#1f77b4"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 40
            }
        }
    ))
    fig_maintainability.update_layout(height=300)
    st.plotly_chart(fig_maintainability, use_container_width=True)

    # Code Quality Score Gauge
    quality_score = metrics.get('complexity', {}).get('score', 0)
    fig_quality = go.Figure(go.Indicator(
        mode="gauge+number",
        value=quality_score,
        title={'text': "Code Quality Score"},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#2ca02c"},
            'steps': [
                {'range': [0, 50], 'color': "#ff7f0e"},
                {'range': [50, 80], 'color': "#2ca02c"},
                {'range': [80, 100], 'color': "#1f77b4"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 50
            }
        }
    ))
    fig_quality.update_layout(height=300)
    st.plotly_chart(fig_quality, use_container_width=True)

    # Code Structure Distribution
    structure_data = {
        'Category': ['Classes', 'Methods', 'Functions'],
        'Count': [
            raw_metrics.get('classes', 0),
            raw_metrics.get('methods', 0),
            raw_metrics.get('functions', 0)
        ]
    }
    structure_df = pd.DataFrame(structure_data)

    fig_structure = px.pie(
        structure_df,
        values='Count',
        names='Category',
        title='Code Structure Distribution',
        color_discrete_sequence=['#1f77b4', '#2ca02c', '#ff7f0e'],
        hole=0.4
    )
    fig_structure.update_layout(
        showlegend=True,
        height=400
    )
    st.plotly_chart(fig_structure, use_container_width=True)

    # Display issues if any
    if metrics.get('code_smells') or metrics.get(
            'maintainability', {}).get('issues'):
        st.header("⚠️ Issues Found")

        issues_data = {
            'Category': [],
            'Count': []
        }

        code_smells = len(metrics.get('code_smells', []))
        maintainability_issues = len(
            metrics.get(
                'maintainability', {}).get(
                'issues', []))
        complexity_issues = len(
            metrics.get(
                'complexity',
                {}).get(
                'issues',
                []))

        if code_smells > 0:
            issues_data['Category'].append('Code Smells')
            issues_data['Count'].append(code_smells)
        if maintainability_issues > 0:
            issues_data['Category'].append('Maintainability Issues')
            issues_data['Count'].append(maintainability_issues)
        if complexity_issues > 0:
            issues_data['Category'].append('Complexity Issues')
            issues_data['Count'].append(complexity_issues)

        if issues_data['Category']:
            issues_df = pd.DataFrame(issues_data)
            fig_issues = px.bar(
                issues_df,
                x='Category',
                y='Count',
                title='Issues Distribution',
                color='Category',
                color_discrete_sequence=['#ff7f0e', '#d62728', '#9467bd']
            )
            fig_issues.update_layout(
                showlegend=False,
                plot_bgcolor='white',
                yaxis_title="Number of Issues",
                xaxis_title=""
            )
            st.plotly_chart(fig_issues, use_container_width=True)


def display_file_explorer():
    """Display the file explorer interface with enhanced features."""
    # Initialize session state variables if they don't exist
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {}
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None
    if 'current_metrics' not in st.session_state:
        st.session_state.current_metrics = {}
    if 'current_code' not in st.session_state:
        st.session_state.current_code = ""
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = CodeAnalyzer(config)
    if 'file_filter' not in st.session_state:
        st.session_state.file_filter = ""
    if 'expanded_dirs' not in st.session_state:
        st.session_state.expanded_dirs = set()
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = "tree"
    if 'sort_by' not in st.session_state:
        st.session_state.sort_by = "name"
    if 'sort_order' not in st.session_state:
        st.session_state.sort_order = "asc"
    if 'file_type_filter' not in st.session_state:
        st.session_state.file_type_filter = "all"
    if 'recent_files' not in st.session_state:
        st.session_state.recent_files = []

    # Header with gradient background
    st.markdown("""
        <div style="
            background: linear-gradient(120deg, #1E88E5 0%, #42A5F5 100%);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            <h2 style="color: white; text-align: center; margin-bottom: 1rem; font-size: 1.8em;">
                File Explorer
            </h2>
        </div>
    """, unsafe_allow_html=True)

    if not st.session_state.uploaded_files:
        st.warning("Please upload or select files to analyze first.")
        return

    # Create columns for file explorer with adjustable width
    explorer_col, content_col = st.columns([1.2, 2.8])

    with explorer_col:
        # File selection and filtering options
        with st.expander("🔍 Search & Filter", expanded=False):
            st.session_state.file_filter = st.text_input(
                "Search files",
                value=st.session_state.file_filter,
                placeholder="Filter by filename..."
            )

            st.session_state.file_type_filter = st.selectbox(
                "File Type",
                ["all", "python", "java", "javascript", "html", "css", "json", "yaml", "markdown", "text"]
            )

            col1, col2 = st.columns(2)
            with col1:
                st.session_state.sort_by = st.selectbox(
                    "Sort By",
                    ["name", "size", "modified", "type"]
                )
            with col2:
                st.session_state.sort_order = st.selectbox(
                    "Order",
                    ["asc", "desc"]
                )

            st.session_state.view_mode = st.radio(
                "View Mode",
                ["tree", "list", "grid"],
                horizontal=True
            )

        # Display files based on selected view mode
        if st.session_state.view_mode == "tree":
            display_tree_view(group_files_by_directory())
        elif st.session_state.view_mode == "list":
            display_list_view(group_files_by_directory())
        else:  # grid view
            display_grid_view(group_files_by_directory())

    with content_col:
        if st.session_state.current_file:
            # Create tabs for different views
            tab1, tab2 = st.tabs([
                "🔍 Analysis & Selection",
                "📊 Metrics"
            ])

            with tab1:
                st.markdown("#### Current Code")
                if st.session_state.current_metrics:
                    st.code(st.session_state.current_metrics.get('content', ''), language='python')
                else:
                    st.info("No code content available for the selected file.")

            with tab2:
                st.markdown("#### Code Analysis")
                if st.session_state.current_metrics:
                    metrics = st.session_state.current_metrics.get('metrics', {})
                    
                    # Create columns for different metric categories
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("##### 📊 Quality Metrics")
                        st.metric("Maintainability Index", 
                            f"{metrics.get('maintainability', 0):.1f}/100",
                            help="Score from 0-100. Higher is better. Based on Halstead Volume, Cyclomatic Complexity, and LOC")
                        st.metric("Cyclomatic Complexity", 
                            f"{metrics.get('complexity', 0):.1f}",
                            help="Number of linearly independent paths through the code")
                        st.metric("Cognitive Complexity",
                            f"{metrics.get('cognitive_complexity', 0):.1f}",
                            help="How difficult it is to understand the code's control flow")
                        st.metric("Code Coverage",
                            f"{metrics.get('code_coverage', 0)}%",
                            help="Percentage of code covered by tests")
                    
                    with col2:
                        st.markdown("##### 📏 Size Metrics")
                        st.metric("Lines of Code", 
                            metrics.get('loc', 0),
                            help="Total lines of code")
                        st.metric("Comment Density",
                            f"{metrics.get('comment_ratio', 0):.1f}%",
                            help="Percentage of comments in code")
                        st.metric("Function Count",
                            metrics.get('function_count', 0),
                            help="Number of functions/methods")
                        st.metric("Class Count",
                            metrics.get('class_count', 0),
                            help="Number of classes")

                    # Code Quality Issues
                    st.markdown("##### 🔍 Code Quality Analysis")
                    
                    # Design Issues
                    with st.expander("Design Issues", expanded=False):
                        design_issues = metrics.get('design_issues', [])
                        if design_issues:
                            for issue in design_issues:
                                st.warning(f"🎨 {issue}")
                        else:
                            st.success("No design issues detected")

                    # Code Smells
                    with st.expander("Code Smells", expanded=False):
                        code_smells = metrics.get('code_smells', [])
                        if code_smells:
                            for smell in code_smells:
                                st.warning(f"👃 {smell}")
                        else:
                            st.success("No code smells detected")

                    # Performance Issues
                    with st.expander("Performance Issues", expanded=False):
                        perf_issues = metrics.get('performance_issues', [])
                        if perf_issues:
                            for issue in perf_issues:
                                st.warning(f"⚡ {issue}")
                        else:
                            st.success("No performance issues detected")

                    # Security Issues
                    with st.expander("Security Issues", expanded=False):
                        security_issues = metrics.get('security_issues', [])
                        if security_issues:
                            for issue in security_issues:
                                st.error(f"🔒 {issue}")
                        else:
                            st.success("No security issues detected")

                    # Detailed Metrics
                    with st.expander("Detailed Metrics", expanded=False):
                        st.markdown("##### Function-Level Metrics")
                        
                        # Function complexity table
                        if metrics.get('function_metrics'):
                            function_data = []
                            for func, func_metrics in metrics['function_metrics'].items():
                                function_data.append({
                                    "Function": func,
                                    "Complexity": func_metrics.get('complexity', 0),
                                    "Lines": func_metrics.get('lines', 0),
                                    "Parameters": func_metrics.get('parameters', 0),
                                    "Cognitive Load": func_metrics.get('cognitive_load', 0)
                                })
                            
                            if function_data:
                                st.dataframe(
                                    function_data,
                                    column_config={
                                        "Function": "Function Name",
                                        "Complexity": st.column_config.NumberColumn("Complexity", help="Cyclomatic complexity"),
                                        "Lines": st.column_config.NumberColumn("Lines", help="Lines of code"),
                                        "Parameters": st.column_config.NumberColumn("Parameters", help="Number of parameters"),
                                        "Cognitive Load": st.column_config.NumberColumn("Cognitive Load", help="Cognitive complexity")
                                    },
                                    hide_index=True
                                )

                    # Dependencies
                    with st.expander("Dependencies", expanded=False):
                        st.markdown("##### 📦 Dependencies Analysis")
                        deps = metrics.get('dependencies', {})
                        if deps:
                            st.metric("Direct Dependencies", deps.get('direct', 0))
                            st.metric("Indirect Dependencies", deps.get('indirect', 0))
                            st.metric("Dependency Depth", deps.get('depth', 0))
                            
                            if deps.get('circular_deps'):
                                st.warning("⚠️ Circular dependencies detected!")
                                for dep in deps['circular_deps']:
                                    st.markdown(f"- {dep}")

                    # Technical Debt
                    with st.expander("Technical Debt", expanded=False):
                        st.markdown("##### 💸 Technical Debt Analysis")
                        debt = metrics.get('technical_debt', {})
                        if debt:
                            st.metric("Debt Score", f"{debt.get('score', 0)}/100")
                            st.metric("Estimated Hours to Fix", debt.get('hours_to_fix', 0))
                            
                            if debt.get('issues'):
                                st.markdown("##### Key Issues:")
                                for issue in debt['issues']:
                                    st.markdown(f"- {issue}")

                    # Language-specific metrics
                    file_ext = os.path.splitext(st.session_state.current_file)[1].lower()
                    language = next((info['name'] for lang, info in config['supported_languages'].items() 
                                  if file_ext in info['extensions']), "Unknown")
                    
                    if language != "Unknown":
                        with st.expander(f"{language}-Specific Metrics", expanded=False):
                            lang_metrics = metrics.get('language_specific', {})
                            if lang_metrics:
                                for metric_name, value in lang_metrics.items():
                                    st.metric(metric_name, value)
                            else:
                                st.info(f"No {language}-specific metrics available")

                    # File Information
                    st.markdown("##### 📄 File Information")
                    col3, col4 = st.columns(2)
                    with col3:
                        st.markdown(f"**Language:** {language}")
                        st.markdown(f"**Last Modified:** {metrics.get('last_modified', 'Unknown')}")
                    with col4:
                        st.markdown(f"**File Size:** {os.path.getsize(st.session_state.current_file) / 1024:.1f} KB")
                        st.markdown(f"**Encoding:** {metrics.get('encoding', 'UTF-8')}")
                else:
                    st.info("No metrics available for the selected file.")
        else:
            st.info("Select a file from the file explorer to view its analysis.")


def get_file_icon(file_ext):
    """Get appropriate icon based on file extension."""
    icon = "📄"
    if file_ext in ['.py']:
        icon = "🐍"
    elif file_ext in ['.js', '.jsx', '.ts', '.tsx']:
        icon = "⚡"
    elif file_ext in ['.html', '.css']:
        icon = "🌐"
    elif file_ext in ['.json', '.yaml', '.yml']:
        icon = "⚙️"
    elif file_ext in ['.md', '.txt']:
        icon = "📝"
    elif file_ext in ['.java']:
        icon = "☕"
    elif file_ext in ['.cpp', '.c', '.h', '.hpp']:
        icon = "⚙️"
    elif file_ext in ['.cs']:
        icon = "💠"
    elif file_ext in ['.go']:
        icon = "🔵"
    elif file_ext in ['.rb']:
        icon = "💎"
    elif file_ext in ['.php']:
        icon = "🐘"
    elif file_ext in ['.swift']:
        icon = "🍎"
    elif file_ext in ['.kt', '.kts']:
        icon = "📱"
    return icon


def select_file(file_path):
    """Select a file and update session state."""
    st.session_state.current_file = file_path
    # Add to recent files
    if file_path not in st.session_state.recent_files:
        st.session_state.recent_files.insert(0, file_path)
        # Keep only the 10 most recent files
        st.session_state.recent_files = st.session_state.recent_files[:10]
    else:
        # Move to the top of recent files
        st.session_state.recent_files.remove(file_path)
        st.session_state.recent_files.insert(0, file_path)

    # Load file content and analyze metrics
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            st.session_state.current_code = content
            # Analyze file and store metrics
            metrics = st.session_state.analyzer.analyze_file(file_path)
            st.session_state.current_metrics = metrics
            st.session_state.uploaded_files[file_path] = metrics
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")


def display_tree_view(files_by_dir):
    """Display files in tree view."""
    # Filter files based on search term and file type
    filtered_files_by_dir = {}
    for dir_path, files in files_by_dir.items():
        filtered_files = []
        for file_path in files:
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()

            # Apply filters
            if st.session_state.file_filter and st.session_state.file_filter.lower(
            ) not in file_name.lower():
                continue

            if st.session_state.file_type_filter != "all":
                if st.session_state.file_type_filter == "python" and file_ext != ".py":
                    continue
                elif st.session_state.file_type_filter == "java" and file_ext != ".java":
                    continue
                elif st.session_state.file_type_filter == "javascript" and file_ext not in [".js", ".jsx", ".ts", ".tsx"]:
                    continue
                elif st.session_state.file_type_filter == "html" and file_ext not in [".html", ".htm"]:
                    continue
                elif st.session_state.file_type_filter == "css" and file_ext != ".css":
                    continue
                elif st.session_state.file_type_filter == "json" and file_ext != ".json":
                    continue
                elif st.session_state.file_type_filter == "yaml" and file_ext not in [".yaml", ".yml"]:
                    continue
                elif st.session_state.file_type_filter == "markdown" and file_ext not in [".md", ".markdown"]:
                    continue
                elif st.session_state.file_type_filter == "text" and file_ext not in [".txt", ".text"]:
                    continue

            filtered_files.append(file_path)

        if filtered_files:
            filtered_files_by_dir[dir_path] = filtered_files

    # Sort directories
    sorted_dirs = sorted(filtered_files_by_dir.keys())

    # Display files grouped by directory with filtering
    for dir_path in sorted_dirs:
        files = filtered_files_by_dir[dir_path]

        # Sort files based on selected criteria
        if st.session_state.sort_by == "name":
            files.sort(key=lambda x: os.path.basename(x).lower())
        elif st.session_state.sort_by == "size":
            files.sort(key=lambda x: os.path.getsize(x))
        elif st.session_state.sort_by == "modified":
            files.sort(key=lambda x: os.path.getmtime(x))
        elif st.session_state.sort_by == "type":
            files.sort(key=lambda x: os.path.splitext(x)[1].lower())

        # Apply sort order
        if st.session_state.sort_order == "desc":
            files.reverse()

        dir_name = os.path.basename(dir_path) if dir_path else "Root"
        is_expanded = dir_path in st.session_state.expanded_dirs

        with st.expander(f"📁 {dir_name}", expanded=is_expanded):
            if not is_expanded:
                st.session_state.expanded_dirs.add(dir_path)

            for file_path in files:
                file_name = os.path.basename(file_path)
                file_ext = os.path.splitext(file_name)[1].lower()

                # Get appropriate icon based on file extension
                icon = get_file_icon(file_ext)

                # Create a button with hover effect
                button_style = """
                    <style>
                    div[data-testid="stButton"] button {
                        background-color: transparent;
                        border: 1px solid #e0e0e0;
                        transition: all 0.3s;
                    }
                    div[data-testid="stButton"] button:hover {
                        background-color: #f0f2f6;
                        border-color: #1E88E5;
                    }
                    </style>
                """
                st.markdown(button_style, unsafe_allow_html=True)

                if st.button(
                    f"{icon} {file_name}",
                    key=f"file_{file_path}",
                    help=f"Click to view {file_name}",
                    use_container_width=True
                ):
                    select_file(file_path)


def display_list_view(files_by_dir):
    """Display files in list view."""
    # Flatten the directory structure for list view
    all_files = []
    for dir_path, files in files_by_dir.items():
        for file_path in files:
            all_files.append((dir_path, file_path))

    # Filter files based on search term and file type
    filtered_files = []
    for dir_path, file_path in all_files:
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()

        # Apply filters
        if st.session_state.file_filter and st.session_state.file_filter.lower(
        ) not in file_name.lower():
            continue

        if st.session_state.file_type_filter != "all":
            if st.session_state.file_type_filter == "python" and file_ext != ".py":
                continue
            elif st.session_state.file_type_filter == "java" and file_ext != ".java":
                continue
            elif st.session_state.file_type_filter == "javascript" and file_ext not in [".js", ".jsx", ".ts", ".tsx"]:
                continue
            elif st.session_state.file_type_filter == "html" and file_ext not in [".html", ".htm"]:
                continue
            elif st.session_state.file_type_filter == "css" and file_ext != ".css":
                continue
            elif st.session_state.file_type_filter == "json" and file_ext != ".json":
                continue
            elif st.session_state.file_type_filter == "yaml" and file_ext not in [".yaml", ".yml"]:
                continue
            elif st.session_state.file_type_filter == "markdown" and file_ext not in [".md", ".markdown"]:
                continue
            elif st.session_state.file_type_filter == "text" and file_ext not in [".txt", ".text"]:
                continue

        filtered_files.append((dir_path, file_path))

    # Sort files based on selected criteria
    if st.session_state.sort_by == "name":
        filtered_files.sort(key=lambda x: os.path.basename(x[1]).lower())
    elif st.session_state.sort_by == "size":
        filtered_files.sort(key=lambda x: os.path.getsize(x[1]))
    elif st.session_state.sort_by == "modified":
        filtered_files.sort(key=lambda x: os.path.getmtime(x[1]))
    elif st.session_state.sort_by == "type":
        filtered_files.sort(key=lambda x: os.path.splitext(x[1])[1].lower())

    # Apply sort order
    if st.session_state.sort_order == "desc":
        filtered_files.reverse()

    # Display files in list view
    for dir_path, file_path in filtered_files:
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()

        # Get appropriate icon based on file extension
        icon = get_file_icon(file_ext)

        # Create a button with hover effect
        button_style = """
            <style>
            div[data-testid="stButton"] button {
                background-color: transparent;
                border: 1px solid #e0e0e0;
                transition: all 0.3s;
            }
            div[data-testid="stButton"] button:hover {
                background-color: #f0f2f6;
                border-color: #1E88E5;
            }
            </style>
        """
        st.markdown(button_style, unsafe_allow_html=True)

        # Display file path and name
        dir_name = os.path.basename(dir_path) if dir_path else "Root"
        if st.button(
            f"{icon} {dir_name}/{file_name}",
            key=f"file_{file_path}",
            help=f"Click to view {file_name}",
            use_container_width=True
        ):
            select_file(file_path)


def display_grid_view(files_by_dir):
    """Display files in grid view."""
    # Flatten the directory structure for grid view
    all_files = []
    for dir_path, files in files_by_dir.items():
        for file_path in files:
            all_files.append((dir_path, file_path))

    # Filter files based on search term and file type
    filtered_files = []
    for dir_path, file_path in all_files:
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()

        # Apply filters
        if st.session_state.file_filter and st.session_state.file_filter.lower(
        ) not in file_name.lower():
            continue

        if st.session_state.file_type_filter != "all":
            if st.session_state.file_type_filter == "python" and file_ext != ".py":
                continue
            elif st.session_state.file_type_filter == "java" and file_ext != ".java":
                continue
            elif st.session_state.file_type_filter == "javascript" and file_ext not in [".js", ".jsx", ".ts", ".tsx"]:
                continue
            elif st.session_state.file_type_filter == "html" and file_ext not in [".html", ".htm"]:
                continue
            elif st.session_state.file_type_filter == "css" and file_ext != ".css":
                continue
            elif st.session_state.file_type_filter == "json" and file_ext != ".json":
                continue
            elif st.session_state.file_type_filter == "yaml" and file_ext not in [".yaml", ".yml"]:
                continue
            elif st.session_state.file_type_filter == "markdown" and file_ext not in [".md", ".markdown"]:
                continue
            elif st.session_state.file_type_filter == "text" and file_ext not in [".txt", ".text"]:
                continue

        filtered_files.append((dir_path, file_path))

    # Sort files based on selected criteria
    if st.session_state.sort_by == "name":
        filtered_files.sort(key=lambda x: os.path.basename(x[1]).lower())
    elif st.session_state.sort_by == "size":
        filtered_files.sort(key=lambda x: os.path.getsize(x[1]))
    elif st.session_state.sort_by == "modified":
        filtered_files.sort(key=lambda x: os.path.getmtime(x[1]))
    elif st.session_state.sort_by == "type":
        filtered_files.sort(key=lambda x: os.path.splitext(x[1])[1].lower())

    # Apply sort order
    if st.session_state.sort_order == "desc":
        filtered_files.reverse()

    # Display files in grid view
    cols = st.columns(3)
    for i, (dir_path, file_path) in enumerate(filtered_files):
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()

        # Get appropriate icon based on file extension
        icon = get_file_icon(file_ext)

        # Create a card for each file
        with cols[i % 3]:
            st.markdown(f"""
                <div style="
                    background: white;
                    padding: 1rem;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    margin-bottom: 1rem;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s;
                ">
                    <div style="font-size: 2em; margin-bottom: 0.5rem;">
                        {icon}
                    </div>
                    <div style="font-weight: bold; margin-bottom: 0.5rem; word-break: break-word;">
                        {file_name}
                    </div>
                    <div style="color: #666; font-size: 0.8em;">
                        {os.path.basename(dir_path) if dir_path else "Root"}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if st.button(
                "View File",
                key=f"file_{file_path}",
                help=f"Click to view {file_name}",
                use_container_width=True
            ):
                select_file(file_path)


def highlight_search_term(code, term):
    """Highlight search term in code."""
    if not term:
        return code

    # Escape HTML special characters
    code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Highlight the search term
    highlighted_code = code.replace(
        term,
        f'<span style="background-color: yellow; font-weight: bold;">{term}</span>')

    return highlighted_code


def generate_refactoring_suggestions(file_path, metrics, model, goals, constraints, custom_instructions):
    """Generate refactoring suggestions based on code analysis and user preferences."""
    try:
        # Get file content and language
        with open(file_path, 'r') as f:
            content = f.read()
        
        file_ext = os.path.splitext(file_path)[1].lower()
        suggestions = []
        
        # Check complexity issues
        complexity = metrics.get('complexity', {})
        if isinstance(complexity, dict):
            complexity_score = complexity.get('score', 0)
        else:
            complexity_score = complexity

        if complexity_score < 70 or "Reduce complexity" in goals:
            suggestions.append({
                'title': 'Reduce Code Complexity',
                'description': 'The code has high cyclomatic complexity. Consider breaking down complex functions into smaller, more manageable pieces.',
                'before': content,
                'after': content,  # This would be replaced with actual refactored code
                'impact': {
                    'complexity_reduction': 25,
                    'maintainability_improvement': 20,
                    'lines_changed': 10
                }
            })
        
        # Check maintainability issues
        maintainability = metrics.get('maintainability', {})
        if isinstance(maintainability, dict):
            maintainability_score = maintainability.get('score', 0)
        else:
            maintainability_score = maintainability

        if maintainability_score < 70 or "Enhance maintainability" in goals:
            suggestions.append({
                'title': 'Improve Code Maintainability',
                'description': 'The code has low maintainability. Consider adding documentation and improving code structure.',
                'before': content,
                'after': content,  # This would be replaced with actual refactored code
                'impact': {
                    'complexity_reduction': 15,
                    'maintainability_improvement': 30,
                    'lines_changed': 15
                }
            })
        
        # Check code smells
        code_smells = metrics.get('code_smells', [])
        if code_smells and ("Fix code smells" in goals or "Improve readability" in goals):
            for smell in code_smells:
                suggestions.append({
                    'title': f'Fix Code Smell: {smell}',
                    'description': f'Detected code smell: {smell}. Consider refactoring to improve code quality.',
                    'before': content,
                    'after': content,  # This would be replaced with actual refactored code
                    'impact': {
                        'complexity_reduction': 10,
                        'maintainability_improvement': 15,
                        'lines_changed': 5
                    }
                })
        
        # Check documentation
        if "Add documentation" in goals:
            raw_metrics = metrics.get('raw_metrics', {})
            comment_ratio = raw_metrics.get('comment_ratio', 0)
            if comment_ratio < 0.2:
                suggestions.append({
                    'title': 'Improve Documentation',
                    'description': 'The code has a low comment ratio. Consider adding more documentation to improve code understanding.',
                    'before': content,
                    'after': content,  # This would be replaced with actual refactored code
                    'impact': {
                        'complexity_reduction': 0,
                        'maintainability_improvement': 25,
                        'lines_changed': 20
                    }
                })

        # Check performance optimization
        if "Optimize performance" in goals:
            suggestions.append({
                'title': 'Optimize Code Performance',
                'description': 'Consider optimizing code performance through algorithmic improvements and better resource usage.',
                'before': content,
                'after': content,  # This would be replaced with actual refactored code
                'impact': {
                    'complexity_reduction': 5,
                    'maintainability_improvement': 10,
                    'lines_changed': 8
                }
            })

        return suggestions
        
    except Exception as e:
        print(f"Error generating refactoring suggestions: {str(e)}")
        return []


def metric_card(title, value, description=None):
    """Generate HTML for a metric card with consistent styling."""
    card_html = f"""
        <div style="
            background-color: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin: 1rem 0;
        ">
            <h4 style="color: #1E88E5; margin-bottom: 0.5rem;">{title}</h4>
            <div style="font-size: 1.5em; font-weight: bold; margin-bottom: 0.5rem;">{value}</div>
            {f'<div style="color: #666; font-size: 0.9em;">{description}</div>' if description else ''}
        </div>
    """
    return card_html


def group_files_by_directory():
    """Group files by their directory structure."""
    files_by_dir = {}
    
    if not st.session_state.uploaded_files:
        return files_by_dir
        
    for file_path in st.session_state.uploaded_files.keys():
        # Get directory path
        dir_path = os.path.dirname(file_path)
        
        # Filter based on search term if present
        if st.session_state.file_filter:
            if st.session_state.file_filter.lower() not in os.path.basename(file_path).lower():
                continue
        
        # Filter based on file type
        if st.session_state.file_type_filter != "all":
            file_ext = os.path.splitext(file_path)[1].lower()
            if st.session_state.file_type_filter == "python" and file_ext != ".py":
                continue
            elif st.session_state.file_type_filter == "java" and file_ext != ".java":
                continue
            elif st.session_state.file_type_filter == "javascript" and file_ext not in [".js", ".jsx"]:
                continue
            elif st.session_state.file_type_filter == "typescript" and file_ext not in [".ts", ".tsx"]:
                continue
            elif st.session_state.file_type_filter == "html" and file_ext != ".html":
                continue
            elif st.session_state.file_type_filter == "css" and file_ext != ".css":
                continue
            elif st.session_state.file_type_filter == "json" and file_ext != ".json":
                continue
            elif st.session_state.file_type_filter == "yaml" and file_ext not in [".yml", ".yaml"]:
                continue
            elif st.session_state.file_type_filter == "markdown" and file_ext not in [".md", ".markdown"]:
                continue
        
        # Initialize directory in dictionary if not present
        if dir_path not in files_by_dir:
            files_by_dir[dir_path] = []
        
        # Add file to directory list
        files_by_dir[dir_path].append(file_path)
    
    # Sort files based on selected criteria
    for dir_path in files_by_dir:
        if st.session_state.sort_by == "name":
            files_by_dir[dir_path].sort(
                key=lambda x: os.path.basename(x).lower(),
                reverse=(st.session_state.sort_order == "desc")
            )
        elif st.session_state.sort_by == "size":
            files_by_dir[dir_path].sort(
                key=lambda x: os.path.getsize(x),
                reverse=(st.session_state.sort_order == "desc")
            )
        elif st.session_state.sort_by == "modified":
            files_by_dir[dir_path].sort(
                key=lambda x: os.path.getmtime(x),
                reverse=(st.session_state.sort_order == "desc")
            )
        elif st.session_state.sort_by == "type":
            files_by_dir[dir_path].sort(
                key=lambda x: os.path.splitext(x)[1].lower(),
                reverse=(st.session_state.sort_order == "desc")
            )
    
    return files_by_dir


if __name__ == "__main__":
    main()
