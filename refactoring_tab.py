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
        if 'current_code' not in st.session_state:
            st.session_state.current_code = None
        if 'current_file' not in st.session_state:
            st.session_state.current_file = None

    def load_file_content(self, file_path: str) -> str:
        """Load content from a file."""
        try:
            # First check uploaded_files (primary storage)
            if 'uploaded_files' in st.session_state and file_path in st.session_state.uploaded_files:
                file_data = st.session_state.uploaded_files[file_path]
                if isinstance(file_data, dict):
                    if 'content' in file_data:
                        return file_data['content']
                    elif 'code' in file_data:
                        return file_data['code']
                elif isinstance(file_data, str):
                    return file_data

            # Then check files (secondary storage)
            if 'files' in st.session_state and file_path in st.session_state.files:
                file_data = st.session_state.files[file_path]
                if isinstance(file_data, dict):
                    if 'content' in file_data:
                        return file_data['content']
                    elif 'code' in file_data:
                        return file_data['code']
                elif isinstance(file_data, str):
                    return file_data

            # If not in session state, read from file
            with open(file_path, 'r') as f:
                content = f.read()
                # Store in both session states
                if 'uploaded_files' not in st.session_state:
                    st.session_state.uploaded_files = {}
                if 'files' not in st.session_state:
                    st.session_state.files = {}
                file_data = {'content': content}
                st.session_state.uploaded_files[file_path] = file_data
                st.session_state.files[file_path] = file_data
                return content
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
            return None

    def render(self):
        """Render the refactoring tab with file selection and code display."""
        st.markdown("## Code Refactoring")
        
        # Debug information
        st.write("Debug Info:")
        if 'uploaded_files' in st.session_state:
            st.write("Files in uploaded_files:", list(st.session_state.uploaded_files.keys()))
        else:
            st.write("No files in uploaded_files")
            
        if 'files' in st.session_state:
            st.write("Files in files:", list(st.session_state.files.keys()))
        else:
            st.write("No files in files")
        
        if 'current_file' in st.session_state:
            st.write("Current file:", st.session_state.current_file)
        else:
            st.write("No current file selected")
        
        # File selection - use uploaded_files as primary source
        available_files = []
        if 'uploaded_files' in st.session_state:
            available_files.extend(st.session_state.uploaded_files.keys())
        if 'files' in st.session_state:
            available_files.extend(st.session_state.files.keys())
        available_files = sorted(set(available_files))  # Remove duplicates
        
        if available_files:
            selected_file = st.selectbox(
                "Choose a file to refactor",
                available_files,
                index=available_files.index(st.session_state.current_file) if st.session_state.current_file in available_files else 0
            )

            if selected_file:
                # Debug selected file
                st.write("Selected file:", selected_file)
                
                # Load and display file content
                content = self.load_file_content(selected_file)
                if content is not None:
                    # Debug content
                    st.write("Content loaded successfully, length:", len(content))
                    
                    st.session_state.current_file = selected_file
                    st.session_state.current_code = content

                    # Display file information
                    st.markdown("### File Information")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text(f"File: {selected_file.split('/')[-1]}")
                        st.text(f"Size: {len(content)} bytes")
                    with col2:
                        st.text(f"Lines: {len(content.splitlines())}")

                    # Code editor
                    st.markdown("### Edit Code")
                    selection_mode = st.radio(
                        "Selection Mode",
                        ["Entire File", "Function/Method", "Custom Selection"],
                        horizontal=True
                    )

                    # Debug before displaying code
                    st.write("About to display code with length:", len(content))
                    
                    # Use text_area instead of st.code for editing
                    edited_code = st.text_area(
                        "Edit Code",
                        value=content,
                        height=400,
                        key="code_editor"
                    )
                    
                    # Save and Undo buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 Save Changes"):
                            try:
                                with open(selected_file, 'w') as f:
                                    f.write(edited_code)
                                st.success("Changes saved successfully!")
                                st.session_state.current_code = edited_code
                                # Update both session states
                                file_data = {'content': edited_code}
                                st.session_state.uploaded_files[selected_file] = file_data
                                st.session_state.files[selected_file] = file_data
                            except Exception as e:
                                st.error(f"Error saving changes: {str(e)}")
                    
                    with col2:
                        if st.button("↩️ Undo Changes"):
                            st.session_state.current_code = content
                            st.rerun()

                    # Refactoring options
                    self._render_refactoring_options()
                else:
                    st.warning("Unable to load file content. Please try another file.")
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