import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

class ConfigManager:
    """Manages application configuration settings."""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the ConfigManager.
        
        Args:
            config_path (str): Path to the configuration file
        """
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in config file: {str(e)}", e.doc, e.pos)
    
    def get_language_config(self, language: str) -> Dict[str, Any]:
        """
        Get configuration for a specific programming language.
        
        Args:
            language (str): Programming language name
            
        Returns:
            Dict[str, Any]: Language configuration
            
        Raises:
            KeyError: If language is not supported
        """
        try:
            return self.config["supported_languages"][language.lower()]
        except KeyError:
            raise KeyError(f"Unsupported language: {language}")
    
    def get_llm_config(self, provider: str) -> Dict[str, Any]:
        """
        Get configuration for a specific LLM provider.
        
        Args:
            provider (str): LLM provider name
            
        Returns:
            Dict[str, Any]: Provider configuration
            
        Raises:
            KeyError: If provider is not configured
        """
        try:
            return self.config["llm_providers"][provider.lower()]
        except KeyError:
            raise KeyError(f"Unconfigured LLM provider: {provider}")
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """
        Get analysis configuration settings.
        
        Returns:
            Dict[str, Any]: Analysis configuration
        """
        return self.config["analysis"]
    
    def get_ui_config(self) -> Dict[str, Any]:
        """
        Get UI configuration settings.
        
        Returns:
            Dict[str, Any]: UI configuration
        """
        return self.config["ui"]
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration settings.
        
        Returns:
            Dict[str, Any]: Logging configuration
        """
        return self.config["logging"]
    
    def is_language_supported(self, file_extension: str) -> bool:
        """
        Check if a file extension is supported.
        
        Args:
            file_extension (str): File extension including the dot
            
        Returns:
            bool: True if supported, False otherwise
        """
        for lang_config in self.config["supported_languages"].values():
            if file_extension in lang_config["extensions"]:
                return True
        return False
    
    def get_language_by_extension(self, file_extension: str) -> Optional[str]:
        """
        Get the programming language name for a file extension.
        
        Args:
            file_extension (str): File extension including the dot
            
        Returns:
            Optional[str]: Language name if supported, None otherwise
        """
        for lang, config in self.config["supported_languages"].items():
            if file_extension in config["extensions"]:
                return lang
        return None
    
    def get_enabled_llm_providers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all enabled LLM providers.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of enabled providers and their configs
        """
        return {
            provider: config
            for provider, config in self.config["llm_providers"].items()
            if config.get("enabled", False)
        }
    
    def get_metric_threshold(self, metric: str, language: str) -> Optional[float]:
        """
        Get the threshold value for a specific metric and language.
        
        Args:
            metric (str): Metric name
            language (str): Programming language
            
        Returns:
            Optional[float]: Threshold value if exists, None otherwise
        """
        try:
            lang_config = self.get_language_config(language)
            return lang_config["default_metrics"].get(metric)
        except KeyError:
            return None 