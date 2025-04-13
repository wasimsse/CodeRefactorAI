import os
from typing import Optional, Dict, Any
import openai
from anthropic import Anthropic
import google.generativeai as genai
import cohere
from config import config

class LLMProvider:
    """Base class for LLM providers"""
    def __init__(self):
        self.client = None
        self.setup_client()
    
    def setup_client(self):
        """Setup the client for the LLM provider"""
        raise NotImplementedError
    
    async def generate_response(self, prompt: str, model: str, **kwargs) -> str:
        """Generate a response from the LLM"""
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    def setup_client(self):
        if config.OPENAI_API_KEY:
            openai.api_key = config.OPENAI_API_KEY
    
    async def generate_response(self, prompt: str, model: str, **kwargs) -> str:
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        response = await openai.ChatCompletion.acreate(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content

class AnthropicProvider(LLMProvider):
    def setup_client(self):
        if config.ANTHROPIC_API_KEY:
            self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    
    async def generate_response(self, prompt: str, model: str, **kwargs) -> str:
        if not self.client:
            raise ValueError("Anthropic API key not configured")
        
        response = await self.client.messages.create(
            model=model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.content[0].text

class GoogleProvider(LLMProvider):
    def setup_client(self):
        if config.GOOGLE_API_KEY:
            genai.configure(api_key=config.GOOGLE_API_KEY)
            self.client = genai
    
    async def generate_response(self, prompt: str, model: str, **kwargs) -> str:
        if not self.client:
            raise ValueError("Google API key not configured")
        
        model = self.client.GenerativeModel(model)
        response = await model.generate_content_async(prompt)
        return response.text

class CohereProvider(LLMProvider):
    def setup_client(self):
        if config.COHERE_API_KEY:
            self.client = cohere.Client(config.COHERE_API_KEY)
    
    async def generate_response(self, prompt: str, model: str, **kwargs) -> str:
        if not self.client:
            raise ValueError("Cohere API key not configured")
        
        response = await self.client.generate(
            model=model,
            prompt=prompt,
            **kwargs
        )
        return response.generations[0].text

class LLMManager:
    """Manager class for handling multiple LLM providers"""
    def __init__(self):
        self.providers = {}
        
        # Initialize OpenAI if API key is available
        if config.OPENAI_API_KEY:
            self.providers['OpenAI'] = OpenAIProvider()
            
        # Initialize Anthropic if API key is available
        if config.ANTHROPIC_API_KEY:
            self.providers['Anthropic'] = AnthropicProvider()
            
        # Initialize Google if API key is available
        if hasattr(config, 'GOOGLE_API_KEY') and config.GOOGLE_API_KEY:
            self.providers['Google'] = GoogleProvider()
            
        # Initialize Cohere if API key is available
        if hasattr(config, 'COHERE_API_KEY') and config.COHERE_API_KEY:
            self.providers['Cohere'] = CohereProvider()
        
        # Ensure at least one provider is available
        if not self.providers:
            raise ValueError("No LLM providers available. Please configure at least one API key.")
    
    async def generate_response(self, provider: str, model: str, prompt: str, **kwargs) -> str:
        """Generate a response using the specified provider and model"""
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not supported or not configured")
        
        return await self.providers[provider].generate_response(prompt, model, **kwargs)

# Create a singleton instance
llm_manager = LLMManager() 