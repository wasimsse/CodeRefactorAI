from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import os
from enum import Enum
import streamlit as st
from dataclasses import dataclass
import json

# Import LLM libraries
from llama_cpp import Llama
import openai
import anthropic
import google.generativeai as genai
import cohere

class LLMType(Enum):
    LOCAL = "Local"
    OPENAI = "OpenAI"
    ANTHROPIC = "Anthropic"
    GOOGLE = "Google"
    COHERE = "Cohere"

@dataclass
class RefactoringResponse:
    refactored_code: str
    explanation: str
    changes_made: List[str]
    confidence: float
    metrics: Dict[str, float]

class LLMRefactoring(ABC):
    @abstractmethod
    def generate_refactoring(self, code: str, context: Dict[str, Any]) -> RefactoringResponse:
        pass

class LocalLLMRefactoring(LLMRefactoring):
    def __init__(self, model_path: str):
        self.llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=4
        )

    def generate_refactoring(self, code: str, context: Dict[str, Any]) -> RefactoringResponse:
        prompt = self._create_refactoring_prompt(code, context)
        
        response = self.llm(
            prompt,
            max_tokens=4096,
            temperature=0.7,
            top_p=0.95,
            stop=["```"]
        )
        
        return self._parse_response(response['choices'][0]['text'])

class OpenAIRefactoring(LLMRefactoring):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        openai.api_key = api_key
        self.model = model

    def generate_refactoring(self, code: str, context: Dict[str, Any]) -> RefactoringResponse:
        prompt = self._create_refactoring_prompt(code, context)
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert code refactoring assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return self._parse_response(response.choices[0].message.content)

class AnthropicRefactoring(LLMRefactoring):
    def __init__(self, api_key: str):
        self.client = anthropic.Client(api_key=api_key)

    def generate_refactoring(self, code: str, context: Dict[str, Any]) -> RefactoringResponse:
        prompt = self._create_refactoring_prompt(code, context)
        
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return self._parse_response(response.content[0].text)

class GoogleRefactoring(LLMRefactoring):
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_refactoring(self, code: str, context: Dict[str, Any]) -> RefactoringResponse:
        prompt = self._create_refactoring_prompt(code, context)
        
        response = self.model.generate_content(prompt)
        
        return self._parse_response(response.text)

class CohereRefactoring(LLMRefactoring):
    def __init__(self, api_key: str):
        self.client = cohere.Client(api_key)

    def generate_refactoring(self, code: str, context: Dict[str, Any]) -> RefactoringResponse:
        prompt = self._create_refactoring_prompt(code, context)
        
        response = self.client.generate(
            prompt=prompt,
            max_tokens=4096,
            temperature=0.7
        )
        
        return self._parse_response(response.generations[0].text)

class LLMRefactoringManager:
    def __init__(self):
        self.llm_instances: Dict[LLMType, LLMRefactoring] = {}
        self._initialize_llms()

    def _initialize_llms(self):
        # Initialize Local LLM if model exists
        model_path = "models/codellama-7b-instruct.Q4_K_M.gguf"
        if os.path.exists(model_path):
            self.llm_instances[LLMType.LOCAL] = LocalLLMRefactoring(model_path)

        # Initialize API-based LLMs if keys exist
        if os.environ.get("OPENAI_API_KEY"):
            self.llm_instances[LLMType.OPENAI] = OpenAIRefactoring(os.environ["OPENAI_API_KEY"])
        
        if os.environ.get("ANTHROPIC_API_KEY"):
            self.llm_instances[LLMType.ANTHROPIC] = AnthropicRefactoring(os.environ["ANTHROPIC_API_KEY"])
        
        if os.environ.get("GOOGLE_API_KEY"):
            self.llm_instances[LLMType.GOOGLE] = GoogleRefactoring(os.environ["GOOGLE_API_KEY"])
        
        if os.environ.get("COHERE_API_KEY"):
            self.llm_instances[LLMType.COHERE] = CohereRefactoring(os.environ["COHERE_API_KEY"])

    def get_available_llms(self) -> List[LLMType]:
        return list(self.llm_instances.keys())

    def refactor_code(self, code: str, llm_type: LLMType, context: Dict[str, Any]) -> RefactoringResponse:
        if llm_type not in self.llm_instances:
            raise ValueError(f"LLM type {llm_type} not available")
        
        return self.llm_instances[llm_type].generate_refactoring(code, context)

def _create_refactoring_prompt(code: str, context: Dict[str, Any]) -> str:
    return f"""
    Please analyze and refactor the following code to improve its quality, maintainability, and performance.
    Apply best practices and design patterns where appropriate.

    Original Code:
    ```
    {code}
    ```

    Context:
    - Language: {context.get('language', 'Unknown')}
    - File Type: {context.get('file_type', 'Unknown')}
    - Current Metrics:
        - Complexity: {context.get('complexity', 'N/A')}
        - Maintainability: {context.get('maintainability', 'N/A')}
        - Lines of Code: {context.get('loc', 'N/A')}

    Please provide:
    1. Refactored code
    2. Explanation of changes
    3. List of specific improvements
    4. Impact on metrics
    """

def _parse_response(response_text: str) -> RefactoringResponse:
    """Parse the LLM response into a structured format."""
    try:
        # Extract code between triple backticks
        code_start = response_text.find("```") + 3
        code_end = response_text.find("```", code_start)
        refactored_code = response_text[code_start:code_end].strip()
        
        # Extract explanation and changes
        explanation = ""
        changes = []
        metrics = {}
        
        # Parse the rest of the response
        lines = response_text[code_end + 3:].split("\n")
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.lower().startswith("explanation:"):
                current_section = "explanation"
                continue
            elif line.lower().startswith("changes:"):
                current_section = "changes"
                continue
            elif line.lower().startswith("metrics:"):
                current_section = "metrics"
                continue
                
            if current_section == "explanation":
                explanation += line + "\n"
            elif current_section == "changes":
                if line.startswith("-"):
                    changes.append(line[1:].strip())
            elif current_section == "metrics":
                if ":" in line:
                    key, value = line.split(":", 1)
                    try:
                        metrics[key.strip()] = float(value.strip())
                    except ValueError:
                        continue
        
        return RefactoringResponse(
            refactored_code=refactored_code,
            explanation=explanation.strip(),
            changes_made=changes,
            confidence=0.85,  # Default confidence
            metrics=metrics
        )
        
    except Exception as e:
        print(f"Error parsing LLM response: {str(e)}")
        return RefactoringResponse(
            refactored_code="",
            explanation="Error parsing LLM response",
            changes_made=[],
            confidence=0.0,
            metrics={}
        ) 