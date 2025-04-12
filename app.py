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
import numpy as np
from smell_analyzer import SmellAnalyzer, SmellType, SmellSeverity
from ui_components import UIComponents

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

# Initialize the smell analyzer
if 'smell_analyzer' not in st.session_state:
    st.session_state.smell_analyzer = SmellAnalyzer()

def init_session_state():
    """Initialize or reset session state variables."""
    # Define all session state variables with their default values
    defaults = {
        'initialized': True,
        'uploaded_files': {},
        'files': {},
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
            'OpenAI': ['gpt-4', 'gpt-3.5-turbo'],
            'Anthropic': ['claude-3-opus-20240229', 'claude-3-sonnet-20240229'],
            'Google': ['gemini-pro'],
            'Cohere': ['command']
        }
    
    async def refactor_code(self, code: str, model: str, prompt: str) -> str:
        """Refactor code using the specified model."""
        # Placeholder for actual refactoring logic
        return code

def main():
    """Main application function."""
    init_session_state()  # Initialize or reset session state
    
    st.title("RefactoringAI")
    st.markdown("""
        ### AI-Powered Code Refactoring Tool
        Upload your code and let AI help you improve its quality, maintainability, and performance.
    """)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Upload & Analyze", "File Explorer", "Refactor"])
    
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
                    <span style='font-size: 1.1em;'>Actionable Results</span>
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
                    f'<span style="padding: 0.2rem 0.5rem; background: #f8f9fa; border-radius: 4px; font-size: 0.8em;">{lang["icon"]} {lang["name"]}</span>'
                    for lang in config['supported_languages'].values()
                ])
            ), unsafe_allow_html=True)
            
            # Update file uploader to accept all supported extensions
            supported_extensions = []
            for lang in config['supported_languages'].values():
                supported_extensions.extend([ext[1:] for ext in lang['extensions']])  # Remove the dot from extensions
            
            uploaded_file = st.file_uploader(
                "Choose a source file",
                type=supported_extensions,
                key="single_file",
                help=f"Supported file types: {', '.join(supported_extensions)}"
            )
            if uploaded_file:
                with st.spinner("🔍 Analyzing your code..."):
                    if handle_file_upload(uploaded_file):
                        st.success("✅ Analysis Complete! View results in the File Explorer tab.")

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
            uploaded_zip = st.file_uploader("Choose a ZIP file", type=['zip'], key="zip_file")
            if uploaded_zip:
                with st.spinner("📊 Processing your project..."):
                    if handle_zip_upload(uploaded_zip):
                        st.success("✅ Project Analysis Complete! View results in the File Explorer tab.")

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
            repo_url = st.text_input("Enter repository URL", 
                placeholder="https://github.com/username/repository",
                help="Enter the URL of a public GitHub repository")
            
            if repo_url:
                if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
                    with st.spinner("🔍 Cloning and analyzing repository..."):
                        handle_github_upload(repo_url)
                        st.success("✅ Repository Analysis Complete! View results in the File Explorer tab.")

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
                        Advanced Features
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
                st.error(f"Unsupported file type. Supported extensions: {', '.join(supported_extensions)}")
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
            
            # Update session state for both files and uploaded_files
            if 'uploaded_files' not in st.session_state:
                st.session_state.uploaded_files = {}
            if 'files' not in st.session_state:
                st.session_state.files = {}
                
            st.session_state.uploaded_files[str(file_path)] = file_metrics
            st.session_state.files[str(file_path)] = file_metrics
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
            st.session_state.files = {}
            
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
                            file_metrics = analyzer.analyze_file(str(file_path))
                            st.session_state.uploaded_files[str(file_path)] = file_metrics
                            st.session_state.files[str(file_path)] = file_metrics
                            
                            # Update statistics
                            st.session_state.stats_manager.update_file_analysis(
                                file,
                                file_metrics
                            )
                        except Exception as e:
                            st.warning(f"Error analyzing {file}: {str(e)}")
            
            if not files_found:
                st.warning(f"No supported files found in the ZIP archive. Supported extensions: {', '.join(supported_extensions)}")
                return False
            
            # Set initial file selection
            st.session_state.current_file = next(iter(st.session_state.uploaded_files))
            
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
        st.session_state.files = {}
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
                        st.session_state.uploaded_files[str(file_path)] = file_metrics
                        st.session_state.files[str(file_path)] = file_metrics
                        
                        # Update statistics
                        st.session_state.stats_manager.update_file_analysis(
                            file,
                            file_metrics
                        )
                    except Exception as e:
                        st.warning(f"Error analyzing {file}: {str(e)}")
        
        if not files_found:
            st.warning(f"No supported files found in the repository. Supported extensions: {', '.join(supported_extensions)}")
            return False
        
        # Set initial file selection
        st.session_state.current_file = next(iter(st.session_state.uploaded_files))
        
        # Generate and update project analysis
        project_metrics = analyzer.analyze_project(str(repo_dir))
        st.session_state.project_analysis = project_metrics
        st.session_state.stats_manager.update_project_analysis()
        
        return True
        
    except Exception as e:
        st.error(f"Error cloning repository: {str(e)}")
        return False

