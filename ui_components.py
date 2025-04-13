import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from smell_analyzer import SmellType, SmellSeverity

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
        
        if 'selected_code' not in st.session_state:
            st.session_state.selected_code = ""
        if 'selection_start' not in st.session_state:
            st.session_state.selection_start = 0
        if 'selection_end' not in st.session_state:
            st.session_state.selection_end = 0
        
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
            .code-selection {
                background-color: rgba(255, 255, 0, 0.2);
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
        
    def display_header(self, title: str, subtitle: Optional[str] = None, gradient: bool = True):
        """Display a styled header with optional subtitle."""
        if gradient:
            st.markdown(f"""
                <div style="
                    background: linear-gradient(120deg, #1E88E5 0%, #42A5F5 100%);
                    padding: 1.5rem;
                    border-radius: 15px;
                    margin: 1rem 0;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    <h2 style="color: white; text-align: center; margin-bottom: 0.5rem; font-size: 1.8em;">
                        {title}
                    </h2>
                    {f'<p style="color: rgba(255,255,255,0.9); text-align: center; font-size: 1.1em;">{subtitle}</p>' if subtitle else ''}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style="
                    background: white;
                    padding: 1.5rem;
                    border-radius: 15px;
                    margin: 1rem 0;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    <h2 style="color: #1E88E5; text-align: center; margin-bottom: 0.5rem; font-size: 1.8em;">
                        {title}
                    </h2>
                    {f'<p style="color: #666; text-align: center; font-size: 1.1em;">{subtitle}</p>' if subtitle else ''}
                </div>
            """, unsafe_allow_html=True)
        
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
        
    def display_code_viewer(self, allow_selection=True):
        """Display a code viewer with optional selection functionality."""
        code = st.text_area(
            "Enter or paste your code here",
            height=400,
            key="code_input"
        )
        
        if allow_selection and code:
            col1, col2 = st.columns(2)
            with col1:
                selection_start = st.number_input(
                    "Selection Start Line",
                    min_value=1,
                    max_value=len(code.splitlines()),
                    value=1,
                    key="selection_start_input"
                )
            with col2:
                selection_end = st.number_input(
                    "Selection End Line",
                    min_value=selection_start,
                    max_value=len(code.splitlines()),
                    value=selection_start,
                    key="selection_end_input"
                )
            
            # Update session state with selection
            lines = code.splitlines()
            st.session_state.selected_code = "\n".join(
                lines[selection_start-1:selection_end]
            )
            st.session_state.selection_start = selection_start
            st.session_state.selection_end = selection_end
            
            # Preview selection
            with st.expander("Preview Selected Code"):
                st.code(st.session_state.selected_code, language="python")
        
        return code
        
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

    @staticmethod
    def display_metric_card(label: str, value: Any, help_text: str = "", delta: Optional[Any] = None):
        """Display a metric card with optional delta value."""
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
                    {f'<span style="color: {"#4CAF50" if delta > 0 else "#F44336"}; font-size: 0.7em; margin-left: 0.5rem;">{delta:+}</span>' if delta is not None else ''}
                </div>
                <div style="color: #999; font-size: 0.8em; margin-top: 0.5rem;">
                    {help_text}
                </div>
            </div>
        """

    @staticmethod
    def display_file_info(file_path: str, metrics: Dict[str, Any]):
        """Display file information in a card."""
        file_name = file_path.split('/')[-1]
        file_ext = file_name.split('.')[-1] if '.' in file_name else ''
        file_size = metrics.get('file_size', 0) / 1024  # Convert to KB
        
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
                        <strong>Type:</strong> {metrics.get('language', 'unknown').upper()}
                    </div>
                    <div>
                        <strong>Size:</strong> {file_size:.1f} KB
                    </div>
                    <div>
                        <strong>Last Modified:</strong> {datetime.fromtimestamp(metrics.get('last_modified', 0)).strftime('%Y-%m-%d %H:%M')}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def display_metrics_dashboard(metrics: Dict[str, Any], prefix: str = ""):
        """Display a dashboard of code metrics."""
        raw_metrics = metrics.get('raw_metrics', {})
        
        # Create three columns for the metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(UIComponents.display_metric_card(
                "Lines of Code", 
                raw_metrics.get('loc', 0),
                "Total number of lines"
            ), unsafe_allow_html=True)
            st.markdown(UIComponents.display_metric_card(
                "Classes", 
                raw_metrics.get('classes', 0),
                "Number of classes"
            ), unsafe_allow_html=True)
            st.markdown(UIComponents.display_metric_card(
                "Methods", 
                raw_metrics.get('methods', 0),
                "Number of methods"
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(UIComponents.display_metric_card(
                "Source Lines", 
                raw_metrics.get('sloc', 0),
                "Actual lines of code"
            ), unsafe_allow_html=True)
            st.markdown(UIComponents.display_metric_card(
                "Functions", 
                raw_metrics.get('functions', 0),
                "Number of functions"
            ), unsafe_allow_html=True)
            st.markdown(UIComponents.display_metric_card(
                "Imports", 
                raw_metrics.get('imports', 0),
                "Number of imports"
            ), unsafe_allow_html=True)
        
        with col3:
            comments = raw_metrics.get('comments', 0) + raw_metrics.get('multi', 0)
            st.markdown(UIComponents.display_metric_card(
                "Comments", 
                comments,
                "Number of comments"
            ), unsafe_allow_html=True)
            st.markdown(UIComponents.display_metric_card(
                "Packages", 
                len(metrics.get('imported_packages', [])),
                "Imported packages"
            ), unsafe_allow_html=True)
            comment_ratio = (comments / raw_metrics.get('loc', 1)) * 100 if raw_metrics.get('loc', 0) > 0 else 0
            st.markdown(UIComponents.display_metric_card(
                "Comment Ratio", 
                f"{comment_ratio:.1f}%",
                "Comments to code ratio"
            ), unsafe_allow_html=True)
    
    @staticmethod
    def display_quality_metrics(metrics: Dict[str, Any]):
        """Display quality metrics with gauges."""
        maintainability = metrics.get('maintainability', {}).get('score', 0)
        complexity = metrics.get('complexity', {}).get('score', 0)
        
        col1, col2 = st.columns(2)
        with col1:
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
    
    @staticmethod
    def display_code_composition(metrics: Dict[str, Any]):
        """Display code composition chart."""
        raw_metrics = metrics.get('raw_metrics', {})
        comments = raw_metrics.get('comments', 0) + raw_metrics.get('multi', 0)
        
        composition_data = {
            'Category': ['Source Lines', 'Comments', 'Blank Lines'],
            'Lines': [
                raw_metrics.get('sloc', 0),
                comments,
                raw_metrics.get('blank', 0)
            ]
        }
        composition_df = pd.DataFrame(composition_data)
        
        fig = px.bar(
            composition_df,
            x='Category',
            y='Lines',
            title='Code Composition',
            color='Category',
            color_discrete_sequence=['#1f77b4', '#2ca02c', '#d62728']
        )
        fig.update_layout(
            showlegend=True,
            plot_bgcolor='white',
            yaxis_title="Number of Lines",
            xaxis_title=""
        )
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def display_issues(metrics: Dict[str, Any]):
        """Display code issues and smells."""
        complexity_issues = metrics.get('complexity', {}).get('issues', [])
        maintainability_issues = metrics.get('maintainability', {}).get('issues', [])
        code_smells = metrics.get('code_smells', [])
        
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
    
    @staticmethod
    def display_smell_analysis(smells: List[Any]):
        """Display code smell analysis results."""
        if not smells:
            st.success("No code smells detected in this file!")
            return
        
        # Display smell statistics
        stats = {
            'total_smells': len(smells),
            'by_type': {
                'code_smells': len([s for s in smells if s.type == SmellType.CODE_SMELL]),
                'design_smells': len([s for s in smells if s.type == SmellType.DESIGN_SMELL]),
                'architectural_smells': len([s for s in smells if s.type == SmellType.ARCHITECTURAL_SMELL])
            },
            'by_severity': {
                'low': len([s for s in smells if s.severity == SmellSeverity.LOW]),
                'medium': len([s for s in smells if s.severity == SmellSeverity.MEDIUM]),
                'high': len([s for s in smells if s.severity == SmellSeverity.HIGH]),
                'critical': len([s for s in smells if s.severity == SmellSeverity.CRITICAL])
            }
        }
        
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
            code_smells = [s for s in smells if s.type == SmellType.CODE_SMELL]
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
            design_smells = [s for s in smells if s.type == SmellType.DESIGN_SMELL]
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
            arch_smells = [s for s in smells if s.type == SmellType.ARCHITECTURAL_SMELL]
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
    
    @staticmethod
    def display_refactoring_options(file_path: str, metrics: Dict[str, Any]):
        """Display refactoring options for a file."""
        st.markdown("""
            <div style="margin-bottom: 2rem;">
                <h3 style="color: #1E88E5;">Refactoring Opportunities</h3>
            </div>
        """, unsafe_allow_html=True)
        
        opportunities = metrics.get('refactoring_opportunities', [])
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
    
    @staticmethod
    def display_file_explorer(files_by_dir: Dict[str, List[str]], on_file_select=None):
        """Display a file explorer interface."""
        # Filter options
        with st.expander("🔍 Search & Filter", expanded=False):
            file_filter = st.text_input(
                "Search files",
                placeholder="Filter by filename...",
                help="Type to filter files by name"
            )
            
            file_types = ["all", "python", "java", "javascript", "html", "css", "json", "yaml", "markdown", "text"]
            file_type_filter = st.selectbox(
                "File Type",
                file_types,
                index=0,
                help="Filter by file type"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                sort_by = st.selectbox(
                    "Sort By",
                    ["name", "size", "modified", "type"],
                    index=0,
                    help="Sort files by"
                )
            with col2:
                sort_order = st.selectbox(
                    "Order",
                    ["asc", "desc"],
                    index=0,
                    help="Sort order"
                )
            
            view_mode = st.radio(
                "View Mode",
                ["tree", "list", "grid"],
                index=0,
                horizontal=True,
                help="Select view mode"
            )
        
        # Filter files based on search term and file type
        filtered_files_by_dir = {}
        for dir_path, files in files_by_dir.items():
            filtered_files = []
            for file_path in files:
                file_name = file_path.split('/')[-1]
                file_ext = file_name.split('.')[-1] if '.' in file_name else ''
                
                # Apply filters
                if file_filter and file_filter.lower() not in file_name.lower():
                    continue
                    
                if file_type_filter != "all":
                    if file_type_filter == "python" and file_ext != "py":
                        continue
                    elif file_type_filter == "java" and file_ext != "java":
                        continue
                    elif file_type_filter == "javascript" and file_ext not in ["js", "jsx", "ts", "tsx"]:
                        continue
                    elif file_type_filter == "html" and file_ext not in ["html", "htm"]:
                        continue
                    elif file_type_filter == "css" and file_ext != "css":
                        continue
                    elif file_type_filter == "json" and file_ext != "json":
                        continue
                    elif file_type_filter == "yaml" and file_ext not in ["yaml", "yml"]:
                        continue
                    elif file_type_filter == "markdown" and file_ext not in ["md", "markdown"]:
                        continue
                    elif file_type_filter == "text" and file_ext not in ["txt", "text"]:
                        continue
                
                filtered_files.append(file_path)
            
            if filtered_files:
                filtered_files_by_dir[dir_path] = filtered_files
        
        # Sort directories
        sorted_dirs = sorted(filtered_files_by_dir.keys())
        
        # Display files based on selected view mode
        if view_mode == "tree":
            UIComponents._display_tree_view(sorted_dirs, filtered_files_by_dir, sort_by, sort_order, on_file_select)
        elif view_mode == "list":
            UIComponents._display_list_view(sorted_dirs, filtered_files_by_dir, sort_by, sort_order, on_file_select)
        else:  # grid view
            UIComponents._display_grid_view(sorted_dirs, filtered_files_by_dir, sort_by, sort_order, on_file_select)
    
    @staticmethod
    def _display_tree_view(dirs: List[str], files_by_dir: Dict[str, List[str]], sort_by: str, sort_order: str, on_file_select=None):
        """Display files in tree view."""
        for dir_path in dirs:
            files = files_by_dir[dir_path]
            
            # Sort files based on selected criteria
            if sort_by == "name":
                files.sort(key=lambda x: x.split('/')[-1].lower())
            elif sort_by == "size":
                files.sort(key=lambda x: 0)  # Placeholder for actual file size
            elif sort_by == "modified":
                files.sort(key=lambda x: 0)  # Placeholder for actual modification time
            elif sort_by == "type":
                files.sort(key=lambda x: x.split('.')[-1].lower() if '.' in x else '')
            
            # Apply sort order
            if sort_order == "desc":
                files.reverse()
            
            dir_name = dir_path.split('/')[-1] if dir_path else "Root"
            
            with st.expander(f"📁 {dir_name}", expanded=True):
                for file_path in files:
                    file_name = file_path.split('/')[-1]
                    file_ext = file_name.split('.')[-1] if '.' in file_name else ''
                    
                    # Get appropriate icon based on file extension
                    icon = UIComponents._get_file_icon(file_ext)
                    
                    if st.button(
                        f"{icon} {file_name}",
                        key=f"file_{file_path}",
                        help=f"Click to view {file_name}",
                        use_container_width=True
                    ):
                        if on_file_select:
                            on_file_select(file_path)
    
    @staticmethod
    def _display_list_view(dirs: List[str], files_by_dir: Dict[str, List[str]], sort_by: str, sort_order: str, on_file_select=None):
        """Display files in list view."""
        # Flatten the directory structure for list view
        all_files = []
        for dir_path, files in files_by_dir.items():
            for file_path in files:
                all_files.append((dir_path, file_path))
        
        # Sort files based on selected criteria
        if sort_by == "name":
            all_files.sort(key=lambda x: x[1].split('/')[-1].lower())
        elif sort_by == "size":
            all_files.sort(key=lambda x: 0)  # Placeholder for actual file size
        elif sort_by == "modified":
            all_files.sort(key=lambda x: 0)  # Placeholder for actual modification time
        elif sort_by == "type":
            all_files.sort(key=lambda x: x[1].split('.')[-1].lower() if '.' in x[1] else '')
        
        # Apply sort order
        if sort_order == "desc":
            all_files.reverse()
        
        # Display files in list view
        for dir_path, file_path in all_files:
            file_name = file_path.split('/')[-1]
            file_ext = file_name.split('.')[-1] if '.' in file_name else ''
            
            # Get appropriate icon based on file extension
            icon = UIComponents._get_file_icon(file_ext)
            
            # Display file path and name
            dir_name = dir_path.split('/')[-1] if dir_path else "Root"
            if st.button(
                f"{icon} {dir_name}/{file_name}",
                key=f"file_{file_path}",
                help=f"Click to view {file_name}",
                use_container_width=True
            ):
                if on_file_select:
                    on_file_select(file_path)
    
    @staticmethod
    def _display_grid_view(dirs: List[str], files_by_dir: Dict[str, List[str]], sort_by: str, sort_order: str, on_file_select=None):
        """Display files in grid view."""
        # Flatten the directory structure for grid view
        all_files = []
        for dir_path, files in files_by_dir.items():
            for file_path in files:
                all_files.append((dir_path, file_path))
        
        # Sort files based on selected criteria
        if sort_by == "name":
            all_files.sort(key=lambda x: x[1].split('/')[-1].lower())
        elif sort_by == "size":
            all_files.sort(key=lambda x: 0)  # Placeholder for actual file size
        elif sort_by == "modified":
            all_files.sort(key=lambda x: 0)  # Placeholder for actual modification time
        elif sort_by == "type":
            all_files.sort(key=lambda x: x[1].split('.')[-1].lower() if '.' in x[1] else '')
        
        # Apply sort order
        if sort_order == "desc":
            all_files.reverse()
        
        # Display files in grid view
        cols = st.columns(3)
        for i, (dir_path, file_path) in enumerate(all_files):
            file_name = file_path.split('/')[-1]
            file_ext = file_name.split('.')[-1] if '.' in file_name else ''
            
            # Get appropriate icon based on file extension
            icon = UIComponents._get_file_icon(file_ext)
            
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
                            {dir_path.split('/')[-1] if dir_path else "Root"}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button(
                    "View File",
                    key=f"file_{file_path}",
                    help=f"Click to view {file_name}",
                    use_container_width=True
                ):
                    if on_file_select:
                        on_file_select(file_path)
    
    @staticmethod
    def _get_file_icon(file_ext: str) -> str:
        """Get appropriate icon based on file extension."""
        icon = "📄"
        if file_ext in ['py']:
            icon = "🐍"
        elif file_ext in ['js', 'jsx', 'ts', 'tsx']:
            icon = "⚡"
        elif file_ext in ['html', 'css']:
            icon = "🌐"
        elif file_ext in ['json', 'yaml', 'yml']:
            icon = "⚙️"
        elif file_ext in ['md', 'txt']:
            icon = "📝"
        elif file_ext in ['java']:
            icon = "☕"
        elif file_ext in ['cpp', 'c', 'h', 'hpp']:
            icon = "⚙️"
        elif file_ext in ['cs']:
            icon = "💠"
        elif file_ext in ['go']:
            icon = "🔵"
        elif file_ext in ['rb']:
            icon = "💎"
        elif file_ext in ['php']:
            icon = "🐘"
        elif file_ext in ['swift']:
            icon = "🍎"
        elif file_ext in ['kt', 'kts']:
            icon = "📱"
        return icon 