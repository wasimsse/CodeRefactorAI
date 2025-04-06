import ast
import re
from typing import Dict, Any, List
from pathlib import Path
import os
import mimetypes

def is_binary_file(file_path: str) -> bool:
    """
    Check if a file is binary based on its extension or content.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        bool: True if the file is binary, False otherwise
    """
    # Check file extension
    ext = os.path.splitext(file_path)[1].lower()
    
    # List of known binary file extensions
    binary_extensions = [
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.ico', '.svg', '.webp',
        # Audio
        '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a',
        # Video
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm',
        # Documents
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        # Archives
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
        # Executables
        '.exe', '.dll', '.so', '.dylib', '.bin',
        # Other binary formats
        '.db', '.sqlite', '.sqlite3', '.dat', '.bin'
    ]
    
    if ext in binary_extensions:
        return True
    
    # If extension is not in our list, check mime type
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and not mime_type.startswith('text/'):
        return True
    
    return False

def analyze_file(file_path: str, content: str = None, config: Dict = None) -> dict:
    """
    Standalone function to analyze a single file and return its metrics.
    
    Args:
        file_path: Path to the file to analyze
        content: Optional file content if already loaded
        config: Optional configuration dictionary
        
    Returns:
        dict: Dictionary containing all metrics and analysis results
    """
    analyzer = CodeAnalyzer(config or {})
    return analyzer.analyze_file(file_path, content)

