import json
import os
from datetime import datetime
from typing import Dict, Any, List

class StatsManager:
    """Manages application statistics and analytics."""
    
    def __init__(self):
        """Initialize StatsManager."""
        self.stats = {
            'files_analyzed': 0,
            'total_loc': 0,
            'total_complexity': 0,
            "refactorings_applied": 0,
            "history": [],
            'projects_analyzed': 0,
            'language_stats': {
                'Python': {'files': 0, 'errors': 0},
                'Java': {'files': 0, 'errors': 0},
                'JavaScript': {'files': 0, 'errors': 0},
                'C++': {'files': 0, 'errors': 0},
                'C#': {'files': 0, 'errors': 0}
            },
            'daily_stats': {},
            'quality_improvements': {
                'complexity_reduced': 0,
                'maintainability_improved': 0,
                'bugs_fixed': 0
            }
        }
    
    def update_stats(self, metrics: Dict[str, Any]):
        """Update statistics with new metrics."""
        raw_metrics = metrics.get('raw_metrics', {})
        self.stats['files_analyzed'] += 1
        self.stats['total_loc'] += raw_metrics.get('loc', 0)
        self.stats['total_complexity'] += metrics.get('complexity', {}).get('score', 0)
    
    def update_file_analysis(self, file_path: str, metrics: Dict[str, Any]):
        """Update statistics after analyzing a file."""
        # Update basic counters
        self.stats['files_analyzed'] += 1
        self.stats['total_loc'] += metrics.get('raw_metrics', {}).get('loc', 0)
        
        # Update language statistics
        ext = os.path.splitext(file_path)[1].lower()
        language = {
            '.py': 'Python',
            '.java': 'Java',
            '.js': 'JavaScript',
            '.cpp': 'C++',
            '.cs': 'C#'
        }.get(ext)
        
        if language and language in self.stats['language_stats']:
            self.stats['language_stats'][language]['files'] += 1
        
        # Update quality improvements
        if metrics.get('complexity', {}).get('improved', False):
            self.stats['quality_improvements']['complexity_reduced'] += 1
        if metrics.get('maintainability', {}).get('improved', False):
            self.stats['quality_improvements']['maintainability_improved'] += 1
        
        # Update daily stats
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.stats['daily_stats']:
            self.stats['daily_stats'][today] = {
                'files_analyzed': 0,
                'lines_analyzed': 0,
                'issues_found': 0
            }
        
        self.stats['daily_stats'][today]['files_analyzed'] += 1
        self.stats['daily_stats'][today]['lines_analyzed'] += metrics.get('raw_metrics', {}).get('loc', 0)
        self.stats['daily_stats'][today]['issues_found'] += len(metrics.get('code_smells', []))
    
    def update_project_analysis(self, project_metrics: Dict[str, Any] = None):
        """Update statistics after analyzing a project."""
        self.stats['projects_analyzed'] += 1
        
        if project_metrics:
            # Update total metrics
            self.stats['total_loc'] += project_metrics.get('raw_metrics', {}).get('loc', 0)
            self.stats['total_complexity'] += project_metrics.get('complexity', {}).get('score', 0)
            
            # Update files analyzed
            self.stats['files_analyzed'] += project_metrics.get('files_analyzed', 0)
            
            # Update quality improvements if any were found
            if project_metrics.get('improvements'):
                self.stats['quality_improvements']['complexity_reduced'] += project_metrics['improvements'].get('complexity_reduced', 0)
                self.stats['quality_improvements']['maintainability_improved'] += project_metrics['improvements'].get('maintainability_improved', 0)
                self.stats['quality_improvements']['bugs_fixed'] += project_metrics['improvements'].get('bugs_fixed', 0)
    
    def record_refactoring(self, file_path: str, changes: Dict[str, Any]):
        """Record a refactoring operation."""
        self.stats['refactorings_applied'] += 1
        self.stats['history'].append({
            'timestamp': datetime.now().isoformat(),
            'file': file_path,
            'changes': changes
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return self.stats
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get refactoring history."""
        return self.stats['history']
    
    def save_stats(self, file_path: str):
        """Save statistics to a file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"Error saving stats: {str(e)}")
    
    def load_stats(self, file_path: str):
        """Load statistics from a file."""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
        except Exception as e:
            print(f"Error loading stats: {str(e)}")

# Create a default stats manager instance
stats_manager = StatsManager() 