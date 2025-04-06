import streamlit as st
import requests
import pandas as pd
from typing import Dict, List, Any
import os
import tempfile
import zipfile
import shutil
from git import Repo
import time

class DatasetAnalyzer:
    def __init__(self):
        """Initialize DatasetAnalyzer."""
        self.data = None
        self.benchmark_repos = {
            'Python': {
                'Flask': {
                    'url': 'https://github.com/pallets/flask',
                    'description': 'Lightweight web framework',
                    'size': 'Medium',
                    'tags': ['web-framework', 'python']
                },
                'Requests': {
                    'url': 'https://github.com/psf/requests',
                    'description': 'HTTP library for Python',
                    'size': 'Medium',
                    'tags': ['http-client', 'networking']
                },
                'Django': {
                    'url': 'https://github.com/django/django',
                    'description': 'High-level Python web framework',
                    'size': 'Large',
                    'tags': ['web-framework', 'full-stack']
                }
            },
            'Java': {
                'JUnit4': {
                    'url': 'https://github.com/junit-team/junit4',
                    'description': 'Testing framework for Java',
                    'size': 'Medium',
                    'tags': ['testing', 'legacy']
                },
                'Commons-Lang': {
                    'url': 'https://github.com/apache/commons-lang',
                    'description': 'Java utility classes',
                    'size': 'Large',
                    'tags': ['utilities', 'apache']
                }
            },
            'JavaScript': {
                'Express': {
                    'url': 'https://github.com/expressjs/express',
                    'description': 'Web framework for Node.js',
                    'size': 'Medium',
                    'tags': ['web-framework', 'node']
                },
                'Vue': {
                    'url': 'https://github.com/vuejs/vue',
                    'description': 'Progressive JavaScript framework',
                    'size': 'Large',
                    'tags': ['frontend', 'framework']
                }
            }
        }
        
    def load_data(self, data: pd.DataFrame):
        """Load data for analysis."""
        self.data = data
    
    def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the dataset."""
        if self.data is None:
            return {}
        
        return {
            'rows': len(self.data),
            'columns': len(self.data.columns),
            'missing_values': self.data.isnull().sum().to_dict(),
            'dtypes': self.data.dtypes.astype(str).to_dict()
        }
    
    def get_column_stats(self, column: str) -> Dict[str, Any]:
        """Get statistics for a specific column."""
        if self.data is None or column not in self.data.columns:
            return {}
        
        stats = {}
        series = self.data[column]
        
        if pd.api.types.is_numeric_dtype(series):
            stats.update({
                'mean': series.mean(),
                'median': series.median(),
                'std': series.std(),
                'min': series.min(),
                'max': series.max()
            })
        
        stats.update({
            'unique_values': series.nunique(),
            'missing_values': series.isnull().sum(),
            'dtype': str(series.dtype)
        })
        
        return stats

    def clone_repository(self, url: str, temp_dir: str) -> str:
        """Clone a repository to a temporary directory."""
        try:
            repo_name = url.split('/')[-1]
            repo_path = os.path.join(temp_dir, repo_name)
            Repo.clone_from(url, repo_path)
            return repo_path
        except Exception as e:
            st.error(f"Error cloning repository: {str(e)}")
            return None

    def analyze_repository(self, repo_path: str, analyzer) -> Dict[str, Any]:
        """Analyze a repository using the provided code analyzer."""
        try:
            results = {
                'total_files': 0,
                'analyzed_files': 0,
                'code_smells': [],
                'complexity_issues': [],
                'maintainability_issues': [],
                'file_metrics': []
            }
            
            for root, _, files in os.walk(repo_path):
                for file in files:
                    if file.endswith(('.py', '.java', '.js', '.jsx', '.ts', '.tsx')):
                        file_path = os.path.join(root, file)
                        results['total_files'] += 1
                        
                        try:
                            analysis = analyzer.analyze_file(file_path)
                            results['analyzed_files'] += 1
                            
                            if 'code_smells' in analysis:
                                results['code_smells'].extend(analysis['code_smells'])
                            
                            if 'complexity' in analysis and 'issues' in analysis['complexity']:
                                results['complexity_issues'].extend(analysis['complexity']['issues'])
                            
                            if 'maintainability' in analysis and 'issues' in analysis['maintainability']:
                                results['maintainability_issues'].extend(analysis['maintainability']['issues'])
                            
                            results['file_metrics'].append({
                                'file': os.path.relpath(file_path, repo_path),
                                'metrics': analysis
                            })
                        except Exception as e:
                            st.warning(f"Could not analyze {file}: {str(e)}")
            
            return results
        except Exception as e:
            st.error(f"Error analyzing repository: {str(e)}")
            return None

    def display_benchmark_interface(self, code_analyzer):
        """Display the benchmark analysis interface."""
        st.title("Benchmark Dataset Analysis")
        
        st.markdown("""
        This section allows you to analyze and compare code quality metrics across various benchmark repositories.
        Select a repository to analyze or compare multiple repositories.
        """)
        
        # Repository selection
        selected_language = st.selectbox(
            "Select Programming Language",
            options=list(self.benchmark_repos.keys())
        )
        
        selected_repo = st.selectbox(
            "Select Repository",
            options=list(self.benchmark_repos[selected_language].keys())
        )
        
        repo_info = self.benchmark_repos[selected_language][selected_repo]
        
        # Display repository information
        st.markdown(f"""
        ### Selected Repository: {selected_repo}
        - **Description**: {repo_info['description']}
        - **Size**: {repo_info['size']}
        - **Tags**: {', '.join(repo_info['tags'])}
        - **URL**: [{repo_info['url']}]({repo_info['url']})
        """)
        
        if st.button("Analyze Repository"):
            with st.spinner("Cloning and analyzing repository..."):
                # Create temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Clone repository
                    repo_path = self.clone_repository(repo_info['url'], temp_dir)
                    if repo_path:
                        # Analyze repository
                        results = self.analyze_repository(repo_path, code_analyzer)
                        if results:
                            self.display_analysis_results(results)
    
    def display_analysis_results(self, results: Dict[str, Any]):
        """Display the analysis results in a structured format."""
        st.markdown("## Analysis Results")
        
        # Overview metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Files", results['total_files'])
        with col2:
            st.metric("Analyzed Files", results['analyzed_files'])
        with col3:
            success_rate = (results['analyzed_files'] / results['total_files'] * 100) if results['total_files'] > 0 else 0
            st.metric("Analysis Success Rate", f"{success_rate:.1f}%")
        
        # Code smells summary
        st.markdown("### Code Quality Issues")
        
        tabs = st.tabs(["Code Smells", "Complexity Issues", "Maintainability Issues"])
        
        with tabs[0]:
            if results['code_smells']:
                df_smells = pd.DataFrame(results['code_smells'], columns=['Issue'])
                st.dataframe(df_smells)
            else:
                st.success("No code smells detected!")
        
        with tabs[1]:
            if results['complexity_issues']:
                df_complexity = pd.DataFrame(results['complexity_issues'], columns=['Issue'])
                st.dataframe(df_complexity)
            else:
                st.success("No complexity issues detected!")
        
        with tabs[2]:
            if results['maintainability_issues']:
                df_maintainability = pd.DataFrame(results['maintainability_issues'], columns=['Issue'])
                st.dataframe(df_maintainability)
            else:
                st.success("No maintainability issues detected!")
        
        # File metrics
        st.markdown("### Detailed File Metrics")
        if results['file_metrics']:
            # Create a more detailed DataFrame for file metrics
            metrics_data = []
            for file_metric in results['file_metrics']:
                metrics = file_metric['metrics']
                metrics_data.append({
                    'File': file_metric['file'],
                    'Complexity Score': metrics.get('complexity', {}).get('score', 0),
                    'Maintainability Score': metrics.get('maintainability', {}).get('score', 0),
                    'Code Smells Count': len(metrics.get('code_smells', [])),
                    'Lines of Code': metrics.get('raw_metrics', {}).get('loc', 0)
                })
            
            df_metrics = pd.DataFrame(metrics_data)
            st.dataframe(df_metrics)
        else:
            st.warning("No detailed metrics available.")

# Create a default dataset analyzer instance
dataset_analyzer = DatasetAnalyzer() 