from enum import Enum
import streamlit as st
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from refactoring_engine import RefactoringEngine, RefactoringType, RefactoringSuggestion
from llm_refactoring import LLMRefactoringManager, LLMType

class RefactoringPhase(Enum):
    ANALYSIS = "Analysis"
    PLANNING = "Planning"
    IMPLEMENTATION = "Implementation"

@dataclass
class CodeMetrics:
    complexity: float
    maintainability: float
    code_smells: List[str]
    lines_of_code: int

@dataclass
class RefactoringSuggestion:
    title: str
    description: str
    impact: Dict[str, float]
    priority: int
    effort: str
    risks: List[str]
    before_code: str
    after_code: Optional[str] = None

class RefactoringPhases:
    def __init__(self):
        self.engine = RefactoringEngine()
        self.llm_manager = LLMRefactoringManager()
        if 'current_phase' not in st.session_state:
            st.session_state.current_phase = RefactoringPhase.ANALYSIS
        if 'code_metrics' not in st.session_state:
            st.session_state.code_metrics = None
        if 'refactoring_plan' not in st.session_state:
            st.session_state.refactoring_plan = []
        if 'implementation_status' not in st.session_state:
            st.session_state.implementation_status = {}

    def render(self):
        """Render the current phase of the refactoring workflow."""
        st.header("Code Refactoring")

        if not st.session_state.get('current_file'):
            st.info("Please select a file from the File Explorer to start refactoring.")
            return

        # Phase navigation
        phases = [phase.value for phase in RefactoringPhase]
        current_phase_idx = phases.index(st.session_state.current_phase.value)
        
        cols = st.columns(len(phases))
        for i, phase in enumerate(phases):
            with cols[i]:
                if i < current_phase_idx:
                    st.button(f"← {phase}", key=f"phase_{phase}", 
                            on_click=self._set_phase, args=(RefactoringPhase(phase),))
                elif i == current_phase_idx:
                    st.button(phase, key=f"phase_{phase}", disabled=True)
                else:
                    st.button(f"{phase} →", key=f"phase_{phase}", 
                            disabled=not self._can_proceed_to_phase(RefactoringPhase(phase)))

        # Render current phase
        if st.session_state.current_phase == RefactoringPhase.ANALYSIS:
            self._render_analysis_phase()
        elif st.session_state.current_phase == RefactoringPhase.PLANNING:
            self._render_planning_phase()
        else:
            self._render_implementation_phase()

    def _render_analysis_phase(self):
        """Render the Analysis phase interface."""
        st.subheader("Code Analysis")
        
        # Run analysis
        if st.button("Analyze Code"):
            with st.spinner("Analyzing code..."):
                metrics = self._analyze_code()
                st.session_state.code_metrics = metrics

        # Display metrics if available
        if st.session_state.code_metrics:
            metrics = st.session_state.code_metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Complexity Score", f"{metrics.complexity:.2f}")
                st.metric("Lines of Code", metrics.lines_of_code)
            with col2:
                st.metric("Maintainability Index", f"{metrics.maintainability:.2f}")
                st.metric("Code Smells", len(metrics.code_smells))

            if metrics.code_smells:
                st.subheader("Detected Code Smells")
                for smell in metrics.code_smells:
                    st.write(f"- {smell}")

    def _render_planning_phase(self):
        """Render the Planning phase interface."""
        st.subheader("Refactoring Planning")

        # LLM provider selection
        llm_type = st.selectbox("Select LLM Provider", 
                               [llm.value for llm in LLMType],
                               key="llm_type")

        # Refactoring type selection
        refactoring_type = st.selectbox("Select Refactoring Type",
                                       [ref.value for ref in RefactoringType],
                                       key="refactoring_type")

        if st.button("Generate Suggestions"):
            with st.spinner("Generating refactoring suggestions..."):
                suggestions = self.llm_manager.generate_suggestions(
                    st.session_state.current_file,
                    LLMType(llm_type),
                    RefactoringType(refactoring_type)
                )
                st.session_state.refactoring_suggestions = suggestions

        # Display suggestions
        if st.session_state.get('refactoring_suggestions'):
            st.subheader("Refactoring Suggestions")
            for i, suggestion in enumerate(st.session_state.refactoring_suggestions):
                with st.expander(f"Suggestion {i + 1}: {suggestion.title}"):
                    st.write(suggestion.description)
                    st.code(suggestion.code_example)
                    if st.button("Apply This Suggestion", key=f"apply_{i}"):
                        st.session_state.selected_suggestion = suggestion
                        st.session_state.current_phase = RefactoringPhase.IMPLEMENTATION

    def _render_implementation_phase(self):
        """Render the Implementation phase interface."""
        st.subheader("Refactoring Implementation")

        if not st.session_state.get('selected_suggestion'):
            st.warning("No refactoring suggestion selected. Please go back to the Planning phase.")
            return

        suggestion = st.session_state.selected_suggestion
        st.write("### Selected Refactoring")
        st.write(suggestion.title)
        st.write(suggestion.description)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Original Code")
            st.code(suggestion.original_code)
        with col2:
            st.subheader("Refactored Code")
            st.code(suggestion.code_example)

        if st.button("Apply Refactoring"):
            with st.spinner("Applying refactoring..."):
                success = self.engine.apply_refactoring(suggestion)
                if success:
                    st.success("Refactoring applied successfully!")
                    st.session_state.current_phase = RefactoringPhase.ANALYSIS
                else:
                    st.error("Failed to apply refactoring. Please try again.")

    def _analyze_code(self) -> CodeMetrics:
        """Analyze the current file and return metrics."""
        file_path = st.session_state.current_file
        analysis_result = self.engine.analyze_file(file_path)
        
        return CodeMetrics(
            complexity=analysis_result.get('complexity', 0.0),
            maintainability=analysis_result.get('maintainability', 0.0),
            code_smells=analysis_result.get('code_smells', []),
            lines_of_code=analysis_result.get('lines_of_code', 0)
        )

    def _set_phase(self, phase: RefactoringPhase):
        """Set the current phase of the refactoring workflow."""
        st.session_state.current_phase = phase

    def _can_proceed_to_phase(self, phase: RefactoringPhase) -> bool:
        """Check if we can proceed to the given phase."""
        current_phase = st.session_state.current_phase
        
        if phase == RefactoringPhase.PLANNING:
            return current_phase == RefactoringPhase.ANALYSIS and st.session_state.get('code_metrics')
        elif phase == RefactoringPhase.IMPLEMENTATION:
            return current_phase == RefactoringPhase.PLANNING and st.session_state.get('selected_suggestion')
        
        return True

    def _reset_workflow(self):
        """Reset the workflow state."""
        st.session_state.current_phase = RefactoringPhase.ANALYSIS
        st.session_state.code_metrics = None
        st.session_state.refactoring_plan = []
        st.session_state.implementation_status = {}
        st.session_state.selected_suggestion = None

    def _generate_refactoring_suggestions(self) -> List[RefactoringSuggestion]:
        """Generate refactoring suggestions based on analysis results."""
        # This is a placeholder implementation
        suggestions = []
        metrics = st.session_state.code_metrics
        
        if metrics.complexity > 10:
            suggestions.append(RefactoringSuggestion(
                title="Extract Complex Methods",
                description="Break down complex methods into smaller, more focused functions",
                impact={"complexity": -20, "maintainability": +15},
                priority=1,
                effort="Medium",
                risks=["May require updating method calls"],
                before_code="def complex_method():\n    # Complex implementation",
                after_code=None
            ))
        
        if metrics.maintainability < 70:
            suggestions.append(RefactoringSuggestion(
                title="Improve Code Organization",
                description="Reorganize code structure to improve maintainability",
                impact={"maintainability": +25},
                priority=2,
                effort="High",
                risks=["Requires careful testing"],
                before_code="# Poorly organized code",
                after_code=None
            ))
        
        return suggestions 