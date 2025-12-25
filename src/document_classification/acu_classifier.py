"""ACU-only document classifier implementation."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .utils.config import Config
from .utils.acu_client import AzureContentUnderstandingClient
from .utils.auth import create_token_provider


logger = logging.getLogger(__name__)


class ACUClassifier:
    """
    Document classifier using Azure Content Understanding only.
    
    This implementation uses Azure Content Understanding's built-in
    classification capabilities without additional LLM processing.
    """
    
    def __init__(self, config: Config = None):
        """
        Initialize the ACU classifier.
        
        Args:
            config: Configuration object (uses default if None)
        """
        self.config = config or Config()
        self.config.validate()
        
        # Create token provider
        self._token_provider = create_token_provider(self.config.AZURE_TENANT_ID)
        
        # Initialize ACU client
        self.client = AzureContentUnderstandingClient(
            endpoint=self.config.CU_ENDPOINT,
            api_version=self.config.CU_API_VERSION,
            token_provider=self._token_provider
        )
        
        self._classifier_id = self.config.CLASSIFIER_ID
        self._confidence_threshold = self.config.CONFIDENCE_THRESHOLD
        self._classifier_info = None
        
        logger.info(f"ACU Classifier initialized with endpoint: {self.config.CU_ENDPOINT}")
    
    def _ensure_classifier_exists(self):
        """Ensure the classifier exists, create if needed."""
        if self._classifier_info is not None:
            return self._classifier_info
        
        logger.info(f"Checking if classifier exists: {self._classifier_id}")
        
        # Check if classifier already exists
        if self.client.check_analyzer_exists(self._classifier_id):
            logger.info(f"Classifier '{self._classifier_id}' already exists - reusing")
            
            self._classifier_info = {
                'classifier_id': self._classifier_id,
                'categories': list(self.config.DOCUMENT_CATEGORIES.keys()),
                'segmentation_enabled': True,
                'status': 'existing'
            }
            return self._classifier_info
        
        logger.info(f"Creating new classifier: {self._classifier_id}")
        
        # Create classifier schema
        classifier_template = {
            "baseAnalyzerId": "prebuilt-document",
            "description": f"HSBC Document Classifier with segmentation - {self._classifier_id}",
            "config": {
                "returnDetails": True,
                "enableSegment": True,
                "contentCategories": {
                    name: {"description": desc}
                    for name, desc in self.config.DOCUMENT_CATEGORIES.items()
                }
            },
            "models": {"completion": "gpt-4.1"},
            "tags": {
                "created_by": "hsbc_document_classification",
                "purpose": "insurance_underwriting"
            }
        }
        
        # Create the classifier
        response = self.client.begin_create_classifier(
            classifier_id=self._classifier_id,
            classifier_schema=classifier_template
        )
        
        logger.info("Waiting for classifier creation to complete...")
        result = self.client.poll_result(response)
        logger.info(f"Classifier '{self._classifier_id}' created successfully")
        
        self._classifier_info = {
            'classifier_id': self._classifier_id,
            'categories': list(self.config.DOCUMENT_CATEGORIES.keys()),
            'segmentation_enabled': True,
            'status': 'created'
        }
        
        return self._classifier_info
    
    def classify(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a document using ACU.
        
        Args:
            document: Document dict with 'path' key pointing to file
            
        Returns:
            Classification result with document_type, confidence, segments, etc.
        """
        # Ensure classifier exists
        self._ensure_classifier_exists()
        
        # Get file path from document
        file_path = document.get('path') or document.get('file_path')
        if not file_path:
            raise ValueError("Document must contain 'path' or 'file_path' key")
        
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Classifying document: {file_path}")
        
        # Classify the document
        response = self.client.classify_document(self._classifier_id, file_path)
        
        # Poll for results
        result = self.client.poll_result(response)
        
        # Extract classification results
        return self._parse_classification_result(result, file_path)
    
    def _parse_classification_result(
        self, 
        result: Dict[str, Any], 
        file_path: str
    ) -> Dict[str, Any]:
        """
        Parse the ACU classification result.
        
        Args:
            result: Raw result from ACU API
            file_path: Path to the classified file
            
        Returns:
            Parsed classification result
        """
        actual_result = result.get('result', {})
        contents = actual_result.get('contents', [])
        
        # Extract token usage
        token_usage = None
        if 'usage' in result:
            usage_data = result['usage']
            tokens = usage_data.get('tokens', {})
            
            prompt_tokens = tokens.get('gpt-4.1-input', 0)
            completion_tokens = tokens.get('gpt-4.1-output', 0)
            
            token_usage = {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': prompt_tokens + completion_tokens
            }
        
        # Extract segments with categories
        segment_classifications = []
        
        for content in contents:
            segments = content.get('segments', [])
            
            for segment in segments:
                if 'category' in segment:
                    classification = {
                        'segment_id': segment.get('segmentId', 'unknown'),
                        'category': segment.get('category'),
                        'start_page': segment.get('startPageNumber', 1),
                        'end_page': segment.get('endPageNumber', 1),
                        'confidence': segment.get('confidence')
                    }
                    segment_classifications.append(classification)
        
        if not segment_classifications:
            return {
                'document_type': 'Other',
                'confidence': 0.0,
                'alternatives': [],
                'segments': [],
                'error': 'No classification segments found',
                'metadata': {
                    'file_path': file_path,
                    'method': 'acu_only',
                    'token_usage': token_usage
                }
            }
        
        # Primary category from first segment
        primary_category = segment_classifications[0]['category']
        primary_confidence = segment_classifications[0].get('confidence', 1.0)
        
        # Build alternatives list from other segments
        alternatives = []
        seen_categories = {primary_category}
        
        for seg in segment_classifications[1:]:
            cat = seg['category']
            if cat not in seen_categories:
                alternatives.append({
                    'document_type': cat,
                    'confidence': seg.get('confidence', 0.0)
                })
                seen_categories.add(cat)
        
        logger.info(f"Classified as: {primary_category} (confidence: {primary_confidence})")
        
        result = {
            'document_type': primary_category,
            'confidence': primary_confidence if primary_confidence else 1.0,
            'alternatives': alternatives,
            'segments': segment_classifications,
            'metadata': {
                'file_path': file_path,
                'filename': Path(file_path).name,
                'method': 'acu_only',
                'total_segments': len(segment_classifications),
                'token_usage': token_usage,
                'analyzer_id': actual_result.get('analyzerId'),
                'api_version': actual_result.get('apiVersion')
            }
        }
        
        # Save result if configured
        if self.config.SAVE_RESULTS:
            self._save_results([result])
        
        return result
    
    def classify_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classify multiple documents.
        
        Args:
            documents: List of document dicts
            
        Returns:
            List of classification results
        """
        results = []
        
        for doc in documents:
            try:
                result = self.classify(doc)
                result['status'] = 'success'
            except Exception as e:
                logger.error(f"Error classifying {doc.get('path', 'unknown')}: {e}")
                result = {
                    'document_type': 'Other',
                    'confidence': 0.0,
                    'alternatives': [],
                    'error': str(e),
                    'status': 'error',
                    'metadata': {
                        'file_path': doc.get('path', 'unknown'),
                        'method': 'acu_only'
                    }
                }
            
            results.append(result)
        
        # Save results if configured
        if self.config.SAVE_RESULTS and results:
            self._save_results(results)
        
        return results
    
    def _save_results(self, results: List[Dict[str, Any]]):
        """Save classification results to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.config.OUTPUT_DIR / f"acu_classification_results_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {output_file}")
    
    def get_document_types(self) -> List[str]:
        """Get list of possible document types."""
        return list(self.config.DOCUMENT_CATEGORIES.keys())
    
    def set_confidence_threshold(self, threshold: float):
        """Set minimum confidence threshold for classification."""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        self._confidence_threshold = threshold
        logger.info(f"Confidence threshold set to: {threshold}")
    
    @property
    def confidence_threshold(self) -> float:
        """Get current confidence threshold."""
        return self._confidence_threshold
