import requests
import json
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)

class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    GEMINI = "gemini"

class LLMInterface(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    def analyze_event(self, event_text: str) -> Dict[str, Any]:
        pass

class OllamaProvider(LLMInterface):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model
        
    def generate(self, prompt: str, **kwargs) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    **kwargs
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return ""
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return ""
    
    def analyze_event(self, event_text: str) -> Dict[str, Any]:
        """Analyze event using LLM"""
        prompt = f"""
        Analyze this supply chain event and extract key information:
        
        Event: {event_text}
        
        Extract in JSON format:
        1. event_type: (port_closure, weather, geopolitical, labor_dispute, supply_shortage)
        2. severity: (critical, high, medium, low)
        3. location: (country or city)
        4. affected_ports: (list of port names)
        5. estimated_duration_days: (number)
        6. key_impact: (brief description)
        7. recommended_actions: (list of actions)
        
        Return ONLY valid JSON.
        """
        
        response = self.generate(prompt)
        try:
            # Clean response and parse JSON
            response = response.strip()
            # Find JSON block if present
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM response: {e}")
            return {"error": "Failed to parse response", "raw": response}

class LLMService:
    def __init__(self, provider: LLMProvider = LLMProvider.OLLAMA):
        self.provider = provider
        self._instance = self._create_provider()
    
    def _create_provider(self) -> LLMInterface:
        if self.provider == LLMProvider.OLLAMA:
            return OllamaProvider()
        elif self.provider == LLMProvider.OPENAI:
            # Placeholder for OpenAI integration
            raise NotImplementedError("OpenAI integration coming soon")
        elif self.provider == LLMProvider.GEMINI:
            # Placeholder for Gemini integration
            raise NotImplementedError("Gemini integration coming soon")
        else:
            return OllamaProvider()
    
    def generate(self, prompt: str, **kwargs) -> str:
        return self._instance.generate(prompt, **kwargs)
    
    def analyze_event(self, event_text: str) -> Dict[str, Any]:
        return self._instance.analyze_event(event_text)

# Singleton instance
llm_service = LLMService()