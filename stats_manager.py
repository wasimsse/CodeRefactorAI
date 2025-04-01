import json
import os
from datetime import datetime
from typing import Dict, Any

class StatsManager:
    """Manages application statistics and analytics."""
    
    def __init__(self):
        self.stats_file = "data/stats.json"
        self.default_stats = {
            "total_files_analyzed": 0,
            "total_projects": 0,
            "total_lines_analyzed": 0,
            "issues_identified": 0,
            "analysis_accuracy": 99.0,
            "available_metrics": 50,
            "last_updated": "",
            "daily_stats": {},
            "language_stats": {
                "Python": 0,
                "JavaScript": 0,
                "Java": 0,
                "Other": 0
            },
            "quality_improvements": {
                "complexity_reduced": 0,
                "maintainability_improved": 0,
                "bugs_fixed": 0
            }
        }
        self._initialize_stats()
    
    def _initialize_stats(self):
        """Initialize statistics file if it doesn't exist."""
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
        if not os.path.exists(self.stats_file):
            with open(self.stats_file, 'w') as f:
                json.dump(self.default_stats, f)
    
    def _load_stats(self) -> Dict[str, Any]:
        """Load current statistics from file."""
        try:
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        except Exception:
            return self.default_stats.copy()
    
    def _save_stats(self, stats: Dict[str, Any]):
        """Save statistics to file."""
        with open(self.stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
    
    def update_file_analysis(self, file_path: str, metrics: Dict[str, Any]):
        """Update statistics after analyzing a file."""
        stats = self._load_stats()
        
        # Update basic counters
        stats["total_files_analyzed"] += 1
        stats["total_lines_analyzed"] += metrics.get("raw_metrics", {}).get("loc", 0)
        stats["issues_identified"] += len(metrics.get("code_smells", []))
        
        # Update language statistics
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.py':
            stats["language_stats"]["Python"] += 1
        elif ext in ['.js', '.jsx']:
            stats["language_stats"]["JavaScript"] += 1
        elif ext in ['.java']:
            stats["language_stats"]["Java"] += 1
        else:
            stats["language_stats"]["Other"] += 1
        
        # Update quality improvements
        if metrics.get("complexity", {}).get("improved", False):
            stats["quality_improvements"]["complexity_reduced"] += 1
        if metrics.get("maintainability", {}).get("improved", False):
            stats["quality_improvements"]["maintainability_improved"] += 1
        
        # Update daily stats
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in stats["daily_stats"]:
            stats["daily_stats"][today] = {
                "files_analyzed": 0,
                "lines_analyzed": 0,
                "issues_found": 0
            }
        stats["daily_stats"][today]["files_analyzed"] += 1
        stats["daily_stats"][today]["lines_analyzed"] += metrics.get("raw_metrics", {}).get("loc", 0)
        stats["daily_stats"][today]["issues_found"] += len(metrics.get("code_smells", []))
        
        # Update timestamp
        stats["last_updated"] = datetime.now().isoformat()
        
        self._save_stats(stats)
    
    def update_project_analysis(self):
        """Update statistics after analyzing a project."""
        stats = self._load_stats()
        stats["total_projects"] += 1
        self._save_stats(stats)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return self._load_stats()
    
    def get_display_stats(self) -> Dict[str, Any]:
        """Get formatted statistics for display."""
        stats = self._load_stats()
        return {
            "analysis_accuracy": f"{stats['analysis_accuracy']}%",
            "code_metrics": f"{stats['available_metrics']}+",
            "projects_analyzed": f"{stats['total_projects']}+",
            "availability": "24/7",
            "total_files": stats["total_files_analyzed"],
            "total_lines": stats["total_lines_analyzed"],
            "issues_found": stats["issues_identified"],
            "languages": stats["language_stats"],
            "improvements": stats["quality_improvements"]
        } 