"""Component registry for orchestration."""

from typing import Any, Dict, Optional, Type
from src.interfaces.processor import IDocumentProcessor


class ComponentRegistry:
    """
    Registry for managing and discovering components in the system.
    
    Enables runtime component registration and lookup for
    plug-and-play architecture.
    """
    
    def __init__(self):
        """Initialize empty component registry."""
        self._components: Dict[str, IDocumentProcessor] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    def register(
        self, 
        name: str, 
        component: IDocumentProcessor,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a component in the registry.
        
        Args:
            name: Unique component name
            component: Component instance implementing IDocumentProcessor
            metadata: Optional metadata about the component
            
        Raises:
            ValueError: If component name already registered
        """
        if name in self._components:
            raise ValueError(f"Component already registered: {name}")
        
        self._components[name] = component
        self._metadata[name] = metadata or {}
    
    def unregister(self, name: str) -> None:
        """
        Unregister a component from the registry.
        
        Args:
            name: Component name to unregister
            
        Raises:
            KeyError: If component not found
        """
        if name not in self._components:
            raise KeyError(f"Component not found: {name}")
        
        del self._components[name]
        del self._metadata[name]
    
    def get(self, name: str) -> IDocumentProcessor:
        """
        Get a registered component by name.
        
        Args:
            name: Component name
            
        Returns:
            Component instance
            
        Raises:
            KeyError: If component not found
        """
        if name not in self._components:
            raise KeyError(f"Component not found: {name}")
        
        return self._components[name]
    
    def get_metadata(self, name: str) -> Dict[str, Any]:
        """
        Get metadata for a component.
        
        Args:
            name: Component name
            
        Returns:
            Component metadata dictionary
            
        Raises:
            KeyError: If component not found
        """
        if name not in self._metadata:
            raise KeyError(f"Component not found: {name}")
        
        return self._metadata[name]
    
    def list_components(self) -> list[str]:
        """
        Get list of all registered component names.
        
        Returns:
            List of component names
        """
        return list(self._components.keys())
    
    def has_component(self, name: str) -> bool:
        """
        Check if a component is registered.
        
        Args:
            name: Component name
            
        Returns:
            True if component is registered
        """
        return name in self._components
    
    def clear(self) -> None:
        """Clear all registered components."""
        self._components.clear()
        self._metadata.clear()
    
    def __len__(self) -> int:
        """Get number of registered components."""
        return len(self._components)
    
    def __contains__(self, name: str) -> bool:
        """Check if component name is registered."""
        return name in self._components


# Global registry instance
registry = ComponentRegistry()
