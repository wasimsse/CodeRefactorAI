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
        
        if language:
            self.stats['language_stats'][language]['files'] += 1
            if metrics.get('error'):
                self.stats['language_stats'][language]['errors'] += 1
        
        # Update daily stats
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.stats['daily_stats']:
            self.stats['daily_stats'][today] = {
                'files_analyzed': 0,
                'loc_analyzed': 0,
                'refactorings': 0
            }
        
        self.stats['daily_stats'][today]['files_analyzed'] += 1
        self.stats['daily_stats'][today]['loc_analyzed'] += metrics.get('raw_metrics', {}).get('loc', 0)
        
        # Record in history
        self.stats['history'].append({
            'timestamp': datetime.now().isoformat(),
            'file_path': file_path,
            'metrics': metrics
        })
    
    def update_project_analysis(self, project_metrics: Dict[str, Any] = None):
        """Update statistics after analyzing a project."""
        self.stats['projects_analyzed'] += 1
        
        if project_metrics:
            self.stats['total_loc'] += project_metrics.get('raw_metrics', {}).get('loc', 0)
            self.stats['total_complexity'] += project_metrics.get('complexity', {}).get('score', 0)
            
            # Update quality improvements
            quality = project_metrics.get('quality_improvements', {})
            self.stats['quality_improvements']['complexity_reduced'] += quality.get('complexity_reduced', 0)
            self.stats['quality_improvements']['maintainability_improved'] += quality.get('maintainability_improved', 0)
            self.stats['quality_improvements']['bugs_fixed'] += quality.get('bugs_fixed', 0)
    
    def record_refactoring(self, file_path: str, changes: Dict[str, Any]):
        """Record a refactoring operation."""
        self.stats['refactorings_applied'] += 1
        
        # Update daily stats
        today = datetime.now().strftime('%Y-%m-%d')
        if today in self.stats['daily_stats']:
            self.stats['daily_stats'][today]['refactorings'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get all statistics."""
        return self.stats
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get analysis history."""
        return self.stats['history']
    
    def save_stats(self, file_path: str):
        """Save statistics to a file."""
        with open(file_path, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def load_stats(self, file_path: str):
        """Load statistics from a file."""
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                self.stats = json.load(f)
    
    def get_display_stats(self) -> Dict[str, Any]:
        """Get statistics formatted for display on the landing page."""
        # Calculate some derived statistics
        avg_complexity = self.stats['total_complexity'] / max(1, self.stats['files_analyzed'])
        avg_loc = self.stats['total_loc'] / max(1, self.stats['files_analyzed'])
        
        # Get the most analyzed language
        language_stats = self.stats['language_stats']
        most_analyzed_lang = max(language_stats.items(), key=lambda x: x[1]['files'])[0]
        
        # Get recent activity (last 7 days)
        today = datetime.now().strftime('%Y-%m-%d')
        recent_activity = sum(
            day_stats.get('files_analyzed', 0) 
            for day, day_stats in self.stats['daily_stats'].items() 
            if (datetime.strptime(today, '%Y-%m-%d') - datetime.strptime(day, '%Y-%m-%d')).days <= 7
        )
        
        # Calculate analysis accuracy (placeholder - in a real app this would be based on actual metrics)
        # For now, we'll use a simple heuristic based on the number of files analyzed
        analysis_accuracy = min(100, 95 + (self.stats['files_analyzed'] // 100))
        
        # Calculate code metrics (placeholder - in a real app this would be based on actual metrics)
        # For now, we'll use a simple heuristic based on the number of files analyzed
        code_metrics = self.stats['files_analyzed'] * 10
        
        # Calculate availability (placeholder - in a real app this would be based on actual metrics)
        # For now, we'll use a simple heuristic based on the number of files analyzed
        availability = min(100, 98 + (self.stats['files_analyzed'] // 200))
        
        # Calculate total files (placeholder - in a real app this would be based on actual metrics)
        # For now, we'll use a simple heuristic based on the number of files analyzed
        total_files = self.stats['files_analyzed'] * 2
        
        # Calculate total lines (placeholder - in a real app this would be based on actual metrics)
        # For now, we'll use a simple heuristic based on the total_loc
        total_lines = self.stats['total_loc'] * 1.2  # Assuming each LOC is about 1.2 lines
        
        # Calculate issues found (placeholder - in a real app this would be based on actual metrics)
        # For now, we'll use a simple heuristic based on the number of files analyzed
        issues_found = self.stats['files_analyzed'] * 3  # Assuming 3 issues per file on average
        
        # Create improvements data (placeholder - in a real app this would be based on actual metrics)
        improvements = {
            'complexity_reduced': self.stats['quality_improvements']['complexity_reduced'],
            'maintainability_improved': self.stats['quality_improvements']['maintainability_improved'],
            'bugs_fixed': self.stats['quality_improvements']['bugs_fixed'],
            'refactorings_applied': self.stats['refactorings_applied']
        }
        
        return {
            'files_analyzed': self.stats['files_analyzed'],
            'projects_analyzed': self.stats['projects_analyzed'],
            'total_loc': self.stats['total_loc'],
            'avg_complexity': round(avg_complexity, 2),
            'avg_loc': round(avg_loc, 2),
            'most_analyzed_language': most_analyzed_lang,
            'recent_activity': recent_activity,
            'refactorings_applied': self.stats['refactorings_applied'],
            'quality_improvements': self.stats['quality_improvements'],
            'analysis_accuracy': analysis_accuracy,
            'code_metrics': code_metrics,
            'availability': availability,
            'total_files': total_files,
            'total_lines': int(total_lines),
            'issues_found': issues_found,
            'improvements': improvements
        }

# Create a default stats manager instance
stats_manager = StatsManager() 