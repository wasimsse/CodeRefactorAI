import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class Logger:
    def __init__(self, config):
        """Initialize the logger with configuration."""
        self.config = config
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Set up logging configuration
        logging.basicConfig(
            level=logging.INFO if not config.DEBUG else logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / "app.log"),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("RefactoringAI")
        
    def log_info(self, message: str):
        """Log an info message."""
        self.logger.info(message)
        
    def log_debug(self, message: str):
        """Log a debug message."""
        self.logger.debug(message)
        
    def log_warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)
        
    def log_error(self, message: str):
        """Log an error message."""
        self.logger.error(message)
        
    def log_critical(self, message: str):
        """Log a critical message."""
        self.logger.critical(message)
        
    def log_analysis_result(self, file_path: str, results: Dict[str, Any]):
        """Log code analysis results."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "results": results
        }
        self._append_json_log("analysis_results.json", log_entry)
        
    def log_refactoring_result(self, file_path: str, original_code: str, 
                             refactored_code: str, model: str):
        """Log refactoring results."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "model": model,
            "original_code": original_code,
            "refactored_code": refactored_code
        }
        self._append_json_log("refactoring_results.json", log_entry)
        
    def log_metrics(self, metrics: Dict[str, Any]):
        """Log system metrics."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }
        self._append_json_log("system_metrics.json", log_entry)
        
    def log_exception(self, exception: Exception, context: str):
        """Log an exception with context."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "exception_type": type(exception).__name__,
            "message": str(exception)
        }
        self._append_json_log("exceptions.json", log_entry)
        self.log_error(f"{context}: {str(exception)}")
        
    def log_startup_diagnostics(self):
        """Log system startup diagnostics."""
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "python_version": os.sys.version,
            "config": {
                "debug": self.config.DEBUG,
                "log_level": self.config.LOG_LEVEL,
                "max_file_size": self.config.MAX_FILE_SIZE,
                "max_upload_size": self.config.MAX_UPLOAD_SIZE
            }
        }
        self._append_json_log("startup_diagnostics.json", diagnostics)
        
    def log_shutdown(self):
        """Log application shutdown."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "application_shutdown"
        }
        self._append_json_log("shutdown.json", log_entry)
        self.log_info("Application shutting down")
        
    def _append_json_log(self, filename: str, log_entry: Dict[str, Any]):
        """Append a log entry to a JSON log file."""
        log_file = self.log_dir / filename
        try:
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
                
            logs.append(log_entry)
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            self.log_error(f"Error writing to log file {filename}: {str(e)}") 