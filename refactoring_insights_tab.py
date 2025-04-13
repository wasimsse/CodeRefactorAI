import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime

class RefactoringInsightsTab:
    def __init__(self):
        self.insights = []
        if 'refactoring_history' not in st.session_state:
            st.session_state.refactoring_history = []
    
    def add_insight(self, insight):
        """Add a new refactoring insight."""
        self.insights.append({
            'timestamp': datetime.now(),
            'description': insight,
            'status': 'pending'
        })
    
    def render(self):
        """Render the refactoring insights tab."""
        st.header("Refactoring Insights")
        
        # Display overview metrics
        if st.session_state.refactoring_history:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Refactorings", len(st.session_state.refactoring_history))
            with col2:
                successful = sum(1 for r in st.session_state.refactoring_history if r.get('status') == 'success')
                st.metric("Successful Refactorings", successful)
            with col3:
                st.metric("Success Rate", f"{(successful/len(st.session_state.refactoring_history))*100:.1f}%")
            
            # Display refactoring history
            st.subheader("Refactoring History")
            history_df = pd.DataFrame(st.session_state.refactoring_history)
            if not history_df.empty:
                # Create timeline visualization
                fig = px.timeline(
                    history_df,
                    x_start='timestamp',
                    y='file',
                    color='status',
                    hover_data=['suggestion']
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Display detailed history
                for item in st.session_state.refactoring_history:
                    with st.expander(f"{item['timestamp']} - {item['file']}", expanded=False):
                        st.write(f"**Suggestion:** {item['suggestion']}")
                        st.write(f"**Status:** {item['status']}")
                        if 'impact' in item:
                            st.write("**Impact:**")
                            for metric, value in item['impact'].items():
                                st.write(f"- {metric}: {value}")
        else:
            st.info("No refactoring history available yet. Start refactoring files to see insights here.")
            
            # Display sample insights
            st.markdown("""
                ### How to Get Started
                1. Select a file from the File Explorer
                2. Navigate to the Code Smells tab
                3. Review suggested refactorings
                4. Apply refactorings to improve code quality
                
                ### Benefits of Refactoring
                - Improved code maintainability
                - Better code organization
                - Enhanced performance
                - Reduced technical debt
            """) 