class CodeAnalyzer:
    def __init__(self, config: Dict = None):
        """Initialize CodeAnalyzer with configuration."""
        self.config = config or {}
        
    def analyze_file(self, file_path: str, content: str = None) -> dict:
        """
        Analyze a single file and return its metrics.
        
        Args:
            file_path: Path to the file to analyze
            content: Optional file content if already loaded
            
        Returns:
            dict: Dictionary containing all metrics and analysis results
        """
        try:
            # Initialize metrics dictionary
            metrics = {
                'file_path': file_path,
                'raw_metrics': {
                    'loc': 0,
                    'sloc': 0,
                    'comments': 0,
                    'blank': 0,
                    'classes': 0,
                    'methods': 0,
                    'functions': 0,
                    'imports': 0
                },
                'complexity': {'score': 0, 'issues': []},
                'maintainability': {'score': 0, 'issues': []},
                'code_smells': [],
                'refactoring_opportunities': []
            }
            
            # Skip binary files
            if is_binary_file(file_path):
                metrics['raw_metrics']['loc'] = 0
                metrics['complexity']['score'] = 0
                metrics['maintainability']['score'] = 0
                metrics['code_smells'] = ["Binary file - analysis skipped"]
                return metrics
            
            # Read file content if not provided
            if content is None:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    print(f"Error analyzing file {file_path}: File appears to be binary or uses an unsupported encoding")
                    metrics['code_smells'] = ["Binary file - analysis skipped"]
                    return metrics
            
            # Get file extension
            ext = os.path.splitext(file_path)[1].lower()
            
            # Basic analysis
            lines = content.splitlines()
            metrics['raw_metrics']['loc'] = len(lines)
            
            # Count blank lines and comments
            for line in lines:
                line = line.strip()
                if not line:
                    metrics['raw_metrics']['blank'] += 1
                elif line.startswith('#'):
                    metrics['raw_metrics']['comments'] += 1
            
            # Calculate SLOC
            metrics['raw_metrics']['sloc'] = metrics['raw_metrics']['loc'] - metrics['raw_metrics']['blank'] - metrics['raw_metrics']['comments']
            
            # Parse AST for deeper analysis
            try:
                tree = ast.parse(content)
                metrics.update(self._analyze_ast(tree))
            except SyntaxError:
                # If AST parsing fails, still return basic metrics
                pass
            
            # Calculate quality scores
            metrics['complexity']['score'] = self._calculate_complexity_score(metrics)
            metrics['maintainability']['score'] = self._calculate_maintainability_score(metrics)
            
            # Detect code smells and suggest refactoring
            metrics['code_smells'] = self._detect_code_smells(metrics)
            metrics['refactoring_opportunities'] = self._suggest_refactoring(metrics)
            
            return metrics
            
        except Exception as e:
            print(f"Error analyzing file {file_path}: {str(e)}")
            return metrics
    
    def _analyze_ast(self, tree: ast.AST) -> dict:
        """Analyze AST to gather code metrics."""
        metrics = {
            'raw_metrics': {
                'classes': 0,
                'methods': 0,
                'functions': 0,
                'imports': 0
            },
            'complexity': {
                'score': 0,
                'issues': []
            }
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                metrics['raw_metrics']['classes'] += 1
                # Check class complexity
                if len(node.body) > 20:
                    metrics['complexity']['issues'].append(
                        f"Class {node.name} is too large ({len(node.body)} lines)")
            
            elif isinstance(node, ast.FunctionDef):
                if isinstance(node.parent, ast.ClassDef):
                    metrics['raw_metrics']['methods'] += 1
                else:
                    metrics['raw_metrics']['functions'] += 1
                # Check function complexity
                if len(node.body) > 15:
                    metrics['complexity']['issues'].append(
                        f"Function {node.name} is too long ({len(node.body)} lines)")
            
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                metrics['raw_metrics']['imports'] += 1
        
        return metrics
    
    def _calculate_complexity_score(self, metrics: Dict) -> float:
        """Calculate code complexity score (0-100)."""
        score = 100
        
        # Reduce score based on various metrics
        raw = metrics['raw_metrics']
        
        # Penalize for large files
        if raw['loc'] > 500:
            score -= 10
        elif raw['loc'] > 1000:
            score -= 20
        
        # Penalize for low comment ratio
        comment_ratio = raw['comments'] / raw['loc'] if raw['loc'] > 0 else 0
        if comment_ratio < 0.1:
            score -= 10
        
        # Penalize for complexity issues
        score -= len(metrics['complexity']['issues']) * 5
        
        return max(0, min(100, score))
    
    def _calculate_maintainability_score(self, metrics: Dict) -> float:
        """Calculate code maintainability score (0-100)."""
        score = 100
        
        # Reduce score based on various metrics
        raw = metrics['raw_metrics']
        
        # Penalize for large classes and functions
        score -= raw['classes'] * 2
        score -= raw['methods'] * 1
        score -= raw['functions'] * 1
        
        # Penalize for complexity
        score -= (100 - metrics['complexity']['score']) * 0.3
        
        # Penalize for code smells
        score -= len(metrics.get('code_smells', [])) * 5
        
        return max(0, min(100, score))
    
    def _detect_code_smells(self, metrics: Dict) -> List[str]:
        """Detect code smells based on metrics."""
        smells = []
        raw = metrics['raw_metrics']
        
        # Large file smell
        if raw['loc'] > 500:
            smells.append(f"File is too large ({raw['loc']} lines)")
        
        # Low comment ratio smell
        comment_ratio = raw['comments'] / raw['loc'] if raw['loc'] > 0 else 0
        if comment_ratio < 0.1:
            smells.append("Insufficient comments")
        
        # Too many methods smell
        if raw['methods'] > 10:
            smells.append(f"Too many methods ({raw['methods']})")
        
        # Too many imports smell
        if raw['imports'] > 15:
            smells.append(f"Too many imports ({raw['imports']})")
        
        return smells
    
    def _suggest_refactoring(self, metrics: Dict) -> List[str]:
        """Suggest refactoring opportunities based on metrics."""
        suggestions = []
        raw = metrics['raw_metrics']
        
        # Suggest file splitting
        if raw['loc'] > 500:
            suggestions.append("Consider splitting this file into smaller modules")
        
        # Suggest class extraction
        if raw['methods'] > 10:
            suggestions.append("Consider extracting some methods into a new class")
        
        # Suggest adding comments
        comment_ratio = raw['comments'] / raw['loc'] if raw['loc'] > 0 else 0
        if comment_ratio < 0.1:
            suggestions.append("Add more comments to improve code documentation")
        
        # Add complexity-based suggestions
        if metrics['complexity']['score'] < 60:
            suggestions.append("Consider simplifying complex code sections")
        
        return suggestions
    
    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analyze an entire project directory and return metrics."""
        try:
            project_metrics = {
                'complexity': {'score': 0, 'issues': []},
                'maintainability': {'score': 0, 'issues': []},
                'code_smells': [],
                'raw_metrics': {
                    'loc': 0,
                    'sloc': 0,
                    'comments': 0,
                    'blank': 0
                },
                'files_analyzed': 0,
                'total_files': 0
            }
            
            # Walk through the project directory
            for root, _, files in os.walk(project_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_metrics = self.analyze_file(file_path)
                        
                        # Aggregate metrics
                        project_metrics['complexity']['score'] += file_metrics['complexity'].get('score', 0)
                        project_metrics['maintainability']['score'] += file_metrics['maintainability'].get('score', 0)
                        project_metrics['code_smells'].extend(file_metrics.get('code_smells', []))
                        
                        # Aggregate raw metrics
                        for key in project_metrics['raw_metrics'].keys():
                            project_metrics['raw_metrics'][key] += file_metrics.get('raw_metrics', {}).get(key, 0)
                        
                        project_metrics['files_analyzed'] += 1
                    except Exception as e:
                        print(f"Error analyzing file {file_path}: {str(e)}")
                        continue
                    
                    project_metrics['total_files'] += 1
            
            # Calculate average scores
            if project_metrics['files_analyzed'] > 0:
                project_metrics['complexity']['score'] /= project_metrics['files_analyzed']
                project_metrics['maintainability']['score'] /= project_metrics['files_analyzed']
            
            return project_metrics
            
        except Exception as e:
            print(f"Error analyzing project: {str(e)}")
            return {
                'complexity': {'score': 0, 'issues': [str(e)]},
                'maintainability': {'score': 0, 'issues': [str(e)]},
                'code_smells': [],
                'raw_metrics': {
                    'loc': 0,
                    'sloc': 0,
                    'comments': 0,
                    'blank': 0
                },
                'files_analyzed': 0,
                'total_files': 0
            } 