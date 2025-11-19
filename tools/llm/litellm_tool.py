"""LiteLLM tool implementation for unified LLM access."""

import logging
import os
from typing import Dict, Optional, Type, Union

from pydantic import BaseModel
import litellm

from registry.base_tool import BaseLLMTool, ModelType


logger = logging.getLogger(__name__)


class LiteLLMTool(BaseLLMTool):
    """LiteLLM implementation for unified access to multiple LLM providers."""
    
    name = "litellm"
    
    def __init__(self, routing: Dict[str, str], extra_params: Optional[Dict] = None, api_keys: Optional[Dict] = None):
        """
        Initialize LiteLLM tool with model routing configuration.
        
        Args:
            routing: Dictionary mapping ModelType to model names
                    e.g., {"fast": "gpt-3.5-turbo", "balanced": "gpt-4-turbo-preview", "powerful": "gpt-4"}
            extra_params: Optional dictionary of common parameters for all LLM calls
                         e.g., {"temperature": 0.7, "max_tokens": 4000}
            api_keys: Optional dictionary of API keys for different providers
                     e.g., {"openai": "sk-...", "anthropic": "sk-ant-..."}
        """
        self.routing = routing
        self.extra_params = extra_params or {}
        
        # Set API keys from environment or provided dict
        if api_keys:
            for provider, key_ref in api_keys.items():
                if key_ref and isinstance(key_ref, str):
                    if key_ref.startswith("env:"):
                        env_var = key_ref.replace("env:", "")
                        key_value = os.getenv(env_var)
                        if key_value:
                            os.environ[f"{provider.upper()}_API_KEY"] = key_value
                        else:
                            logger.warning(f"Environment variable {env_var} not found for provider {provider}")
                    else:
                        os.environ[f"{provider.upper()}_API_KEY"] = key_ref
        
        logger.info(f"Initialized LiteLLM tool with routing: {routing}")
    
    def generate(
        self,
        prompt: str,
        model_type: ModelType,
        structured_output_schema: Optional[Type[BaseModel]] = None
    ) -> Union[str, BaseModel]:
        """
        Generate text or structured output using appropriate model.
        
        Args:
            prompt: Input prompt for the LLM
            model_type: Type of model to use (fast/balanced/powerful)
            structured_output_schema: Optional Pydantic schema for structured output
            
        Returns:
            Generated text string or Pydantic model instance if schema provided
            
        Raises:
            Exception: If LLM call fails after error handling
        """
        # Get model name from routing configuration
        model_name = self.routing.get(model_type.value)
        if not model_name:
            error_msg = f"No model configured for type: {model_type.value}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            logger.info(f"Generating with model: {model_name} (type: {model_type.value})")
            
            # Prepare messages
            messages = [{"role": "user", "content": prompt}]
            
            # Prepare kwargs
            kwargs = {
                "model": model_name,
                "messages": messages,
                **self.extra_params
            }
            
            # Handle structured output if schema provided
            if structured_output_schema:
                logger.debug(f"Using structured output with schema: {structured_output_schema.__name__}")
                
                # Add response format for structured output
                # LiteLLM supports JSON mode for compatible models
                kwargs["response_format"] = {"type": "json_object"}
                
                # Add schema instructions to prompt
                schema_json = structured_output_schema.model_json_schema()
                enhanced_prompt = f"{prompt}\n\nPlease respond with a JSON object matching this schema:\n{schema_json}"
                kwargs["messages"] = [{"role": "user", "content": enhanced_prompt}]
                
                # Make the API call
                response = litellm.completion(**kwargs)
                
                # Extract content
                content = response.choices[0].message.content
                
                # Parse into Pydantic model
                try:
                    result = structured_output_schema.model_validate_json(content)
                    logger.info(f"Successfully generated structured output")
                    return result
                except Exception as parse_error:
                    logger.warning(f"Failed to parse structured output: {parse_error}")
                    logger.debug(f"Raw content: {content}")
                    # Fall back to returning raw content
                    return content
            
            else:
                # Standard text generation
                response = litellm.completion(**kwargs)
                content = response.choices[0].message.content
                
                logger.info(f"Successfully generated text output ({len(content)} chars)")
                return content
        
        except Exception as e:
            error_msg = f"LiteLLM generation failed with model {model_name}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
