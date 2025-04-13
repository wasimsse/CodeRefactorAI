import streamlit as st
from refactoring_miner_wrapper import RefactoringMinerWrapper
import os # Import os

def display_refactoring_miner_results(file_path):
    """
    Display refactoring detection results from RefactoringMiner.
    
    Args:
        file_path: Path to the file to analyze.
    """
    # Check if the file exists and is a Java file
    if not file_path or not os.path.exists(file_path) or not file_path.endswith('.java'):
        # Don't show any message if it's not a Java file, just return silently
        return 
        
    st.markdown("### 🔍 Refactoring Detection (Experimental)")
    
    with st.spinner("Analyzing code for potential refactorings using RefactoringMiner..."):
        # Initialize the wrapper (assuming RefactoringMiner executable is in PATH or specified)
        miner = RefactoringMinerWrapper() 
        
        # Detect refactorings
        refactorings = miner.detect_refactorings_in_file(file_path)
        
        if not refactorings:
            st.info("No specific refactoring patterns detected by RefactoringMiner in this file.")
            return
            
        # Display refactorings
        st.markdown(f"Found **{len(refactorings)}** potential refactoring patterns:")
        
        for i, ref in enumerate(refactorings):
            with st.expander(f"**{i+1}. {ref['type']}** ({ref['location']})"):
                st.markdown(f"**Description:** {ref['description']}")
                
                # Display details if available and not empty
                if ref.get('details'):
                    st.markdown("**Details:**")
                    # Convert details to a more readable format if necessary
                    st.json(ref['details'], expanded=False) 
                        
        st.markdown("---")
        st.markdown("*Note: Refactoring detection is performed using [RefactoringMiner](https://github.com/tsantalis/RefactoringMiner). This analysis focuses on identifying known refactoring patterns between code versions.*") 