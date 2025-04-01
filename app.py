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

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="RefactoringAI",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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

# Initialize configuration
config = {
    'max_line_length': 100,
    'max_function_length': 50,
    'max_complexity': 10,
    'min_comment_ratio': 0.1
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

        # Upload section with improved styling
        st.markdown("""
            <div style='margin: 2rem 0;'>
                <h2 style='color: #1E88E5; font-size: 1.8em; margin-bottom: 1rem; font-weight: 500;'>
                    Start Your Analysis
                </h2>
                <p style='color: #666; margin-bottom: 2rem; font-size: 1.1em;'>
                    Choose your preferred method to analyze your code
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Create three columns for upload methods with improved styling
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
                <div class="feature-card">
                    <div style='text-align: center; margin-bottom: 1.5rem;'>
                        <span style='font-size: 3.5em; color: #1E88E5;'>📄</span>
                    </div>
                    <h3 style='color: #1E88E5; margin-bottom: 1rem; text-align: center; font-size: 1.3em;'>
                        Single File
                    </h3>
                    <p style='color: #666; margin-bottom: 1.5rem; text-align: center; font-size: 0.95em; line-height: 1.5;'>
                        Quick analysis of individual Python files with instant feedback and recommendations
                    </p>
                    <div style='background-color: #f8f9fa; padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem;'>
                        <p style='color: #666; font-size: 0.9em; margin-bottom: 0.5rem;'>✓ Instant analysis</p>
                        <p style='color: #666; font-size: 0.9em; margin-bottom: 0.5rem;'>✓ Detailed metrics</p>
                        <p style='color: #666; font-size: 0.9em;'>✓ Quick recommendations</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Choose a Python file", type=['py'], key="single_file")
            if uploaded_file:
                with st.spinner("🔍 Analyzing your code..."):
                    if handle_file_upload(uploaded_file):
                        st.markdown("""
                            <div style='background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
                                      padding: 1rem; border-radius: 10px; margin-top: 1rem; text-align: center;
                                      box-shadow: 0 2px 4px rgba(46,125,50,0.1);'>
                                <p style='color: #2e7d32; margin: 0; font-weight: 500; font-size: 1.1em;'>
                                    ✅ Analysis Complete!
                                </p>
                                <p style='color: #2e7d32; margin: 0.5rem 0 0 0; font-size: 0.9em;'>
                                    View detailed results in the File Explorer tab →
                                </p>
                            </div>
                        """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
                <div class="feature-card">
                    <div style='text-align: center; margin-bottom: 1.5rem;'>
                        <span style='font-size: 3.5em; color: #1E88E5;'>📦</span>
                    </div>
                    <h3 style='color: #1E88E5; margin-bottom: 1rem; text-align: center; font-size: 1.3em;'>
                        Project Archive
                    </h3>
                    <p style='color: #666; margin-bottom: 1.5rem; text-align: center; font-size: 0.95em; line-height: 1.5;'>
                        Comprehensive analysis of multiple files with project-wide insights
                    </p>
                    <div style='background-color: #f8f9fa; padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem;'>
                        <p style='color: #666; font-size: 0.9em; margin-bottom: 0.5rem;'>✓ Multi-file analysis</p>
                        <p style='color: #666; font-size: 0.9em; margin-bottom: 0.5rem;'>✓ Project overview</p>
                        <p style='color: #666; font-size: 0.9em;'>✓ Dependency scanning</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            uploaded_zip = st.file_uploader("Choose a ZIP file", type=['zip'], key="zip_file")
            if uploaded_zip:
                with st.spinner("📊 Processing your project..."):
                    if handle_zip_upload(uploaded_zip):
                        st.markdown("""
                            <div style='background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
                                      padding: 1rem; border-radius: 10px; margin-top: 1rem; text-align: center;
                                      box-shadow: 0 2px 4px rgba(46,125,50,0.1);'>
                                <p style='color: #2e7d32; margin: 0; font-weight: 500; font-size: 1.1em;'>
                                    ✅ Project Analysis Complete!
                                </p>
                                <p style='color: #2e7d32; margin: 0.5rem 0 0 0; font-size: 0.9em;'>
                                    View project overview in the File Explorer tab →
                                </p>
                            </div>
                        """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
                <div class="feature-card">
                    <div style='text-align: center; margin-bottom: 1.5rem;'>
                        <span style='font-size: 3.5em; color: #1E88E5;'>🔗</span>
                    </div>
                    <h3 style='color: #1E88E5; margin-bottom: 1rem; text-align: center; font-size: 1.3em;'>
                        GitHub Repository
                    </h3>
                    <p style='color: #666; margin-bottom: 1.5rem; text-align: center; font-size: 0.95em; line-height: 1.5;'>
                        Direct analysis from your GitHub repositories with branch support
                    </p>
                    <div style='background-color: #f8f9fa; padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem;'>
                        <p style='color: #666; font-size: 0.9em; margin-bottom: 0.5rem;'>✓ Repository integration</p>
                        <p style='color: #666; font-size: 0.9em; margin-bottom: 0.5rem;'>✓ Branch analysis</p>
                        <p style='color: #666; font-size: 0.9em;'>✓ Commit history review</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            repo_url = st.text_input("Enter repository URL", 
                placeholder="https://github.com/username/repository",
                help="Enter the URL of a public GitHub repository")
            
            col_btn1, col_btn2 = st.columns([2, 3])
            with col_btn2:
                if repo_url:
                    if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
                        with st.spinner("🔍 Cloning and analyzing repository..."):
                            handle_github_upload(repo_url)
                            st.markdown("""
                                <div style='background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
                                          padding: 1rem; border-radius: 10px; margin-top: 1rem; text-align: center;
                                          box-shadow: 0 2px 4px rgba(46,125,50,0.1);'>
                                    <p style='color: #2e7d32; margin: 0; font-weight: 500; font-size: 1.1em;'>
                                        ✅ Repository Analysis Complete!
                                    </p>
                                    <p style='color: #2e7d32; margin: 0.5rem 0 0 0; font-size: 0.9em;'>
                                        View repository analysis in the File Explorer tab →
                                    </p>
                                </div>
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
                        if st.session_state.current_file in st.session_state.uploaded_files:
                            file_metrics = st.session_state.uploaded_files[st.session_state.current_file]
                            raw_metrics = file_metrics.get('raw_metrics', {})
                            
                            # Display raw metrics using Streamlit's native components
                            st.subheader("Code Statistics")
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
                                    raw_metrics.get('loc', 0),
                                    raw_metrics.get('sloc', 0),
                                    raw_metrics.get('comments', 0) + raw_metrics.get('multi', 0),
                                    raw_metrics.get('blank', 0),
                                    raw_metrics.get('average_method_length', 0),
                                    f"{raw_metrics.get('comment_ratio', 0) * 100:.1f}%"
                                ]
                            })
                            st.dataframe(
                                metrics_data,
                                hide_index=True,
                                use_container_width=True
                            )
                            
                            # Add visualizations
                            st.subheader("Code Composition")
                            composition_data = {
                                'Category': ['Code', 'Comments', 'Blank'],
                                'Lines': [
                                    raw_metrics.get('sloc', 0),
                                    raw_metrics.get('comments', 0) + raw_metrics.get('multi', 0),
                                    raw_metrics.get('blank', 0)
                                ]
                            }
                            fig = px.pie(
                                composition_data,
                                values='Lines',
                                names='Category',
                                title='Code Composition',
                                color_discrete_sequence=['#1E88E5', '#43A047', '#FB8C00']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    
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
    """Handle single file upload."""
    if uploaded_file is not None:
        try:
            # Create temp directory if it doesn't exist
            temp_dir = Path("temp_analysis")
            temp_dir.mkdir(exist_ok=True)
            
            # Save uploaded file
            file_path = temp_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Analyze file
            analyzer = CodeAnalyzer(config)
            file_metrics = analyzer.analyze_file(str(file_path))
            
            # Update session state
            st.session_state.uploaded_files = {str(file_path): file_metrics}
            st.session_state.current_file = str(file_path)
            
            # Update statistics after analysis
            st.session_state.stats_manager.update_file_analysis(
                uploaded_file.name,
                file_metrics
            )
            
            return True
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return False

def handle_zip_upload(uploaded_zip):
    """Handle ZIP file upload."""
    if uploaded_zip is not None:
        try:
            # Create temp directory
            temp_dir = Path("temp_analysis")
            temp_dir.mkdir(exist_ok=True)
            
            # Save and extract ZIP file
            zip_path = temp_dir / uploaded_zip.name
            with open(zip_path, "wb") as f:
                f.write(uploaded_zip.getbuffer())
            
            # Extract ZIP contents
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Initialize analyzer with config
            analyzer = CodeAnalyzer(config)
            uploaded_files = {}
            total_metrics = {
                'complexity': {'score': 0, 'issues': []},
                'maintainability': {'score': 0, 'issues': []},
                'code_smells': [],
                'raw_metrics': {
                    'loc': 0, 'lloc': 0, 'sloc': 0,
                    'comments': 0, 'multi': 0, 'blank': 0,
                    'classes': 0, 'functions': 0,
                    'average_method_length': 0,
                    'max_complexity': 0,
                    'comment_ratio': 0
                }
            }
            
            file_count = 0
            
            # Analyze all Python files
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            # Analyze individual file
                            file_metrics = analyzer.analyze_file(file_path)
                            uploaded_files[file_path] = file_metrics
                            
                            # Aggregate metrics for project-level analysis
                            file_count += 1
                            total_metrics['complexity']['score'] += file_metrics.get('complexity', {}).get('score', 0)
                            total_metrics['complexity']['issues'].extend(file_metrics.get('complexity', {}).get('issues', []))
                            total_metrics['maintainability']['score'] += file_metrics.get('maintainability', {}).get('score', 0)
                            total_metrics['maintainability']['issues'].extend(file_metrics.get('maintainability', {}).get('issues', []))
                            total_metrics['code_smells'].extend(file_metrics.get('code_smells', []))
                            
                            # Aggregate raw metrics
                            raw = file_metrics.get('raw_metrics', {})
                            for key in total_metrics['raw_metrics'].keys():
                                if key in raw:
                                    total_metrics['raw_metrics'][key] += raw[key]
                            
                            # Update max complexity
                            total_metrics['raw_metrics']['max_complexity'] = max(
                                total_metrics['raw_metrics']['max_complexity'],
                                raw.get('max_complexity', 0)
                            )
                            
                        except Exception as e:
                            st.warning(f"Error analyzing {file}: {str(e)}")
            
            # Calculate averages for project-level metrics
            if file_count > 0:
                total_metrics['complexity']['score'] /= file_count
                total_metrics['maintainability']['score'] /= file_count
                total_metrics['raw_metrics']['average_method_length'] = (
                    total_metrics['raw_metrics']['average_method_length'] / file_count
                )
                total_metrics['raw_metrics']['comment_ratio'] = (
                    (total_metrics['raw_metrics']['comments'] + total_metrics['raw_metrics']['multi']) /
                    total_metrics['raw_metrics']['loc'] if total_metrics['raw_metrics']['loc'] > 0 else 0
                )
            
            # Update session state
            st.session_state.uploaded_files = uploaded_files
            st.session_state.project_analysis = total_metrics
            
            # Update statistics
            st.session_state.stats_manager.update_project_analysis()
            for file_path, metrics in uploaded_files.items():
                st.session_state.stats_manager.update_file_analysis(file_path, metrics)
            
            return True
            
        except Exception as e:
            st.error(f"Error processing ZIP file: {str(e)}")
            return False

def handle_github_upload(repo_url):
    """Handle GitHub repository upload."""
    clear_analysis_state()  # This will also clean up the upload directory
    
    try:
        # Create a unique directory for this repository
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_dir = config.UPLOAD_DIR / f"{repo_name}_{os.urandom(6).hex()}"
        
        # Clone the repository
        git.Repo.clone_from(repo_url, repo_dir)
        
        # Only process supported file types
        supported_extensions = {'.py', '.java', '.cpp', '.js', '.cs'}
        for root, _, files in os.walk(repo_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in supported_extensions):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_dir)
                    st.session_state.uploaded_files[rel_path] = file_path
        
        if not st.session_state.uploaded_files:
            st.warning("No supported code files found in the repository.")
            return
        
        # Analyze the project
        with st.spinner("Analyzing project..."):
            st.session_state.project_analysis = st.session_state.project_analyzer.analyze_project(str(repo_dir))
            display_project_analysis()
            
            # Update statistics
            st.session_state.stats_manager.update_project_analysis()
            for file_path, metrics in st.session_state.uploaded_files.items():
                st.session_state.stats_manager.update_file_analysis(file_path, metrics)
    except Exception as e:
        st.error(f"Error cloning repository: {str(e)}")

