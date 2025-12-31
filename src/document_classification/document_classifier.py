"""ACU-only document classifier implementation."""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .utils.config import Config, ClassificationMethod
from .utils.acu_client import AzureContentUnderstandingClient
from .utils.auth import create_token_provider
from .utils.split_document import split_document_from_response, DocumentSplitter
from src.shared.models.classification import ClassificationResponse, PageClassification, TokenUsage, Documents

logger = logging.getLogger(__name__)


class DirectDocumentClassifier:
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
                "estimateFieldSourceAndConfidence": True,
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
    

    def classify(self, document: Dict[str, Any]) -> ClassificationResponse:
        """
        Classify a document using ACU.
        
        Args:
            document: Document dict with 'path' key pointing to file
            
        Returns:
            Classification result with document_type, confidence, segments, etc.
        """
        # Start timing
        total_start_time = time.time()
        
        # Ensure classifier exists
        self._ensure_classifier_exists()
        
        # Get file path from document
        file_path = document.get('path') or document.get('file_path')
        if not file_path:
            raise ValueError("Document must contain 'path' or 'file_path' key")
        
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Classifying document: {file_path}")
        
        # Classify the document (track only the actual classification operation)
        # Note: This timing excludes analyzer creation/validation which happens above
        acu_start_time = time.time()
        response = self.client.classify_document(self._classifier_id, file_path)
        
        # Poll for results (included in ACU timing as it's part of the classification process)
        result = self.client.poll_result(response)
        acu_duration = time.time() - acu_start_time
        
        # Extract classification results
        classification_result = self._parse_classification_result(result, file_path)
        
        # Add timing information to metadata
        total_duration = time.time() - total_start_time
        
        # Create ClassificationResponse object
        response = self._create_classification_response(classification_result, file_path)
        

        split_response = split_document_from_response(response, self.config.OUTPUT_DIR)
        
        # Add split document paths to the classification response
        if split_response and isinstance(split_response, dict):
            # split_response is a dictionary with document_type as keys and file paths as values
            # Convert to list of Documents objects for response.documents field
            split_documents = []
            for doc_type, file_path in split_response.items():
                split_documents.append(Documents(
                    document_type=doc_type,
                    file_path=file_path
                ))
            
            if split_documents:
                response.documents = split_documents
        logger.info(f"Document split completed. Output files: {response}")


        # Save result with complete timing information if configured
        if self.config.SAVE_RESULTS:
            # Add timing to metadata for saving
            classification_result['metadata'].update({
                'total_duration': total_duration,
                'acu_duration': acu_duration,
                'timing_breakdown': {
                    'total_duration': total_duration,
                    'acu_duration': acu_duration,
                    'other_duration': total_duration - acu_duration
                }
            })
            self._save_results([classification_result])
        
        return response
    
    def _get_segment_confidence(self, segment: Dict[str, Any], default_value: float = 1.0) -> float:
        """
        Extract confidence value from segment with consistent default handling.
        
        Args:
            segment: Segment dictionary from ACU API
            default_value: Default confidence if not provided
            
        Returns:
            Confidence value as float
        """
        confidence = segment.get('confidence')
        if confidence is None:
            return default_value
        return float(confidence) if confidence is not None else default_value

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
            contextualization_tokens = usage_data.get('contextualizationTokens', 0)
            
            token_usage = {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': prompt_tokens + completion_tokens,
                'contextualization_tokens': contextualization_tokens
            }
        
        # Extract segments with categories
        segment_classifications = []
        logger.info(f"Processing contents for classification segments: {contents}")
        for content in contents:
            segments = content.get('segments', [])
            
            for segment in segments:
                logger.info(f"Processing segment: {segment}")
                if 'category' in segment:
                    classification = {
                        'segment_id': segment.get('segmentId', 'unknown'),
                        'category': segment.get('category'),
                        'start_page': segment.get('startPageNumber', 1),
                        'end_page': segment.get('endPageNumber', 1),
                        'confidence': self._get_segment_confidence(segment)
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
                    'method': ClassificationMethod.DIRECT_CLASSIFICATION.value,
                    'token_usage': token_usage
                }
            }
        
        # Primary category from first segment
        primary_category = segment_classifications[0]['category']
        primary_confidence = self._get_segment_confidence(segment_classifications[0])
        
        # Process all segments to build alternatives and page classifications in a single loop
        alternatives = []
        page_classifications = []
        seen_categories = {primary_category}
        
        for i, seg in enumerate(segment_classifications):
            segment_confidence = self._get_segment_confidence(seg)
            
            # Build alternatives list (skip first segment as it's the primary)
            if i > 0:
                cat = seg['category']
                if cat not in seen_categories:
                    alternatives.append({
                        'document_type': cat,
                        'confidence': segment_confidence
                    })
                    seen_categories.add(cat)
            
            # Generate page-level classifications for all segments
            for page_num in range(seg['start_page'], seg['end_page'] + 1):
                page_classifications.append({
                    'page_number': page_num,
                    'document_type': seg['category'],
                    'category': seg['category'],  # For consistency with other classifiers
                    'confidence': segment_confidence,
                    'segment_id': seg['segment_id']
                })
        
        logger.info(f"Classified as: {primary_category} (confidence: {primary_confidence})")
        
        # Sort page classifications by page number
        page_classifications.sort(key=lambda x: x['page_number'])
        
        result = {
            'document_type': primary_category,
            'confidence': primary_confidence,
            'alternatives': alternatives,
            'segments': segment_classifications,
            'page_classifications': page_classifications,
            'metadata': {
                'file_path': file_path,
                'filename': Path(file_path).name,
                'method': ClassificationMethod.DIRECT_CLASSIFICATION.value,
                'total_segments': len(segment_classifications),
                'total_pages': len(page_classifications),
                'token_usage': token_usage,
                'analyzer_id': actual_result.get('analyzerId'),
                'api_version': actual_result.get('apiVersion')
            }
        }
        
        return result
    
    def _create_classification_response(
        self, 
        classification_result: Dict[str, Any], 
        file_path: str
    ) -> ClassificationResponse:
        """Create a ClassificationResponse object from the parsed result.
        
        Args:
            classification_result: Parsed classification result
            file_path: Path to the classified document
            
        Returns:
            ClassificationResponse object
        """
        # Convert page_classifications to PageClassification objects
        page_classifications = [
            PageClassification(
                page_number=page['page_number'],
                document_type=page['document_type'],
                segment_id=page['segment_id'],
                confidence=page['confidence']
            )
            for page in classification_result.get('page_classifications', [])
        ]
        
        # Create TokenUsage object if token usage data exists
        token_usage = None
        metadata = classification_result.get('metadata', {})
        token_data = metadata.get('token_usage')
        if token_data:
            token_usage = TokenUsage(
                prompt_tokens=token_data.get('prompt_tokens', 0),
                completion_tokens=token_data.get('completion_tokens', 0),
                total_tokens=token_data.get('total_tokens', 0),
                contextualization_tokens=token_data.get('contextualization_tokens')
            )
        
        # Create ClassificationResponse object
        return ClassificationResponse(
            analyzer_id=metadata.get('analyzer_id', self._classifier_id),
            file_path=file_path,
            total_pages=metadata.get('total_pages', 0),
            total_segments=metadata.get('total_segments', 0),
            token_usage=token_usage,
            pages=page_classifications,
            documents=None  # Initialize as None to avoid serialization warnings
        )

    
    def _save_results(self, results: List[Dict[str, Any]]):
        """Save classification results to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.config.OUTPUT_DIR / f"classification_results_{timestamp}.json"
        
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