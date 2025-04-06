import os
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
from code_analyzer import CodeAnalyzer

class ProjectAnalyzer:
    def __init__(self, config):
        """Initialize ProjectAnalyzer with configuration."""
        self.config = config
        self.code_analyzer = CodeAnalyzer(config)
    
    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analyze the entire project and return metrics."""
        try:
            project_path = Path(project_path)
            project_structure = self._get_project_structure(project_path)
            project_metrics = self._calculate_project_metrics(project_path)
            
            return {
                'structure': project_structure,
                'metrics': project_metrics
            }
        except Exception as e:
            return {
                'error': str(e),
                'structure': self._get_default_structure(),
                'metrics': self._get_default_metrics()
            }
    
    def analyze_directory(self, dir_path: str) -> Dict[str, Any]:
        """Analyze a specific directory and return metrics."""
        try:
            dir_path = Path(dir_path)
            dir_structure = self._get_directory_structure(dir_path)
            dir_metrics = self._calculate_directory_metrics(dir_path)
            
            return {
                'structure': dir_structure,
                'metrics': dir_metrics,
                'visualizations': self._generate_visualizations(dir_metrics)
            }
        except Exception as e:
            return {
                'error': str(e),
                'structure': {},
                'metrics': self._get_default_metrics(),
                'visualizations': {}
            }
    
    def _get_project_structure(self, project_path: Path) -> Dict[str, Any]:
        """Get the project structure as a nested dictionary."""
        def build_tree(path: Path) -> Dict[str, Any]:
            tree = {}
            try:
                for item in path.iterdir():
                    if item.name.startswith('.'):
                        continue
                    
                    if item.is_file():
                        if item.suffix.lower() in ['.py', '.java', '.cpp', '.js', '.cs']:
                            tree[item.name] = 'file'
                    else:
                        subtree = build_tree(item)
                        if subtree:  # Only add non-empty directories
                            tree[item.name] = {
                                'type': 'directory',
                                'files': len([x for x in subtree.items() if x[1] == 'file']),
                                'subdirs': len([x for x in subtree.items() if isinstance(x[1], dict)]),
                                'children': subtree
                            }
            except Exception:
                pass
            return tree
        
        return build_tree(project_path)
    
    def _get_directory_structure(self, dir_path: Path) -> Dict[str, Any]:
        """Get the structure of a specific directory."""
        structure = {
            'files': {},
            'subdirs': {},
            'total_files': 0,
            'total_subdirs': 0
        }
        
        for item in dir_path.iterdir():
            if item.is_file():
                ext = item.suffix.lower()
                structure['files'][ext] = structure['files'].get(ext, 0) + 1
                structure['total_files'] += 1
            elif item.is_dir():
                structure['subdirs'][item.name] = {
                    'files': len(list(item.glob('**/*'))),
                    'subdirs': len(list(item.glob('**/*/'))),
                    'path': str(item)
                }
                structure['total_subdirs'] += 1
        
        return structure
    
    def _calculate_project_metrics(self, project_path: Path) -> Dict[str, Any]:
        """Calculate project metrics with improved structure for visualization."""
        metrics = {
            'overall_score': 0,
            'complexity_by_file': {},
            'quality_metrics': {
                'Maintainability': [],
                'Complexity': []
            },
            'issues_by_severity': {
                'High': 0,
                'Medium': 0,
                'Low': 0
            },
            'language_stats': {
                'Java': {'files': 0, 'errors': 0},
                'Python': {'files': 0, 'errors': 0},
                'JavaScript': {'files': 0, 'errors': 0},
                'C++': {'files': 0, 'errors': 0},
                'C#': {'files': 0, 'errors': 0}
            }
        }
        
        total_files = 0
        for root, _, files in os.walk(project_path):
            for file in files:
                file_path = Path(root) / file
                file_ext = file_path.suffix.lower()
                
                # Skip non-source files
                if file_ext not in ['.py', '.java', '.cpp', '.js', '.cs']:
                    continue
                    
                try:
                    # Determine language
                    language = {
                        '.py': 'Python',
                        '.java': 'Java',
                        '.cpp': 'C++',
                        '.js': 'JavaScript',
                        '.cs': 'C#'
                    }.get(file_ext, 'Unknown')
                    
                    # Update language stats
                    metrics['language_stats'][language]['files'] += 1
                    
                    # Analyze file
                    file_metrics = self.code_analyzer.analyze_file(str(file_path))
                    
                    # Store complexity score
                    rel_path = file_path.relative_to(project_path)
                    metrics['complexity_by_file'][str(rel_path)] = file_metrics.get('complexity', {}).get('score', 0)
                    
                    # Store quality metrics
                    metrics['quality_metrics']['Maintainability'].append(
                        file_metrics.get('maintainability', {}).get('score', 0)
                    )
                    metrics['quality_metrics']['Complexity'].append(
                        file_metrics.get('complexity', {}).get('score', 0)
                    )
                    
                    # Count issues by severity
                    self._categorize_issues(file_metrics, metrics['issues_by_severity'])
                    
                    total_files += 1
                    
                except Exception as e:
                    # Log error and update language stats
                    metrics['language_stats'][language]['errors'] += 1
                    print(f"Error analyzing {file_path}: {str(e)}")
                    continue
        
        # Calculate overall score
        if total_files > 0:
            metrics['overall_score'] = sum(metrics['quality_metrics']['Maintainability']) / total_files
        
        return metrics
    
    def _calculate_directory_metrics(self, dir_path: Path) -> Dict[str, Any]:
        """Calculate metrics for a specific directory."""
        metrics = {
            'complexity': {'score': 0, 'issues': []},
            'maintainability': {'score': 0, 'issues': []},
            'code_smells': [],
            'performance': {'score': 0, 'issues': []},
            'raw_metrics': {
                'loc': 0,
                'lloc': 0,
                'sloc': 0,
                'comments': 0,
                'multi': 0,
                'blank': 0
            },
            'halstead_metrics': {
                'vocabulary': 0,
                'length': 0,
                'volume': 0,
                'difficulty': 0,
                'effort': 0,
                'time': 0,
                'bugs': 0
            }
        }
        
        total_files = 0
        for item in dir_path.iterdir():
            if item.is_file() and item.suffix.lower() in ['.py', '.java', '.cpp', '.js', '.cs']:
                file_metrics = self.code_analyzer.analyze_file(str(item))
                
                # Aggregate metrics
                metrics['complexity']['score'] += file_metrics['complexity']['score']
                metrics['maintainability']['score'] += file_metrics['maintainability']['score']
                metrics['code_smells'].extend(file_metrics['code_smells'])
                metrics['performance']['score'] += file_metrics['performance']['score']
                
                # Aggregate raw metrics
                for key in metrics['raw_metrics']:
                    metrics['raw_metrics'][key] += file_metrics['raw_metrics'][key]
                
                # Aggregate Halstead metrics
                for key in metrics['halstead_metrics']:
                    metrics['halstead_metrics'][key] += file_metrics['halstead_metrics'][key]
                
                total_files += 1
        
        # Calculate averages
        if total_files > 0:
            metrics['complexity']['score'] /= total_files
            metrics['maintainability']['score'] /= total_files
            metrics['performance']['score'] /= total_files
        
        return metrics
    
    def _categorize_issues(self, file_metrics: Dict, issues_by_severity: Dict) -> None:
        """Categorize issues by severity with improved handling."""
        try:
            # Handle code smells
            for smell in file_metrics.get('code_smells', []):
                if any(keyword in smell.lower() for keyword in ['critical', 'severe', 'error']):
                    issues_by_severity['High'] += 1
                elif any(keyword in smell.lower() for keyword in ['warning', 'caution']):
                    issues_by_severity['Medium'] += 1
                else:
                    issues_by_severity['Low'] += 1
            
            # Handle complexity issues
            complexity_issues = file_metrics.get('complexity', {}).get('issues', [])
            for issue in complexity_issues:
                if 'high' in issue.lower() or 'critical' in issue.lower():
                    issues_by_severity['High'] += 1
                elif 'medium' in issue.lower() or 'moderate' in issue.lower():
                    issues_by_severity['Medium'] += 1
                else:
                    issues_by_severity['Low'] += 1
            
            # Handle maintainability issues
            maintainability_issues = file_metrics.get('maintainability', {}).get('issues', [])
            for issue in maintainability_issues:
                if 'high' in issue.lower() or 'critical' in issue.lower():
                    issues_by_severity['High'] += 1
                elif 'medium' in issue.lower() or 'moderate' in issue.lower():
                    issues_by_severity['Medium'] += 1
                else:
                    issues_by_severity['Low'] += 1
                
        except Exception as e:
            print(f"Error categorizing issues: {str(e)}")
            # Default to medium severity if categorization fails
            issues_by_severity['Medium'] += 1
    
    def _get_default_structure(self) -> Dict[str, Any]:
        """Get default project structure."""
        return {'root': {'type': 'directory', 'files': 0, 'subdirs': 0, 'children': {}}}
    
    def _get_default_metrics(self) -> Dict[str, Any]:
        """Get default metrics."""
        return {
            'overall_score': 0,
            'complexity_by_file': {},
            'quality_metrics': pd.DataFrame({
                'Maintainability': [],
                'Complexity': []
            }),
            'issues_by_severity': {
                'High': 0,
                'Medium': 0,
                'Low': 0
            }
        }
    
    def _generate_visualizations(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate visualizations for the metrics."""
        visualizations = {}
        
        # Create radar chart for quality metrics
        quality_metrics = {
            'Complexity': metrics['complexity']['score'],
            'Maintainability': metrics['maintainability']['score'],
            'Performance': metrics['performance']['score']
        }
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=list(quality_metrics.values()),
            theta=list(quality_metrics.keys()),
            fill='toself',
            name='Code Quality'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=False,
            title='Code Quality Overview'
        )
        
        visualizations['quality_radar'] = fig
        
        # Create bar chart for code composition
        raw_metrics = metrics['raw_metrics']
        composition_data = {
            'Metric': [
                'Lines of Code',
                'Logical Lines',
                'Source Lines',
                'Comments',
                'Multi-line Strings',
                'Blank Lines'
            ],
            'Value': [
                raw_metrics['loc'],
                raw_metrics['lloc'],
                raw_metrics['sloc'],
                raw_metrics['comments'],
                raw_metrics['multi'],
                raw_metrics['blank']
            ]
        }
        
        df = pd.DataFrame(composition_data)
        fig = px.bar(df, x='Metric', y='Value', title='Code Composition')
        visualizations['composition_bar'] = fig
        
        # Create pie chart for code distribution
        if 'structure' in metrics:
            structure = metrics['structure']
            if 'files' in structure:
                file_types = pd.DataFrame({
                    'Type': list(structure['files'].keys()),
                    'Count': list(structure['files'].values())
                })
                fig = px.pie(file_types, values='Count', names='Type', title='File Type Distribution')
                visualizations['file_distribution'] = fig
        
        return visualizations 