def display_refactoring_options():
    """Display refactoring options and interface."""
    st.subheader("Refactoring Options")
    
    # Model selection
    model_provider = st.selectbox(
        "Select AI Model Provider",
        ["OpenAI", "Anthropic", "Google", "Cohere"]
    )
    
    model = st.selectbox(
        "Select Model",
        ["gpt-4", "gpt-3.5-turbo", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "gemini-pro", "command"]
    )
    
    # Refactoring options
    st.checkbox("Improve code structure")
    st.checkbox("Add proper documentation")
    st.checkbox("Implement error handling")
    st.checkbox("Apply SOLID principles")
    
    if st.button("Start Refactoring"):
        with st.spinner("Refactoring in progress..."):
            # Placeholder for actual refactoring
            st.success("Refactoring completed!")

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
        <div style='
            background: linear-gradient(120deg, #1E88E5 0%, #42A5F5 100%);
            padding: 2rem;
            border-radius: 20px;
            margin: 2rem 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <h2 style='
                color: white;
                text-align: center;
                margin-bottom: 2rem;
                font-size: 2em;
            '>
                Empowering Better Code Quality
            </h2>
        </div>
    """, unsafe_allow_html=True)
    
    # Display key metrics in a 4-column layout
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div style='text-align: center;'>
                <h1 style='color: #1E88E5; font-size: 2.5em; margin: 0;'>
                    {}
                </h1>
                <p style='color: #666; font-size: 1.1em;'>Analysis Accuracy</p>
            </div>
        """.format(stats["analysis_accuracy"]), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='text-align: center;'>
                <h1 style='color: #1E88E5; font-size: 2.5em; margin: 0;'>
                    {}
                </h1>
                <p style='color: #666; font-size: 1.1em;'>Code Metrics</p>
            </div>
        """.format(stats["code_metrics"]), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style='text-align: center;'>
                <h1 style='color: #1E88E5; font-size: 2.5em; margin: 0;'>
                    {}
                </h1>
                <p style='color: #666; font-size: 1.1em;'>Projects Analyzed</p>
            </div>
        """.format(stats["projects_analyzed"]), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div style='text-align: center;'>
                <h1 style='color: #1E88E5; font-size: 2.5em; margin: 0;'>
                    {}
                </h1>
                <p style='color: #666; font-size: 1.1em;'>Availability</p>
            </div>
        """.format(stats["availability"]), unsafe_allow_html=True)
    
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
        lang_data = stats["languages"]
        st.bar_chart(lang_data)
    
    # Quality improvements
    st.markdown("### Quality Improvements")
    improvements = stats["improvements"]
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Complexity Reduced", improvements["complexity_reduced"])
    with col2:
        st.metric("Maintainability Improved", improvements["maintainability_improved"])
    with col3:
        st.metric("Bugs Fixed", improvements["bugs_fixed"])

if __name__ == "__main__":
    main() 