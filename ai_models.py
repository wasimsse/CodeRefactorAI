import os
from typing import Dict, List, Optional
import openai
import anthropic
import google.generativeai as genai
import cohere
from dotenv import load_dotenv

load_dotenv()

class AIModelManager:
    def __init__(self):
        """Initialize AI model manager."""
        self.models = {
            'GPT-4': self._call_gpt4,
            'GPT-3.5': self._call_gpt35,
            'Claude': self._call_claude,
            'PaLM': self._call_palm
        }
        self._initialize_api_keys()
        self._initialize_clients()
        
    def _initialize_api_keys(self):
        """Initialize API keys from environment variables."""
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.google_key = os.getenv('GOOGLE_API_KEY')
        self.cohere_key = os.getenv('COHERE_API_KEY')
        
    def _initialize_clients(self):
        """Initialize API clients."""
        if self.openai_key:
            openai.api_key = self.openai_key
            
        if self.anthropic_key:
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)
            
        if self.google_key:
            genai.configure(api_key=self.google_key)
            
        if self.cohere_key:
            self.cohere_client = cohere.Client(api_key=self.cohere_key)
            
    async def refactor_code(self, code: str, model: str, options: Dict[str, bool]) -> str:
        """Refactor code using specified AI model."""
        # Get the appropriate model function
        model_func = self.models.get(model)
        if not model_func:
            raise ValueError(f"Unsupported model: {model}")

        # Create prompt based on options
        prompt = self._create_refactoring_prompt(code, options)
        
        # Call model
        try:
            refactored_code = await model_func(prompt)
            return refactored_code
        except Exception as e:
            raise Exception(f"Error during refactoring with {model}: {str(e)}")

    def _create_refactoring_prompt(self, code: str, options: Dict[str, bool]) -> str:
        """Create a prompt for code refactoring based on selected options."""
        prompt = "Refactor the following code"
        
        # Add specific instructions based on options
        if options.get('improve_structure'):
            prompt += ", improving its structure and organization"
        if options.get('add_documentation'):
            prompt += ", adding comprehensive documentation"
        if options.get('error_handling'):
            prompt += ", implementing proper error handling"
        if options.get('solid_principles'):
            prompt += ", applying SOLID principles"
            
        prompt += ":\n\n```\n" + code + "\n```"
        return prompt

    async def _call_gpt4(self, prompt: str) -> str:
        """Call GPT-4 model."""
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional code refactoring assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"GPT-4 API error: {str(e)}")

    async def _call_gpt35(self, prompt: str) -> str:
        """Call GPT-3.5 model."""
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional code refactoring assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"GPT-3.5 API error: {str(e)}")

    async def _call_claude(self, prompt: str) -> str:
        """Call Claude model."""
        try:
            client = anthropic.Client()
            response = await client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")

    async def _call_palm(self, prompt: str) -> str:
        """Call PaLM model."""
        try:
            response = genai.generate_text(prompt=prompt)
            return response.result
        except Exception as e:
            raise Exception(f"PaLM API error: {str(e)}")

    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate that all necessary API keys are present."""
        return {
            'GPT-4': bool(openai.api_key),
            'GPT-3.5': bool(openai.api_key),
            'Claude': bool(anthropic.api_key),
            'PaLM': bool(genai.configure)
        } 