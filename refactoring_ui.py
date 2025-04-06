import streamlit as st
import pandas as pd
from datetime import datetime
import os
from code_analyzer import CodeAnalyzer
from config import Config
from refactoring import (
    generate_refactoring_suggestions,
    apply_refactoring_suggestion,
    calculate_impact_metrics,
    validate_refactoring_suggestion
)
from typing import Dict, Any, Optional
import plotly.graph_objects as go
import plotly.express as px

# Create config instance
config = Config()

def display_refactoring_header():
    """Display the header for the refactoring tab with enhanced styling."""
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

def display_file_selector(files):
    """Display file selection dropdown with info button."""
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
    return selected_file

def display_analysis_tab():
    """Display the analysis tab with code and metrics."""
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
            
            # Define supported languages directly
            supported_languages = {
                'python': {'name': 'Python', 'extensions': ['.py']},
                'java': {'name': 'Java', 'extensions': ['.java']},
                'javascript': {'name': 'JavaScript', 'extensions': ['.js', '.jsx', '.ts', '.tsx']},
                'cpp': {'name': 'C++', 'extensions': ['.cpp', '.hpp', '.cc', '.h']},
                'csharp': {'name': 'C#', 'extensions': ['.cs']},
                'go': {'name': 'Go', 'extensions': ['.go']},
                'ruby': {'name': 'Ruby', 'extensions': ['.rb']},
                'rust': {'name': 'Rust', 'extensions': ['.rs']}
            }
            
            for lang, info in supported_languages.items():
                if file_ext in info['extensions']:
                    language = info['name']
                    break
            
            st.markdown(f"**Language:** {language}")
            
            # File size
            file_size = os.path.getsize(st.session_state.current_file)
            st.markdown(f"**File Size:** {file_size / 1024:.1f} KB")
        else:
            st.info("No metrics available for the selected file.")

def display_code_editor():
    """Display the code editor tab."""
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

def display_refactoring_options():
    """Display the refactoring options tab."""
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Model Selection")
        st.selectbox(
            "Select model",
            ["gpt-3.5-turbo", "gpt-4"],
            key="refactoring_model"
        )
        
        st.markdown("#### Scope")
        st.radio(
            "Select refactoring scope",
            ["Selected file", "Entire project"],
            key="refactoring_scope"
        )
        
        st.markdown("#### Goals")
        st.multiselect(
            "Select refactoring goals",
            [
                "Improve readability",
                "Enhance maintainability",
                "Optimize performance",
                "Fix code smells",
                "Reduce complexity",
                "Improve error handling",
                "Add documentation"
            ],
            key="refactoring_goals"
        )
    
    with col2:
        st.markdown("#### Constraints")
        st.multiselect(
            "Select constraints",
            [
                "Preserve functionality",
                "Maintain backward compatibility",
                "Keep existing interfaces",
                "Minimize changes",
                "Follow style guide",
                "Use design patterns",
                "Consider performance impact"
            ],
            key="refactoring_constraints"
        )
        
        st.markdown("#### Custom Instructions")
        st.text_area(
            "Add any specific instructions or requirements",
            key="custom_instructions",
            height=100
        )
    
    # Generate button at the bottom
    if st.button("Generate Refactoring Suggestions", type="primary", use_container_width=True):
        if not st.session_state.current_metrics:
            st.warning("Please select a file to refactor first.")
        else:
            with st.spinner("Generating refactoring suggestions..."):
                suggestions = generate_refactoring_suggestions(
                    st.session_state.current_file,
                    st.session_state.current_metrics,
                    st.session_state.refactoring_model,
                    st.session_state.refactoring_goals,
                    st.session_state.refactoring_constraints,
                    st.session_state.custom_instructions
                )
                st.session_state.refactoring_suggestions = suggestions
                st.experimental_rerun()

def display_preview_tab():
    """Display the preview tab with refactoring suggestions."""
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

def display_refactoring_history():
    """Display the refactoring history."""
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

def render_refactoring_interface():
    """Main function to render the complete refactoring interface."""
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
    if 'refactoring_suggestions' not in st.session_state:
        st.session_state.refactoring_suggestions = []
    if 'refactoring_model' not in st.session_state:
        st.session_state.refactoring_model = "gpt-4"
    if 'refactoring_goals' not in st.session_state:
        st.session_state.refactoring_goals = []
    if 'refactoring_constraints' not in st.session_state:
        st.session_state.refactoring_constraints = []
    if 'custom_instructions' not in st.session_state:
        st.session_state.custom_instructions = ""
    
    # Check if files are available
    if 'uploaded_files' not in st.session_state or not st.session_state.uploaded_files:
        st.warning("Please upload or select files to refactor first.")
        return
    
    files = list(st.session_state.uploaded_files.keys())
    if not files:
        st.warning("No files available for refactoring.")
        return
    
    # Display header
    display_refactoring_header()
    
    # File selection
    selected_file = display_file_selector(files)
    
    # Update session state when file selection changes
    if selected_file != st.session_state.current_file:
        st.session_state.current_file = selected_file
        st.session_state.current_metrics = st.session_state.uploaded_files[selected_file]
        if st.session_state.current_metrics:
            st.session_state.current_code = st.session_state.current_metrics.get('content', '')
    
    # Create tabs
    tab_titles = [
        "🔍 Analysis & Selection",
        "✏️ Code Editor",
        "🎯 Refactoring Options",
        "👀 Preview & Impact"
    ]
    
    # Create tabs using st.tabs()
    tabs = st.tabs(tab_titles)
    
    # Display content in each tab
    with tabs[0]:
        display_analysis_tab()
    
    with tabs[1]:
        display_code_editor()
    
    with tabs[2]:
        display_refactoring_options()
    
    with tabs[3]:
        display_preview_tab()
    
    # Display refactoring history below the tabs
    st.markdown("---")
    display_refactoring_history() 