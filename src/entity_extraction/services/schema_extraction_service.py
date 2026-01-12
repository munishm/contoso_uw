"""Service for schema-based document extraction."""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import jsonschema

from ..models import (
    DocumentTypeVersion,
    ExtractedField,
    ExtractionResult,
    ExtractionStatus,
    ModelType,
)
from ..repositories import ExtractionRepository, SchemaRepository, ExtractionModelRepository
from ..adapters.base import ExtractionModelAdapter
from ..adapters import AzureOpenAIVisionAdapter
from ..config import get_config
from src.evaluation.entity_extraction.evaluation_service import EvaluationService

EVALUATION_AVAILABLE = True
# Import Azure Document Intelligence 
try:
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    HAS_DOC_INTELLIGENCE = True
except ImportError:
    HAS_DOC_INTELLIGENCE = False
    
logger = logging.getLogger(__name__)


class SchemaExtractionService:
    """Main service for orchestrating schema-based extraction."""
    
    def __init__(
        self,
        schema_repo: SchemaRepository,
        extraction_repo: ExtractionRepository,
        model_repo: ExtractionModelRepository,
        adapters: Optional[Dict[str, ExtractionModelAdapter]] = None,
        enable_evaluation: bool = True
    ):
        """
        Initialize extraction service.
        
        Args:
            schema_repo: Repository for schema access
            extraction_repo: Repository for result storage
            model_repo: Repository for model registry
            adapters: Dictionary of model adapters (name -> adapter instance)
            enable_evaluation: Whether to run batch evaluation after extraction (default: True)
        """
        self.schema_repo = schema_repo
        self.extraction_repo = extraction_repo
        self.model_repo = model_repo
        self.adapters = adapters or {}
        
        # Always enable evaluation if available (ignore parameter)
        self.enable_evaluation = EVALUATION_AVAILABLE
        print(f"[SchemaExtractionService.__init__] EVALUATION_AVAILABLE={EVALUATION_AVAILABLE}")
        print(f"[SchemaExtractionService.__init__] enable_evaluation={self.enable_evaluation}")
        
        # Initialize evaluation service if available
        self.evaluation_service = None
        if EVALUATION_AVAILABLE:
            try:
                print(f"[SchemaExtractionService.__init__] Attempting to initialize evaluation service...")
                from azure.identity import DefaultAzureCredential
                config = get_config()
                credential = DefaultAzureCredential()
                print(f"[SchemaExtractionService.__init__] Config: endpoint={getattr(config, 'openai_endpoint', None)}, deployment={getattr(config, 'openai_deployment_gpt4_vision', None)}")
                self.evaluation_service = EvaluationService(
                    azure_endpoint=getattr(config, 'openai_endpoint', None),
                    deployment_name=getattr(config, 'openai_deployment_gpt4_vision', None),
                    api_version="2024-08-01-preview",
                    credential=credential
                )
                print(f"[SchemaExtractionService.__init__] Evaluation service created successfully")
                logger.info("Evaluation service initialized and enabled")
            except Exception as e:
                print(f"[SchemaExtractionService.__init__] Failed to initialize evaluation service: {e}")
                logger.error(f"Failed to initialize evaluation service: {e}", exc_info=True)
                self.evaluation_service = None
                self.enable_evaluation = False
        else:
            print(f"[SchemaExtractionService.__init__] Evaluation not available - module not found")
            logger.warning("Evaluation not available - evaluation module not found")
    
    def register_adapter(self, name: str, adapter: ExtractionModelAdapter):
        """Register a model adapter."""
        self.adapters[name] = adapter
    
    async def extract_document(
        self,
        document_id: str,
        document_content: bytes,
        document_type_id: UUID,
        version: str
    ) -> ExtractionResult:
        """
        Extract structured data from a document using configured schema.
        
        Args:
            document_id: Unique document identifier
            document_content: Raw document bytes
            document_type_id: Document type ID
            version: Schema version to use
        
        Returns:
            Extraction result with all fields
        
        Raises:
            ValueError: If schema not found or invalid
        """
        logger.info("-" * 50)
        logger.info("SchemaExtractionService.extract_document()")
        logger.info("-" * 50)
        logger.info(f"  document_id: {document_id}")
        logger.info(f"  document_type_id: {document_type_id}")
        logger.info(f"  version: {version}")
        logger.info(f"  content_size: {len(document_content)} bytes")
        logger.info(f"  registered_adapters: {list(self.adapters.keys())}")
        logger.info(f"  enable_evaluation: {self.enable_evaluation}")
        logger.info(f"  evaluation_service: {self.evaluation_service is not None}")
        
        print(f"\n>>> extract_document() called")
        print(f">>> enable_evaluation={self.enable_evaluation}, evaluation_service={self.evaluation_service is not None}")
        
        start_time = time.time()
        
        # Create initial extraction record
        extraction = ExtractionResult(
            document_id=document_id,
            document_type_id=document_type_id,
            version_id=UUID(int=0),  # Will update after schema lookup
            status=ExtractionStatus.IN_PROGRESS
        )
        extraction = await self.extraction_repo.create_extraction(extraction)
        logger.info(f"  Created extraction record: {extraction.id}")
        
        try:
            # 1. Look up schema version
            logger.info(f"  Looking up schema version...")
            schema_version = await self.schema_repo.get_schema_version(
                document_type_id,
                version
            )
            if not schema_version:
                logger.error(f"  ✗ Schema NOT FOUND for document_type_id={document_type_id}, version={version}")
                raise ValueError(
                    f"Schema not found for document type {document_type_id} version {version}"
                )
            
            logger.info(f"  ✓ Found schema: {schema_version.id}")
            extraction.version_id = schema_version.id
            
            # 2. Get document type for context
            document_type = await self.schema_repo.get_document_type(document_type_id)
            if not document_type:
                logger.error(f"  ✗ Document type {document_type_id} not found")
                raise ValueError(f"Document type {document_type_id} not found")
            
            logger.info(f"  ✓ Document type: {document_type.name}")
            
            # 3. Determine which model(s) to use
            extraction_config = schema_version.extraction_config
            models = extraction_config.get("models", [])
            logger.info(f"  extraction_config.models: {len(models)} configured")
            
            if not models:
                logger.error(f"  ✗ No models configured in extraction_config")
                raise ValueError("No models configured for this schema version")
            
            # For MVP, use first primary model (Phase 4 will add multi-model support)
            primary_model = next(
                (m for m in models if m.get("strategy") == "primary"),
                models[0]
            )
            logger.info(f"  Primary model config: {primary_model}")
            
            # Fetch model from database
            model_id = UUID(primary_model.get("model_id"))
            logger.info(f"  Looking up model_id: {model_id}")
            db_model = await self.model_repo.get_model(model_id)
            
            if not db_model:
                logger.error(f"  ✗ Model {model_id} not found in registry")
                raise ValueError(f"Model {model_id} not found in registry")
            
            logger.info(f"  ✓ Found model: {db_model.name}, type={db_model.type}, active={db_model.is_active}")
            
            if not db_model.is_active:
                logger.error(f"  ✗ Model {db_model.name} is not active")
                raise ValueError(f"Model {db_model.name} is not active")
            
            # Create adapter dynamically based on model type
            logger.info(f"  Creating adapter for model type: {db_model.type}")
            if db_model.type == ModelType.VISION:
                logger.info(f"    endpoint: {db_model.endpoint}")
                logger.info(f"    deployment/version: {db_model.version}")
                logger.info(f"    api_version: {db_model.api_version}")
                
                # Get Document Intelligence config for precise bounding boxes
                config = get_config()
                di_endpoint = config.doc_intelligence_endpoint
                di_key = config.doc_intelligence_key
                
                print(f"[SchemaExtractionService] Document Intelligence config from ExtractionConfig:")
                print(f"  - doc_intelligence_endpoint: {di_endpoint}")
                print(f"  - doc_intelligence_key: {'***' if di_key else 'None (using DefaultAzureCredential)'}")
                
                adapter = AzureOpenAIVisionAdapter(
                    endpoint=db_model.endpoint,
                    api_key=None,  # Use Azure AD
                    deployment=db_model.version,
                    api_version=db_model.api_version or "2024-02-15-preview",
                    doc_intelligence_endpoint=di_endpoint,
                    doc_intelligence_key=di_key
                )
            else:
                logger.error(f"  ✗ Unsupported model type: {db_model.type}")
                raise ValueError(f"Unsupported model type: {db_model.type}")
            
            model_name = db_model.name
            
            # 4. Execute extraction
            field_names = primary_model.get("fields", ["*"])
            logger.info(f"  Calling adapter.extract() with fields: {field_names}")
            raw_results = await adapter.extract(
                document_content,
                document_type.name,
                schema_version,
                field_names
            )
            logger.info(f"  ✓ Extraction returned {len(raw_results)} raw fields")
            logger.info(f"  Raw results: {list(raw_results.keys())}")
            
            extraction.models_used = [model_name]
            
            # 5. Map extracted data to output schema fields
            extracted_fields = self._map_to_output_schema(
                raw_results,
                schema_version,
                model_name
            )
            
            # 6. Handle missing required fields
            extracted_fields = self._handle_missing_fields(
                extracted_fields,
                schema_version
            )
            
            # 7. Validate against output schema
            validation_errors = self._validate_output(extracted_fields, schema_version)
            if validation_errors:
                extraction.error_message = f"Validation errors: {validation_errors}"
                extraction.status = ExtractionStatus.REVIEW_REQUIRED
            else:
                extraction.status = ExtractionStatus.COMPLETED
            
            extraction.fields = extracted_fields
            extraction.completed_at = datetime.utcnow()
            extraction.processing_duration_ms = int((time.time() - start_time) * 1000)
            
            print(f"\n>>> Step 8: About to run evaluation")
            print(f">>> enable_evaluation={self.enable_evaluation}, evaluation_service={self.evaluation_service is not None}")
            
            # 8. Run batch evaluation if enabled
            evaluation_results = None
            logger.info(f"[Evaluation] Check: enable_evaluation={self.enable_evaluation}, evaluation_service={self.evaluation_service is not None}")
            if self.enable_evaluation and self.evaluation_service:
                try:
                    eval_start = time.time()
                    logger.info("Running batch evaluation...")
                    print(f">>> Running batch evaluation...")
                    # Pass the adapter to reuse OCR text from extraction
                    evaluation_results = await self._evaluate_extraction(
                        extraction, document_content, adapter
                    )
                    eval_duration_ms = int((time.time() - eval_start) * 1000)
                    
                    if evaluation_results:
                        avg_score = evaluation_results.get('aggregate_summary', {}).get('average_correctness_score', 'N/A')
                        field_count = len(evaluation_results.get('results', []))
                        logger.info(f"Evaluation completed in {eval_duration_ms}ms: {field_count} fields evaluated, avg correctness score: {avg_score}")
                        print(f">>> Evaluation completed: {field_count} fields, avg score: {avg_score}")
                    else:
                        logger.warning(f"Evaluation returned no results after {eval_duration_ms}ms")
                        print(f">>> Evaluation returned no results!")
                except Exception as eval_error:
                    logger.error(f"Evaluation failed: {eval_error}", exc_info=True)
                    print(f">>> Evaluation FAILED: {eval_error}")
            else:
                logger.info("[Evaluation] Skipped - not enabled or service not available")
                print(f">>> Evaluation SKIPPED")
            
            # 9. Save result with evaluation
            print(f"\n>>> Step 9: Saving extraction with evaluation_results={evaluation_results is not None}")
            if evaluation_results:
                print(f">>> Evaluation results structure: total_fields={evaluation_results.get('total_fields')}, results_count={len(evaluation_results.get('results', []))}")
                import json
                print(f">>> Full evaluation_results JSON:")
                print(json.dumps(evaluation_results, indent=2, default=str))
            else:
                print(f">>> WARNING: evaluation_results is None or empty!")
            logger.info(f"[Save] Updating extraction {extraction.id} with evaluation_results={evaluation_results is not None}")
            extraction = await self.extraction_repo.update_extraction(extraction, evaluation_results)
            logger.info(f"[Save] Extraction updated successfully")
            print(f">>> Save completed")
            
            # 10. Log extraction
            self._log_extraction(extraction, document_type.name, version)
            
            return extraction
            
        except Exception as e:
            # Handle errors
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = str(e)
            extraction.completed_at = datetime.utcnow()
            extraction.processing_duration_ms = int((time.time() - start_time) * 1000)
            
            await self.extraction_repo.update_extraction(extraction)
            
            self._log_extraction(extraction, "unknown", version, success=False)
            
            raise
    
    def _map_to_output_schema(
        self,
        raw_results: Dict[str, Any],
        schema_version: DocumentTypeVersion,
        model_source: str
    ) -> List[ExtractedField]:
        """
        Map raw extraction results to output schema format.
        
        Args:
            raw_results: Raw results from model adapter
            schema_version: Schema defining output structure
            model_source: Name of model that produced results
        
        Returns:
            List of extracted fields
        """
        fields = []
        output_schema = schema_version.output_schema
        properties = output_schema.get("properties", {})
        
        for field_name in properties.keys():
            field_result = raw_results.get(field_name, {})
            
            value = field_result.get("value")
            confidence = field_result.get("confidence", 0.0)
            citations = field_result.get("citations", [])
            
            # Determine if review is needed
            needs_review = False
            review_reason = None
            
            if value is None:
                needs_review = True
                review_reason = "Field not found in document"
            elif confidence < schema_version.confidence_threshold:
                needs_review = True
                review_reason = f"Confidence {confidence:.2f} below threshold {schema_version.confidence_threshold}"
            
            # Determine value type
            value_type = type(value).__name__ if value is not None else "null"
            
            field = ExtractedField(
                field_name=field_name,
                value=value,
                value_type=value_type,
                confidence=confidence,
                citations=citations,
                needs_review=needs_review,
                review_reason=review_reason,
                model_source=model_source
            )
            fields.append(field)
        
        return fields
    
    def _handle_missing_fields(
        self,
        fields: List[ExtractedField],
        schema_version: DocumentTypeVersion
    ) -> List[ExtractedField]:
        """
        Handle missing required fields by adding null indicators.
        
        Args:
            fields: Currently extracted fields
            schema_version: Schema defining required fields
        
        Returns:
            Fields list with null entries for missing required fields
        """
        input_schema = schema_version.input_schema
        required_fields = set(input_schema.get("required", []))
        extracted_field_names = {f.field_name for f in fields}
        
        missing_required = required_fields - extracted_field_names
        
        for field_name in missing_required:
            field = ExtractedField(
                field_name=field_name,
                value=None,
                value_type="null",
                confidence=0.0,
                citations=[],
                needs_review=True,
                review_reason="Required field missing from extraction",
                model_source="system"
            )
            fields.append(field)
        
        return fields
    
    def _validate_output(
        self,
        fields: List[ExtractedField],
        schema_version: DocumentTypeVersion
    ) -> List[str]:
        """
        Validate extracted data against output schema.
        
        Args:
            fields: Extracted fields
            schema_version: Schema with validation rules
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Build output data structure
        output_data = {}
        for field in fields:
            output_data[field.field_name] = {
                "value": field.value,
                "confidence": field.confidence,
                "citations": [c.model_dump() for c in field.citations],
                "needs_review": field.needs_review
            }
        
        # Validate against output schema
        try:
            jsonschema.validate(output_data, schema_version.output_schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
        
        return errors
    
    def _log_extraction(
        self,
        extraction: ExtractionResult,
        document_type: str,
        version: str,
        success: bool = True
    ):
        """
        Log extraction attempt for monitoring.
        
        Args:
            extraction: Extraction result
            document_type: Document type name
            version: Schema version
            success: Whether extraction succeeded
        """
        # TODO: Integrate with Azure Application Insights in Phase 7
        log_entry = {
            "extraction_id": str(extraction.id),
            "document_id": extraction.document_id,
            "document_type": document_type,
            "version": version,
            "models_used": extraction.models_used,
            "duration_ms": extraction.processing_duration_ms,
            "status": extraction.status.value,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # For now, just print (will be replaced with proper logging)
        print(f"EXTRACTION_LOG: {log_entry}")
    
    async def get_extraction_result(self, extraction_id: UUID) -> Optional[ExtractionResult]:
        """Get extraction result by ID."""
        return await self.extraction_repo.get_extraction(extraction_id)
    
    async def _evaluate_extraction(
        self,
        extraction: ExtractionResult,
        document_content: bytes,
        adapter: ExtractionModelAdapter = None
    ) -> Optional[Dict[str, Any]]:
        """
        Run batch evaluation on extracted fields.
        
        Args:
            extraction: The extraction result with fields and citations
            document_content: Document bytes (fallback if no OCR text available)
            adapter: The adapter used for extraction (to get OCR text)
        """
        if not self.evaluation_service:
            return None
        
        try:
            # Try to get OCR text from adapter (already extracted during extraction)
            source_text = None
            ocr_source = "unknown"
            if adapter and hasattr(adapter, 'get_ocr_text'):
                source_text = adapter.get_ocr_text()
                if source_text:
                    ocr_source = "adapter_cache"
                    logger.info(f"[Evaluation] Using cached OCR text from extraction adapter ({len(source_text)} chars)")
            
            # Fallback to extracting text from document
            if not source_text:
                ocr_source = "document_extraction"
                logger.info("[Evaluation] No cached OCR text, extracting from document...")
                source_text = self._extract_text_from_document(document_content)
                logger.info(f"[Evaluation] Extracted {len(source_text)} chars from document")
            
            # Prepare fields for evaluation with page info from citations
            fields_to_evaluate = []
            for field in extraction.fields:
                # Include all fields, even those with None values
                field_data = {
                    "field_name": field.field_name,
                    "value": str(field.value) if field.value is not None else ""
                }
                # Add page info from citation if available
                if field.citations and len(field.citations) > 0:
                    field_data["page"] = field.citations[0].page
                fields_to_evaluate.append(field_data)
            
            if not fields_to_evaluate:
                logger.warning("[Evaluation] No fields to evaluate")
                return None
            
            logger.info(f"[Evaluation] Evaluating {len(fields_to_evaluate)} fields using {ocr_source} text source")
            logger.debug(f"[Evaluation] Fields to evaluate: {[f['field_name'] for f in fields_to_evaluate]}")
            
            # Run batch evaluation with both correctness and completeness
            eval_results = self.evaluation_service.evaluate_batch(
                fields=fields_to_evaluate,
                source_text=source_text,
                evaluators=["correctness", "completeness"]
            )
            
            # Log individual field results (evaluation service returns 'results' not 'field_results')
            if eval_results and 'results' in eval_results:
                logger.info(f"[Evaluation] Got {len(eval_results['results'])} evaluation results")
                for field_result in eval_results['results']:
                    field_name = field_result.get('field_name')
                    correctness_eval = field_result.get('evaluations', {}).get('correctness', {})
                    correctness = correctness_eval.get('score', 'N/A')
                    extraction_correct = correctness_eval.get('extraction_correct', False)
                    logger.debug(f"[Evaluation] {field_name}: correctness={correctness}, correct={extraction_correct}")
            else:
                logger.warning(f"[Evaluation] No results returned. eval_results keys: {eval_results.keys() if eval_results else 'None'}")
            
            print(f">>> _evaluate_extraction returning: {eval_results is not None}, total_fields={eval_results.get('total_fields') if eval_results else 'N/A'}")
            return eval_results
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return None
    
    def _extract_text_from_document(self, document_content: bytes) -> str:
        """
        Extract text from document page-wise using Azure Document Intelligence.
        
        Args:
            document_content: Raw document bytes (PDF, image, etc.)
            
        Returns:
            Text organized by pages for evaluation
        """
        try:
            # First try simple text decode for text files
            try:
                text = document_content.decode('utf-8', errors='strict')
                if len(text.strip()) > 0 and '\x00' not in text[:1000]:
                    # Looks like a text file, return directly
                    return text[:50000]
            except (UnicodeDecodeError, AttributeError):
                pass
            
            # Check if Document Intelligence is available
            if not HAS_DOC_INTELLIGENCE:
                logger.warning("Azure Document Intelligence SDK not installed")
                return "[Document content - OCR library not installed]"
            
            # Use Azure Document Intelligence for OCR
            from azure.identity import DefaultAzureCredential
            
            config = get_config()
            
            # Get Document Intelligence endpoint
            doc_intel_endpoint = getattr(config, 'doc_intelligence_endpoint', None)
            if not doc_intel_endpoint:
                logger.warning("Document Intelligence endpoint not configured")
                return "[Document content - OCR not configured]"
            
            # Initialize client
            credential = DefaultAzureCredential()
            client = DocumentIntelligenceClient(
                endpoint=doc_intel_endpoint,
                credential=credential
            )
            
            # Analyze document with prebuilt-read model
            logger.info("Extracting text using Azure Document Intelligence...")
            poller = client.begin_analyze_document(
                model_id="prebuilt-read",
                body=document_content,
                content_type="application/octet-stream"
            )
            
            result = poller.result()
            
            # Extract text page by page
            page_texts = []
            if result.pages:
                for page in result.pages:
                    page_num = page.page_number
                    page_text_lines = []
                    
                    # Extract all lines from the page
                    if page.lines:
                        for line in page.lines:
                            page_text_lines.append(line.content)
                    
                    # Format page text
                    page_content = "\n".join(page_text_lines)
                    page_texts.append(f"[Page {page_num}]\n{page_content}")
                
                # Combine all pages
                full_text = "\n\n".join(page_texts)
                logger.info(f"Extracted {len(result.pages)} pages, total {len(full_text)} characters")
                return full_text[:100000]  # Limit to 100K characters
            
            return "[No text extracted]"
            
        except Exception as e:
            logger.error(f"Error extracting text from document: {e}")
            return "[Error extracting document text]"
