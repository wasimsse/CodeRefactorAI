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
from code_analyzer import CodeAnalyzer
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
    
    st.title("🔄 RefactoringAI")
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
        st.markdown("""
            <style>
            .file-explorer {
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 2rem;
                border-radius: 20px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }
            .file-tree {
                background: white;
                padding: 1.5rem;
                border-radius: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                border: 1px solid #e0e0e0;
            }
            .file-button {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 0.8rem 1rem;
                margin: 0.5rem 0;
                width: 100%;
                text-align: left;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            .file-button:hover {
                background: #f8f9fa;
                border-color: #1E88E5;
                transform: translateX(5px);
            }
            .file-button.active {
                background: #e3f2fd;
                border-color: #1E88E5;
                color: #1E88E5;
            }
            .content-viewer {
                background: white;
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                border: 1px solid #e0e0e0;
            }
            .metric-card {
                background: white;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                border: 1px solid #e0e0e0;
                margin-bottom: 1rem;
            }
            .metric-title {
                color: #1E88E5;
                font-size: 1.1em;
                font-weight: 500;
                margin-bottom: 1rem;
            }
            .metric-value {
                font-size: 1.8em;
                font-weight: 600;
                color: #424242;
                margin-bottom: 0.5rem;
            }
            .metric-label {
                color: #666;
                font-size: 0.9em;
            }
            .tab-content {
                background: white;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                border: 1px solid #e0e0e0;
            }
            .issue-card {
                background: white;
                padding: 1.2rem;
                border-radius: 8px;
                margin: 0.5rem 0;
                border-left: 4px solid #1E88E5;
            }
            .issue-card.warning {
                border-left-color: #ffa726;
            }
            .issue-card.error {
                border-left-color: #ef5350;
            }
            .issue-card.info {
                border-left-color: #42a5f5;
            }
            </style>
        """, unsafe_allow_html=True)

        if st.session_state.uploaded_files:
            # Create columns for file explorer
            explorer_col, content_col = st.columns([1, 3])
            
            with explorer_col:
                st.markdown("""
                    <div class="file-tree">
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
                
                # Display files grouped by directory
                for dir_path, files in sorted(files_by_dir.items()):
                    if dir_path:
                        with st.expander(f"📁 {os.path.basename(dir_path)}", expanded=True):
                            for file_path in sorted(files):
                                file_name = os.path.basename(file_path)
                                if st.button(f"📄 {file_name}", key=f"file_{file_path}", use_container_width=True):
                                    st.session_state.current_file = file_path
            
            with content_col:
                if st.session_state.current_file:
                    file_name = os.path.basename(st.session_state.current_file)
                    st.markdown(f"""
                        <div class="content-viewer">
                            <h3 style="color: #1E88E5; font-size: 1.4em; margin-bottom: 1.5rem; font-weight: 500;">
                                {file_name}
                            </h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Create tabs for different views
                    code_tab, analysis_tab, metrics_tab, issues_tab = st.tabs([
                        "📝 Source Code",
                        "📊 Analysis",
                        "📈 Metrics",
                        "⚠️ Issues"
                    ])
                    
                    with code_tab:
                        try:
                            with open(st.session_state.current_file, 'r') as f:
                                code_content = f.read()
                                st.code(code_content, language='python')
                        except Exception as e:
                            st.error(f"Error reading file: {str(e)}")
                    
                    with analysis_tab:
                        if st.session_state.current_file in st.session_state.uploaded_files:
                            file_metrics = st.session_state.uploaded_files[st.session_state.current_file]
                            
                            # Display key metrics using Streamlit metrics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric(
                                    "Code Quality",
                                    f"{file_metrics.get('complexity', {}).get('score', 0):.1f}%",
                                    help="Overall quality score"
                                )
                            with col2:
                                st.metric(
                                    "Lines of Code",
                                    file_metrics.get('raw_metrics', {}).get('loc', 0),
                                    help="Total lines of code"
                                )
                            with col3:
                                st.metric(
                                    "Functions",
                                    file_metrics.get('raw_metrics', {}).get('functions', 0),
                                    help="Total number of functions"
                                )
                            with col4:
                                st.metric(
                                    "Classes",
                                    file_metrics.get('raw_metrics', {}).get('classes', 0),
                                    help="Total number of classes"
                                )
                            
                            # Display complexity metrics
                            st.subheader("Complexity Analysis")
                            complexity_data = pd.DataFrame({
                                'Metric': ['Cyclomatic Complexity', 'Cognitive Complexity', 'Maintainability Index'],
                                'Value': [
                                    file_metrics.get('raw_metrics', {}).get('max_complexity', 0),
                                    file_metrics.get('complexity', {}).get('cognitive_complexity', 0),
                                    file_metrics.get('maintainability', {}).get('score', 0)
                                ]
                            })
                            st.dataframe(
                                complexity_data,
                                hide_index=True,
                                use_container_width=True
                            )
                    
                    with metrics_tab:
                        display_metrics_tab(file_metrics)
                    
                    with issues_tab:
                        if st.session_state.current_file in st.session_state.uploaded_files:
                            file_metrics = st.session_state.uploaded_files[st.session_state.current_file]
                            
                            # Display issues using Streamlit's native components
                            code_smells = file_metrics.get('code_smells', [])
                            complexity_issues = file_metrics.get('complexity', {}).get('issues', [])
                            maintainability_issues = file_metrics.get('maintainability', {}).get('issues', [])
                            
                            if code_smells:
                                st.subheader("Code Smells")
                                for smell in code_smells:
                                    st.warning(smell)
                            
                            if complexity_issues:
                                st.subheader("Complexity Issues")
                                for issue in complexity_issues:
                                    st.error(issue)
                            
                            if maintainability_issues:
                                st.subheader("Maintainability Issues")
                                for issue in maintainability_issues:
                                    st.info(issue)
                            
                            if not any([code_smells, complexity_issues, maintainability_issues]):
                                st.success("✅ This file has no significant issues")
                else:
                    st.info("👈 Select a file from the list to view its contents and analysis")
            
            # Project Overview Section
            if st.session_state.project_analysis:
                st.markdown("---")
                st.header("Project Overview")
                
                project_metrics = st.session_state.project_analysis
                
                # Project summary metrics using Streamlit metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(
                        "Total Files",
                        len(st.session_state.uploaded_files),
                        help="Number of analyzed files"
                    )
                with col2:
                    st.metric(
                        "Project Quality",
                        f"{project_metrics.get('complexity', {}).get('score', 0):.1f}%",
                        help="Overall project quality score"
                    )
                with col3:
                    st.metric(
                        "Total Lines",
                        project_metrics.get('raw_metrics', {}).get('loc', 0),
                        help="Total lines of code in project"
                    )
                with col4:
                    st.metric(
                        "Total Issues",
                        len(project_metrics.get('code_smells', [])),
                        help="Number of identified issues"
                    )
                
                # Add project-level visualizations
                st.subheader("Project Metrics")
                
                # Code quality metrics chart
                quality_data = {
                    'Metric': ['Code Quality', 'Maintainability', 'Documentation'],
                    'Score': [
                        project_metrics.get('complexity', {}).get('score', 0),
                        project_metrics.get('maintainability', {}).get('score', 0),
                        project_metrics.get('raw_metrics', {}).get('comment_ratio', 0) * 100
                    ]
                }
                fig = px.bar(
                    quality_data,
                    x='Metric',
                    y='Score',
                    title='Project Quality Metrics',
                    color_discrete_sequence=['#1E88E5'],
                    text='Score'
                )
                fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📁 Upload your Python files in the Upload & Analyze tab to start exploring your code")
    
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
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            analyzer = CodeAnalyzer(config)
            file_metrics = analyzer.analyze_file(str(file_path))
            
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
                            file_metrics = analyzer.analyze_file(str(file_path))
                            st.session_state.uploaded_files[str(file_path)] = file_metrics
                            
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
        st.session_state.refactoring_model = "GPT-4"
    if 'refactoring_goals' not in st.session_state:
        st.session_state.refactoring_goals = []
    if 'refactoring_constraints' not in st.session_state:
        st.session_state.refactoring_constraints = []
    
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
            <h2 style="
                color: white;
                text-align: center;
                margin-bottom: 1rem;
                font-size: 1.8em;
            ">
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
                # Automatically switch to code editor tab
                st.session_state.selected_tab = "✏️ Code Editor"
        
        # Create tabs for different aspects of refactoring
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔍 Analysis & Selection",
            "✏️ Code Editor",
            "🎯 Refactoring Options",
            "👀 Preview & Impact"
        ])
        
        # Display the selected tab content
        if st.session_state.selected_tab == "🔍 Analysis & Selection":
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
                        
                        # Quality metrics
                        st.metric("Maintainability", f"{metrics.get('maintainability', 0):.1f}")
                        st.metric("Complexity", f"{metrics.get('complexity', 0):.1f}")
                        
                        # Code smells
                        smells = metrics.get('code_smells', [])
                        if smells:
                            st.markdown("**Detected Issues:**")
                            for smell in smells:
                                st.warning(smell)
                        else:
                            st.success("No code smells detected")
                        
                        # Language detection
                        file_ext = os.path.splitext(st.session_state.current_file)[1].lower()
                        language = "Unknown"
                        for lang, info in config['supported_languages'].items():
                            if file_ext in info['extensions']:
                                language = info['name']
                                break
                        
                        st.markdown(f"**Language:** {language}")
                        
                        # File size
                        file_size = os.path.getsize(st.session_state.current_file)
                        st.markdown(f"**File Size:** {file_size / 1024:.1f} KB")
                    else:
                        st.info("No metrics available for the selected file.")
        
        elif st.session_state.selected_tab == "✏️ Code Editor":
            with tab2:
                st.markdown("#### Code Editor")
                
                if st.session_state.current_code:
                    # Editor options in a compact format
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        editor_options = st.radio(
                            "Editor Options",
                            ["Syntax Highlighting", "Line Numbers", "Auto-indent"],
                            horizontal=True
                        )
                    with col2:
                        if st.button("💾 Save", use_container_width=True):
                            try:
                                with open(st.session_state.current_file, 'w') as f:
                                    f.write(st.session_state.current_code)
                                st.success("Changes saved successfully!")
                            except Exception as e:
                                st.error(f"Error saving changes: {str(e)}")
                    with col3:
                        if st.button("↺ Reset", use_container_width=True):
                            st.session_state.current_code = st.session_state.uploaded_files[st.session_state.current_file].get('content', '')
                            st.experimental_rerun()
                    
                    # Code editor with session state
                    edited_code = st.text_area(
                        "Edit Code",
                        value=st.session_state.current_code,
                        height=400,
                        key="code_editor"
                    )
                    
                    # Update session state with edited code
                    if edited_code != st.session_state.current_code:
                        st.session_state.current_code = edited_code
                else:
                    st.info("No code available to edit. Please select a file first.")
        
        elif st.session_state.selected_tab == "🎯 Refactoring Options":
            with tab3:
                # Refactoring configuration
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("#### Model Selection")
                    model = st.selectbox(
                        "Select AI Model",
                        ["GPT-4", "Claude", "Local Model"],
                        help="Choose the AI model for refactoring",
                        key="model_selector"
                    )
                    st.session_state.refactoring_model = model
                    
                    st.markdown("#### Scope")
                    scope = st.radio(
                        "Select refactoring scope",
                        ["File", "Function", "Class", "Module"],
                        horizontal=True
                    )
                    
                    st.markdown("#### Primary Goals")
                    goals = st.multiselect(
                        "Select refactoring goals",
                        [
                            "Improve Code Structure",
                            "Enhance Readability",
                            "Reduce Complexity",
                            "Apply SOLID Principles",
                            "Optimize Performance",
                            "Add Documentation",
                            "Fix Code Smells"
                        ],
                        key="goals_selector"
                    )
                    st.session_state.refactoring_goals = goals
                
                with col2:
                    st.markdown("#### Constraints")
                    constraints = st.multiselect(
                        "Select constraints",
                        [
                            "Maintain Backward Compatibility",
                            "Preserve Function Signatures",
                            "Keep Existing Comments",
                            "Follow PEP 8",
                            "Minimize Changes"
                        ],
                        key="constraints_selector"
                    )
                    st.session_state.refactoring_constraints = constraints
                    
                    st.markdown("#### Advanced Settings")
                    with st.expander("Configure Advanced Settings"):
                        st.slider("Max Changes", 0, 100, 50, help="Maximum percentage of code to change")
                        st.slider("Complexity Threshold", 0, 100, 70, help="Maximum allowed complexity")
                        st.checkbox("Preserve Variable Names", value=True)
                        st.checkbox("Add Type Hints", value=False)
                        
                        # Additional advanced options
                        st.markdown("##### Code Style")
                        st.selectbox(
                            "Indentation Style",
                            ["Spaces (4)", "Spaces (2)", "Tabs"],
                            help="Select indentation style for refactored code"
                        )
                        
                        st.selectbox(
                            "Line Length",
                            ["80", "100", "120", "No Limit"],
                            help="Maximum line length for refactored code"
                        )
                        
                        st.checkbox("Sort Imports", value=True, help="Sort import statements")
                        st.checkbox("Remove Unused Imports", value=True, help="Remove unused import statements")
                
                # Generate button at the bottom
                if st.button("Generate Refactoring Suggestions", type="primary", use_container_width=True):
                    if not st.session_state.current_metrics:
                        st.warning("Please select a file to refactor first.")
                    else:
                        with st.spinner("Analyzing code and generating suggestions..."):
                            # Placeholder for actual refactoring suggestions
                            st.session_state.refactoring_suggestions = [
                                {
                                    'title': 'Improve Function Structure',
                                    'description': 'This refactoring improves the structure of the main function by breaking it down into smaller, more focused functions.',
                                    'before': st.session_state.current_code,
                                    'after': st.session_state.current_code.replace('def main():', 'def main():\n    """Main function that orchestrates the application flow."""'),
                                    'impact': {
                                        'complexity_reduction': 15,
                                        'maintainability_improvement': 20,
                                        'lines_changed': 5
                                    }
                                },
                                {
                                    'title': 'Add Type Hints',
                                    'description': 'This refactoring adds type hints to function parameters and return values to improve code readability and enable better static analysis.',
                                    'before': st.session_state.current_code,
                                    'after': st.session_state.current_code.replace('def process_data(data):', 'def process_data(data: Dict[str, Any]) -> Dict[str, Any]:'),
                                    'impact': {
                                        'complexity_reduction': 5,
                                        'maintainability_improvement': 25,
                                        'lines_changed': 3
                                    }
                                }
                            ]
                            st.session_state.selected_tab = "👀 Preview & Impact"
                            st.experimental_rerun()
        
        elif st.session_state.selected_tab == "👀 Preview & Impact":
            with tab4:
                if st.session_state.refactoring_suggestions:
                    for i, suggestion in enumerate(st.session_state.refactoring_suggestions, 1):
                        with st.expander(f"Suggestion {i}: {suggestion['title']}", expanded=True):
                            st.markdown(suggestion['description'])
                            
                            # Before/After comparison
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Before:**")
                                st.code(suggestion['before'], language='python')
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
                            if st.button(f"Apply Suggestion {i}", key=f"apply_{i}"):
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
                    st.info("No refactoring suggestions available. Generate suggestions from the Refactoring Options tab.")
                    if st.button("Go to Refactoring Options", use_container_width=True):
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

