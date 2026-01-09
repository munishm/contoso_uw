from typing import Dict, Optional


class PromptBuilder:
    """Utility class for building prompts for LLM summarization."""
    
    DEFAULT_SYSTEM_PROMPT = "You are a professional insurance documentation assistant."
    
    DEFAULT_INSTRUCTIONS = """You are an insurance application summarization assistant. Below are the extracted details from an insurance application form.

Your task is to create a clear, professional, and comprehensive natural language summary of the applicant's information.

**Guidelines:**
1. Write in paragraph form, not bullet points
2. Group related information logically (personal details, employment, health, etc.)
3. Use professional language suitable for insurance documentation
4. Include all provided information
5. Do not add any information that is not present in the extracted data
6. If there are measurements, include units"""
    
    @staticmethod
    def format_entities(entities: Dict[str, str]) -> str:
        """
        Format entities into a readable list.
        
        Args:
            entities: Dictionary of entity names and values
            
        Returns:
            Formatted string of entities
        """
        return "\n".join([f"- {name}: {value}" for name, value in entities.items()])
    
    def build_summary_prompt(
        self,
        entities: Dict[str, str],
        context: Optional[str] = None,
        custom_instructions: Optional[str] = None
    ) -> str:
        """
        Build a complete prompt for summary generation.
        
        Args:
            entities: Dictionary of entity names and values
            context: Optional context about the document type
            custom_instructions: Optional custom instructions to override defaults
            
        Returns:
            Complete prompt string
        """
        instructions = custom_instructions or self.DEFAULT_INSTRUCTIONS
        entity_text = self.format_entities(entities)
        
        prompt_parts = [instructions]
        
        if context:
            prompt_parts.append(f"\n**Document Context:**\n{context}")
        
        prompt_parts.append(f"\n**Extracted Entities:**\n{entity_text}")
        prompt_parts.append("\n**Summary:**")
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def get_system_prompt() -> str:
        """
        Get the system prompt for the LLM.
        
        Returns:
            System prompt string
        """
        return PromptBuilder.DEFAULT_SYSTEM_PROMPT
