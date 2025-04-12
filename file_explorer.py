import streamlit as st
import os
from pathlib import Path
from typing import Dict, List, Optional

def handle_file_explorer():
    """Handle file explorer functionality."""
    # Initialize session state variables if they don't exist
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {}

    st.markdown("""
        <div style="
            background: linear-gradient(120deg, #1E88E5 0%, #42A5F5 100%);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            <h2 style="color: white; text-align: center; margin-bottom: 1rem;">
                File Explorer
            </h2>
        </div>
    """, unsafe_allow_html=True)

    # File upload section
    uploaded_file = st.file_uploader(
        "Upload a file",
        type=['py', 'java', 'js', 'cpp', 'cs', 'go', 'rb', 'php'],
        help="Upload a source code file to analyze"
    )

    if uploaded_file:
        try:
            # Save uploaded file to temp directory
            temp_dir = Path("temp_analysis")
            temp_dir.mkdir(exist_ok=True)
            
            file_path = temp_dir / uploaded_file.name
            content = uploaded_file.getvalue().decode('utf-8')
            
            with open(file_path, "w") as f:
                f.write(content)
            
            # Update session state
            st.session_state.current_file = str(file_path)
            st.session_state.uploaded_files[str(file_path)] = {
                'content': content,
                'metrics': {}  # To be filled by analyzer
            }
            
            st.success(f"File {uploaded_file.name} uploaded successfully!")
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

    # Display current files
    if st.session_state.uploaded_files:
        st.markdown("### 📁 Uploaded Files")
        
        for file_path in st.session_state.uploaded_files.keys():
            file_name = os.path.basename(file_path)
            
            # Create a button for each file
            if st.button(
                f"📄 {file_name}",
                key=f"file_{file_path}",
                help=f"Click to select {file_name}",
                use_container_width=True
            ):
                st.session_state.current_file = file_path
                st.experimental_rerun()
    else:
        st.info("No files uploaded yet. Please upload a file to begin analysis.") 