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
from refactoring_ui import render_refactoring_interface

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
        # Options: all, python, java, javascript, etc.
        st.session_state.file_type_filter = "all"
    if 'recent_files' not in st.session_state:
        st.session_state.recent_files = []

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
            file_types = [
                "all",
                "python",
                "java",
                "javascript",
                "html",
                "css",
                "json",
                "yaml",
                "markdown",
                "text"]
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
                    "Sort By", [
                        "name", "size", "modified", "type"], index=[
                        "name", "size", "modified", "type"].index(
                        st.session_state.sort_by), help="Sort files by")
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
            code_tab, metrics_tab, issues_tab, refactoring_tab = st.tabs([
                "📝 Source Code",
                "📊 Metrics",
                "⚠️ Issues",
                "🔄 Refactoring"
            ])

            with code_tab:
                if st.session_state.current_code:
                    # Code actions toolbar
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        if st.button("📋 Copy Code", use_container_width=True):
                            st.toast("Code copied to clipboard!", icon="✅")
                    with col2:
                        if st.button(
                            "🔍 Find in Code",
                                use_container_width=True):
                            st.session_state.show_find = True
                    with col3:
                        if st.button("📝 Edit Code", use_container_width=True):
                            st.session_state.edit_mode = True

                    # Find in code functionality
                    if st.session_state.get('show_find', False):
                        find_term = st.text_input(
                            "Search in code", key="find_term")
                        if find_term:
                            # Highlight search term in code
                            highlighted_code = highlight_search_term(
                                st.session_state.current_code, find_term)
                            st.markdown(f"""
                                <div class="code-viewer">
                                    <pre><code>{highlighted_code}</code></pre>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Display code with syntax highlighting
                            st.code(
                                st.session_state.current_code,
                                language=st.session_state.current_metrics.get(
                                    'language',
                                    'python'))
                    else:
                        # Display code with syntax highlighting
                        st.code(
                            st.session_state.current_code,
                            language=st.session_state.current_metrics.get(
                                'language',
                                'python'))
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
                                <h3 style="color: #1E88E5; margin-bottom: 1rem;">🔗 Dependencies</h3>
                            </div>
                        """, unsafe_allow_html=True)

                        for dep in st.session_state.current_metrics['dependencies']:
                            st.code(dep, language="plaintext")
                else:
                    st.info("No metrics data available for this file.")

            with issues_tab:
                if st.session_state.current_metrics:
                    st.markdown("""
                        <div style="margin-bottom: 2rem;">
                            <h3 style="color: #1E88E5;">⚠️ Code Issues</h3>
                        </div>
                    """, unsafe_allow_html=True)

                    # Create expandable sections for different types of issues
                    complexity_issues = st.session_state.current_metrics.get(
                        'complexity', {}).get('issues', [])
                    maintainability_issues = st.session_state.current_metrics.get(
                        'maintainability', {}).get('issues', [])
                    code_smells = st.session_state.current_metrics.get(
                        'code_smells', [])

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

                    if not any(
                            [complexity_issues, maintainability_issues, code_smells]):
                        st.success(
                            "✨ No significant issues detected in this file.")
                else:
                    st.info("No issues data available for this file.")

            with refactoring_tab:
                if st.session_state.current_metrics:
                    st.markdown("""
                        <div style="margin-bottom: 2rem;">
                            <h3 style="color: #1E88E5;">🔄 Refactoring Opportunities</h3>
                        </div>
                    """, unsafe_allow_html=True)

                    opportunities = st.session_state.current_metrics.get(
                        'refactoring_opportunities', [])
                    if opportunities:
                        for opportunity in opportunities:
                            st.info(opportunity)

                        if st.button(
                            "🚀 Generate Detailed Refactoring Plan",
                                use_container_width=True):
                            st.markdown("#### Suggested Refactoring Steps")
                            for i, opportunity in enumerate(opportunities, 1):
                                with st.expander(f"Step {i}: {opportunity[:50]}...", expanded=True):
                                    st.markdown(
                                        f"**Description:** {opportunity}")
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.markdown("**Impact:** Medium")
                                    with col2:
                                        st.markdown("**Effort:** Medium")
                                    with col3:
                                        st.markdown("**Priority:** High")
                    else:
                        st.success(
                            "✨ No immediate refactoring opportunities identified.")
                else:
                    st.info("No refactoring data available for this file.")
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


