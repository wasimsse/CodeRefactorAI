import streamlit as st
import plotly.express as px
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from refactoring_engine import RefactoringEngine, RefactoringType, RefactoringSuggestion
from llm_refactoring import LLMRefactoringManager, LLMType
from refactoring_phases import RefactoringPhases

class RefactoringTab:
    def __init__(self):
        self.engine = RefactoringEngine()
        self.llm_manager = LLMRefactoringManager()
        self.phases = RefactoringPhases()
        if 'refactoring_suggestions' not in st.session_state:
            st.session_state.refactoring_suggestions = []
        if 'selected_suggestion' not in st.session_state:
            st.session_state.selected_suggestion = None
        if 'refactoring_history' not in st.session_state:
            st.session_state.refactoring_history = []
        if 'selected_llm' not in st.session_state:
            st.session_state.selected_llm = None

    def render(self):
        """Render the refactoring tab with the three-phase workflow."""
        self.phases.render()

    def _render_file_info(self):
        """Render information about the current file."""
        with st.expander("📄 Current File Information", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "File Size",
                    f"{len(st.session_state.current_code) / 1024:.1f} KB"
                )
            
            with col2:
                metrics = st.session_state.current_metrics.get('metrics', {})
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
        """Render refactoring configuration options."""
        with st.expander("⚙️ Refactoring Options", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Analysis Settings")
                analysis_options = {
                    'detect_long_methods': st.checkbox("Detect Long Methods", value=True),
                    'detect_complex_conditions': st.checkbox("Detect Complex Conditions", value=True),
                    'detect_duplicate_code': st.checkbox("Detect Code Duplication", value=True),
                    'detect_naming_issues': st.checkbox("Detect Naming Issues", value=True),
                    'detect_god_classes': st.checkbox("Detect God Classes", value=True)
                }
            
            with col2:
                st.markdown("#### Refactoring Scope")
                scope_options = st.radio(
                    "Select scope",
                    ["Selected file", "Current function/method", "Entire project"],
                    index=0
                )

    def _render_llm_options(self):
        """Render LLM selection and configuration."""
        with st.expander("🤖 AI Model Selection", expanded=True):
            # Get available LLMs
            available_llms = self.llm_manager.get_available_llms()
            
            if not available_llms:
                st.warning("No LLM models available. Please check your configuration and API keys.")
                return
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Select AI Model")
                selected_llm = st.selectbox(
                    "Choose AI Model",
                    options=available_llms,
                    format_func=lambda x: x.value,
                    key="llm_selector"
                )
                
                if selected_llm != st.session_state.selected_llm:
                    st.session_state.selected_llm = selected_llm
            
            with col2:
                st.markdown("#### Model Information")
                if selected_llm == LLMType.LOCAL:
                    st.info("Using local CodeLlama model")
                    st.markdown("- Fast execution")
                    st.markdown("- No API costs")
                    st.markdown("- Limited capabilities")
                elif selected_llm == LLMType.OPENAI:
                    st.info("Using OpenAI GPT-4")
                    st.markdown("- High accuracy")
                    st.markdown("- Best for complex refactoring")
                    st.markdown("- Pay per token")
                elif selected_llm == LLMType.ANTHROPIC:
                    st.info("Using Anthropic Claude")
                    st.markdown("- Strong code understanding")
                    st.markdown("- Detailed explanations")
                    st.markdown("- Pay per token")
                elif selected_llm == LLMType.GOOGLE:
                    st.info("Using Google Gemini")
                    st.markdown("- Good performance")
                    st.markdown("- Competitive pricing")
                elif selected_llm == LLMType.COHERE:
                    st.info("Using Cohere")
                    st.markdown("- Specialized in code")
                    st.markdown("- Custom fine-tuning")
            
            # Add refactoring button
            if st.button("🔄 Generate Refactoring Suggestions", type="primary", use_container_width=True):
                with st.spinner("Analyzing code and generating suggestions..."):
                    try:
                        # Get current file context
                        context = {
                            'language': st.session_state.current_metrics.get('language', 'unknown'),
                            'file_type': st.session_state.current_file.split('.')[-1],
                            'complexity': st.session_state.current_metrics.get('complexity', {}).get('score', 0),
                            'maintainability': st.session_state.current_metrics.get('maintainability', {}).get('score', 0),
                            'loc': st.session_state.current_metrics.get('raw_metrics', {}).get('loc', 0)
                        }
                        
                        # Get refactoring suggestions from selected LLM
                        response = self.llm_manager.refactor_code(
                            st.session_state.current_code,
                            st.session_state.selected_llm,
                            context
                        )
                        
                        if response.refactored_code:
                            # Create a suggestion object
                            suggestion = RefactoringSuggestion(
                                type=RefactoringType.EXTRACT_METHOD,  # Default type
                                title="AI-Generated Refactoring",
                                description=response.explanation,
                                before_code=st.session_state.current_code,
                                after_code=response.refactored_code,
                                start_line=1,
                                end_line=len(st.session_state.current_code.splitlines()),
                                confidence=response.confidence,
                                impact=response.metrics,
                                prerequisites=[],
                                risks=[]
                            )
                            
                            st.session_state.refactoring_suggestions.append(suggestion)
                            st.success("Generated refactoring suggestions!")
                        else:
                            st.error("Failed to generate refactoring suggestions.")
                            
                    except Exception as e:
                        st.error(f"Error generating refactoring suggestions: {str(e)}")

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