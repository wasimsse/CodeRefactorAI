import os
import streamlit as st
from typing import Dict, List, Optional
import json
from pathlib import Path

class LocalModelManager:
    """Manager class for handling local LLM models"""
    
    def __init__(self):
        self.models_config_path = Path("config/local_models.json")
        self.models = self._load_models()
        
    def _load_models(self) -> Dict:
        """Load models configuration from JSON file"""
        if not self.models_config_path.exists():
            # Create default configuration if it doesn't exist
            default_models = {
                "llama2": {
                    "name": "Llama 2",
                    "path": "/path/to/llama2",
                    "type": "llama",
                    "parameters": {
                        "context_length": 2048,
                        "temperature": 0.7
                    }
                },
                "codellama": {
                    "name": "Code Llama",
                    "path": "/path/to/codellama",
                    "type": "llama",
                    "parameters": {
                        "context_length": 4096,
                        "temperature": 0.5
                    }
                },
                "mistral": {
                    "name": "Mistral",
                    "path": "/path/to/mistral",
                    "type": "mistral",
                    "parameters": {
                        "context_length": 8192,
                        "temperature": 0.7
                    }
                }
            }
            os.makedirs(self.models_config_path.parent, exist_ok=True)
            with open(self.models_config_path, 'w') as f:
                json.dump(default_models, f, indent=4)
            return default_models
        
        with open(self.models_config_path, 'r') as f:
            return json.load(f)
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return list(self.models.keys())
    
    def get_model_config(self, model_id: str) -> Optional[Dict]:
        """Get configuration for a specific model"""
        return self.models.get(model_id)
    
    def add_model(self, model_id: str, config: Dict) -> None:
        """Add a new model configuration"""
        self.models[model_id] = config
        self._save_models()
    
    def remove_model(self, model_id: str) -> None:
        """Remove a model configuration"""
        if model_id in self.models:
            del self.models[model_id]
            self._save_models()
    
    def _save_models(self) -> None:
        """Save models configuration to JSON file"""
        with open(self.models_config_path, 'w') as f:
            json.dump(self.models, f, indent=4)

def display_model_selector() -> Optional[str]:
    """Display model selector dropdown in Streamlit UI"""
    manager = LocalModelManager()
    available_models = manager.get_available_models()
    
    if not available_models:
        st.warning("No local models configured. Please add models in the configuration.")
        return None
    
    selected_model = st.selectbox(
        "Select Local Model",
        options=available_models,
        format_func=lambda x: manager.get_model_config(x)["name"],
        help="Choose a local LLM model for code refactoring"
    )
    
    if selected_model:
        model_config = manager.get_model_config(selected_model)
        with st.expander("Model Configuration"):
            st.json(model_config)
    
    return selected_model

def get_model_parameters(model_id: str) -> Dict:
    """Get parameters for a specific model"""
    manager = LocalModelManager()
    model_config = manager.get_model_config(model_id)
    return model_config.get("parameters", {}) if model_config else {}

# Create a singleton instance
local_model_manager = LocalModelManager() 