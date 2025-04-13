import streamlit as st
import plotly.express as px
import pandas as pd
from typing import Dict, List
import os

def display_code_smells_tab():
    """Display code smells analysis tab."""
    if not st.session_state.get('current_file'):
        st.info("Please select a file to analyze code smells.")
        return

    st.markdown("""
        <div style="
            background: linear-gradient(120deg, #1E88E5 0%, #42A5F5 100%);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            <h2 style="color: white; text-align: center; margin-bottom: 1rem;">
                Code Smells Analysis
            </h2>
        </div>
    """, unsafe_allow_html=True)

    # Get metrics from session state
    metrics = st.session_state.current_metrics.get('metrics', {})
    code_smells = metrics.get('code_smells', [])

    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Smells", len(code_smells))
    with col2:
        st.metric("Complexity", metrics.get('complexity', 0))
    with col3:
        st.metric("Maintainability", metrics.get('maintainability', 0))

    # Display code smells if any
    if code_smells:
        st.markdown("### 🔍 Detected Code Smells")
        
        # Group smells by category
        smell_categories = {
            'Long Method': [],
            'Complex Condition': [],
            'Duplicate Code': [],
            'Large Class': [],
            'Other': []
        }

        for smell in code_smells:
            category = 'Other'
            for cat in smell_categories.keys():
                if cat.lower() in smell.lower():
                    category = cat
                    break
            smell_categories[category].append(smell)

        # Create visualization
        smell_data = {
            'Category': [],
            'Count': []
        }
        for category, smells in smell_categories.items():
            if smells:
                smell_data['Category'].append(category)
                smell_data['Count'].append(len(smells))

        if smell_data['Category']:
            df = pd.DataFrame(smell_data)
            fig = px.pie(
                df,
                values='Count',
                names='Category',
                title='Code Smells Distribution',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)

        # Display detailed information
        for category, smells in smell_categories.items():
            if smells:
                with st.expander(f"{category} ({len(smells)})", expanded=True):
                    for smell in smells:
                        st.markdown(f"""
                            <div style="
                                background: white;
                                padding: 1rem;
                                border-radius: 8px;
                                margin: 0.5rem 0;
                                border-left: 4px solid #1E88E5;
                            ">
                                {smell}
                            </div>
                        """, unsafe_allow_html=True)

        # Add recommendations
        st.markdown("### 💡 Recommendations")
        for category, smells in smell_categories.items():
            if smells:
                with st.expander(f"Recommendations for {category}", expanded=False):
                    if category == "Long Method":
                        st.markdown("""
                            - Extract complex logic into separate methods
                            - Consider breaking down methods longer than 20 lines
                            - Use meaningful method names for extracted code
                        """)
                    elif category == "Complex Condition":
                        st.markdown("""
                            - Extract complex conditions into well-named methods
                            - Use intermediate boolean variables
                            - Consider using the Strategy pattern
                        """)
                    elif category == "Duplicate Code":
                        st.markdown("""
                            - Extract duplicate code into shared methods
                            - Consider using inheritance or composition
                            - Create utility classes for shared functionality
                        """)
                    elif category == "Large Class":
                        st.markdown("""
                            - Split class into smaller, focused classes
                            - Extract related functionality into new classes
                            - Consider using composition over inheritance
                        """)
    else:
        st.success("No code smells detected in this file! 🎉") 