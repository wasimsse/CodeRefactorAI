import os
from typing import Dict, Optional, List
from dataclasses import dataclass
from llama_integration import LlamaCppManager
from llm_integration import LLMProvider
import streamlit as st

@dataclass
class RefactoringOptions:
    """Options for code refactoring."""
    improve_structure: bool = True
    add_documentation: bool = True
    enhance_readability: bool = True
    implement_error_handling: bool = True
    optimize_performance: bool = False
    add_tests: bool = False

@dataclass
class RefactoringResult:
    """Result of code refactoring."""
    original_code: str
    refactored_code: str
    improvements: List[str]
    execution_time: float
    actions_performed: List[str]

class RefactoringManager:
    def __init__(self, model_manager: LlamaCppManager):
        self.model_manager = model_manager
        self.refactoring_types = {
            "General Improvement": "Improve code quality, readability and maintainability",
            "Performance Optimization": "Optimize code for better performance",
            "Code Style": "Fix code style issues and follow best practices",
            "Documentation": "Add or improve code documentation",
            "Error Handling": "Improve error handling and add validation"
        }
    
    def get_refactoring_prompt(self, code: str, refactoring_type: str) -> str:
        """Generate a prompt for code refactoring based on the selected type."""
        base_prompt = f"""Please refactor the following Python code. 
Focus on {self.refactoring_types[refactoring_type]}.
Provide a clear explanation of the changes made.

Original code:
```python
{code}
```

Refactored code with explanations:"""
        return base_prompt
    
    def refactor_code(self, 
                     code: str, 
                     refactoring_type: str,
                     model_path: str,
                     context_length: int = 2048,
                     temperature: float = 0.7) -> Dict:
        """Refactor code using the selected model and refactoring type."""
        if not code:
            return {
                "success": False,
                "error": "No code provided for refactoring"
            }
        
        try:
            # Generate prompt
            prompt = self.get_refactoring_prompt(code, refactoring_type)
            
            # Run model
            response = self.model_manager.run_model(
                model_path=model_path,
                prompt=prompt,
                max_tokens=context_length,
                temperature=temperature
            )
            
            # Parse response
            if not response:
                return {
                    "success": False,
                    "error": "Model did not generate a response"
                }
            
            # Extract refactored code and explanations
            parts = response.split("```")
            explanations = []
            refactored_code = ""
            
            for i, part in enumerate(parts):
                if i % 2 == 0:  # Outside code blocks
                    explanations.append(part.strip())
                else:  # Inside code blocks
                    if part.startswith("python"):
                        part = part[6:]  # Remove "python" from the start
                    refactored_code = part.strip()
            
            return {
                "success": True,
                "original_code": code,
                "refactored_code": refactored_code,
                "explanations": [exp for exp in explanations if exp],
                "refactoring_type": refactoring_type
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error during refactoring: {str(e)}"
            }

    def _construct_prompt(self, code: str, options: RefactoringOptions) -> str:
        """Construct a prompt for the LLM based on refactoring options."""
        prompt = "Please refactor the following code"
        if options.improve_structure:
            prompt += ", improving its structure and organization"
        if options.add_documentation:
            prompt += ", adding comprehensive documentation"
        if options.enhance_readability:
            prompt += ", enhancing readability"
        if options.implement_error_handling:
            prompt += ", implementing proper error handling"
        if options.optimize_performance:
            prompt += ", optimizing performance"
        if options.add_tests:
            prompt += ", adding unit tests"
        
        prompt += ". Provide the refactored code and explain the improvements made.\n\nOriginal code:\n```\n"
        prompt += code + "\n```"
        return prompt
        
    async def refactor_code_async(
        self, 
        code: str, 
        options: RefactoringOptions,
        model_config: Dict,
        use_local_model: bool = True
    ) -> RefactoringResult:
        """Refactor code using either local or cloud LLM."""
        import time
        start_time = time.time()
        
        prompt = self._construct_prompt(code, options)
        
        try:
            if use_local_model:
                # Use local LLM (llama.cpp)
                response = self.model_manager.run_model(
                    model_path=model_config['path'],
                    prompt=prompt,
                    max_tokens=model_config.get('max_tokens', 2048),
                    temperature=model_config.get('temperature', 0.7),
                    repeat_penalty=model_config.get('repeat_penalty', 1.1)
                )
            else:
                # Use cloud LLM provider
                response = await self.llm_provider.generate_completion(
                    prompt=prompt,
                    max_tokens=model_config.get('max_tokens', 2048),
                    temperature=model_config.get('temperature', 0.7)
                )
            
            # Extract refactored code and improvements from response
            refactored_code = self._extract_code(response)
            improvements = self._extract_improvements(response)
            
            execution_time = time.time() - start_time
            
            return RefactoringResult(
                original_code=code,
                refactored_code=refactored_code,
                improvements=improvements,
                execution_time=execution_time,
                actions_performed=self._get_actions_performed(options)
            )
            
        except Exception as e:
            st.error(f"Error during refactoring: {str(e)}")
            return None
            
    def _extract_code(self, response: str) -> str:
        """Extract refactored code from LLM response."""
        # Look for code blocks between triple backticks
        import re
        code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", response, re.DOTALL)
        return code_blocks[0] if code_blocks else response
        
    def _extract_improvements(self, response: str) -> List[str]:
        """Extract list of improvements from LLM response."""
        # Look for improvements after the code block
        improvements = []
        in_improvements = False
        
        for line in response.split('\n'):
            if line.strip().lower().startswith(('improvement', 'change', '- ')):
                improvements.append(line.strip())
                in_improvements = True
            elif in_improvements and line.strip():
                improvements.append(line.strip())
                
        return improvements
        
    def _get_actions_performed(self, options: RefactoringOptions) -> List[str]:
        """Get list of refactoring actions performed based on options."""
        actions = []
        if options.improve_structure:
            actions.append("Improved code structure and organization")
        if options.add_documentation:
            actions.append("Added comprehensive documentation")
        if options.enhance_readability:
            actions.append("Enhanced code readability")
        if options.implement_error_handling:
            actions.append("Implemented error handling")
        if options.optimize_performance:
            actions.append("Optimized performance")
        if options.add_tests:
            actions.append("Added unit tests")
        return actions 