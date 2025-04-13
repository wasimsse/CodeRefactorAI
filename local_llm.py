import os
from typing import Dict, List, Optional
from pathlib import Path
import ctypes
from llama_cpp import Llama

class LocalLLMManager:
    def __init__(self, models_dir: str = "models/llm"):
        """Initialize LocalLLMManager with models directory."""
        self.models_dir = Path(models_dir)
        self.models = self._load_available_models()
        self.loaded_model = None
        self.model_configs = {
            "deepseek-coder": {
                "context_length": 4096,
                "temperature": 0.7,
                "top_p": 0.95,
                "repeat_penalty": 1.1
            },
            "codellama": {
                "context_length": 4096,
                "temperature": 0.7,
                "top_p": 0.95,
                "repeat_penalty": 1.1
            },
            "phi-2": {
                "context_length": 2048,
                "temperature": 0.7,
                "top_p": 0.95,
                "repeat_penalty": 1.1
            }
        }
        
    def _load_available_models(self) -> Dict[str, Path]:
        """Load available models from the models directory."""
        models = {}
        if not self.models_dir.exists():
            return models
            
        for file in self.models_dir.glob("*.gguf"):
            model_name = file.stem.split(".")[0]
            models[model_name] = file
            
        return models
        
    def load_model(self, model_name: str) -> bool:
        """Load a specific model."""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found in {self.models_dir}")
            
        model_path = self.models[model_name]
        config = self._get_model_config(model_name)
        
        try:
            self.loaded_model = Llama(
                model_path=str(model_path),
                n_ctx=config["context_length"],
                n_threads=os.cpu_count() or 4
            )
            return True
        except Exception as e:
            print(f"Error loading model {model_name}: {str(e)}")
            return False
            
    def _get_model_config(self, model_name: str) -> Dict:
        """Get configuration for a specific model."""
        for key, config in self.model_configs.items():
            if key in model_name.lower():
                return config
        return self.model_configs["codellama"]  # default config
        
    async def generate_refactoring(self, code: str, model_name: str, options: Dict[str, bool]) -> str:
        """Generate refactoring suggestions using the local LLM."""
        if not self.loaded_model or model_name not in str(self.models.get(self.loaded_model)):
            self.load_model(model_name)
            
        prompt = self._create_refactoring_prompt(code, options)
        config = self._get_model_config(model_name)
        
        try:
            response = self.loaded_model(
                prompt,
                max_tokens=4096,
                temperature=config["temperature"],
                top_p=config["top_p"],
                repeat_penalty=config["repeat_penalty"],
                echo=False
            )
            return response["choices"][0]["text"]
        except Exception as e:
            raise Exception(f"Error generating refactoring with {model_name}: {str(e)}")
            
    def _create_refactoring_prompt(self, code: str, options: Dict[str, bool]) -> str:
        """Create a prompt for code refactoring based on selected options."""
        prompt = """You are an expert code refactoring assistant. Please refactor the following code"""
        
        if options.get('improve_structure'):
            prompt += ", improving its structure and organization"
        if options.get('add_documentation'):
            prompt += ", adding comprehensive documentation"
        if options.get('error_handling'):
            prompt += ", implementing proper error handling"
        if options.get('solid_principles'):
            prompt += ", applying SOLID principles"
            
        prompt += ". Provide only the refactored code without any explanations:\n\n```\n" + code + "\n```"
        return prompt
        
    def get_available_models(self) -> List[str]:
        """Get list of available local models."""
        return list(self.models.keys())
        
    def is_model_loaded(self, model_name: str) -> bool:
        """Check if a specific model is currently loaded."""
        return (
            self.loaded_model is not None and
            model_name in str(self.models.get(self.loaded_model))
        ) 