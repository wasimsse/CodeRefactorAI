import streamlit as st
import plotly.express as px
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from refactoring_engine import RefactoringEngine, RefactoringType, RefactoringSuggestion
from llm_refactoring import LLMRefactoringManager, LLMType
from refactoring_phases import RefactoringPhases
from llama_integration import llama_cpp_manager
from local_models import local_model_manager
import os

class RefactoringTab:
    def __init__(self):
        """Initialize the refactoring tab."""
        # Initialize session state variables
        if 'refactoring_suggestions' not in st.session_state:
            st.session_state.refactoring_suggestions = []
        if 'selected_suggestion' not in st.session_state:
            st.session_state.selected_suggestion = None
        if 'refactoring_history' not in st.session_state:
            st.session_state.refactoring_history = []
        if 'selected_llm' not in st.session_state:
            st.session_state.selected_llm = 'local'  # Default to local
        if 'selected_local_model' not in st.session_state:
            st.session_state.selected_local_model = 'codellama-7b'
        if 'current_file' not in st.session_state:
            st.session_state.current_file = None
        if 'current_code' not in st.session_state:
            st.session_state.current_code = None
        if 'uploaded_files' not in st.session_state:
            st.session_state.uploaded_files = {}
        if 'files' not in st.session_state:
            st.session_state.files = {}
        if 'source_code' not in st.session_state:
            st.session_state.source_code = {}

    def load_file_content(self, file_path: str) -> Optional[str]:
        """Load content from a file."""
        try:
            # First check if the file content is in the source code view
            if 'source_code' in st.session_state and file_path in st.session_state.source_code:
                content = st.session_state.source_code[file_path]
                if content and content.strip():
                    return content

            # Then try to read directly from the file
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        # Update source code state to maintain consistency
                        if 'source_code' not in st.session_state:
                            st.session_state.source_code = {}
                        st.session_state.source_code[file_path] = content
                        return content
                    else:
                        st.warning(f"File {os.path.basename(file_path)} exists but is empty.")
                        return None
            
            # If file doesn't exist, check session state
            if file_path in st.session_state.uploaded_files:
                file_data = st.session_state.uploaded_files[file_path]
                if isinstance(file_data, dict):
                    content = file_data.get('content') or file_data.get('code')
                    if content and content.strip():
                        # Update source code state to maintain consistency
                        if 'source_code' not in st.session_state:
                            st.session_state.source_code = {}
                        st.session_state.source_code[file_path] = content
                        return content
                elif isinstance(file_data, str) and file_data.strip():
                    # Update source code state to maintain consistency
                    if 'source_code' not in st.session_state:
                        st.session_state.source_code = {}
                    st.session_state.source_code[file_path] = file_data
                    return file_data
            
            st.warning(f"No content found for {os.path.basename(file_path)}.")
            return None
        except Exception as e:
            st.error(f"Error loading file {os.path.basename(file_path)}: {str(e)}")
            return None

    def render(self):
        """Render the refactoring tab with file selection and code display."""
        st.markdown("""
            <div style="
                background: linear-gradient(120deg, #1E88E5 0%, #42A5F5 100%);
                padding: 1.5rem;
                border-radius: 15px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <h2 style="color: white; margin: 0;">Code Refactoring</h2>
            </div>
        """, unsafe_allow_html=True)
        
        # File Selection Section
        st.markdown("""
            <div style="
                background: white;
                padding: 1.5rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            ">
                <h3 style="color: #1E88E5; margin-bottom: 1rem;">Select File</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Get available files from both session states and source code
        available_files = list(set(
            list(st.session_state.uploaded_files.keys()) +
            list(st.session_state.files.keys()) +
            list(st.session_state.source_code.keys())
        ))
        
        if not available_files:
            st.warning("No files available. Please upload files first.")
            return

        # Sync with File Explorer selection
        if st.session_state.get('current_file') and st.session_state.current_file not in available_files:
            available_files.append(st.session_state.current_file)

        # File selection with improved UI
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_file = st.selectbox(
                "Choose a file to refactor",
                available_files,
                index=available_files.index(st.session_state.current_file) if st.session_state.current_file in available_files else 0,
                format_func=lambda x: os.path.basename(x) if x else "Select a file"
            )
        
        with col2:
            if st.button("🔄 Refresh Files", use_container_width=True):
                st.rerun()

        if selected_file:
            # Load file content
            content = self.load_file_content(selected_file)
            
            if content is not None and content.strip():  # Check if content exists and is not empty
                # Update session state
                st.session_state.current_file = selected_file
                st.session_state.current_code = content
                # Update source code state to maintain consistency
                st.session_state.source_code[selected_file] = content

                # Display file information in a card
                st.markdown("""
                    <div style="
                        background: white;
                        padding: 1.5rem;
                        border-radius: 10px;
                        margin: 2rem 0;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    ">
                        <h3 style="color: #1E88E5; margin-bottom: 1rem;">File Information</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("File", os.path.basename(selected_file))
                with col2:
                    st.metric("Size", f"{len(content)} bytes")
                with col3:
                    st.metric("Lines", len(content.splitlines()))

                # Code Editor Section
                st.markdown("""
                    <div style="
                        background: white;
                        padding: 1.5rem;
                        border-radius: 10px;
                        margin: 2rem 0;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    ">
                        <h3 style="color: #1E88E5; margin-bottom: 1rem;">Code Editor</h3>
                    </div>
                """, unsafe_allow_html=True)

                # Selection Mode with better styling
                selection_mode = st.radio(
                    "Selection Mode",
                    ["Entire File", "Function/Method", "Custom Selection"],
                    horizontal=True,
                    help="Choose how you want to select code for refactoring"
                )

                # Code editor with syntax highlighting
                st.markdown("""
                    <style>
                        .stTextArea textarea {
                            font-family: 'Courier New', Courier, monospace;
                            font-size: 14px;
                            line-height: 1.4;
                            background-color: #f8f9fa;
                            border: 1px solid #e9ecef;
                            border-radius: 5px;
                        }
                    </style>
                """, unsafe_allow_html=True)
                
                edited_code = st.text_area(
                    "Edit Code",
                    value=content,
                    height=500,
                    key="code_editor"
                )

                # Action buttons with improved styling
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("💾 Save Changes", use_container_width=True):
                        if not edited_code or not edited_code.strip():
                            st.error("Cannot save empty file content!")
                        else:
                            try:
                                with open(selected_file, 'w') as f:
                                    f.write(edited_code)
                                st.success("Changes saved successfully!")
                                st.session_state.current_code = edited_code
                                # Update all session states for consistency
                                file_data = {'content': edited_code}
                                st.session_state.uploaded_files[selected_file] = file_data
                                st.session_state.files[selected_file] = file_data
                                st.session_state.source_code[selected_file] = edited_code
                            except Exception as e:
                                st.error(f"Error saving changes: {str(e)}")

                with col2:
                    if st.button("↩️ Undo Changes", use_container_width=True):
                        original_content = st.session_state.source_code.get(selected_file)
                        if original_content:
                            st.session_state.current_code = original_content
                            st.rerun()
                        else:
                            st.error("Original content not found in source code view.")

                # Refactoring options with improved styling
                st.markdown("""
                    <div style="
                        background: white;
                        padding: 1.5rem;
                        border-radius: 10px;
                        margin: 2rem 0;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    ">
                        <h3 style="color: #1E88E5; margin-bottom: 1rem;">Refactoring Options</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                self._render_refactoring_options()
            else:
                st.error(f"Unable to load content from {os.path.basename(selected_file)}. The file appears to be empty or inaccessible.")
        else:
            st.info("Please select a file to begin refactoring.")

    def _render_file_info(self):
        """Render information about the current file."""
        with st.expander("📄 Current File Information", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "File Size",
                    f"{len(st.session_state.current_code) / 1024:.1f} KB" if st.session_state.current_code else "0 KB"
                )
            
            with col2:
                metrics = st.session_state.current_metrics.get('metrics', {}) if hasattr(st.session_state, 'current_metrics') else {}
                st.metric(
                    "Complexity",
                    f"{metrics.get('complexity', 0):.1f}"
                )
            
            with col3:
                st.metric(
                    "Issues Found",
                    len(st.session_state.refactoring_suggestions)
                )

    def _render_refactoring_options(self):
        """Render refactoring options and controls."""
        st.markdown("### Refactoring Options")
        
        col1, col2 = st.columns(2)
        with col1:
            refactoring_type = st.selectbox(
                "Refactoring Type",
                [t.value for t in RefactoringType]
            )
            
            goals = st.multiselect(
                "Refactoring Goals",
                ["Improve readability", "Reduce complexity", "Enhance maintainability", "Optimize performance"],
                default=["Improve readability"]
            )
        
        with col2:
            constraints = st.multiselect(
                "Constraints",
                ["Preserve functionality", "Maintain backward compatibility", "Keep existing tests", "Follow style guide"],
                default=["Preserve functionality"]
            )
            
            if st.button("Generate Refactoring", type="primary"):
                if not st.session_state.current_code:
                    st.error("Please select a file to refactor first")
                else:
                    with st.spinner("Generating refactoring suggestions..."):
                        if st.session_state.get('selected_local_model'):
                            # Use local LLM
                            refactored_code = self._perform_local_refactoring(
                                st.session_state.current_code,
                                refactoring_type,
                                goals,
                                constraints
                            )
                            if refactored_code:
                                st.success("Generated refactoring suggestions!")
                        else:
                            # Use cloud LLM
                            refactored_code = self.llm_manager.refactor_code(
                                st.session_state.current_code,
                                refactoring_type,
                                goals,
                                constraints
                            )
                            if refactored_code:
                                st.session_state.current_code = refactored_code
                                st.success("Refactoring completed successfully!")
                            else:
                                st.error("Failed to generate refactoring suggestions")

    def _render_llm_options(self):
        """Render LLM selection and configuration options."""
        with st.expander("🤖 LLM Configuration", expanded=True):
            # LLM Type Selection
            llm_type = st.radio(
                "Select LLM Type",
                ["Cloud LLM", "Local LLM"],
                horizontal=True
            )
            
            if llm_type == "Cloud LLM":
                # Cloud LLM options
                st.session_state.selected_llm = st.selectbox(
                    "Select Cloud LLM",
                    ["GPT-4", "GPT-3.5", "Claude"],
                    index=0
                )
                
                # Cloud LLM specific settings
                with st.expander("Advanced Settings"):
                    temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
                    max_tokens = st.slider("Max Tokens", 100, 2000, 500)
            else:
                # Local LLM options
                available_models = local_model_manager.get_available_models()
                if not available_models:
                    st.warning("No local models configured. Please add models in the configuration.")
                    return
                
                st.session_state.selected_local_model = st.selectbox(
                    "Select Local Model",
                    options=available_models,
                    format_func=lambda x: local_model_manager.get_model_config(x)["name"],
                    help="Choose a local LLM model for code refactoring"
                )
                
                if st.session_state.selected_local_model:
                    model_config = local_model_manager.get_model_config(st.session_state.selected_local_model)
                    with st.expander("Model Configuration"):
                        st.json(model_config)
                    
                    # Local model specific settings
                    with st.expander("Advanced Settings"):
                        temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
                        context_length = st.slider("Context Length", 512, 8192, 2048)

    def _perform_local_refactoring(self, code: str, refactoring_type: str, goals: List[str], constraints: List[str]) -> Optional[str]:
        """Perform refactoring using local LLM."""
        if not st.session_state.selected_local_model:
            st.error("Please select a local model first")
            return None
            
        if not code:
            st.error("No code selected for refactoring")
            return None
            
        model_config = local_model_manager.get_model_config(st.session_state.selected_local_model)
        
        # Load model
        model = llama_cpp_manager.load_model(
            st.session_state.selected_local_model,
            model_config["path"],
            model_config["parameters"]
        )
        
        if not model:
            st.error("Failed to load model")
            return None
            
        # Generate refactoring
        refactored_code = llama_cpp_manager.generate_refactoring(
            model=model,
            code=code,
            refactoring_type=refactoring_type,
            goals=goals,
            constraints=constraints
        )
        
        if refactored_code:
            # Add to refactoring history
            st.session_state.refactoring_history.append({
                'timestamp': datetime.now(),
                'type': refactoring_type,
                'model': st.session_state.selected_local_model,
                'before': code,
                'after': refactored_code
            })
            
            # Update the current code
            st.session_state.current_code = refactored_code
            st.rerun()  # Use st.rerun() instead of experimental_rerun
            
        return refactored_code

    def _render_suggestions(self):
        """Render refactoring suggestions."""
        if not st.session_state.refactoring_suggestions:
            return

        st.markdown("### 💡 Refactoring Suggestions")
        
        # Group suggestions by type
        suggestions_by_type = {}
        for suggestion in st.session_state.refactoring_suggestions:
            if suggestion.type not in suggestions_by_type:
                suggestions_by_type[suggestion.type] = []
            suggestions_by_type[suggestion.type].append(suggestion)

        # Create tabs for different types of suggestions
        tabs = st.tabs([t.value for t in suggestions_by_type.keys()])
        
        for tab, (refactoring_type, suggestions) in zip(tabs, suggestions_by_type.items()):
            with tab:
                for i, suggestion in enumerate(suggestions, 1):
                    with st.expander(
                        f"Suggestion {i}: {suggestion.title} (Confidence: {suggestion.confidence:.0%})",
                        expanded=i == 1
                    ):
                        # Description and impact
                        st.markdown(f"**Description:** {suggestion.description}")
                        
                        # Impact metrics
                        impact_cols = st.columns(len(suggestion.impact))
                        for col, (metric, value) in zip(impact_cols, suggestion.impact.items()):
                            with col:
                                st.metric(
                                    metric.title(),
                                    f"{abs(value):.0%}",
                                    delta=f"{value:.0%}" if value > 0 else f"{value:.0%}",
                                    delta_color="normal" if value > 0 else "inverse"
                                )
                        
                        # Code comparison
                        st.markdown("##### Code Changes")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Before:**")
                            st.code(suggestion.before_code, language="python")
                        with col2:
                            st.markdown("**After:**")
                            if suggestion.after_code:
                                st.code(suggestion.after_code, language="python")
                            else:
                                st.info("Refactored code will be generated when applied")
                        
                        # Apply button
                        if st.button("✨ Apply Refactoring", key=f"apply_{i}", use_container_width=True):
                            self._apply_suggestion(suggestion)

    def _render_history(self):
        """Render refactoring history."""
        if not st.session_state.refactoring_history:
            return

        st.markdown("### 📜 Refactoring History")
        
        # Convert history to DataFrame for display
        history_data = pd.DataFrame(st.session_state.refactoring_history)
        
        # Display history in a table
        st.dataframe(
            history_data,
            column_config={
                "timestamp": "Timestamp",
                "type": "Type",
                "description": "Description",
                "success": st.column_config.BooleanColumn(
                    "Success",
                    help="Whether the refactoring was successful"
                )
            },
            hide_index=True
        )

    def _apply_suggestion(self, suggestion: RefactoringSuggestion):
        """Apply a refactoring suggestion."""
        try:
            # Update the file content
            with open(st.session_state.current_file, 'w') as f:
                f.write(suggestion.after_code)
            
            # Update session state
            st.session_state.current_code = suggestion.after_code
            
            # Add to history
            st.session_state.refactoring_history.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': suggestion.type.value,
                'description': suggestion.description,
                'success': True
            })
            
            # Remove the applied suggestion
            st.session_state.refactoring_suggestions.remove(suggestion)
            
            st.success("Refactoring applied successfully!")
            
        except Exception as e:
            st.error(f"Failed to apply refactoring: {str(e)}")
            st.session_state.refactoring_history.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': suggestion.type.value,
                'description': suggestion.description,
                'success': False,
                'error': str(e)
            }) 