def display_refactoring_options():
    """Display refactoring options and interface."""
    # Initialize session state variables if not present
    if 'current_metrics' not in st.session_state:
        st.session_state.current_metrics = None
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None
    if 'refactoring_history' not in st.session_state:
        st.session_state.refactoring_history = []
    if 'edited_code' not in st.session_state:
        st.session_state.edited_code = None
    if 'refactoring_suggestions' not in st.session_state:
        st.session_state.refactoring_suggestions = None
    if 'impact_analysis' not in st.session_state:
        st.session_state.impact_analysis = None

    # Check if files are available for refactoring
    if not st.session_state.files:
        st.warning("No files available for refactoring. Please upload files first.")
        return

    # Display header with gradient background
    st.markdown("""
        <div style="
            background: linear-gradient(90deg, #1E88E5, #1565C0);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            color: white;
        ">
            <h1 style="margin: 0;">Code Refactoring</h1>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Transform your code with AI-powered refactoring</p>
        </div>
    """, unsafe_allow_html=True)

    # Main layout
    col1, col2 = st.columns([1, 2])

    with col1:
        # File selection section
        st.markdown("### Select File")
        file_options = list(st.session_state.files.keys())
        selected_file = st.selectbox(
            "Choose a file to refactor",
            file_options,
            index=file_options.index(st.session_state.current_file) if st.session_state.current_file in file_options else 0
        )

        # Update session state when file selection changes
        if selected_file != st.session_state.current_file:
            st.session_state.current_file = selected_file
            st.session_state.current_metrics = st.session_state.files[selected_file]
            st.session_state.edited_code = None
            st.session_state.refactoring_suggestions = None
            st.session_state.impact_analysis = None

        # Display file information
        if st.session_state.current_file:
            file_info = st.session_state.files[st.session_state.current_file]
            st.markdown("#### File Information")
            st.markdown(f"**Language:** {file_info.get('language', 'Unknown')}")
            st.markdown(f"**Size:** {file_info.get('size', 0)} bytes")
            st.markdown(f"**Lines:** {file_info.get('lines', 0)}")

    with col2:
        # Create tabs for different aspects of refactoring
        tab1, tab2, tab3 = st.tabs(["Code Editor", "Refactoring Options", "Analysis & Impact"])

        with tab1:
            # Display current code
            if st.session_state.current_file:
                code = st.session_state.files[st.session_state.current_file].get('code', '')
                edited_code = st.text_area(
                    "Edit Code",
                    value=st.session_state.edited_code if st.session_state.edited_code else code,
                    height=400
                )
                st.session_state.edited_code = edited_code

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Save Changes"):
                        try:
                            with open(st.session_state.current_file, 'w') as f:
                                f.write(edited_code)
                            st.success("Changes saved successfully!")
                        except Exception as e:
                            st.error(f"Error saving changes: {str(e)}")
                with col2:
                    if st.button("Reset"):
                        st.session_state.edited_code = code
                        st.rerun()

        with tab2:
            # Refactoring options
            st.markdown("### Refactoring Configuration")
            
            # Model selection
            model = st.selectbox(
                "Select AI Model",
                ["GPT-4", "GPT-3.5", "Claude"],
                index=0
            )
            
            # Refactoring scope
            scope = st.multiselect(
                "Refactoring Scope",
                ["Function Level", "Class Level", "File Level", "Project Level"],
                default=["Function Level"]
            )
            
            # Refactoring goals
            goals = st.multiselect(
                "Refactoring Goals",
                ["Improve Readability", "Reduce Complexity", "Enhance Maintainability", "Optimize Performance"],
                default=["Improve Readability", "Reduce Complexity"]
            )
            
            # Constraints
            constraints = st.multiselect(
                "Constraints",
                ["Preserve Functionality", "Maintain Backward Compatibility", "Follow Style Guide", "Minimize Changes"],
                default=["Preserve Functionality"]
            )
            
            # Generate refactoring suggestions
            if st.button("Generate Refactoring Suggestions"):
                with st.spinner("Analyzing code and generating suggestions..."):
                    # Placeholder for actual refactoring logic
                    st.session_state.refactoring_suggestions = {
                        "suggestions": [
                            {
                                "type": "Extract Method",
                                "description": "Extract repeated code into a new method",
                                "location": "Lines 45-52",
                                "impact": "High",
                                "effort": "Medium"
                            }
                        ]
                    }
                    st.session_state.impact_analysis = {
                        "complexity_reduction": 15,
                        "maintainability_improvement": 20,
                        "readability_improvement": 25
                    }

        with tab3:
            # Display refactoring suggestions and impact analysis
            if st.session_state.refactoring_suggestions:
                st.markdown("### Refactoring Suggestions")
                for suggestion in st.session_state.refactoring_suggestions["suggestions"]:
                    with st.expander(f"{suggestion['type']} - {suggestion['location']}"):
                        st.markdown(f"**Description:** {suggestion['description']}")
                        st.markdown(f"**Impact:** {suggestion['impact']}")
                        st.markdown(f"**Effort:** {suggestion['effort']}")
                        
                        if st.button("Apply This Suggestion", key=f"apply_{suggestion['type']}"):
                            # Placeholder for applying suggestion
                            st.success("Suggestion applied successfully!")
                
                if st.session_state.impact_analysis:
                    st.markdown("### Impact Analysis")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Complexity Reduction", f"{st.session_state.impact_analysis['complexity_reduction']}%")
                    with col2:
                        st.metric("Maintainability Improvement", f"{st.session_state.impact_analysis['maintainability_improvement']}%")
                    with col3:
                        st.metric("Readability Improvement", f"{st.session_state.impact_analysis['readability_improvement']}%")
            else:
                st.info("No refactoring suggestions available. Configure and generate suggestions in the Refactoring Options tab.")

    # Display refactoring history
    if st.session_state.refactoring_history:
        st.markdown("### Refactoring History")
        for entry in st.session_state.refactoring_history:
            with st.expander(f"Refactoring on {entry['timestamp']}"):
                st.markdown(f"**File:** {entry['file']}")
                st.markdown(f"**Changes:** {entry['changes']}")
                st.markdown(f"**Impact:** {entry['impact']}")

