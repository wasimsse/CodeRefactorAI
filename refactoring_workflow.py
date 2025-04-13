import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class ModelSource(Enum):
    LOCAL = "Local Machine"
    API = "API Integration"

class RefactoringLevel(Enum):
    METHOD = "Method Level"
    CLASS = "Class Level"
    MODULE = "Module Level"

@dataclass
class CodeMetrics:
    complexity: float
    maintainability: float
    cohesion: float
    coupling: float
    code_smells: int
    design_smells: int
    duplicated_code: float
    large_methods: int
    large_classes: int

@dataclass
class RefactoringResult:
    original_metrics: CodeMetrics
    refactored_metrics: CodeMetrics
    improvements: Dict[str, float]
    execution_time: float
    refactoring_actions: List[str]

class RefactoringWorkflow:
    def __init__(self):
        self.initialize_session_state()

    def initialize_session_state(self):
        """Initialize session state variables for the workflow."""
        if 'selected_model_source' not in st.session_state:
            st.session_state.selected_model_source = None
        if 'selected_model' not in st.session_state:
            st.session_state.selected_model = None
        if 'pre_analysis_results' not in st.session_state:
            st.session_state.pre_analysis_results = None
        if 'refactoring_results' not in st.session_state:
            st.session_state.refactoring_results = None
        if 'post_analysis_results' not in st.session_state:
            st.session_state.post_analysis_results = None
        if 'workflow_stage' not in st.session_state:
            st.session_state.workflow_stage = 'model_selection'

    def render(self):
        """Render the main workflow interface."""
        st.markdown("""
            <div style="text-align: center; padding: 1rem; background: linear-gradient(120deg, #1E88E5 0%, #42A5F5 100%); 
                border-radius: 10px; margin-bottom: 2rem;">
                <h2 style="color: white;">Intelligent Refactoring Workflow</h2>
            </div>
        """, unsafe_allow_html=True)

        # Create workflow progress bar
        progress_stages = ['Model Selection', 'Pre-Analysis', 'Refactoring', 'Post-Analysis']
        current_stage = progress_stages.index(self.get_current_stage_name()) + 1
        st.progress(current_stage / len(progress_stages))

        # Display current stage
        st.markdown(f"### Current Stage: {self.get_current_stage_name()}")

        # Render appropriate stage
        if st.session_state.workflow_stage == 'model_selection':
            self.render_model_selection()
        elif st.session_state.workflow_stage == 'pre_analysis':
            self.render_pre_analysis()
        elif st.session_state.workflow_stage == 'refactoring':
            self.render_refactoring()
        elif st.session_state.workflow_stage == 'post_analysis':
            self.render_post_analysis()

    def get_current_stage_name(self) -> str:
        """Get the name of the current workflow stage."""
        stage_names = {
            'model_selection': 'Model Selection',
            'pre_analysis': 'Pre-Analysis',
            'refactoring': 'Refactoring',
            'post_analysis': 'Post-Analysis'
        }
        return stage_names.get(st.session_state.workflow_stage, 'Unknown')

    def render_model_selection(self):
        """Render the model selection interface."""
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🤖 Model Source")
            model_source = st.radio(
                "Select Model Source",
                [source.value for source in ModelSource],
                key="model_source_radio"
            )

            if model_source == ModelSource.LOCAL.value:
                local_models = ["LLAMA2-7B", "CodeLLAMA-7B", "StarCoder-7B"]
                selected_model = st.selectbox(
                    "Select Local Model",
                    local_models,
                    key="local_model_select"
                )
            else:
                api_models = ["GPT-4", "Claude-3", "PaLM-2", "CodeGen"]
                selected_model = st.selectbox(
                    "Select API Model",
                    api_models,
                    key="api_model_select"
                )

                # API Configuration
                with st.expander("API Configuration"):
                    st.text_input("API Key", type="password", key="api_key")
                    st.number_input("Max Tokens", min_value=100, max_value=4000, value=2000)
                    st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7)

        with col2:
            st.markdown("### 📁 Code Selection")
            if st.session_state.current_file:
                st.success(f"Selected File: {st.session_state.current_file}")
            else:
                st.warning("Please select a file from the File Explorer tab")

            # Refactoring Level Selection
            st.markdown("### 🎯 Refactoring Level")
            selected_levels = st.multiselect(
                "Select Refactoring Levels",
                [level.value for level in RefactoringLevel],
                default=[RefactoringLevel.METHOD.value]
            )

        # Proceed button
        if st.session_state.current_file and selected_model:
            if st.button("Proceed to Pre-Analysis", type="primary", use_container_width=True):
                st.session_state.selected_model_source = model_source
                st.session_state.selected_model = selected_model
                st.session_state.workflow_stage = 'pre_analysis'
                st.rerun()

    def render_pre_analysis(self):
        """Render the pre-analysis interface."""
        if not st.session_state.pre_analysis_results:
            with st.spinner("Performing Pre-Analysis..."):
                # Simulate pre-analysis
                st.session_state.pre_analysis_results = self.perform_pre_analysis()

        # Display pre-analysis results
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📊 Code Quality Metrics")
            metrics = st.session_state.pre_analysis_results
            
            # Create metrics dashboard
            fig = go.Figure()
            
            # Add metrics as a spider chart
            fig.add_trace(go.Scatterpolar(
                r=[
                    metrics.complexity,
                    metrics.maintainability,
                    metrics.cohesion,
                    metrics.coupling,
                    metrics.code_smells / 10  # Normalized for scale
                ],
                theta=['Complexity', 'Maintainability', 'Cohesion', 'Coupling', 'Code Smells'],
                fill='toself',
                name='Current Code'
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("### 🔍 Detected Issues")
            
            # Display code smells
            with st.expander("Code Smells", expanded=True):
                st.metric("Total Code Smells", metrics.code_smells)
                st.metric("Design Smells", metrics.design_smells)
                st.metric("Duplicated Code", f"{metrics.duplicated_code:.1f}%")

            # Display structural issues
            with st.expander("Structural Issues", expanded=True):
                st.metric("Large Methods", metrics.large_methods)
                st.metric("Large Classes", metrics.large_classes)

        # Recommendations
        st.markdown("### 💡 Recommendations")
        self.display_refactoring_recommendations()

        # Navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Model Selection", use_container_width=True):
                st.session_state.workflow_stage = 'model_selection'
                st.rerun()
        with col2:
            if st.button("Proceed to Refactoring →", type="primary", use_container_width=True):
                st.session_state.workflow_stage = 'refactoring'
                st.rerun()

    def render_refactoring(self):
        """Render the refactoring interface."""
        st.markdown("### 🔄 Refactoring Execution")

        if not st.session_state.refactoring_results:
            # Display refactoring options
            with st.expander("Refactoring Options", expanded=True):
                st.checkbox("Enable aggressive refactoring", value=False)
                st.checkbox("Preserve comments", value=True)
                st.checkbox("Generate documentation", value=True)
                st.slider("Safety level", 0, 100, 75, help="Higher values mean more conservative refactoring")

            # Start refactoring button
            if st.button("Start Refactoring", type="primary", use_container_width=True):
                with st.spinner("Performing refactoring..."):
                    # Simulate refactoring process
                    st.session_state.refactoring_results = self.perform_refactoring()

        if st.session_state.refactoring_results:
            self.display_refactoring_results()

            # Navigation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back to Pre-Analysis", use_container_width=True):
                    st.session_state.workflow_stage = 'pre_analysis'
                    st.rerun()
            with col2:
                if st.button("Proceed to Post-Analysis →", type="primary", use_container_width=True):
                    st.session_state.workflow_stage = 'post_analysis'
                    st.rerun()

    def render_post_analysis(self):
        """Render the post-analysis interface."""
        st.markdown("### 📊 Post-Refactoring Analysis")

        if not st.session_state.post_analysis_results:
            with st.spinner("Performing post-analysis..."):
                # Use refactoring results for post-analysis
                st.session_state.post_analysis_results = st.session_state.refactoring_results

        # Display comparison metrics
        self.display_comparison_metrics()

        # Display detailed improvements
        self.display_detailed_improvements()

        # Final actions
        st.markdown("### 🎯 Final Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Apply Changes", type="primary", use_container_width=True):
                self.apply_refactoring_changes()
        
        with col2:
            if st.button("Download Report", use_container_width=True):
                self.generate_report()
        
        with col3:
            if st.button("Start New Refactoring", use_container_width=True):
                self.reset_workflow()
                st.rerun()

    def perform_pre_analysis(self) -> CodeMetrics:
        """Perform pre-analysis of the code."""
        # Simulate pre-analysis results
        return CodeMetrics(
            complexity=75.5,
            maintainability=62.3,
            cohesion=58.7,
            coupling=45.2,
            code_smells=12,
            design_smells=5,
            duplicated_code=15.3,
            large_methods=4,
            large_classes=2
        )

    def perform_refactoring(self) -> RefactoringResult:
        """Perform the refactoring process."""
        # Simulate refactoring results
        original_metrics = st.session_state.pre_analysis_results
        refactored_metrics = CodeMetrics(
            complexity=45.5,
            maintainability=85.3,
            cohesion=78.7,
            coupling=25.2,
            code_smells=3,
            design_smells=1,
            duplicated_code=5.3,
            large_methods=1,
            large_classes=0
        )
        
        return RefactoringResult(
            original_metrics=original_metrics,
            refactored_metrics=refactored_metrics,
            improvements={
                'complexity': 39.7,
                'maintainability': 37.0,
                'cohesion': 34.1,
                'coupling': 44.2,
                'code_smells': 75.0,
                'design_smells': 80.0,
                'duplicated_code': 65.4
            },
            execution_time=3.5,
            refactoring_actions=[
                "Extracted method 'processData' from large method",
                "Split large class 'DataManager' into smaller classes",
                "Removed duplicate code in utility functions",
                "Improved method naming for better readability",
                "Reduced method complexity through decomposition"
            ]
        )

    def display_refactoring_recommendations(self):
        """Display refactoring recommendations based on pre-analysis."""
        metrics = st.session_state.pre_analysis_results
        
        # Create recommendations based on metrics
        recommendations = []
        if metrics.complexity > 70:
            recommendations.append({
                "title": "High Complexity",
                "description": "Consider breaking down complex methods and classes",
                "priority": "High"
            })
        if metrics.code_smells > 10:
            recommendations.append({
                "title": "Code Smells",
                "description": "Address identified code smells to improve maintainability",
                "priority": "Medium"
            })
        if metrics.duplicated_code > 10:
            recommendations.append({
                "title": "Code Duplication",
                "description": "Extract duplicate code into reusable methods",
                "priority": "High"
            })

        # Display recommendations
        for rec in recommendations:
            st.markdown(f"""
                <div style="
                    background-color: white;
                    padding: 1rem;
                    border-radius: 10px;
                    margin-bottom: 1rem;
                    border-left: 4px solid {'#F44336' if rec['priority'] == 'High' else '#FFA726'};
                ">
                    <h4 style="color: #1E88E5; margin-bottom: 0.5rem;">{rec['title']}</h4>
                    <p style="color: #666; margin-bottom: 0.5rem;">{rec['description']}</p>
                    <span style="
                        background-color: {'#ffebee' if rec['priority'] == 'High' else '#fff3e0'};
                        color: {'#F44336' if rec['priority'] == 'High' else '#FFA726'};
                        padding: 0.2rem 0.5rem;
                        border-radius: 4px;
                        font-size: 0.8em;
                    ">
                        {rec['priority']} Priority
                    </span>
                </div>
            """, unsafe_allow_html=True)

    def display_refactoring_results(self):
        """Display the results of the refactoring process."""
        results = st.session_state.refactoring_results
        
        # Display execution summary
        st.markdown(f"""
            <div style="
                background-color: #E3F2FD;
                padding: 1rem;
                border-radius: 10px;
                margin-bottom: 1rem;
            ">
                <h4 style="color: #1E88E5; margin-bottom: 0.5rem;">Refactoring Complete</h4>
                <p style="color: #666;">Execution Time: {results.execution_time:.1f} seconds</p>
            </div>
        """, unsafe_allow_html=True)

        # Display refactoring actions
        st.markdown("### 📝 Refactoring Actions")
        for action in results.refactoring_actions:
            st.markdown(f"✓ {action}")

        # Display metrics improvements
        st.markdown("### 📈 Metrics Improvements")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Complexity Reduction",
                f"{results.improvements['complexity']:.1f}%",
                delta=-results.improvements['complexity']
            )
        with col2:
            st.metric(
                "Maintainability Improvement",
                f"{results.improvements['maintainability']:.1f}%",
                delta=results.improvements['maintainability']
            )
        with col3:
            st.metric(
                "Code Smells Reduction",
                f"{results.improvements['code_smells']:.1f}%",
                delta=-results.improvements['code_smells']
            )

    def display_comparison_metrics(self):
        """Display comparison metrics between original and refactored code."""
        results = st.session_state.post_analysis_results
        
        # Create comparison chart
        metrics_comparison = pd.DataFrame({
            'Metric': ['Complexity', 'Maintainability', 'Cohesion', 'Coupling', 'Code Smells'],
            'Original': [
                results.original_metrics.complexity,
                results.original_metrics.maintainability,
                results.original_metrics.cohesion,
                results.original_metrics.coupling,
                results.original_metrics.code_smells
            ],
            'Refactored': [
                results.refactored_metrics.complexity,
                results.refactored_metrics.maintainability,
                results.refactored_metrics.cohesion,
                results.refactored_metrics.coupling,
                results.refactored_metrics.code_smells
            ]
        })

        # Create bar chart
        fig = px.bar(
            metrics_comparison,
            x='Metric',
            y=['Original', 'Refactored'],
            barmode='group',
            title='Metrics Comparison',
            color_discrete_sequence=['#FFA726', '#66BB6A']
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def display_detailed_improvements(self):
        """Display detailed improvements in various aspects of the code."""
        results = st.session_state.post_analysis_results
        
        st.markdown("### 🎯 Detailed Improvements")
        
        # Create tabs for different aspects
        tab1, tab2, tab3 = st.tabs(["Quality Metrics", "Code Smells", "Structure"])
        
        with tab1:
            # Display quality metrics improvements
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Before Refactoring")
                self.display_metrics_card(results.original_metrics)
            with col2:
                st.markdown("#### After Refactoring")
                self.display_metrics_card(results.refactored_metrics)
        
        with tab2:
            # Display code smells reduction
            self.display_smells_comparison(results)
        
        with tab3:
            # Display structural improvements
            self.display_structural_improvements(results)

    def display_metrics_card(self, metrics: CodeMetrics):
        """Display a card with code metrics."""
        st.markdown(f"""
            <div style="
                background-color: white;
                padding: 1rem;
                border-radius: 10px;
                margin-bottom: 1rem;
            ">
                <p><strong>Complexity:</strong> {metrics.complexity:.1f}</p>
                <p><strong>Maintainability:</strong> {metrics.maintainability:.1f}</p>
                <p><strong>Cohesion:</strong> {metrics.cohesion:.1f}</p>
                <p><strong>Coupling:</strong> {metrics.coupling:.1f}</p>
            </div>
        """, unsafe_allow_html=True)

    def display_smells_comparison(self, results: RefactoringResult):
        """Display comparison of code smells before and after refactoring."""
        # Create comparison data
        smells_data = pd.DataFrame({
            'Category': ['Code Smells', 'Design Smells', 'Duplicated Code (%)'],
            'Before': [
                results.original_metrics.code_smells,
                results.original_metrics.design_smells,
                results.original_metrics.duplicated_code
            ],
            'After': [
                results.refactored_metrics.code_smells,
                results.refactored_metrics.design_smells,
                results.refactored_metrics.duplicated_code
            ]
        })

        # Create comparison chart
        fig = px.bar(
            smells_data,
            x='Category',
            y=['Before', 'After'],
            barmode='group',
            title='Code Smells Comparison',
            color_discrete_sequence=['#FFA726', '#66BB6A']
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def display_structural_improvements(self, results: RefactoringResult):
        """Display structural improvements in the code."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Methods")
            st.metric(
                "Large Methods",
                results.refactored_metrics.large_methods,
                delta=results.original_metrics.large_methods - results.refactored_metrics.large_methods
            )
        
        with col2:
            st.markdown("#### Classes")
            st.metric(
                "Large Classes",
                results.refactored_metrics.large_classes,
                delta=results.original_metrics.large_classes - results.refactored_metrics.large_classes
            )

    def apply_refactoring_changes(self):
        """Apply the refactoring changes to the code."""
        st.success("Changes applied successfully!")

    def generate_report(self):
        """Generate and download a detailed report."""
        st.success("Report generated and downloaded!")

    def reset_workflow(self):
        """Reset the workflow state."""
        st.session_state.selected_model_source = None
        st.session_state.selected_model = None
        st.session_state.pre_analysis_results = None
        st.session_state.refactoring_results = None
        st.session_state.post_analysis_results = None
        st.session_state.workflow_stage = 'model_selection' 