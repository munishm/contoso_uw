import json
import logging
from typing import Dict, List


logger = logging.getLogger(__name__)


class EntityLoader:
    """Utility class for loading and extracting entities from JSON files."""
    
    @staticmethod
    def load_from_file(file_path: str) -> List[Dict]:
        """
        Load entity data from JSON file.
        
        Args:
            file_path: Path to the JSON file containing entity data
            
        Returns:
            List of dictionaries containing entity data per page
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Successfully loaded {len(data)} pages of entity data")
            return data
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading entity data: {e}")
            raise
    
    @staticmethod
    def extract_english_entities(pages: List[Dict]) -> Dict[str, str]:
        """
        Extract all English entity values from the page data.
        
        Args:
            pages: List of page dictionaries containing entity data
            
        Returns:
            Dictionary mapping entity names to their English values
        """
        entities = {}
        
        try:
            for page in pages:
                page_num = page.get("page_number", "unknown")
                entity_presence = page.get("entity_presence", {})
                entity_value = page.get("entity_value", {})
                
                # Only include entities that are present
                for entity_name, is_present in entity_presence.items():
                    if is_present and entity_name in entity_value:
                        value = entity_value[entity_name]
                        # Only include non-empty English values
                        if value and isinstance(value, str) and value.strip():
                            entities[entity_name] = value.strip()
                            logger.debug(f"Page {page_num}: {entity_name} = {value}")
            
            logger.info(f"Extracted {len(entities)} English entities")
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            raise
    
    @staticmethod
    def load_and_extract(file_path: str) -> Dict[str, str]:
        """
        Load JSON file and extract English entities in one step.
        
        Args:
            file_path: Path to the JSON file containing entity data
            
        Returns:
            Dictionary mapping entity names to their English values
        """
        pages = EntityLoader.load_from_file(file_path)
        return EntityLoader.extract_english_entities(pages)
