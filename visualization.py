import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Any

class VisualizationManager:
    def __init__(self):
        """Initialize visualization manager."""
        self.color_scheme = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ecc71',
            'warning': '#f1c40f',
            'danger': '#e74c3c'
        }

    def create_metrics_gauge(self, value: float, title: str) -> go.Figure:
        """Create a gauge chart for metrics visualization."""
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': self.color_scheme['primary']},
                'steps': [
                    {'range': [0, 30], 'color': self.color_scheme['danger']},
                    {'range': [30, 70], 'color': self.color_scheme['warning']},
                    {'range': [70, 100], 'color': self.color_scheme['success']}
                ]
            }
        ))
        
        fig.update_layout(height=200, margin=dict(l=10, r=10, t=50, b=10))
        return fig

    def display_analysis_dashboard(self, results: Dict[str, Any]):
        """Display comprehensive analysis dashboard."""
        st.subheader("Code Analysis Dashboard")
        
        # Create metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.plotly_chart(
                self.create_metrics_gauge(results.get('complexity', 0), "Complexity"),
                use_container_width=True
            )
        
        with col2:
            st.plotly_chart(
                self.create_metrics_gauge(results.get('maintainability', 0), "Maintainability"),
                use_container_width=True
            )
            
        with col3:
            st.plotly_chart(
                self.create_metrics_gauge(100 - results.get('code_smells', 0), "Code Quality"),
                use_container_width=True
            )
            
        with col4:
            st.plotly_chart(
                self.create_metrics_gauge(results.get('performance', 0), "Performance"),
                use_container_width=True
            )
            
        # Display detailed metrics
        if 'history' in results and results['history']:
            self._display_history_charts(results['history'])
            
        if 'issues' in results and results['issues']:
            self._display_issues_summary(results['issues'])

    def _display_history_charts(self, history: List[Dict[str, Any]]):
        """Display historical trends charts."""
        st.subheader("Historical Trends")
        
        # Convert history to DataFrame
        df = pd.DataFrame(history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create line chart
        fig = px.line(
            df,
            x='timestamp',
            y=['complexity', 'maintainability', 'code_quality'],
            title='Code Metrics Over Time'
        )
        
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Score",
            legend_title="Metrics",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def _display_issues_summary(self, issues: List[str]):
        """Display summary of code issues."""
        st.subheader("Code Issues Summary")
        
        # Count issue types
        issue_counts = {}
        for issue in issues:
            issue_type = issue.split(':')[0] if ':' in issue else 'Other'
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
            
        # Create pie chart
        fig = px.pie(
            values=list(issue_counts.values()),
            names=list(issue_counts.keys()),
            title='Distribution of Code Issues'
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    def create_comparison_chart(self, before: Dict[str, float], after: Dict[str, float]) -> go.Figure:
        """Create before/after comparison chart."""
        metrics = list(before.keys())
        
        fig = go.Figure(data=[
            go.Bar(name='Before', x=metrics, y=[before[m] for m in metrics]),
            go.Bar(name='After', x=metrics, y=[after[m] for m in metrics])
        ])
        
        fig.update_layout(
            title='Code Metrics Comparison',
            barmode='group',
            height=400,
            xaxis_title="Metrics",
            yaxis_title="Score"
        )
        
        return fig

    def create_timeline(self, events: List[Dict[str, Any]]) -> go.Figure:
        """Create timeline visualization of events."""
        df = pd.DataFrame(events)
        
        fig = px.timeline(
            df,
            x_start='start_time',
            x_end='end_time',
            y='event',
            color='category',
            title='Refactoring Timeline'
        )
        
        fig.update_layout(height=400)
        return fig

    def create_radar_chart(self, metrics: Dict[str, float]) -> go.Figure:
        """Create a radar chart for code quality metrics."""
        categories = list(metrics.keys())
        values = list(metrics.values())
        
        fig = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            line_color=self.color_scheme['primary']
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=False,
            height=400
        )
        return fig

    def create_issues_breakdown(self, issues: List[Dict]) -> go.Figure:
        """Create a treemap for code issues breakdown."""
        if not issues:
            return None
            
        df = pd.DataFrame(issues)
        fig = px.treemap(
            df,
            path=['category', 'severity', 'type'],
            values='count',
            color='severity',
            color_discrete_map={
                'high': '#ff4b4b',
                'medium': '#ffa600',
                'low': '#00cc96'
            }
        )
        fig.update_layout(height=400)
        return fig

    def create_complexity_timeline(self, history: List[Dict]) -> go.Figure:
        """Create a line chart for complexity trends over time."""
        if not history:
            return None
            
        df = pd.DataFrame(history)
        fig = px.line(
            df,
            x='timestamp',
            y=['complexity', 'maintainability', 'performance'],
            title='Code Quality Trends',
            labels={'value': 'Score', 'variable': 'Metric'},
            line_shape='spline'
        )
        fig.update_layout(height=300)
        return fig

    def display_analysis_dashboard(self, analysis_results: Dict):
        """Display the main analysis dashboard with all visualizations."""
        st.subheader("Code Quality Dashboard")
        
        # Create metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.plotly_chart(
                self.create_metrics_gauge(
                    analysis_results.get('complexity', 0), 
                    "Complexity"
                ),
                use_container_width=True
            )
        with col2:
            st.plotly_chart(
                self.create_metrics_gauge(
                    analysis_results.get('maintainability', 0),
                    "Maintainability"
                ),
                use_container_width=True
            )
        with col3:
            st.plotly_chart(
                self.create_metrics_gauge(
                    analysis_results.get('code_smells', 0),
                    "Code Smells"
                ),
                use_container_width=True
            )
        with col4:
            st.plotly_chart(
                self.create_metrics_gauge(
                    analysis_results.get('performance', 0),
                    "Performance"
                ),
                use_container_width=True
            )

        # Create detailed analysis section
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Quality Metrics Overview")
            radar_metrics = {
                'Complexity': analysis_results.get('complexity', 0),
                'Maintainability': analysis_results.get('maintainability', 0),
                'Code Smells': analysis_results.get('code_smells', 0),
                'Performance': analysis_results.get('performance', 0),
                'Test Coverage': analysis_results.get('test_coverage', 0)
            }
            st.plotly_chart(
                self.create_radar_chart(radar_metrics),
                use_container_width=True
            )

        with col2:
            st.subheader("Issues Breakdown")
            issues_chart = self.create_issues_breakdown(
                analysis_results.get('issues', [])
            )
            if issues_chart:
                st.plotly_chart(issues_chart, use_container_width=True)
            else:
                st.info("No issues found in the analysis.")

        # Historical trends
        st.subheader("Quality Trends")
        history_chart = self.create_complexity_timeline(
            analysis_results.get('history', [])
        )
        if history_chart:
            st.plotly_chart(history_chart, use_container_width=True)
        else:
            st.info("No historical data available yet.") 