import streamlit as st
import os
from typing import Dict, List, Any
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from metrics_calculator import MetricsCalculator

class VisualizationManager:
    def __init__(self):
        """Initialize visualization manager."""
        self.color_scheme = {
            'primary': '#FF4B4B',
            'secondary': '#4B4BFF',
            'tertiary': '#4BFF4B',
            'background': '#FFFFFF',
            'text': '#333333'
        }
        
    def create_quality_metrics_chart(self, metrics_data: dict, chart_id: str = None) -> go.Figure:
        """Create a line chart showing quality metrics over files."""
        try:
            # Handle different input types
            if isinstance(metrics_data, pd.DataFrame):
                df = metrics_data
            elif isinstance(metrics_data, dict):
                # Extract metrics
                if 'quality_metrics' in metrics_data:
                    df = pd.DataFrame(metrics_data['quality_metrics'])
                else:
                    files = []
                    complexity_scores = []
                    maintainability_scores = []
                    
                    for file_path, data in metrics_data.items():
                        files.append(os.path.basename(file_path))
                        if isinstance(data, dict):
                            complexity = data.get('complexity', {}).get('score', 0)
                            maintainability = data.get('maintainability', {}).get('score', 0)
                            
                            # Convert numpy types to native Python types
                            if hasattr(complexity, 'item'):
                                complexity = complexity.item()
                            if hasattr(maintainability, 'item'):
                                maintainability = maintainability.item()
                                
                            complexity_scores.append(float(complexity))
                            maintainability_scores.append(float(maintainability))
                        else:
                            complexity_scores.append(0)
                            maintainability_scores.append(0)
                    
                    df = pd.DataFrame({
                        'Files': files,
                        'Maintainability': maintainability_scores,
                        'Complexity': complexity_scores
                    })
            else:
                raise ValueError("Invalid metrics data format")
            
            # Create figure
            fig = go.Figure()
            
            # Add traces for each metric column (excluding 'Files' if it exists)
            for column in df.columns:
                if column.lower() != 'files':
                    fig.add_trace(go.Scatter(
                        x=df.index if 'Files' not in df.columns else df['Files'],
                        y=df[column],
                        name=column,
                        mode='lines+markers',  # Ensure both lines and markers are shown
                        line=dict(
                            color='#4BFF4B' if 'maintainability' in column.lower() else '#FF4B4B',
                            width=2,
                            shape='linear'  # Use linear interpolation between points
                        ),
                        marker=dict(
                            size=8,
                            symbol='circle'
                        )
                    ))
            
            # Update layout
            fig.update_layout(
                title='Quality Metrics by File',
                xaxis_title='Files',
                yaxis_title='Score',
                yaxis=dict(
                    range=[0, 100],
                    gridcolor='lightgray',
                    zerolinecolor='lightgray'
                ),
                plot_bgcolor='white',
                hovermode='x unified',
                showlegend=True,
                height=400,
                margin=dict(l=50, r=50, t=50, b=50),
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="right",
                    x=0.99
                )
            )
            
            # Rotate x-axis labels for better readability
            fig.update_xaxes(
                tickangle=45,
                gridcolor='lightgray',
                showgrid=True
            )
            
            if chart_id:
                fig.update_layout(title_text=f'Quality Metrics - {chart_id}')
                
            return fig
        except Exception as e:
            print(f"Error creating quality metrics chart: {str(e)}")
            # Return an empty figure with an error message
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False
            )
            return fig
        
    def create_gauge_chart(self, value: float, title: str, chart_id: str = None) -> go.Figure:
        """Create a gauge chart for displaying metrics."""
        # Ensure value is between 0 and 100
        value = max(0, min(100, value))
        
        # Define colors based on value
        if value >= 80:
            color = '#4BFF4B'  # Green
        elif value >= 60:
            color = '#FFB74B'  # Orange
        else:
            color = '#FF4B4B'  # Red
            
        # Create gauge chart
        fig = go.Figure(go.Indicator(
            mode='gauge+number',
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 60], 'color': '#FFE5E5'},
                    {'range': [60, 80], 'color': '#FFF5E5'},
                    {'range': [80, 100], 'color': '#E5FFE5'}
                ],
                'threshold': {
                    'line': {'color': 'black', 'width': 2},
                    'thickness': 0.75,
                    'value': value
                }
            }
        ))
        
        # Update layout
        fig.update_layout(
            title=title,
            height=300,
            margin=dict(l=30, r=30, t=50, b=30)
        )
        
        if chart_id:
            fig.update_layout(title_text=f'{title} - {chart_id}')
            
        return fig
        
    def create_issues_pie_chart(self, issues_data: dict, chart_id: str = None) -> go.Figure:
        """Create a pie chart showing distribution of issues by severity."""
        try:
            # Count issues by severity
            if isinstance(issues_data, dict) and 'issues_by_severity' in issues_data:
                severity_counts = issues_data['issues_by_severity']
            else:
                severity_counts = {
                    'High': len([i for i in issues_data.get('complexity', {}).get('issues', []) if i]),
                    'Medium': len([i for i in issues_data.get('maintainability', {}).get('issues', []) if i]),
                    'Low': len([i for i in issues_data.get('code_smells', []) if i])
                }
            
            # Calculate percentages
            total = sum(severity_counts.values())
            
            # Get overall score if available
            overall_score = 0
            if isinstance(issues_data, dict):
                if 'overall_score' in issues_data:
                    overall_score = float(issues_data['overall_score'])
                elif 'complexity' in issues_data and isinstance(issues_data['complexity'], dict):
                    overall_score = float(issues_data['complexity'].get('score', 0))
            
            # Create chart for no detected issues case
            if total == 0:
                fig = go.Figure()
                
                if overall_score < 60:
                    # Show potential issues message when score is low
                    fig.add_trace(go.Bar(
                        x=['Potential Issues'],
                        y=[1],
                        marker_color='rgba(255, 183, 75, 0.5)',  # Orange, semi-transparent
                        width=[0.3],
                        hoverinfo='skip'
                    ))
                    
                    message = "No specific issues detected, but code quality score indicates room for improvement"
                else:
                    # Show success message when score is good
                    fig.add_trace(go.Bar(
                        x=['Clean Code'],
                        y=[1],
                        marker_color='rgba(75, 255, 75, 0.5)',  # Green, semi-transparent
                        width=[0.3],
                        hoverinfo='skip'
                    ))
                    
                    message = "No issues found - Code appears well-structured"
                
                # Add the message annotation
                fig.add_annotation(
                    text=message,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=14, color='#666666')
                )
                
                # Update layout
                fig.update_layout(
                    title={
                        'text': 'Code Quality Status',
                        'y': 0.95,
                        'x': 0.5,
                        'xanchor': 'center',
                        'yanchor': 'top',
                        'font': dict(size=18)
                    },
                    showlegend=False,
                    height=300,
                    margin=dict(l=30, r=30, t=50, b=30),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    xaxis=dict(
                        showgrid=False,
                        showticklabels=False,
                        zeroline=False
                    ),
                    yaxis=dict(
                        showgrid=False,
                        showticklabels=False,
                        zeroline=False,
                        range=[0, 1]
                    )
                )
                
                return fig
            
            # If there are issues, create the pie chart
            labels = []
            values = []
            colors = []
            
            # Sort severities to ensure consistent order (High -> Medium -> Low)
            for severity in ['High', 'Medium', 'Low']:
                if severity in severity_counts and severity_counts[severity] > 0:
                    labels.append(f"{severity} ({severity_counts[severity]} {'issue' if severity_counts[severity] == 1 else 'issues'})")
                    values.append(severity_counts[severity])
                    colors.append('#FF4B4B' if severity == 'High' else '#FFB74B' if severity == 'Medium' else '#4BFF4B')
            
            # Create pie chart
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                marker=dict(
                    colors=colors,
                    line=dict(color='#FFFFFF', width=2)
                ),
                textinfo='label+percent',
                textposition='outside',
                pull=[0.1 if 'High' in label else 0.05 if 'Medium' in label else 0 for label in labels]
            )])
            
            # Update layout
            fig.update_layout(
                title={
                    'text': 'Issues by Severity',
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(size=18)
                },
                showlegend=False,
                height=300,
                margin=dict(l=30, r=30, t=50, b=30),
                paper_bgcolor='white',
                annotations=[
                    dict(
                        text=f"Total Issues: {total}",
                        x=0.5,
                        y=-0.2,
                        showarrow=False,
                        font=dict(size=14)
                    )
                ]
            )
            
            if chart_id:
                fig.update_layout(title_text=f'Issues by Severity - {chart_id}')
                
            return fig
        except Exception as e:
            print(f"Error creating issues pie chart: {str(e)}")
            # Return an empty figure with an error message
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14, color='#666666')
            )
            return fig
        
    def create_complexity_bar_chart(self, data: dict) -> go.Figure:
        """Create a bar chart for complexity by file."""
        try:
            # Handle different data formats
            complexity_data = {}
            
            if isinstance(data, dict):
                if 'complexity_by_file' in data:
                    # Direct complexity scores format
                    complexity_data = data['complexity_by_file']
                elif 'complexity' in data:
                    # Single file format
                    if isinstance(data['complexity'], dict) and 'score' in data['complexity']:
                        complexity_data = {'Current File': data['complexity']['score']}
                    else:
                        complexity_data = {'Current File': float(data['complexity'])}
                else:
                    # Multiple files format
                    for k, v in data.items():
                        if isinstance(v, dict) and 'complexity' in v:
                            if isinstance(v['complexity'], dict):
                                score = v['complexity'].get('score', 0)
                            else:
                                score = float(v['complexity'])
                            complexity_data[k] = score
                        elif isinstance(v, (int, float)):
                            complexity_data[k] = float(v)
                        else:
                            complexity_data[k] = 0

            # Convert any numpy values to native Python types
            complexity_data = {
                k: float(v.item() if hasattr(v, 'item') else v)
                for k, v in complexity_data.items()
            }

            # Format file names for better display
            formatted_data = {
                os.path.basename(str(k)): v 
                for k, v in complexity_data.items()
            }
            
            # Create DataFrame
            df = pd.DataFrame(list(formatted_data.items()), columns=['File', 'Complexity'])
            
            if df.empty:
                # Return empty chart with message if no data
                fig = go.Figure()
                fig.add_annotation(
                    text="No complexity data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False
                )
                return fig
            
            # Create bar chart
            fig = go.Figure(data=[
                go.Bar(
                    x=df['File'],
                    y=df['Complexity'],
                    marker_color=df['Complexity'].apply(
                        lambda x: '#4BFF4B' if x >= 80 else '#FFB74B' if x >= 60 else '#FF4B4B'
                    )
                )
            ])
            
            # Update layout
            fig.update_layout(
                title='Complexity by File',
                xaxis_title='Files',
                yaxis_title='Complexity Score',
                yaxis=dict(range=[0, 100]),
                showlegend=False,
                height=400,
                margin=dict(l=50, r=50, t=50, b=100),
                xaxis=dict(tickangle=45)
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating complexity bar chart: {str(e)}")
            # Return an empty figure with an error message
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False
            )
            return fig

    def create_metrics_dashboard(self, metrics_data: dict, file_path: str) -> Dict[str, go.Figure]:
        """Create a complete dashboard of metrics visualizations."""
        # Get file name for chart IDs
        file_name = os.path.basename(file_path)
        
        return {
            'quality_score': self.create_gauge_chart(
                metrics_data['complexity']['score'],
                'Code Quality Score',
                file_name
            ),
            'issues_distribution': self.create_issues_pie_chart(
                metrics_data,
                file_name
            ),
            'metrics_comparison': self.create_quality_metrics_chart(
                {file_path: metrics_data},
                file_name
            )
        }

    @staticmethod
    def shorten_path(path: str, max_length: int = 20) -> str:
        """Shorten file path for better display."""
        if len(path) <= max_length:
            return path
        
        parts = path.split(os.sep)
        if len(parts) <= 2:
            return f"...{path[-max_length:]}"
        
        return os.path.join("...", parts[-2], parts[-1])[:max_length] + "..."

    @staticmethod
    def display_project_structure(structure: dict):
        """Display project structure as an interactive tree."""
        st.subheader("Project Structure")
        
        # Display only directories at the root level
        for name, info in structure.items():
            if isinstance(info, dict) and info.get('type') == 'directory':
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"📁 **{name}**")
                with col2:
                    st.caption(f"Files: {info.get('files', 0)}")
                with col3:
                    st.caption(f"Subdirs: {info.get('subdirs', 0)}")
                
                # Show immediate subdirectories without nesting
                if 'children' in info:
                    for subdir, subinfo in info['children'].items():
                        if isinstance(subinfo, dict) and subinfo.get('type') == 'directory':
                            with st.container():
                                subcol1, subcol2, subcol3 = st.columns([3, 1, 1])
                                with subcol1:
                                    st.markdown(f"└─ 📁 {subdir}")
                                with subcol2:
                                    st.caption(f"Files: {subinfo.get('files', 0)}")
                                with subcol3:
                                    st.caption(f"Subdirs: {subinfo.get('subdirs', 0)}")
                st.markdown("---")

    def display_metrics_dashboard(self, metrics: dict):
        """Display a comprehensive metrics dashboard."""
        try:
            st.header("Code Quality Analysis")
            
            # Display quality score gauge
            quality_score = self._calculate_overall_score(metrics)
            gauge_fig = self.create_gauge_chart(quality_score, "Code Quality Score")
            st.plotly_chart(gauge_fig, use_container_width=True)
            
            # Create columns for metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Core Metrics")
                raw_metrics = metrics.get('raw_metrics', {})
                core_metrics = {
                    'Metric': [
                        'File Length',
                        'Classes',
                        'Methods',
                        'Avg Method Length',
                        'Max Complexity',
                        'Comment Ratio (%)'
                    ],
                    'Value': [
                        raw_metrics.get('loc', 0),
                        raw_metrics.get('classes', 0),
                        raw_metrics.get('functions', 0),
                        round(raw_metrics.get('average_method_length', 0), 1),
                        raw_metrics.get('max_complexity', 0),
                        round(raw_metrics.get('comment_ratio', 0) * 100, 1)
                    ]
                }
                df = pd.DataFrame(core_metrics)
                st.dataframe(df.style.format({'Value': '{:.1f}'}))
            
            with col2:
                # Create issues pie chart
                st.subheader("Issues Distribution")
                issues_fig = self.create_issues_pie_chart(metrics)
                st.plotly_chart(issues_fig, use_container_width=True)
            
            # Display complexity analysis
            st.subheader("Complexity Analysis")
            complexity_cols = st.columns(3)
            
            with complexity_cols[0]:
                cyclomatic = raw_metrics.get('max_complexity', 0)
                st.metric("Cyclomatic Complexity", 
                         cyclomatic,
                         delta="normal" if cyclomatic < 10 else "high",
                         delta_color="normal" if cyclomatic < 10 else "inverse")
            
            with complexity_cols[1]:
                cognitive = metrics.get('cognitive_complexity', 0)
                st.metric("Cognitive Complexity",
                         cognitive,
                         delta="normal" if cognitive < 15 else "high",
                         delta_color="normal" if cognitive < 15 else "inverse")
            
            with complexity_cols[2]:
                nesting = metrics.get('max_nesting_depth', 0)
                st.metric("Maximum Nesting Depth",
                         nesting,
                         delta="normal" if nesting < 4 else "high",
                         delta_color="normal" if nesting < 4 else "inverse")
            
            # Display maintainability analysis
            st.subheader("Maintainability Analysis")
            maintainability_fig = self.create_quality_metrics_chart(metrics)
            st.plotly_chart(maintainability_fig, use_container_width=True)
            
            # Display code smells
            st.subheader("Code Quality Issues")
            code_smells = metrics.get('code_smells', [])
            if code_smells:
                issues_df = pd.DataFrame({
                    'Issue': code_smells,
                    'Severity': ['High' if 'complex' in str(smell).lower() or 'nest' in str(smell).lower()
                                else 'Medium' if 'length' in str(smell).lower()
                                else 'Low' for smell in code_smells]
                })
                
                # Group issues by severity
                for severity in ['High', 'Medium', 'Low']:
                    severity_issues = issues_df[issues_df['Severity'] == severity]
                    if not severity_issues.empty:
                        with st.expander(f"{severity} Priority Issues ({len(severity_issues)})", expanded=severity == 'High'):
                            for issue in severity_issues['Issue']:
                                if severity == 'High':
                                    st.error(issue)
                                elif severity == 'Medium':
                                    st.warning(issue)
                                else:
                                    st.info(issue)
            else:
                st.success("No significant code quality issues detected")
            
            # Display recommendations
            if metrics.get('recommendations', []):
                st.subheader("Recommendations")
                for rec in metrics['recommendations']:
                    st.info(rec)
            
        except Exception as e:
            st.error(f"Error displaying metrics dashboard: {str(e)}")
            import traceback
            st.error(f"Detailed error: {traceback.format_exc()}")
            st.info("Please ensure you have uploaded a valid Python file for analysis.")

    def _calculate_overall_score(self, metrics: dict) -> float:
        """Calculate overall code quality score based on metrics."""
        try:
            # Initialize weights for different aspects
            weights = {
                'complexity': 0.3,
                'maintainability': 0.3,
                'structure': 0.2,
                'documentation': 0.2
            }
            
            # Calculate complexity score (0-100)
            max_acceptable_complexity = 10
            complexity_score = 100 * (1 - min(metrics.get('cyclomatic', 0) / max_acceptable_complexity, 1))
            
            # Calculate maintainability score
            maintainability_score = 100 * (1 - min(metrics.get('cognitive', 0) / 15, 1))
            
            # Calculate structure score
            avg_method_length = metrics.get('avg_method_length', 0)
            structure_score = 100 * (1 - min(avg_method_length / 20, 1))
            
            # Calculate documentation score
            documentation_score = metrics.get('comment_ratio', 0)
            
            # Calculate weighted average
            overall_score = (
                weights['complexity'] * complexity_score +
                weights['maintainability'] * maintainability_score +
                weights['structure'] * structure_score +
                weights['documentation'] * documentation_score
            )
            
            return max(0, min(100, overall_score))
        except Exception as e:
            print(f"Error calculating overall score: {str(e)}")
            return 0

    def _display_recommendations(self, metrics: dict):
        """Display actionable recommendations based on metrics."""
        recommendations = []
        
        # Complexity recommendations
        if metrics.get('cyclomatic', 0) > 10:
            recommendations.append(
                "🔄 High cyclomatic complexity detected. Consider breaking down complex methods into smaller, more focused functions."
            )
        
        # Method length recommendations
        if metrics.get('avg_method_length', 0) > 15:
            recommendations.append(
                "📏 Methods are longer than recommended. Aim for methods under 15 lines for better maintainability."
            )
        
        # Nesting recommendations
        if metrics.get('max_depth', 0) > 3:
            recommendations.append(
                "⚠️ Deep nesting detected. Consider extracting nested logic into separate methods or using early returns."
            )
        
        # Documentation recommendations
        if metrics.get('comment_ratio', 0) < 10:
            recommendations.append(
                "📝 Low comment ratio. Consider adding more documentation for complex logic and public interfaces."
            )
        
        # Display recommendations
        for rec in recommendations:
            st.info(rec)

    def create_code_smells_treemap(self, code_smells: list) -> go.Figure:
        """Create a treemap visualization of code smells."""
        try:
            if not code_smells:
                return None

            # Create hierarchical data structure
            data = {
                'High': {
                    'Long Method': [],
                    'Complex Code': [],
                    'Deep Nesting': [],
                    'Large Class': [],
                    'Duplicate Code': []
                },
                'Medium': {
                    'Parameter Issues': [],
                    'Naming Issues': [],
                    'Code Organization': []
                },
                'Low': {
                    'Style Issues': [],
                    'Documentation': [],
                    'Minor Issues': []
                }
            }

            # Categorize code smells
            for smell in code_smells:
                smell_lower = str(smell).lower()
                if any(x in smell_lower for x in ['long method', 'function too long']):
                    data['High']['Long Method'].append(smell)
                elif any(x in smell_lower for x in ['complex', 'cyclomatic']):
                    data['High']['Complex Code'].append(smell)
                elif 'nest' in smell_lower:
                    data['High']['Deep Nesting'].append(smell)
                elif 'class' in smell_lower:
                    data['High']['Large Class'].append(smell)
                elif 'duplicate' in smell_lower:
                    data['High']['Duplicate Code'].append(smell)
                elif 'parameter' in smell_lower:
                    data['Medium']['Parameter Issues'].append(smell)
                elif any(x in smell_lower for x in ['name', 'naming']):
                    data['Medium']['Naming Issues'].append(smell)
                elif any(x in smell_lower for x in ['organization', 'structure']):
                    data['Medium']['Code Organization'].append(smell)
                elif any(x in smell_lower for x in ['style', 'format']):
                    data['Low']['Style Issues'].append(smell)
                elif any(x in smell_lower for x in ['doc', 'comment']):
                    data['Low']['Documentation'].append(smell)
                else:
                    data['Low']['Minor Issues'].append(smell)

            # Prepare data for treemap
            labels = []
            parents = []
            values = []
            colors = []

            color_map = {
                'High': '#FF4B4B',    # Red
                'Medium': '#FFB74B',  # Orange
                'Low': '#4BFF4B'     # Green
            }

            # Add root
            labels.append('All Issues')
            parents.append('')
            values.append(sum(len(items) for severity in data.values() for items in severity.values()))
            colors.append('#FFFFFF')

            # Add severity levels and categories
            for severity, categories in data.items():
                labels.append(severity)
                parents.append('All Issues')
                values.append(sum(len(items) for items in categories.values()))
                colors.append(color_map[severity])

                for category, items in categories.items():
                    if items:  # Only add categories with issues
                        labels.append(category)
                        parents.append(severity)
                        values.append(len(items))
                        colors.append(color_map[severity])

            # Create treemap
            fig = go.Figure(go.Treemap(
                labels=labels,
                parents=parents,
                values=values,
                marker=dict(colors=colors),
                textinfo="label+value",
                hovertemplate='<b>%{label}</b><br>Issues: %{value}<extra></extra>'
            ))

            fig.update_layout(
                title='Code Smells Distribution',
                width=800,
                height=500
            )

            return fig
        except Exception as e:
            print(f"Error creating code smells treemap: {str(e)}")
            return None

    def display_code_smells_matrix(self, code_smells: list):
        """Display code smells in a matrix format with severity and impact."""
        try:
            if not code_smells:
                st.info("No code smells detected.")
                return

            # Create matrix data
            matrix_data = {
                'High Impact': {
                    'High Frequency': [],
                    'Medium Frequency': [],
                    'Low Frequency': []
                },
                'Medium Impact': {
                    'High Frequency': [],
                    'Medium Frequency': [],
                    'Low Frequency': []
                },
                'Low Impact': {
                    'High Frequency': [],
                    'Medium Frequency': [],
                    'Low Frequency': []
                }
            }

            # Categorize smells by impact and frequency
            for smell in code_smells:
                smell_lower = str(smell).lower()
                
                # Determine impact
                if any(x in smell_lower for x in ['complex', 'nest', 'duplicate', 'long method']):
                    impact = 'High Impact'
                elif any(x in smell_lower for x in ['parameter', 'naming', 'class']):
                    impact = 'Medium Impact'
                else:
                    impact = 'Low Impact'

                # Determine frequency (this could be enhanced with actual frequency analysis)
                if smell_lower.count('high') > 0 or smell_lower.count('critical') > 0:
                    frequency = 'High Frequency'
                elif smell_lower.count('medium') > 0:
                    frequency = 'Medium Frequency'
                else:
                    frequency = 'Low Frequency'

                matrix_data[impact][frequency].append(smell)

            # Display matrix
            st.markdown("### Code Quality Matrix")
            st.markdown("This matrix shows the distribution of code smells by their impact and frequency:")

            # Create columns for each impact level
            cols = st.columns(3)

            for idx, (impact, frequencies) in enumerate(matrix_data.items()):
                with cols[idx]:
                    st.markdown(f"#### {impact}")
                    for freq, smells in frequencies.items():
                        if smells:
                            with st.expander(f"{freq} ({len(smells)})", expanded=False):
                                for smell in smells:
                                    st.markdown(f"- {smell}")

            # Add legend
            st.markdown("""
            #### Matrix Legend
            - **Impact**: How much the issue affects code quality
            - **Frequency**: How often the issue occurs in the codebase
            """)
        except Exception as e:
            st.error(f"Error displaying code smells matrix: {str(e)}")
            return

    def display_hierarchical_issues(self, code_smells: list):
        """Display code smells in a hierarchical tree structure."""
        if not code_smells:
            return

        st.markdown("### Hierarchical Issue View")
        
        # Create hierarchy
        hierarchy = {
            "Design Issues": {
                "Class Design": [],
                "Method Design": [],
                "Code Organization": []
            },
            "Implementation Issues": {
                "Complexity": [],
                "Duplication": [],
                "Size": []
            },
            "Maintainability Issues": {
                "Naming": [],
                "Documentation": [],
                "Style": []
            }
        }

        # Categorize issues
        for smell in code_smells:
            smell_lower = str(smell).lower()
            if 'class' in smell_lower:
                hierarchy["Design Issues"]["Class Design"].append(smell)
            elif 'method' in smell_lower or 'function' in smell_lower:
                hierarchy["Design Issues"]["Method Design"].append(smell)
            elif 'organization' in smell_lower or 'structure' in smell_lower:
                hierarchy["Design Issues"]["Code Organization"].append(smell)
            elif 'complex' in smell_lower or 'nest' in smell_lower:
                hierarchy["Implementation Issues"]["Complexity"].append(smell)
            elif 'duplicate' in smell_lower:
                hierarchy["Implementation Issues"]["Duplication"].append(smell)
            elif 'long' in smell_lower or 'size' in smell_lower:
                hierarchy["Implementation Issues"]["Size"].append(smell)
            elif 'name' in smell_lower or 'naming' in smell_lower:
                hierarchy["Maintainability Issues"]["Naming"].append(smell)
            elif 'doc' in smell_lower or 'comment' in smell_lower:
                hierarchy["Maintainability Issues"]["Documentation"].append(smell)
            else:
                hierarchy["Maintainability Issues"]["Style"].append(smell)

        # Display hierarchy
        for category, subcategories in hierarchy.items():
            if any(subcategories.values()):
                with st.expander(f"📁 {category}", expanded=True):
                    for subcategory, issues in subcategories.items():
                        if issues:
                            st.markdown(f"**{subcategory}** ({len(issues)})")
                            for issue in issues:
                                st.markdown(f"""
                                <div style='margin-left: 20px; padding: 5px; border-left: 3px solid #ccc;'>
                                    {issue}
                                </div>
                                """, unsafe_allow_html=True)

    def create_enhanced_code_smell_display(self, code_smells: list, file_content: dict = None):
        """Create an enhanced display for code smells with detailed context and recommendations."""
        if not code_smells:
            return

        # Group issues by type
        issues_by_type = {
            'long_lines': [],
            'long_functions': [],
            'complexity': [],
            'other': []
        }

        for smell in code_smells:
            smell_lower = str(smell).lower()
            if 'line' in smell_lower and 'too long' in smell_lower:
                issues_by_type['long_lines'].append(smell)
            elif 'function' in smell_lower and 'too long' in smell_lower:
                issues_by_type['long_functions'].append(smell)
            elif 'complex' in smell_lower or 'cyclomatic' in smell_lower:
                issues_by_type['complexity'].append(smell)
            else:
                issues_by_type['other'].append(smell)

        # Display statistical overview
        st.markdown("### 📊 Code Quality Overview")
        total_issues = len(code_smells)
        cols = st.columns(4)
        cols[0].metric("Total Issues", total_issues)
        cols[1].metric("Long Lines", len(issues_by_type['long_lines']))
        cols[2].metric("Long Functions", len(issues_by_type['long_functions']))
        cols[3].metric("Complexity Issues", len(issues_by_type['complexity']))

        # Display issues by category
        if issues_by_type['long_lines']:
            with st.expander("📏 Long Lines", expanded=True):
                st.markdown("""
                #### Why it matters:
                - Reduces code readability
                - Makes debugging more difficult
                - Violates PEP 8 standards (79 characters limit)
                
                #### How to fix:
                - Split long lines into multiple lines
                - Use line continuation with parentheses
                - Consider extracting parts into variables
                """)
                for issue in issues_by_type['long_lines']:
                    line_info = self._parse_line_issue(issue)
                    st.markdown(f"""
                    <div style='background-color: #FFE5E5; padding: 15px; border-radius: 5px; margin: 10px 0;'>
                        <strong>📍 Line {line_info['line_num']}</strong> ({line_info['chars']} characters)<br>
                        <code style='background-color: #FFF0F0; display: block; padding: 10px; margin: 5px 0;'>
                            {line_info['preview'] if line_info['preview'] else 'Line content not available'}
                        </code>
                        <strong>Suggestion:</strong> Split this line into multiple lines or extract parts into variables.
                    </div>
                    """, unsafe_allow_html=True)

        if issues_by_type['long_functions']:
            with st.expander("📚 Long Functions", expanded=True):
                st.markdown("""
                #### Why it matters:
                - Increases cognitive complexity
                - Makes testing more difficult
                - Violates Single Responsibility Principle
                
                #### How to fix:
                - Extract related code into smaller functions
                - Use meaningful function names
                - Consider breaking down by responsibility
                """)
                for issue in issues_by_type['long_functions']:
                    func_info = self._parse_function_issue(issue)
                    st.markdown(f"""
                    <div style='background-color: #FFF0E0; padding: 15px; border-radius: 5px; margin: 10px 0;'>
                        <strong>📍 Function</strong> ({func_info['lines']} lines)<br>
                        <strong>Suggestion:</strong> Break this function into smaller functions of 15-20 lines each.
                        Consider grouping related operations into their own functions.
                    </div>
                    """, unsafe_allow_html=True)

        if issues_by_type['complexity']:
            with st.expander("🔄 Complexity Issues", expanded=True):
                st.markdown("""
                #### Why it matters:
                - Makes code harder to understand
                - Increases likelihood of bugs
                - Makes maintenance more difficult
                
                #### How to fix:
                - Simplify complex conditions
                - Extract complex logic into helper methods
                - Use early returns to reduce nesting
                """)
                for issue in issues_by_type['complexity']:
                    st.markdown(f"""
                    <div style='background-color: #E5E5FF; padding: 15px; border-radius: 5px; margin: 10px 0;'>
                        <strong>Issue:</strong> {issue}<br>
                        <strong>Suggestion:</strong> Consider simplifying the logic or breaking it down into smaller, more manageable pieces.
                    </div>
                    """, unsafe_allow_html=True)

        # Add refactoring guide
        with st.expander("💡 Refactoring Guide", expanded=False):
            st.markdown("""
            ### Best Practices for Clean Code
            
            #### Line Length
            - Keep lines under 79 characters
            - Use parentheses for line continuation
            - Break long strings using string concatenation
            
            #### Function Length
            - Aim for functions under 20 lines
            - Each function should do one thing well
            - Use descriptive function names
            
            #### Complexity
            - Limit nesting to 3 levels
            - Simplify complex conditions
            - Use guard clauses for early returns
            
            #### General Tips
            - Use meaningful variable names
            - Add comments for complex logic
            - Follow the Single Responsibility Principle
            """)

    def _parse_line_issue(self, issue: str) -> dict:
        """Parse line issue information."""
        try:
            line_num = int(issue.split('Line')[1].split('is')[0].strip())
            chars = int(issue.split('(')[1].split('characters')[0].strip())
            return {
                'line_num': line_num,
                'chars': chars,
                'preview': None  # Could be populated if file content is available
            }
        except:
            return {'line_num': 0, 'chars': 0, 'preview': None}

    def _parse_function_issue(self, issue: str) -> dict:
        """Parse function issue information."""
        try:
            lines = int(issue.split('(')[1].split('lines')[0].strip())
            return {'lines': lines}
        except:
            return {'lines': 0}

    def create_halstead_metrics_chart(self, halstead_metrics: dict, chart_id: str = None) -> go.Figure:
        """Create a visualization of Halstead metrics."""
        try:
            if not halstead_metrics:
                fig = go.Figure()
                fig.add_annotation(
                    text="No Halstead metrics available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False
                )
                return fig

            # Create radar chart for Halstead metrics
            metrics = {
                'Program Length': halstead_metrics.get('length', 0),
                'Vocabulary Size': halstead_metrics.get('vocabulary', 0),
                'Program Volume': min(halstead_metrics.get('volume', 0) / 100, 100),  # Normalize to 0-100
                'Difficulty Level': min(halstead_metrics.get('difficulty', 0), 100),  # Cap at 100
                'Development Effort': min(halstead_metrics.get('effort', 0) / 1000, 100),  # Normalize and cap
                'Bug Prediction': min(halstead_metrics.get('bugs', 0) * 100, 100)  # Convert to percentage
            }

            fig = go.Figure(data=go.Scatterpolar(
                r=list(metrics.values()),
                theta=list(metrics.keys()),
                fill='toself',
                line_color='#4B4BFF'
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                showlegend=False,
                title='Halstead Metrics Analysis',
                height=400
            )

            return fig
        except Exception as e:
            print(f"Error creating Halstead metrics chart: {str(e)}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False
            )
            return fig

    def analyze_design_patterns(self, metrics: dict) -> dict:
        """Analyze code for common design patterns."""
        patterns = {
            'Factory': 0.0,
            'Singleton': 0.0,
            'Observer': 0.0,
            'Strategy': 0.0,
            'Decorator': 0.0
        }
        
        try:
            # Example pattern detection logic
            if 'class_metrics' in metrics:
                class_metrics = metrics['class_metrics']
                
                # Factory pattern detection
                patterns['Factory'] = 0.8 if any('create' in method.lower() for method in class_metrics.get('methods', [])) else 0.2
                
                # Singleton pattern detection
                patterns['Singleton'] = 0.9 if any('instance' in attr.lower() for attr in class_metrics.get('attributes', [])) else 0.1
                
                # Observer pattern detection
                has_observers = any('notify' in method.lower() or 'update' in method.lower() for method in class_metrics.get('methods', []))
                patterns['Observer'] = 0.7 if has_observers else 0.3
                
                # Strategy pattern detection
                has_strategy = any('strategy' in method.lower() or 'algorithm' in method.lower() for method in class_metrics.get('methods', []))
                patterns['Strategy'] = 0.6 if has_strategy else 0.2
                
                # Decorator pattern detection
                has_decorator = any('wrap' in method.lower() or 'decorate' in method.lower() for method in class_metrics.get('methods', []))
                patterns['Decorator'] = 0.75 if has_decorator else 0.15
                
            return patterns
        except Exception as e:
            print(f"Error in pattern analysis: {str(e)}")
            return patterns

    def analyze_antipatterns(self, metrics: dict) -> dict:
        """Analyze code for anti-patterns."""
        antipatterns = {
            'God Class': 0.0,
            'Long Method': 0.0,
            'Data Class': 0.0,
            'Feature Envy': 0.0,
            'Shotgun Surgery': 0.0
        }
        
        try:
            # Example anti-pattern detection logic
            if 'class_metrics' in metrics:
                class_metrics = metrics['class_metrics']
                
                # God Class detection
                method_count = len(class_metrics.get('methods', []))
                antipatterns['God Class'] = min(method_count / 20, 1.0)  # Normalize to 0-1
                
                # Long Method detection
                avg_method_length = class_metrics.get('avg_method_length', 0)
                antipatterns['Long Method'] = min(avg_method_length / 50, 1.0)
                
                # Data Class detection
                getter_setter_ratio = class_metrics.get('getter_setter_ratio', 0)
                antipatterns['Data Class'] = getter_setter_ratio
                
                # Feature Envy detection
                external_method_calls = class_metrics.get('external_method_calls', 0)
                antipatterns['Feature Envy'] = min(external_method_calls / 10, 1.0)
                
                # Shotgun Surgery detection
                coupling_score = class_metrics.get('coupling_score', 0)
                antipatterns['Shotgun Surgery'] = min(coupling_score / 5, 1.0)
                
            return antipatterns
        except Exception as e:
            print(f"Error in anti-pattern analysis: {str(e)}")
            return antipatterns

    def calculate_complexity_trend(self, metrics: dict) -> list:
        """Calculate complexity trend over time or code sections."""
        try:
            if 'complexity_history' in metrics:
                return metrics['complexity_history']
            
            # Generate sample trend if no history available
            base_complexity = metrics.get('cyclomatic_complexity', 50)
            return [base_complexity + (i * 2) for i in range(-5, 6)]
        except Exception as e:
            print(f"Error calculating complexity trend: {str(e)}")
            return []

    def calculate_quality_indicators(self, metrics: dict) -> dict:
        """Calculate various quality indicators."""
        indicators = {
            'Maintainability': 0.0,
            'Testability': 0.0,
            'Reusability': 0.0
        }
        
        try:
            # Calculate maintainability
            maintainability_factors = [
                metrics.get('cyclomatic_complexity', 100),
                metrics.get('cognitive_complexity', 100),
                metrics.get('halstead_volume', 1000)
            ]
            indicators['Maintainability'] = 1 - (sum(maintainability_factors) / (100 + 100 + 1000))
            
            # Calculate testability
            testability_factors = [
                metrics.get('branch_coverage', 0),
                metrics.get('test_ratio', 0)
            ]
            indicators['Testability'] = sum(testability_factors) / len(testability_factors)
            
            # Calculate reusability
            reusability_factors = [
                1 - metrics.get('coupling_score', 1),
                metrics.get('cohesion_score', 0)
            ]
            indicators['Reusability'] = sum(reusability_factors) / len(reusability_factors)
            
            return indicators
        except Exception as e:
            print(f"Error calculating quality indicators: {str(e)}")
            return indicators

    def analyze_code_smells_and_refactoring(self, metrics: dict) -> dict:
        """Analyze code for common code smells and suggest refactoring patterns based on Martin Fowler's catalog."""
        analysis = {
            'Extract Function/Method': {
                'detected': False,
                'confidence': 0.0,
                'locations': [],
                'refactoring': 'Extract Function',
                'description': 'You have a code fragment that can be grouped together',
                'symptoms': ['Long method', 'Duplicate code', 'Complex logic block']
            },
            'Move Function': {
                'detected': False,
                'confidence': 0.0,
                'locations': [],
                'refactoring': 'Move Function',
                'description': 'A function is used more in another class than in its own class',
                'symptoms': ['Feature envy', 'High coupling', 'Inappropriate intimacy']
            },
            'Replace Conditional with Polymorphism': {
                'detected': False,
                'confidence': 0.0,
                'locations': [],
                'refactoring': 'Replace Conditional with Polymorphism',
                'description': 'You have a conditional that chooses different behavior depending on object type',
                'symptoms': ['Switch statements', 'Type checking', 'Complex conditional logic']
            },
            'Extract Class': {
                'detected': False,
                'confidence': 0.0,
                'locations': [],
                'refactoring': 'Extract Class',
                'description': 'You have one class doing work that should be done by two',
                'symptoms': ['Large class', 'Low cohesion', 'Data clumps']
            },
            'Inline Function': {
                'detected': False,
                'confidence': 0.0,
                'locations': [],
                'refactoring': 'Inline Function',
                'description': 'When a function body is more obvious than the function itself',
                'symptoms': ['Indirection', 'Delegation', 'Simple wrapper']
            },
            'Replace Temp with Query': {
                'detected': False,
                'confidence': 0.0,
                'locations': [],
                'refactoring': 'Replace Temp with Query',
                'description': 'You are using a temporary variable to hold the result of an expression',
                'symptoms': ['Temporary variables', 'Code duplication', 'Complex expressions']
            }
        }
        
        try:
            if 'code_analysis' in metrics:
                code_data = metrics['code_analysis']
                
                # Analyze for Extract Function opportunities
                if any(len(func) > 15 for func in code_data.get('functions', {}).values()):
                    analysis['Extract Function/Method']['detected'] = True
                    analysis['Extract Function/Method']['confidence'] = 0.8
                    # Add specific locations where this refactoring could be applied
                
                # Analyze for Move Function opportunities
                if code_data.get('coupling_score', 0) > 0.7:
                    analysis['Move Function']['detected'] = True
                    analysis['Move Function']['confidence'] = 0.7
                
                # Analyze for Replace Conditional with Polymorphism
                if code_data.get('conditional_complexity', 0) > 5:
                    analysis['Replace Conditional with Polymorphism']['detected'] = True
                    analysis['Replace Conditional with Polymorphism']['confidence'] = 0.6
                
                # Analyze for Extract Class opportunities
                if code_data.get('class_size', 0) > 300:
                    analysis['Extract Class']['detected'] = True
                    analysis['Extract Class']['confidence'] = 0.75
                
                # Analyze for Inline Function opportunities
                if code_data.get('simple_delegation', False):
                    analysis['Inline Function']['detected'] = True
                    analysis['Inline Function']['confidence'] = 0.9
                
                # Analyze for Replace Temp with Query
                if code_data.get('temp_variables', 0) > 5:
                    analysis['Replace Temp with Query']['detected'] = True
                    analysis['Replace Temp with Query']['confidence'] = 0.65

            return analysis
        except Exception as e:
            print(f"Error in refactoring analysis: {str(e)}")
            return analysis

    def display_refactoring_opportunities(self, metrics: dict):
        """Display detected refactoring opportunities based on code smells."""
        st.markdown("## 🔍 Code Smells & Refactoring Opportunities")
        
        analysis = self.analyze_code_smells_and_refactoring(metrics)
        
        # Display detected refactoring opportunities
        detected_refactorings = [ref for ref, data in analysis.items() if data['detected']]
        
        if detected_refactorings:
            st.markdown("### Detected Refactoring Opportunities")
            
            for refactoring in detected_refactorings:
                data = analysis[refactoring]
                confidence = data['confidence'] * 100
                
                # Create expandable section for each refactoring
                with st.expander(f"🔧 {refactoring} (Confidence: {confidence:.1f}%)", expanded=True):
                    # Description
                    st.markdown(f"**What**: {data['description']}")
                    
                    # Symptoms
                    st.markdown("**Symptoms Detected**:")
                    for symptom in data['symptoms']:
                        st.markdown(f"- {symptom}")
                    
                    # Show specific locations if available
                    if data['locations']:
                        st.markdown("**Locations**:")
                        for loc in data['locations']:
                            st.code(loc)
                    
                    # Add refactoring steps
                    st.markdown("**How to Refactor**:")
                    self.display_refactoring_steps(refactoring)
        else:
            st.info("No immediate refactoring opportunities detected. Code appears to follow good design principles.")

    def display_refactoring_steps(self, refactoring: str):
        """Display step-by-step refactoring instructions based on Martin Fowler's catalog."""
        steps = {
            'Extract Function/Method': [
                "1. Create a new function with a name that describes the purpose",
                "2. Copy the extracted code from the source function to the new function",
                "3. Scan the extracted code for variables used only within the extracted code",
                "4. Check if any variables are modified by the extracted code",
                "5. Pass local variables as parameters if needed",
                "6. Replace the extracted code with a call to the new function"
            ],
            'Move Function': [
                "1. Examine all features used by the function in its current class",
                "2. Check if the function references features that should also move",
                "3. Declare the function in the target class",
                "4. Copy the function code to the target class",
                "5. Adjust the function to work in its new home",
                "6. Create a reference from the source to the target"
            ],
            'Replace Conditional with Polymorphism': [
                "1. Create a subclass for each variant",
                "2. Create a factory function to instantiate the appropriate subclass",
                "3. Move the conditional code to the subclasses",
                "4. Override the behavior in each subclass",
                "5. Delete the conditional code in the original class"
            ],
            'Extract Class': [
                "1. Create a new class to hold the split-off features",
                "2. Create an instance of the new class in the old class",
                "3. Move relevant fields to the new class",
                "4. Move relevant methods to the new class",
                "5. Review and adjust access levels",
                "6. Decide how to expose the new class"
            ],
            'Inline Function': [
                "1. Check that the function isn't polymorphic",
                "2. Find all calls to the function",
                "3. Replace each call with the function's body",
                "4. Test after each replacement",
                "5. Remove the function definition"
            ],
            'Replace Temp with Query': [
                "1. Check that the temporary variable is calculated once",
                "2. Extract the assignment of the temp into a new function",
                "3. Replace references to the temp with the new function",
                "4. Test after each replacement",
                "5. Remove the temporary variable"
            ]
        }
        
        if refactoring in steps:
            for step in steps[refactoring]:
                st.markdown(step)
            
            # Add reference to Martin Fowler's catalog
            st.markdown("""
            > 📚 Reference: This refactoring pattern is from Martin Fowler's Refactoring Catalog.
            > For more details, visit [refactoring.com/catalog](https://refactoring.com/catalog/)
            """)

# Create a default visualization manager instance
visualization_manager = VisualizationManager() 