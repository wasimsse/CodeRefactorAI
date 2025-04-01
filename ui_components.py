import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

class UIComponents:
    def __init__(self):
        """Initialize UI components."""
        self.setup_custom_css()
        self.theme = {
            'primary_color': '#1f77b4',
            'secondary_color': '#ff7f0e',
            'background_color': '#f8f9fa',
            'text_color': '#2c3e50'
        }
        
    def setup_custom_css(self):
        """Set up custom CSS styles."""
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
                background-color: white;
                padding: 1rem;
                border-radius: 0.5rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin: 0.5rem;
            }
            .progress-bar {
                height: 10px;
                background-color: #f0f2f6;
                border-radius: 5px;
                overflow: hidden;
            }
            .progress-fill {
                height: 100%;
                background-color: #1f77b4;
                transition: width 0.3s ease-in-out;
            }
            </style>
        """, unsafe_allow_html=True)
        
    def display_header(self):
        """Display the application header."""
        st.title("🔄 RefactoringAI")
        st.markdown("""
            ### AI-Powered Code Refactoring Tool
            Upload your code and let AI help you improve its quality, maintainability, and performance.
        """)
        
    def display_upload_section(self):
        """Display the file upload section."""
        st.header("Upload Your Code")
        upload_method = st.radio(
            "Choose upload method:",
            ["Single File", "ZIP Archive", "GitHub Repository"]
        )
        return upload_method
        
    def display_file_explorer(self, project_structure: Dict[str, List[str]], selected_file: Optional[str] = None):
        """Display the file explorer interface."""
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Files")
            for dir_path, files in project_structure.items():
                with st.expander(dir_path or "Root"):
                    for file_name in files:
                        if st.button(file_name, key=f"file_{file_name}"):
                            selected_file = file_name
                            
        with col2:
            if selected_file:
                st.subheader(f"File: {selected_file}")
                return selected_file
                
        return selected_file
        
    def display_code_viewer(self, code: str, language: str):
        """Display code with syntax highlighting."""
        try:
            from pygments import highlight
            from pygments.lexers import get_lexer_by_name
            from pygments.formatters import HtmlFormatter
            
            lexer = get_lexer_by_name(language)
            formatter = HtmlFormatter(style='monokai')
            highlighted = highlight(code, lexer, formatter)
            
            st.markdown(f'<div class="code-viewer">{highlighted}</div>', unsafe_allow_html=True)
        except:
            st.code(code)
            
    def display_analysis_results(self, results: Dict):
        """Display code analysis results."""
        st.header("Analysis Results")
        
        # Create columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self._display_metric_card(
                "Complexity",
                results.get('complexity', {}).get('score', 0),
                results.get('complexity', {}).get('issues', [])
            )
            
        with col2:
            self._display_metric_card(
                "Maintainability",
                results.get('maintainability', {}).get('score', 0),
                results.get('maintainability', {}).get('issues', [])
            )
            
        with col3:
            self._display_metric_card(
                "Code Smells",
                len(results.get('code_smells', [])),
                results.get('code_smells', [])
            )
            
        with col4:
            self._display_metric_card(
                "Performance",
                results.get('performance', {}).get('score', 0),
                results.get('performance', {}).get('issues', [])
            )
            
        # Display detailed issues
        st.subheader("Detailed Issues")
        self._display_issues_table(results)
        
    def _display_metric_card(self, title: str, value: float, issues: List[str]):
        """Display a metric card with value and issues."""
        st.markdown(f"""
            <div class="metric-card">
                <h3>{title}</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {value}%"></div>
                </div>
                <p>{value:.1f}/100</p>
            </div>
        """, unsafe_allow_html=True)
        
        if issues:
            with st.expander("Issues"):
                for issue in issues:
                    st.warning(issue)
                    
    def _display_issues_table(self, results: Dict):
        """Display issues in a table format."""
        issues_data = []
        
        # Collect all issues
        for category, data in results.items():
            if isinstance(data, dict) and 'issues' in data:
                for issue in data['issues']:
                    issues_data.append({
                        'Category': category,
                        'Issue': issue
                    })
                    
        if issues_data:
            df = pd.DataFrame(issues_data)
            st.dataframe(df)
        else:
            st.info("No issues found.")
            
    def display_refactoring_options(self):
        """Display refactoring options interface."""
        st.header("Refactoring Options")
        
        # Model selection
        col1, col2 = st.columns(2)
        
        with col1:
            model_provider = st.selectbox(
                "Select AI Model Provider",
                ["OpenAI", "Anthropic", "Google", "Cohere"]
            )
            
        with col2:
            model = st.selectbox(
                "Select Model",
                ["gpt-4", "gpt-3.5-turbo", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "gemini-pro", "command"]
            )
            
        # Refactoring options
        st.subheader("Refactoring Options")
        options = {
            'improve_structure': st.checkbox("Improve code structure"),
            'add_documentation': st.checkbox("Add proper documentation"),
            'error_handling': st.checkbox("Implement error handling"),
            'solid_principles': st.checkbox("Apply SOLID principles")
        }
        
        return model_provider, model, options
        
    def display_refactoring_progress(self, progress: float):
        """Display refactoring progress."""
        st.progress(progress)
        
    def display_refactoring_results(self, original_code: str, refactored_code: str):
        """Display refactoring results with diff view."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Original Code")
            self.display_code_viewer(original_code, "python")
            
        with col2:
            st.subheader("Refactored Code")
            self.display_code_viewer(refactored_code, "python")
            
    def display_error(self, error_message: str):
        """Display error message."""
        st.error(error_message)
        
    def display_success(self, message: str):
        """Display success message."""
        st.success(message)
        
    def display_warning(self, message: str):
        """Display warning message."""
        st.warning(message)
        
    def display_info(self, message: str):
        """Display info message."""
        st.info(message)
        
    def display_metrics_chart(self, metrics_history: List[Dict]):
        """Display metrics history chart."""
        if not metrics_history:
            return
            
        df = pd.DataFrame(metrics_history)
        
        fig = go.Figure()
        
        for column in df.columns:
            if column != 'timestamp':
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df[column],
                    name=column,
                    mode='lines+markers'
                ))
                
        fig.update_layout(
            title="Metrics History",
            xaxis_title="Time",
            yaxis_title="Score",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig)
        
    def display_file_tree(self, project_structure: Dict[str, List[str]]):
        """Display project structure as a tree."""
        def create_tree_data(structure: Dict[str, List[str]], parent: str = ""):
            nodes = []
            edges = []
            
            for dir_path, files in structure.items():
                dir_name = dir_path.split('/')[-1] if dir_path else "Root"
                node_id = f"{parent}/{dir_name}" if parent else dir_name
                
                nodes.append({
                    'id': node_id,
                    'label': dir_name,
                    'group': 'directory'
                })
                
                if parent:
                    edges.append({
                        'from': parent,
                        'to': node_id
                    })
                    
                for file_name in files:
                    file_id = f"{node_id}/{file_name}"
                    nodes.append({
                        'id': file_id,
                        'label': file_name,
                        'group': 'file'
                    })
                    edges.append({
                        'from': node_id,
                        'to': file_id
                    })
                    
            return nodes, edges
            
        nodes, edges = create_tree_data(project_structure)
        
        fig = go.Figure()
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=[node['id'] for node in nodes],
            y=[node['label'] for node in nodes],
            mode='markers+text',
            marker=dict(
                size=20,
                color=['#1f77b4' if node['group'] == 'directory' else '#ff7f0e' for node in nodes]
            ),
            text=[node['label'] for node in nodes],
            textposition="top center",
            name="Nodes"
        ))
        
        # Add edges
        for edge in edges:
            fig.add_trace(go.Scatter(
                x=[edge['from'], edge['to']],
                y=[edge['from'].split('/')[-1], edge['to'].split('/')[-1]],
                mode='lines',
                line=dict(color='#888888', width=1),
                showlegend=False
            ))
            
        fig.update_layout(
            title="Project Structure",
            showlegend=False,
            hovermode='closest'
        )
        
        st.plotly_chart(fig)

    def render_header(self, title: str, subtitle: Optional[str] = None):
        """Render page header with optional subtitle."""
        st.title(title)
        if subtitle:
            st.markdown(f"*{subtitle}*")
        st.markdown("---")

    def render_file_upload(self, accepted_types: List[str], help_text: str) -> Optional[Any]:
        """Render file upload component."""
        return st.file_uploader(
            "Choose a file",
            type=accepted_types,
            help=help_text
        )

    def render_progress(self, progress: float, text: str):
        """Render progress bar with text."""
        progress_bar = st.progress(0)
        progress_bar.progress(progress)
        st.text(text)

    def render_metrics_card(self, title: str, value: Any, description: str):
        """Render a metrics card."""
        st.markdown(f"""
        <div style="
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        ">
            <h3 style="color: {self.theme['primary_color']};">{title}</h3>
            <h2 style="margin: 0.5rem 0;">{value}</h2>
            <p style="color: {self.theme['text_color']};">{description}</p>
        </div>
        """, unsafe_allow_html=True)

    def render_code_viewer(self, code: str, language: str):
        """Render code viewer with syntax highlighting."""
        st.code(code, language=language)

    def render_file_tree(self, files: List[str]) -> Optional[str]:
        """Render file tree for selection."""
        if not files:
            st.info("No files available.")
            return None

        return st.selectbox(
            "Select a file",
            files,
            format_func=lambda x: Path(x).name
        )

    def render_options_panel(self, options: Dict[str, bool]) -> Dict[str, bool]:
        """Render options panel with checkboxes."""
        return {
            key: st.checkbox(key.replace('_', ' ').title(), value=default)
            for key, default in options.items()
        }

    def render_model_selector(self, models: List[str], default_index: int = 0) -> str:
        """Render AI model selector."""
        return st.selectbox(
            "Select AI Model",
            models,
            index=default_index,
            help="Choose the AI model for code refactoring"
        )

    def render_alert(self, message: str, type: str = "info"):
        """Render alert message."""
        if type == "info":
            st.info(message)
        elif type == "success":
            st.success(message)
        elif type == "warning":
            st.warning(message)
        elif type == "error":
            st.error(message)

    def render_tabs(self, tabs: List[str]) -> List[Any]:
        """Render tabs."""
        return st.tabs(tabs)

    def render_sidebar_section(self, title: str):
        """Render sidebar section with title."""
        st.sidebar.markdown(f"### {title}")

    def apply_custom_css(self):
        """Apply custom CSS styling."""
        st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stButton>button {
            width: 100%;
            margin-top: 1rem;
            background-color: #1f77b4;
            color: white;
        }
        .stButton>button:hover {
            background-color: #2c3e50;
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