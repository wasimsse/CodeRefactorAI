import streamlit as st
from pygments import highlight
from pygments.lexers import get_lexer_for_filename
from pygments.formatters import HtmlFormatter
import os

def display_code_viewer(file_path: str):
    """Display code with syntax highlighting."""
    if not file_path or not os.path.exists(file_path):
        st.warning("Please select a valid file to view.")
        return

    try:
        # Read file content
        with open(file_path, 'r') as f:
            content = f.read()

        # Get appropriate lexer based on file extension
        lexer = get_lexer_for_filename(file_path)
        
        # Create custom CSS for code highlighting
        st.markdown("""
            <style>
                .code-viewer {
                    background: white;
                    padding: 1rem;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    margin: 1rem 0;
                }
                .code-viewer pre {
                    margin: 0;
                    padding: 1rem;
                    background: #f8f9fa;
                    border-radius: 8px;
                    overflow-x: auto;
                }
            </style>
        """, unsafe_allow_html=True)

        # Highlight code
        formatter = HtmlFormatter(style='github', linenos=True)
        highlighted_code = highlight(content, lexer, formatter)

        # Display code with line numbers
        st.markdown(f"""
            <div class="code-viewer">
                <div style="margin-bottom: 1rem;">
                    <strong>File:</strong> {os.path.basename(file_path)}
                </div>
                {highlighted_code}
            </div>
        """, unsafe_allow_html=True)

        # Add copy button
        if st.button("📋 Copy Code"):
            st.code(content)
            st.success("Code copied to clipboard!")

    except Exception as e:
        st.error(f"Error displaying file: {str(e)}") 