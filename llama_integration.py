import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import subprocess
import json
import tempfile
import streamlit as st
from llama_cpp import Llama
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LlamaCppManager:
    """Manager class for handling llama.cpp integration"""
    
    def __init__(self):
        self.llama_cpp_path = self._find_llama_cpp()
        self.model_cache = {}
        self.loaded_models = {}
        logger.info(f"LlamaCppManager initialized. llama.cpp path: {self.llama_cpp_path}")
    
    def _find_llama_cpp(self) -> Optional[Path]:
        """Find llama.cpp executable in the system"""
        # Check common installation paths
        possible_paths = [
            Path("/usr/local/bin/llama.cpp"),
            Path("/usr/bin/llama.cpp"),
            Path.home() / ".local/bin/llama.cpp",
            Path("llama.cpp"),  # Current directory
            Path("bin/llama.cpp"),  # Local bin directory
            Path("llama.cpp/build/bin/main")  # Built from source
        ]
        
        for path in possible_paths:
            if path.exists() and os.access(path, os.X_OK):
                logger.info(f"Found llama.cpp at: {path}")
                return path
        
        # If not found, check if it's in PATH
        try:
            result = subprocess.run(["which", "llama.cpp"], capture_output=True, text=True)
            if result.returncode == 0:
                path = Path(result.stdout.strip())
                logger.info(f"Found llama.cpp in PATH at: {path}")
                return path
        except Exception as e:
            logger.warning(f"Error checking PATH for llama.cpp: {e}")
        
        logger.warning("llama.cpp executable not found")
        return None

    def load_model(self, model_id: str, model_path: str, parameters: Dict[str, Any]) -> Optional[Llama]:
        """Load a model into memory using llama.cpp Python bindings"""
        if model_id in self.loaded_models:
            logger.info(f"Using cached model: {model_id}")
            return self.loaded_models[model_id]
        
        try:
            logger.info(f"Loading model {model_id} from {model_path}")
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                logger.info(f"Current working directory: {os.getcwd()}")
                logger.info(f"Available files in models/: {os.listdir('models/') if os.path.exists('models/') else 'models/ directory not found'}")
                return None
                
            model = Llama(
                model_path=model_path,
                n_ctx=parameters.get("context_length", 2048),
                n_threads=os.cpu_count() or 4,
                n_gpu_layers=1  # Use GPU acceleration if available
            )
            self.loaded_models[model_id] = model
            logger.info(f"Successfully loaded model: {model_id}")
            return model
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {str(e)}")
            if isinstance(e, FileNotFoundError):
                logger.error(f"File not found: {e.filename}")
            return None

    def generate_refactoring(self, 
                           model: Llama,
                           code: str,
                           refactoring_type: str,
                           goals: List[str],
                           constraints: List[str]) -> Optional[str]:
        """Generate code refactoring using the loaded model"""
        
        # Construct the prompt for code refactoring
        prompt = f"""You are an expert code refactoring assistant. Please refactor the following code according to the specified goals and constraints.

Code to refactor:
```python
{code}
```

Refactoring type: {refactoring_type}

Goals:
{chr(10).join('- ' + goal for goal in goals)}

Constraints:
{chr(10).join('- ' + constraint for constraint in constraints)}

Please provide the refactored code with explanations of the changes made.

Refactored code:"""

        try:
            logger.info(f"Generating refactoring with prompt length: {len(prompt)}")
            
            # Configure generation parameters
            params = {
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 0.95,
                "repeat_penalty": 1.1,
                "stop": ["</code>", "</response>"],
                "echo": False
            }
            
            # Generate completion using the model
            output = model.create_completion(prompt, **params)
            logger.info(f"Got output: {output}")
            
            if output and "choices" in output and len(output["choices"]) > 0:
                response = output["choices"][0]["text"]
                # Extract code between triple backticks
                import re
                code_pattern = r"```(?:python)?(.*?)```"
                matches = re.findall(code_pattern, response, re.DOTALL)
                
                if matches:
                    # Return the first code block found
                    return matches[0].strip()
                else:
                    # If no code blocks found, return the raw response
                    return response.strip()
            return None
            
        except Exception as e:
            logger.error(f"Error generating refactoring: {str(e)}")
            logger.error(f"Error details: {str(type(e))}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def analyze_code_quality(self, model: Llama, code: str) -> Optional[Dict[str, Any]]:
        """Analyze code quality using the model"""
        prompt = f"""Analyze the following code for quality metrics and potential improvements:

```python
{code}
```

Please provide:
1. Code quality metrics
2. Identified issues
3. Suggested improvements
4. Maintainability score

Analysis:"""

        try:
            logger.info(f"Analyzing code quality with prompt length: {len(prompt)}")
            
            # Configure generation parameters
            params = {
                "max_tokens": 2048,
                "temperature": 0.7,
                "top_p": 0.95,
                "repeat_penalty": 1.1,
                "stop": ["</analysis>", "</response>"],
                "echo": False
            }
            
            # Generate completion using the model
            output = model.create_completion(prompt, **params)
            logger.info(f"Got analysis output: {output}")
            
            if output and "choices" in output and len(output["choices"]) > 0:
                # Try to parse the response into a structured format
                analysis_text = output["choices"][0]["text"].strip()
                
                # Extract sections
                sections = {
                    "metrics": [],
                    "issues": [],
                    "improvements": [],
                    "score": None
                }
                
                current_section = None
                for line in analysis_text.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith('1. Code quality metrics'):
                        current_section = "metrics"
                    elif line.startswith('2. Identified issues'):
                        current_section = "issues"
                    elif line.startswith('3. Suggested improvements'):
                        current_section = "improvements"
                    elif line.startswith('4. Maintainability score'):
                        current_section = "score"
                    elif line and current_section:
                        if current_section == "score":
                            # Try to extract numeric score if present
                            import re
                            score_match = re.search(r'(\d+(?:\.\d+)?)', line)
                            if score_match:
                                sections["score"] = float(score_match.group(1))
                        else:
                            # Remove numbering from lines if present
                            cleaned_line = re.sub(r'^\d+\.\s*', '', line)
                            if cleaned_line:
                                sections[current_section].append(cleaned_line)
                
                return {
                    "analysis": analysis_text,
                    "structured": sections,
                    "raw_response": output
                }
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            logger.error(f"Error details: {str(type(e))}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def is_available(self) -> bool:
        """Check if llama.cpp is available"""
        return self.llama_cpp_path is not None
    
    def get_installation_instructions(self) -> str:
        """Get instructions for installing llama.cpp"""
        return """
        To install llama.cpp:
        
        1. Clone the repository:
           ```bash
           git clone https://github.com/ggerganov/llama.cpp.git
           cd llama.cpp
           ```
        
        2. Build the project using CMake:
           ```bash
           mkdir build
           cd build
           cmake ..
           cmake --build . --config Release
           ```
        
        3. Install Python bindings:
           ```bash
           pip install llama-cpp-python
           ```
        
        4. Download models and update paths in config/local_models.json
        """

# Create a singleton instance
llama_cpp_manager = LlamaCppManager()

def check_llama_cpp_installation():
    """Check if llama.cpp is installed and provide instructions if not"""
    if not llama_cpp_manager.is_available():
        st.warning("llama.cpp is not installed or not found in PATH.")
        with st.expander("Installation Instructions"):
            st.markdown(llama_cpp_manager.get_installation_instructions())
        return False
    return True

def run_local_model_refactoring(
    model_id: str,
    code: str,
    refactoring_type: str,
    goals: List[str],
    constraints: List[str]
) -> Optional[str]:
    """Run code refactoring using a local model"""
    from local_models import local_model_manager
    
    if not check_llama_cpp_installation():
        return None
    
    model_config = local_model_manager.get_model_config(model_id)
    if not model_config:
        st.error(f"Model configuration not found: {model_id}")
        return None
    
    model_path = model_config["path"]
    if not os.path.exists(model_path):
        st.error(f"Model file not found: {model_path}")
        return None
    
    try:
        # Load or get cached model
        model = llama_cpp_manager.load_model(
            model_id,
            model_path,
            model_config.get("parameters", {})
        )
        
        if not model:
            return None
            
        # Generate refactoring
        return llama_cpp_manager.generate_refactoring(
            model,
            code,
            refactoring_type,
            goals,
            constraints
        )
        
    except Exception as e:
        st.error(f"Error running model: {str(e)}")
        return None 