def display_metrics_tab(file_metrics):
    """
    Display code metrics in a formatted tab view.
    
    This function creates a visual representation of code metrics including:
    - Basic statistics (lines of code, comments, etc.)
    - Code composition pie chart
    - Quality metrics
    
    All numeric values are properly formatted as strings to avoid Arrow conversion issues.
    
    Args:
        file_metrics: Dictionary containing the analysis results for a file
    """
    if not file_metrics:
        st.info("No metrics available for this file.")
        return
        
    raw_metrics = file_metrics.get('raw_metrics', {})
    
    # Create metrics DataFrame with proper string typing to avoid Arrow conversion issues
    metrics_data = pd.DataFrame({
        'Metric': [
            'Total Lines',
            'Code Lines',
            'Comment Lines',
            'Blank Lines',
            'Average Method Length',
            'Comment Ratio'
        ],
        'Value': [
            str(raw_metrics.get('loc', 0)),
            str(raw_metrics.get('sloc', 0)),
            str(raw_metrics.get('comments', 0) + raw_metrics.get('multi', 0)),
            str(raw_metrics.get('blank', 0)),
            str(raw_metrics.get('average_method_length', 0)),
            f"{raw_metrics.get('comment_ratio', 0) * 100:.1f}%"
        ]
    })
    
    st.dataframe(
        metrics_data,
        hide_index=True,
        use_container_width=True
    )
    
    # Visualize code composition
    st.subheader("Code Composition")
    composition_data = pd.DataFrame({
        'Category': ['Code', 'Comments', 'Blank'],
        'Lines': [
            raw_metrics.get('sloc', 0),
            raw_metrics.get('comments', 0) + raw_metrics.get('multi', 0),
            raw_metrics.get('blank', 0)
        ]
    })
    
    fig = px.pie(
        composition_data,
        values='Lines',
        names='Category',
        title='Code Composition',
        color_discrete_sequence=['#1E88E5', '#43A047', '#FB8C00']
    )
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main() 