def display_project_analysis():
    """Display project analysis results."""
    if not st.session_state.project_analysis:
        return
    
    analysis = st.session_state.project_analysis
    
    # Display metrics dashboard
    viz_manager = VisualizationManager()
    viz_manager.display_metrics_dashboard(analysis['metrics'], prefix="project")
    
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
    viz_manager.display_metrics_dashboard(analysis['metrics'], prefix=f"dir_{dir_path}")
    
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
        comment_ratio = (comments / raw_metrics.get('loc', 1)) * 100 if raw_metrics.get('loc', 0) > 0 else 0
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
    if metrics.get('code_smells') or metrics.get('maintainability', {}).get('issues'):
        st.header("⚠️ Issues Found")
        
        issues_data = {
            'Category': [],
            'Count': []
        }
        
        code_smells = len(metrics.get('code_smells', []))
        maintainability_issues = len(metrics.get('maintainability', {}).get('issues', []))
        complexity_issues = len(metrics.get('complexity', {}).get('issues', []))
        
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
        st.session_state.view_mode = "tree"  # Options: tree, list, grid
    if 'sort_by' not in st.session_state:
        st.session_state.sort_by = "name"  # Options: name, size, modified, type
    if 'sort_order' not in st.session_state:
        st.session_state.sort_order = "asc"  # Options: asc, desc
    if 'file_type_filter' not in st.session_state:
        st.session_state.file_type_filter = "all"  # Options: all, python, java, javascript, etc.
    if 'recent_files' not in st.session_state:
        st.session_state.recent_files = []
    if 'smells' not in st.session_state:
        st.session_state.smells = []

    # Header with gradient background and search bar
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
        # Advanced search and filtering options
        with st.expander("🔍 Search & Filter", expanded=False):
            # Search bar for files
            st.session_state.file_filter = st.text_input(
                "Search files",
                value=st.session_state.file_filter,
                placeholder="Filter by filename...",
                help="Type to filter files by name"
            )
            
            # File type filter
            file_types = ["all", "python", "java", "javascript", "html", "css", "json", "yaml", "markdown", "text"]
            st.session_state.file_type_filter = st.selectbox(
                "File Type",
                file_types,
                index=file_types.index(st.session_state.file_type_filter),
                help="Filter by file type"
            )
            
            # Sort options
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.sort_by = st.selectbox(
                    "Sort By",
                    ["name", "size", "modified", "type"],
                    index=["name", "size", "modified", "type"].index(st.session_state.sort_by),
                    help="Sort files by"
                )
            with col2:
                st.session_state.sort_order = st.selectbox(
                    "Order",
                    ["asc", "desc"],
                    index=["asc", "desc"].index(st.session_state.sort_order),
                    help="Sort order"
                )
            
            # View mode selection
            st.session_state.view_mode = st.radio(
                "View Mode",
                ["tree", "list", "grid"],
                index=["tree", "list", "grid"].index(st.session_state.view_mode),
                horizontal=True,
                help="Select view mode"
            )
        
        # Recent files section
        if st.session_state.recent_files:
            with st.expander("🕒 Recent Files", expanded=True):
                for file_path in st.session_state.recent_files[:5]:
                    if file_path in st.session_state.uploaded_files:
                        file_name = os.path.basename(file_path)
                        file_ext = os.path.splitext(file_name)[1].lower()
                        
                        # Get appropriate icon based on file extension
                        icon = get_file_icon(file_ext)
                        
                        if st.button(
                            f"{icon} {file_name}",
                            key=f"recent_{file_path}",
                            help=f"Click to view {file_name}",
                            use_container_width=True
                        ):
                            select_file(file_path)
        
        # Project files section
        st.markdown("""
            <div class="file-tree" style="margin-top: 1rem;">
                <h3 style="color: #1E88E5; font-size: 1.2em; margin-bottom: 1rem; font-weight: 500;">
                    Project Files
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Group files by directory
        files_by_dir = {}
        for file_path in st.session_state.uploaded_files.keys():
            dir_path = os.path.dirname(file_path)
            if dir_path not in files_by_dir:
                files_by_dir[dir_path] = []
            files_by_dir[dir_path].append(file_path)
        
        # Display files based on selected view mode
        if st.session_state.view_mode == "tree":
            display_tree_view(files_by_dir)
        elif st.session_state.view_mode == "list":
            display_list_view(files_by_dir)
        else:  # grid view
            display_grid_view(files_by_dir)
    
    with content_col:
        if st.session_state.current_file:
            file_name = os.path.basename(st.session_state.current_file)
            file_ext = os.path.splitext(file_name)[1].lower()
            
            # Enhanced file header with metadata
            st.markdown(f"""
                <div style="
                    background: white;
                    padding: 1.5rem;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    margin-bottom: 2rem;
                ">
                    <h3 style="color: #1E88E5; font-size: 1.4em; margin-bottom: 0.5rem;">
                        {file_name}
                    </h3>
                    <div style="display: flex; gap: 2rem; color: #666; font-size: 0.9em;">
                        <div>
                            <strong>Type:</strong> {st.session_state.current_metrics.get('language', 'unknown').upper()}
                        </div>
                        <div>
                            <strong>Size:</strong> {os.path.getsize(st.session_state.current_file) / 1024:.1f} KB
                        </div>
                        <div>
                            <strong>Last Modified:</strong> {datetime.fromtimestamp(os.path.getmtime(st.session_state.current_file)).strftime('%Y-%m-%d %H:%M')}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Create tabs for different views with icons
            code_tab, metrics_tab, issues_tab, refactoring_tab, charts_tab, smells_tab = st.tabs([
                "📝 Source Code",
                "📊 Metrics",
                "⚠️ Issues",
                "🔄 Refactoring",
                "📈 Interactive Charts",
                "🔍 Code Smells"
            ])
            
            with code_tab:
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
                            st.markdown(f"""
                                <div class="code-viewer">
                                    <pre><code>{highlighted_code}</code></pre>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Display code with syntax highlighting
                            st.code(
                                st.session_state.current_code,
                                language=st.session_state.current_metrics.get('language', 'python')
                            )
                    else:
                        # Display code with syntax highlighting
                        st.code(
                            st.session_state.current_code,
                            language=st.session_state.current_metrics.get('language', 'python')
                        )
                else:
                    st.info("No code content available for this file.")
            
            with metrics_tab:
                if st.session_state.current_metrics:
                    # Display file statistics in a modern card layout
                    st.markdown("""
                        <div style="margin-bottom: 2rem;">
                            <h3 style="color: #1E88E5; margin-bottom: 1rem;">📊 File Statistics</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    raw_metrics = st.session_state.current_metrics.get('raw_metrics', {})
                    
                    # Create a modern metrics grid
                    col1, col2, col3 = st.columns(3)
                    
                    def metric_card(label, value, help_text=""):
                        return f"""
                            <div style="
                                background: white;
                                padding: 1rem;
                                border-radius: 10px;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                                margin-bottom: 1rem;
                                text-align: center;
                            ">
                                <h4 style="color: #666; font-size: 0.9em; margin-bottom: 0.5rem;">
                                    {label}
                                </h4>
                                <div style="color: #1E88E5; font-size: 1.8em; font-weight: bold;">
                                    {value}
                                </div>
                                <div style="color: #999; font-size: 0.8em; margin-top: 0.5rem;">
                                    {help_text}
                                </div>
                            </div>
                        """
                    
                    with col1:
                        st.markdown(metric_card(
                            "Lines of Code",
                            raw_metrics.get('loc', 0),
                            "Total number of lines"
                        ), unsafe_allow_html=True)
                        st.markdown(metric_card(
                            "Classes",
                            raw_metrics.get('classes', 0),
                            "Number of classes"
                        ), unsafe_allow_html=True)
                        st.markdown(metric_card(
                            "Methods",
                            raw_metrics.get('methods', 0),
                            "Number of methods"
                        ), unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(metric_card(
                            "Source Lines",
                            raw_metrics.get('sloc', 0),
                            "Actual lines of code"
                        ), unsafe_allow_html=True)
                        st.markdown(metric_card(
                            "Functions",
                            raw_metrics.get('functions', 0),
                            "Number of functions"
                        ), unsafe_allow_html=True)
                        st.markdown(metric_card(
                            "Imports",
                            raw_metrics.get('imports', 0),
                            "Number of imports"
                        ), unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(metric_card(
                            "Comments",
                            raw_metrics.get('comments', 0),
                            "Number of comments"
                        ), unsafe_allow_html=True)
                        st.markdown(metric_card(
                            "Packages",
                            len(st.session_state.current_metrics.get('imported_packages', [])),
                            "Imported packages"
                        ), unsafe_allow_html=True)
                        comment_ratio = raw_metrics.get('comments', 0) / raw_metrics.get('loc', 1) * 100
                        st.markdown(metric_card(
                            "Comment Ratio",
                            f"{comment_ratio:.1f}%",
                            "Comments to code ratio"
                        ), unsafe_allow_html=True)
                    
                    # Display quality metrics with gauges
                    st.markdown("""
                        <div style="margin: 2rem 0;">
                            <h3 style="color: #1E88E5; margin-bottom: 1rem;">🎯 Quality Metrics</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        maintainability = st.session_state.current_metrics.get('maintainability', {}).get('score', 0)
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=maintainability,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            title={'text': "Maintainability Index"},
                            gauge={
                                'axis': {'range': [0, 100]},
                                'bar': {'color': "#1E88E5"},
                                'steps': [
                                    {'range': [0, 50], 'color': "#ef5350"},
                                    {'range': [50, 75], 'color': "#ffb74d"},
                                    {'range': [75, 100], 'color': "#81c784"}
                                ]
                            }
                        ))
                        fig.update_layout(height=250)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        complexity = st.session_state.current_metrics.get('complexity', {}).get('score', 0)
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=complexity,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            title={'text': "Code Quality Score"},
                            gauge={
                                'axis': {'range': [0, 100]},
                                'bar': {'color': "#1E88E5"},
                                'steps': [
                                    {'range': [0, 50], 'color': "#ef5350"},
                                    {'range': [50, 75], 'color': "#ffb74d"},
                                    {'range': [75, 100], 'color': "#81c784"}
                                ]
                            }
                        ))
                        fig.update_layout(height=250)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Display dependencies if available
                    if st.session_state.current_metrics.get('dependencies'):
                        st.markdown("""
                            <div style="margin: 2rem 0;">
                                <h3 style="color: #1E88E5; margin-bottom: 1rem;">
                                    <span style="font-size: 1.5em; margin-right: 0.5rem;">🔗</span> Dependencies
                                </h3>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Organize dependencies by type
                        direct_deps = []
                        indirect_deps = []
                        for dep in st.session_state.current_metrics['dependencies']:
                            if 'direct' in dep.lower():
                                direct_deps.append(dep)
                            else:
                                indirect_deps.append(dep)
                        
                        # Create columns for different dependency types
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("""
                                <div style="
                                    background: white;
                                    padding: 1.5rem;
                                    border-radius: 10px;
                                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                                    margin-bottom: 1rem;
                                ">
                                    <h4 style="color: #1E88E5; font-size: 1.1em; margin-bottom: 1rem;">
                                        📦 Direct Dependencies
                                    </h4>
                                    <div style="
                                        background: #f8f9fa;
                                        padding: 1rem;
                                        border-radius: 8px;
                                        max-height: 300px;
                                        overflow-y: auto;
                                    ">
                            """, unsafe_allow_html=True)
                            
                            if direct_deps:
                                for dep in direct_deps:
                                    st.markdown(f"""
                                        <div style="
                                            background: white;
                                            padding: 0.8rem;
                                            border-radius: 6px;
                                            margin-bottom: 0.5rem;
                                            border: 1px solid #e0e0e0;
                                        ">
                                            <code style="color: #1E88E5;">{dep}</code>
                                        </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.info("No direct dependencies found")
                            
                            st.markdown("</div></div>", unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown("""
                                <div style="
                                    background: white;
                                    padding: 1.5rem;
                                    border-radius: 10px;
                                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                                    margin-bottom: 1rem;
                                ">
                                    <h4 style="color: #1E88E5; font-size: 1.1em; margin-bottom: 1rem;">
                                        🔄 Indirect Dependencies
                                    </h4>
                                    <div style="
                                        background: #f8f9fa;
                                        padding: 1rem;
                                        border-radius: 8px;
                                        max-height: 300px;
                                        overflow-y: auto;
                                    ">
                            """, unsafe_allow_html=True)
                            
                            if indirect_deps:
                                for dep in indirect_deps:
                                    st.markdown(f"""
                                        <div style="
                                            background: white;
                                            padding: 0.8rem;
                                            border-radius: 6px;
                                            margin-bottom: 0.5rem;
                                            border: 1px solid #e0e0e0;
                                        ">
                                            <code style="color: #666;">{dep}</code>
                                        </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.info("No indirect dependencies found")
                            
                            st.markdown("</div></div>", unsafe_allow_html=True)
                        
                        # Add dependency statistics
                        st.markdown("""
                            <div style="
                                background: white;
                                padding: 1.5rem;
                                border-radius: 10px;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                                margin-top: 1rem;
                            ">
                                <h4 style="color: #1E88E5; font-size: 1.1em; margin-bottom: 1rem;">
                                    📊 Dependency Statistics
                                </h4>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Display dependency metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "Total Dependencies",
                                len(direct_deps) + len(indirect_deps),
                                help="Total number of dependencies"
                            )
                        with col2:
                            st.metric(
                                "Direct Dependencies",
                                len(direct_deps),
                                help="Number of direct dependencies"
                            )
                        with col3:
                            st.metric(
                                "Indirect Dependencies",
                                len(indirect_deps),
                                help="Number of indirect dependencies"
                            )
                        
                        # Add dependency graph visualization if available
                        if len(direct_deps) + len(indirect_deps) > 0:
                            st.markdown("""
                                <div style="margin: 2rem 0;">
                                    <h4 style="
                                        color: #1E88E5;
                                        font-size: 1.2em;
                                        margin-bottom: 1rem;
                                        display: flex;
                                        align-items: center;
                                        gap: 0.5rem;
                                    ">
                                        <span style="font-size: 1.2em;">🌳</span>
                                        Dependency Tree
                                    </h4>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Display direct dependencies
                            st.markdown("""
                                <div style="
                                    background: white;
                                    padding: 1.5rem;
                                    border-radius: 12px;
                                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                                ">
                                    <div style="
                                        background: #f8f9fa;
                                        padding: 1.2rem;
                                        border-radius: 8px;
                                        max-height: 400px;
                                        overflow-y: auto;
                                    ">
                            """, unsafe_allow_html=True)

                            # Direct Dependencies Section
                            st.markdown("""
                                <div style="
                                    padding: 0.5rem;
                                    margin-bottom: 1rem;
                                    border-radius: 6px;
                                    background: rgba(30, 136, 229, 0.1);
                                    border-left: 3px solid #1E88E5;
                                ">
                                    <span style="color: #1E88E5; font-size: 0.9em;">
                                        📦 Direct Dependencies ({})
                                    </span>
                                </div>
                            """.format(len(direct_deps)), unsafe_allow_html=True)

                            # Display direct dependencies
                            for dep in direct_deps:
                                st.markdown(f"""
                                    <div style="
                                        padding: 0.8rem;
                                        margin: 0.4rem 0;
                                        background: white;
                                        border-radius: 8px;
                                        border-left: 3px solid #1E88E5;
                                        transition: all 0.2s ease;
                                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                                        display: flex;
                                        align-items: center;
                                    "
                                    onmouseover="this.style.transform='translateX(5px)';this.style.boxShadow='0 2px 5px rgba(0,0,0,0.15)';"
                                    onmouseout="this.style.transform='translateX(0)';this.style.boxShadow='0 1px 3px rgba(0,0,0,0.1)';"
                                    >
                                        <span style="margin-right: 8px; font-size: 1.1em; color: #1E88E5;">📦</span>
                                        <code style="color: #1E88E5; font-size: 0.95em; font-weight: 500;">{dep}</code>
                                    </div>
                                """, unsafe_allow_html=True)

                            # Indirect Dependencies Section
                            st.markdown("""
                                <div style="
                                    padding: 0.5rem;
                                    margin: 1.5rem 0 1rem 0;
                                    border-radius: 6px;
                                    background: rgba(102, 102, 102, 0.1);
                                    border-left: 3px solid #666;
                                ">
                                    <span style="color: #666; font-size: 0.9em;">
                                        🔄 Indirect Dependencies ({})
                                    </span>
                                </div>
                            """.format(len(indirect_deps)), unsafe_allow_html=True)

                            # Display indirect dependencies
                            for dep in indirect_deps:
                                st.markdown(f"""
                                    <div style="
                                        padding: 0.8rem;
                                        margin: 0.4rem 0;
                                        background: white;
                                        border-radius: 8px;
                                        border-left: 3px solid #666;
                                        margin-left: 25px;
                                        transition: all 0.2s ease;
                                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                                        display: flex;
                                        align-items: center;
                                    "
                                    onmouseover="this.style.transform='translateX(5px)';this.style.boxShadow='0 2px 5px rgba(0,0,0,0.15)';"
                                    onmouseout="this.style.transform='translateX(0)';this.style.boxShadow='0 1px 3px rgba(0,0,0,0.1)';"
                                    >
                                        <span style="margin-right: 8px; font-size: 1.1em; color: #666;">↳</span>
                                        <code style="color: #666; font-size: 0.95em; font-weight: 400;">{dep}</code>
                                    </div>
                                """, unsafe_allow_html=True)

                            st.markdown("</div></div>", unsafe_allow_html=True)
                else:
                    st.info("No dependencies data available for this file.")
            
            with issues_tab:
                if st.session_state.current_metrics:
                    st.markdown("""
                        <div style="margin-bottom: 2rem;">
                            <h3 style="color: #1E88E5;">⚠️ Code Issues</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Create expandable sections for different types of issues
                    complexity_issues = st.session_state.current_metrics.get('complexity', {}).get('issues', [])
                    maintainability_issues = st.session_state.current_metrics.get('maintainability', {}).get('issues', [])
                    code_smells = st.session_state.current_metrics.get('code_smells', [])
                    
                    if complexity_issues:
                        with st.expander("Complexity Issues", expanded=True):
                            for issue in complexity_issues:
                                st.warning(issue)
                    
                    if maintainability_issues:
                        with st.expander("Maintainability Issues", expanded=True):
                            for issue in maintainability_issues:
                                st.warning(issue)
                    
                    if code_smells:
                        with st.expander("Code Smells", expanded=True):
                            for smell in code_smells:
                                st.error(smell)
                    
                    if not any([complexity_issues, maintainability_issues, code_smells]):
                        st.success("✨ No significant issues detected in this file.")
                else:
                    st.info("No issues data available for this file.")
            
            with refactoring_tab:
                if st.session_state.current_metrics:
                    st.markdown("""
                        <div style="margin-bottom: 2rem;">
                            <h3 style="color: #1E88E5;">Refactoring Opportunities</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    opportunities = st.session_state.current_metrics.get('refactoring_opportunities', [])
                    if opportunities:
                        for opportunity in opportunities:
                            st.info(opportunity)
                        
                        if st.button("🚀 Generate Detailed Refactoring Plan", use_container_width=True):
                            st.markdown("#### Suggested Refactoring Steps")
                            for i, opportunity in enumerate(opportunities, 1):
                                with st.expander(f"Step {i}: {opportunity[:50]}...", expanded=True):
                                    st.markdown(f"**Description:** {opportunity}")
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.markdown("**Impact:** Medium")
                                    with col2:
                                        st.markdown("**Effort:** Medium")
                                    with col3:
                                        st.markdown("**Priority:** High")
                    else:
                        st.success("✨ No immediate refactoring opportunities identified.")
                else:
                    st.info("No refactoring data available for this file.")
            
            with charts_tab:
                if st.session_state.current_metrics:
                    st.markdown("""
                        <div style="margin-bottom: 2rem;">
                            <h3 style="color: #1E88E5;">📈 Interactive Analysis</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Chart type selector
                    chart_type = st.selectbox(
                        "Select Visualization Type",
                        ["Code Composition", "Quality Metrics", "Time Series", "Dependencies", "Custom Analysis"],
                        key="chart_type_selector"
                    )
                    
                    if chart_type == "Code Composition":
                        # Interactive pie chart for code composition
                        raw_metrics = st.session_state.current_metrics.get('raw_metrics', {})
                        comments = raw_metrics.get('comments', 0) + raw_metrics.get('multi', 0)
                        
                        composition_data = {
                            'Category': ['Source Lines', 'Comments', 'Blank Lines', 'Classes', 'Functions', 'Methods'],
                            'Count': [
                                raw_metrics.get('sloc', 0),
                                comments,
                                raw_metrics.get('blank', 0),
                                raw_metrics.get('classes', 0),
                                raw_metrics.get('functions', 0),
                                raw_metrics.get('methods', 0)
                            ]
                        }
                        df_composition = pd.DataFrame(composition_data)
                        
                        # Add interactivity options
                        chart_style = st.radio(
                            "Chart Style",
                            ["Pie", "Bar", "Treemap"],
                            horizontal=True
                        )
                        
                        if chart_style == "Pie":
                            fig = px.pie(
                                df_composition,
                                values='Count',
                                names='Category',
                                title='Code Composition Analysis',
                                color_discrete_sequence=px.colors.qualitative.Set3
                            )
                        elif chart_style == "Bar":
                            fig = px.bar(
                                df_composition,
                                x='Category',
                                y='Count',
                                title='Code Composition Analysis',
                                color='Category',
                                color_discrete_sequence=px.colors.qualitative.Set3
                            )
                        else:  # Treemap
                            fig = px.treemap(
                                df_composition,
                                path=['Category'],
                                values='Count',
                                title='Code Composition Analysis',
                                color='Count',
                                color_continuous_scale='RdBu'
                            )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Add interactive data table
                        st.dataframe(
                            df_composition,
                            column_config={
                                "Category": "Metric",
                                "Count": st.column_config.NumberColumn(
                                    "Value",
                                    help="Number of occurrences",
                                    format="%d"
                                )
                            },
                            hide_index=True
                        )
                    
                    elif chart_type == "Quality Metrics":
                        # Quality metrics visualization
                        maintainability = st.session_state.current_metrics.get('maintainability', {}).get('score', 0)
                        complexity = st.session_state.current_metrics.get('complexity', {}).get('score', 0)
                        
                        # Add metric selection
                        selected_metrics = st.multiselect(
                            "Select Metrics to Display",
                            ["Maintainability", "Complexity", "Comment Ratio"],
                            default=["Maintainability", "Complexity"]
                        )
                        
                        # Create radar chart data
                        metrics_data = {
                            'Metric': selected_metrics,
                            'Score': [
                                maintainability if "Maintainability" in selected_metrics else None,
                                complexity if "Complexity" in selected_metrics else None,
                                float(raw_metrics.get('comments', 0)) / raw_metrics.get('loc', 1) * 100 if "Comment Ratio" in selected_metrics else None
                            ]
                        }
                        metrics_df = pd.DataFrame(metrics_data)
                        metrics_df = metrics_df.dropna()
                        
                        # Create radar chart
                        fig = go.Figure()
                        fig.add_trace(go.Scatterpolar(
                            r=metrics_df['Score'],
                            theta=metrics_df['Metric'],
                            fill='toself',
                            name='Current File'
                        ))
                        
                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 100]
                                )
                            ),
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif chart_type == "Dependencies":
                        # Dependencies visualization
                        if st.session_state.current_metrics.get('dependencies'):
                            direct_deps = []
                            indirect_deps = []
                            for dep in st.session_state.current_metrics['dependencies']:
                                if 'direct' in dep.lower():
                                    direct_deps.append(dep)
                                else:
                                    indirect_deps.append(dep)
                            
                            # Create Sankey diagram
                            labels = ['Current File'] + direct_deps + indirect_deps
                            source = ([0] * len(direct_deps) +
                                    list(range(1, len(direct_deps) + 1)) * (len(indirect_deps) // len(direct_deps)))
                            target = (list(range(1, len(direct_deps) + 1)) +
                                    list(range(len(direct_deps) + 1, len(labels))))
                            value = [1] * len(source)
                            
                            fig = go.Figure(data=[go.Sankey(
                                node=dict(
                                    pad=15,
                                    thickness=20,
                                    line=dict(color="black", width=0.5),
                                    label=labels,
                                    color="blue"
                                ),
                                link=dict(
                                    source=source,
                                    target=target,
                                    value=value
                                )
                            )])
                            
                            fig.update_layout(title_text="Dependency Flow", font_size=10)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No dependencies data available for visualization")
                    
                    elif chart_type == "Time Series":
                        # Time series analysis of code changes
                        dates = pd.date_range(end=pd.Timestamp.now(), periods=10, freq='D')
                        metrics = ['Complexity', 'Maintainability', 'Lines of Code']
                        
                        # Create sample time series data
                        time_series_data = {
                            'Date': dates,
                            'Complexity': np.random.normal(complexity, 5, 10),
                            'Maintainability': np.random.normal(maintainability, 5, 10),
                            'Lines of Code': np.random.normal(raw_metrics.get('loc', 100), 10, 10)
                        }
                        df_time = pd.DataFrame(time_series_data)
                        
                        # Add metric selector
                        selected_metric = st.selectbox(
                            "Select Metric to Track",
                            metrics
                        )
                        
                        # Create line chart
                        fig = px.line(
                            df_time,
                            x='Date',
                            y=selected_metric,
                            title=f'{selected_metric} Over Time',
                            markers=True
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif chart_type == "Custom Analysis":
                        # Custom analysis options
                        st.markdown("### Create Your Own Analysis")
                        
                        # Get available metrics
                        available_metrics = {
                            'Lines of Code': raw_metrics.get('loc', 0),
                            'Comments': comments,
                            'Functions': raw_metrics.get('functions', 0),
                            'Classes': raw_metrics.get('classes', 0),
                            'Methods': raw_metrics.get('methods', 0),
                            'Complexity': complexity,
                            'Maintainability': maintainability
                        }
                        
                        # Let user select metrics to compare
                        x_axis = st.selectbox("Select X-Axis Metric", list(available_metrics.keys()))
                        y_axis = st.selectbox("Select Y-Axis Metric", list(available_metrics.keys()))
                        
                        # Create scatter plot
                        custom_data = {
                            'x': [available_metrics[x_axis]],
                            'y': [available_metrics[y_axis]]
                        }
                        
                        fig = px.scatter(
                            custom_data,
                            x='x',
                            y='y',
                            title=f'{y_axis} vs {x_axis}',
                            labels={'x': x_axis, 'y': y_axis}
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Add correlation analysis
                        if st.checkbox("Show Correlation Analysis"):
                            correlation = np.corrcoef([available_metrics[x_axis]], [available_metrics[y_axis]])[0, 1]
                            st.metric("Correlation Coefficient", f"{correlation:.2f}")
                else:
                    st.info("Please select a file to view interactive charts.")
            
            with smells_tab:
                if st.session_state.current_file and st.session_state.current_code:
                    st.markdown("""
                        <div style="margin-bottom: 2rem;">
                            <h3 style="color: #1E88E5;">🔍 Code Smell Analysis</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Analyze the current file for smells
                    if st.button("Analyze Code Smells", type="primary", use_container_width=True, key="analyze_smells_btn"):
                        with st.spinner("Analyzing code smells..."):
                            try:
                                smells = st.session_state.smell_analyzer.analyze_file(
                                    st.session_state.current_file,
                                    st.session_state.current_code
                                )
                                st.session_state.smells = smells
                                
                                if not smells:
                                    st.success("No code smells detected in this file!")
                            except Exception as e:
                                st.error(f"Error analyzing code smells: {str(e)}")
                                st.session_state.smells = []
                    
                    if st.session_state.smells:
                        # Display smell statistics
                        stats = st.session_state.smell_analyzer.get_smell_statistics(st.session_state.smells)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Smells", stats['total_smells'])
                        with col2:
                            st.metric("Code Smells", stats['by_type'].get('code_smells', 0))
                        with col3:
                            st.metric("Design Smells", stats['by_type'].get('design_smells', 0))
                        
                        # Create tabs for different smell types
                        smell_type_tabs = st.tabs(["Code Smells", "Design Smells", "Architectural Smells"])
                        
                        with smell_type_tabs[0]:
                            code_smells = [s for s in st.session_state.smells if s.type == SmellType.CODE_SMELL]
                            if code_smells:
                                for smell in code_smells:
                                    with st.expander(f"🔴 {smell.name} - {smell.severity.value}", expanded=True):
                                        st.markdown(f"**Location:** {smell.location}")
                                        st.markdown(f"**Description:** {smell.description}")
                                        if smell.metrics:
                                            st.markdown("**Metrics:**")
                                            for metric, value in smell.metrics.items():
                                                st.markdown(f"- {metric}: {value}")
                                        if smell.recommendations:
                                            st.markdown("**Recommendations:**")
                                            for rec in smell.recommendations:
                                                st.markdown(f"- {rec}")
                            else:
                                st.success("No code smells detected!")
                        
                        with smell_type_tabs[1]:
                            design_smells = [s for s in st.session_state.smells if s.type == SmellType.DESIGN_SMELL]
                            if design_smells:
                                for smell in design_smells:
                                    with st.expander(f"🔴 {smell.name} - {smell.severity.value}", expanded=True):
                                        st.markdown(f"**Location:** {smell.location}")
                                        st.markdown(f"**Description:** {smell.description}")
                                        if smell.metrics:
                                            st.markdown("**Metrics:**")
                                            for metric, value in smell.metrics.items():
                                                st.markdown(f"- {metric}: {value}")
                                        if smell.recommendations:
                                            st.markdown("**Recommendations:**")
                                            for rec in smell.recommendations:
                                                st.markdown(f"- {rec}")
                            else:
                                st.success("No design smells detected!")
                        
                        with smell_type_tabs[2]:
                            arch_smells = [s for s in st.session_state.smells if s.type == SmellType.ARCHITECTURAL_SMELL]
                            if arch_smells:
                                for smell in arch_smells:
                                    with st.expander(f"🔴 {smell.name} - {smell.severity.value}", expanded=True):
                                        st.markdown(f"**Location:** {smell.location}")
                                        st.markdown(f"**Description:** {smell.description}")
                                        if smell.metrics:
                                            st.markdown("**Metrics:**")
                                            for metric, value in smell.metrics.items():
                                                st.markdown(f"- {metric}: {value}")
                                        if smell.recommendations:
                                            st.markdown("**Recommendations:**")
                                            for rec in smell.recommendations:
                                                st.markdown(f"- {rec}")
                            else:
                                st.success("No architectural smells detected!")
                        
                        if len(st.session_state.smells) > 0:
                            # Add visualization of smell distribution
                            st.markdown("### Smell Distribution")
                            smell_data = {
                                'Type': ['Code Smells', 'Design Smells', 'Architectural Smells'],
                                'Count': [
                                    stats['by_type'].get('code_smells', 0),
                                    stats['by_type'].get('design_smells', 0),
                                    stats['by_type'].get('architectural_smells', 0)
                                ]
                            }
                            df_smells = pd.DataFrame(smell_data)
                            
                            fig = px.pie(
                                df_smells,
                                values='Count',
                                names='Type',
                                title='Distribution of Smells by Type',
                                color_discrete_sequence=px.colors.qualitative.Set3
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Add severity distribution
                            st.markdown("### Severity Distribution")
                            severity_data = {
                                'Severity': ['Low', 'Medium', 'High', 'Critical'],
                                'Count': [
                                    stats['by_severity'].get('low', 0),
                                    stats['by_severity'].get('medium', 0),
                                    stats['by_severity'].get('high', 0),
                                    stats['by_severity'].get('critical', 0)
                                ]
                            }
                            df_severity = pd.DataFrame(severity_data)
                            
                            fig = px.bar(
                                df_severity,
                                x='Severity',
                                y='Count',
                                title='Distribution of Smells by Severity',
                                color='Severity',
                                color_discrete_sequence=['#4CAF50', '#FFC107', '#FF5722', '#F44336']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Please select a file to analyze code smells.")
        else:
            # Display welcome message when no file is selected
            st.markdown("""
                <div style="
                    text-align: center;
                    padding: 3rem;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                ">
                    <h3 style="color: #1E88E5; margin-bottom: 1rem;">👈 Select a file to view its contents and analysis</h3>
                    <p style="color: #666;">
                        Choose a file from the file explorer on the left to view its code, metrics, and analysis.
                    </p>
                </div>
            """, unsafe_allow_html=True)

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
            if st.session_state.file_filter and st.session_state.file_filter.lower() not in file_name.lower():
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
        if st.session_state.file_filter and st.session_state.file_filter.lower() not in file_name.lower():
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
        if st.session_state.file_filter and st.session_state.file_filter.lower() not in file_name.lower():
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
    highlighted_code = code.replace(term, f'<span style="background-color: yellow; font-weight: bold;">{term}</span>')
    
    return highlighted_code

if __name__ == "__main__":
    main() 