def display_analysis_tab():
    """Display code analysis results and metrics."""
    if not st.session_state.current_file:
        st.warning("Please select a file to analyze.")
        return
    
    # Get current file metrics
    metrics = st.session_state.uploaded_files.get(st.session_state.current_file, {})
    
    # Create columns for different metric categories
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Code Metrics")
        
        # Basic metrics
        raw_metrics = metrics.get('raw_metrics', {})
        st.metric("Lines of Code", raw_metrics.get('loc', 0))
        st.metric("Source Lines of Code", raw_metrics.get('sloc', 0))
        st.metric("Comment Lines", raw_metrics.get('comments', 0))
        st.metric("Functions", raw_metrics.get('functions', 0))
        st.metric("Classes", raw_metrics.get('classes', 0))
        
        # Display complexity score
        complexity = metrics.get('complexity', {})
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=complexity.get('score', 0),
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Code Complexity"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#1E88E5"},
                'steps': [
                    {'range': [0, 30], 'color': "#81c784"},
                    {'range': [30, 70], 'color': "#ffb74d"},
                    {'range': [70, 100], 'color': "#e57373"}
                ]
            }
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 Quality Indicators")
        
        # Display maintainability score
        maintainability = metrics.get('maintainability', {})
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=maintainability.get('score', 0),
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Maintainability"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#1E88E5"},
                'steps': [
                    {'range': [0, 30], 'color': "#e57373"},
                    {'range': [30, 70], 'color': "#ffb74d"},
                    {'range': [70, 100], 'color': "#81c784"}
                ]
            }
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    # Display code smells and issues
    st.markdown("### ⚠️ Code Smells and Issues")
    code_smells = metrics.get('code_smells', [])
    if code_smells:
        for smell in code_smells:
            st.warning(smell)
    else:
        st.success("No code smells detected! 🎉")
    
    # Display improvement suggestions
    st.markdown("### 💡 Improvement Suggestions")
    suggestions = metrics.get('refactoring_opportunities', [])
    if suggestions:
        for suggestion in suggestions:
            st.info(suggestion)
    else:
        st.success("No immediate improvements needed! 🌟")


def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()
    
    # Display header with gradient background
    st.markdown("""
        <div style="
            background: linear-gradient(120deg, #1E88E5 0%, #42A5F5 100%);
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            <h1 style="
                color: white;
                text-align: center;
                margin-bottom: 1rem;
                font-size: 2.5em;
            ">
                Code Refactoring Assistant
            </h1>
            <p style="
                color: white;
                text-align: center;
                font-size: 1.2em;
                margin-bottom: 0;
            ">
                Enhance your code quality with AI-powered refactoring suggestions
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # If no files are uploaded yet, show the landing page
    if 'uploaded_files' not in st.session_state or not st.session_state.uploaded_files:
        # Tool features section
        st.markdown("### 🚀 Features")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
                #### 📊 Code Analysis
                - Complexity metrics
                - Quality assessment
                - Code smell detection
                - Language detection
            """)
        
        with col2:
            st.markdown("""
                #### 🔄 Smart Refactoring
                - AI-powered suggestions
                - Multiple refactoring goals
                - Impact analysis
                - Preview changes
            """)
        
        with col3:
            st.markdown("""
                #### 🛠️ Developer Tools
                - Code editor
                - File explorer
                - Version tracking
                - Refactoring history
            """)
        
        st.markdown("---")
        
        # Upload section
        st.markdown("### 📁 Upload Your Code")
        st.write("Choose one of the following options to get started:")
        
        # File upload options in columns
        upload_col1, upload_col2, upload_col3 = st.columns([1, 1, 1])
        
        with upload_col1:
            st.markdown("#### Single File")
            uploaded_file = st.file_uploader("Upload a file", type=None, key="single_file")
            if uploaded_file:
                handle_file_upload(uploaded_file)
                st.rerun()
        
        with upload_col2:
            st.markdown("#### Project Archive")
            uploaded_zip = st.file_uploader("Upload ZIP", type=["zip"], key="zip_file")
            if uploaded_zip:
                handle_zip_upload(uploaded_zip)
                st.rerun()
        
        with upload_col3:
            st.markdown("#### GitHub Repository")
            repo_url = st.text_input("Enter repository URL")
            if repo_url and st.button("Fetch Repository"):
                handle_github_upload(repo_url)
                st.rerun()
    
    # If files are uploaded, show the analysis and tabs
    else:
        # Quick stats
        total_files = len(st.session_state.uploaded_files)
        total_lines = sum(len(file.get('content', '').splitlines()) for file in st.session_state.uploaded_files.values())
        
        # Display project stats
        st.markdown("### 📊 Project Overview")
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            st.metric("Total Files", total_files)
        with stat_col2:
            st.metric("Total Lines", total_lines)
        with stat_col3:
            st.metric("Languages", len(set(f.split('.')[-1] for f in st.session_state.uploaded_files.keys())))
        with stat_col4:
            st.metric("Analysis Status", "Complete" if total_files > 0 else "Pending")
        
        st.markdown("---")
        
        # Create main tabs
        tab1, tab2, tab3 = st.tabs([
            "📁 File Explorer",
            "🔍 Code Analysis",
            "♻️ Refactoring"
        ])
        
        # File Explorer tab
        with tab1:
            display_file_explorer()
        
        # Code Analysis tab
        with tab2:
            if st.session_state.current_file:
                display_analysis_tab()
            else:
                st.info("Select a file from the File Explorer to view analysis.")
        
        # Refactoring tab
        with tab3:
            if st.session_state.current_file:
                render_refactoring_interface()
            else:
                st.info("Select a file from the File Explorer to start refactoring.")

if __name__ == "__main__":
    main() 
