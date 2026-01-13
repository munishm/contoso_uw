"""Service for schema-based document extraction."""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
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
                import os
                config = get_config()
                credential = DefaultAzureCredential()
                
                # Get OpenAI endpoint - prefer EXTRACTION_ prefixed, fallback to AZURE_OPENAI_ENDPOINT
                openai_endpoint = os.environ.get('EXTRACTION_OPENAI_ENDPOINT')
                if not openai_endpoint:
                    openai_endpoint = getattr(config, 'openai_endpoint', None)
                if not openai_endpoint:
                    openai_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
                print(f"[SchemaExtractionService.__init__] OpenAI endpoint: {openai_endpoint}")
                
                # Get deployment - prefer EXTRACTION_ prefixed, fallback to AZURE_OPENAI_DEPLOYMENT
                deployment_name = os.environ.get('EXTRACTION_OPENAI_DEPLOYMENT_GPT4_VISION')
                if not deployment_name:
                    deployment_name = getattr(config, 'openai_deployment_gpt4_vision', None)
                if not deployment_name or deployment_name == "gpt-4-vision":  # Default value means not explicitly set
                    deployment_name = os.environ.get('AZURE_OPENAI_DEPLOYMENT', deployment_name)
                print(f"[SchemaExtractionService.__init__] Using deployment: {deployment_name}")
                
                # Get API version - prefer EXTRACTION_ prefixed
                api_version = os.environ.get('EXTRACTION_OPENAI_API_VERSION', '2024-12-01-preview')
                print(f"[SchemaExtractionService.__init__] API version: {api_version}")
                
                print(f"[SchemaExtractionService.__init__] Config: endpoint={openai_endpoint}, deployment={deployment_name}, api_version={api_version}")
                self.evaluation_service = EvaluationService(
                    azure_endpoint=openai_endpoint,
                    deployment_name=deployment_name,
                    api_version=api_version,
                    credential=credential
                )
                print(f"[SchemaExtractionService.__init__] Evaluation service created successfully")
                print(f"[SchemaExtractionService.__init__] Completeness evaluator initialized: {self.evaluation_service.completeness_evaluator is not None}")
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
            combination_strategy = extraction_config.get("combination_strategy", "sequential")
            conflict_resolution = extraction_config.get("conflict_resolution", "flag_for_review")
            logger.info(f"  extraction_config.models: {len(models)} configured")
            logger.info(f"  combination_strategy: {combination_strategy}")
            logger.info(f"  conflict_resolution: {conflict_resolution}")
            
            if not models:
                logger.error(f"  ✗ No models configured in extraction_config")
                raise ValueError("No models configured for this schema version")
            
            # Execute multi-model extraction based on strategy
            raw_results, models_used = await self._execute_multi_model_extraction(
                document_content=document_content,
                document_type=document_type,
                schema_version=schema_version,
                model_configs=models,
                combination_strategy=combination_strategy,
                conflict_resolution=conflict_resolution
            )
            
            extraction.models_used = models_used
            logger.info(f"  ✓ Extraction returned {len(raw_results)} raw fields from {len(models_used)} models")
            logger.info(f"  Raw results: {list(raw_results.keys())}")
            
            # 4. Map extracted data to output schema fields (model_source from merged results)
            extracted_fields = self._map_to_output_schema(
                raw_results,
                schema_version,
                ", ".join(models_used)  # Default model source (overridden per field from merged data)
            )
            
            # 5. Handle missing required fields
            extracted_fields = self._handle_missing_fields(
                extracted_fields,
                schema_version
            )
            
            # 6. Validate against output schema
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
            
            # 7. Run batch evaluation if enabled
            evaluation_results = None
            logger.info(f"[Evaluation] Check: enable_evaluation={self.enable_evaluation}, evaluation_service={self.evaluation_service is not None}")
            if self.enable_evaluation and self.evaluation_service:
                try:
                    eval_start = time.time()
                    logger.info("Running batch evaluation...")
                    print(f">>> Running batch evaluation...")
                    # Pass the last adapter used (stored during multi-model extraction)
                    adapter = getattr(self, '_last_adapter', None)
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
            
            # 8. Save result with evaluation
            print(f"\n>>> Step 8: Saving extraction with evaluation_results={evaluation_results is not None}")
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

    async def _execute_multi_model_extraction(
        self,
        document_content: bytes,
        document_type: Any,
        schema_version: DocumentTypeVersion,
        model_configs: List[Dict[str, Any]],
        combination_strategy: str,
        conflict_resolution: str
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Execute extraction using multiple models based on strategy.
        
        Args:
            document_content: Document bytes
            document_type: Document type object
            schema_version: Schema version with field definitions
            model_configs: List of model configurations
            combination_strategy: How to combine results (sequential, parallel, ensemble, hybrid)
            conflict_resolution: How to resolve conflicts (highest_confidence, flag_for_review, average, vote)
        
        Returns:
            Tuple of (merged_results, list_of_models_used)
        """
        logger.info(f"  Multi-model extraction: {len(model_configs)} models, strategy={combination_strategy}")
        
        # Sort models by order
        sorted_models = sorted(model_configs, key=lambda m: m.get("order", 999))
        
        # Group by strategy
        primary_models = [m for m in sorted_models if m.get("strategy") == "primary"]
        fallback_models = [m for m in sorted_models if m.get("strategy") == "fallback"]
        parallel_models = [m for m in sorted_models if m.get("strategy") == "parallel"]
        
        all_results: List[Tuple[Dict[str, Any], str, List[str]]] = []
        models_used = []
        
        # Execute based on combination strategy
        if combination_strategy == "parallel":
            # Run all models concurrently
            logger.info("  Executing parallel extraction...")
            tasks = []
            for model_config in sorted_models:
                tasks.append(self._run_single_model(
                    document_content, document_type, schema_version, model_config
                ))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result, model_config in zip(results, sorted_models):
                if isinstance(result, Exception):
                    logger.error(f"  Model {model_config.get('model_id')} failed: {result}")
                    continue
                raw_result, model_name = result
                fields = model_config.get("fields", ["*"])
                all_results.append((raw_result, model_name, fields))
                models_used.append(model_name)
                
        elif combination_strategy == "sequential":
            # Run primary first, then fallback if needed, parallel run concurrently
            logger.info("  Executing sequential extraction...")
            
            # 1. Run primary model(s)
            for model_config in primary_models:
                try:
                    raw_result, model_name = await self._run_single_model(
                        document_content, document_type, schema_version, model_config
                    )
                    fields = model_config.get("fields", ["*"])
                    all_results.append((raw_result, model_name, fields))
                    models_used.append(model_name)
                except Exception as e:
                    logger.error(f"  Primary model {model_config.get('model_id')} failed: {e}")
                    # Try fallback models
                    for fb_config in fallback_models:
                        try:
                            raw_result, model_name = await self._run_single_model(
                                document_content, document_type, schema_version, fb_config
                            )
                            fields = fb_config.get("fields", ["*"])
                            all_results.append((raw_result, model_name, fields))
                            models_used.append(model_name)
                            break  # Use first successful fallback
                        except Exception as fb_e:
                            logger.error(f"  Fallback model {fb_config.get('model_id')} failed: {fb_e}")
            
            # 2. Run parallel models concurrently (for additional field coverage)
            if parallel_models:
                tasks = [
                    self._run_single_model(document_content, document_type, schema_version, m)
                    for m in parallel_models
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result, model_config in zip(results, parallel_models):
                    if isinstance(result, Exception):
                        logger.error(f"  Parallel model {model_config.get('model_id')} failed: {result}")
                        continue
                    raw_result, model_name = result
                    fields = model_config.get("fields", ["*"])
                    all_results.append((raw_result, model_name, fields))
                    models_used.append(model_name)
                    
        elif combination_strategy == "ensemble":
            # Run all models, vote/average on results
            logger.info("  Executing ensemble extraction...")
            tasks = []
            for model_config in sorted_models:
                tasks.append(self._run_single_model(
                    document_content, document_type, schema_version, model_config
                ))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result, model_config in zip(results, sorted_models):
                if isinstance(result, Exception):
                    logger.error(f"  Model {model_config.get('model_id')} failed: {result}")
                    continue
                raw_result, model_name = result
                fields = model_config.get("fields", ["*"])
                all_results.append((raw_result, model_name, fields))
                models_used.append(model_name)
        
        else:  # hybrid or default
            # Run primary, then selective parallel for specific fields
            logger.info(f"  Executing {combination_strategy} extraction...")
            for model_config in sorted_models:
                try:
                    raw_result, model_name = await self._run_single_model(
                        document_content, document_type, schema_version, model_config
                    )
                    fields = model_config.get("fields", ["*"])
                    all_results.append((raw_result, model_name, fields))
                    models_used.append(model_name)
                except Exception as e:
                    logger.error(f"  Model {model_config.get('model_id')} failed: {e}")
        
        if not all_results:
            raise ValueError("All models failed during extraction")
        
        # Merge results based on conflict resolution
        merged_results = self._merge_model_results(all_results, conflict_resolution, schema_version)
        
        logger.info(f"  Multi-model extraction complete: {len(models_used)} models, {len(merged_results)} fields")
        return merged_results, models_used

    async def _run_single_model(
        self,
        document_content: bytes,
        document_type: Any,
        schema_version: DocumentTypeVersion,
        model_config: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], str]:
        """
        Run extraction with a single model.
        
        Returns:
            Tuple of (raw_results, model_name)
        """
        model_id = UUID(model_config.get("model_id"))
        db_model = await self.model_repo.get_model(model_id)
        
        if not db_model:
            raise ValueError(f"Model {model_id} not found")
        if not db_model.is_active:
            raise ValueError(f"Model {db_model.name} is not active")
        
        # Create adapter
        if db_model.type == ModelType.VISION:
            config = get_config()
            adapter = AzureOpenAIVisionAdapter(
                endpoint=db_model.endpoint,
                api_key=None,
                deployment=db_model.version,
                api_version=db_model.api_version or "2024-02-15-preview",
                doc_intelligence_endpoint=config.doc_intelligence_endpoint,
                doc_intelligence_key=config.doc_intelligence_key
            )
        else:
            raise ValueError(f"Unsupported model type: {db_model.type}")
        
        # Get fields to extract
        field_names = model_config.get("fields", ["*"])
        
        # Execute extraction
        raw_results = await adapter.extract(
            document_content,
            document_type.name,
            schema_version,
            field_names
        )
        
        # Store adapter for evaluation (last adapter used)
        self._last_adapter = adapter
        
        return raw_results, db_model.name

    def _merge_model_results(
        self,
        all_results: List[Tuple[Dict[str, Any], str, List[str]]],
        conflict_resolution: str,
        schema_version: DocumentTypeVersion
    ) -> Dict[str, Any]:
        """
        Merge results from multiple models based on conflict resolution strategy.
        
        Args:
            all_results: List of (raw_results, model_name, fields_extracted) tuples
            conflict_resolution: Strategy for resolving conflicts
            schema_version: Schema for field definitions
        
        Returns:
            Merged results dictionary
        """
        if len(all_results) == 1:
            # Only one model, return its results directly
            return all_results[0][0]
        
        merged = {}
        output_schema = schema_version.output_schema
        all_fields = output_schema.get("properties", {}).keys()
        
        for field_name in all_fields:
            # Collect all values for this field across models
            field_values = []
            for raw_results, model_name, fields_list in all_results:
                # Check if this model was supposed to extract this field
                if "*" not in fields_list and field_name not in fields_list:
                    continue
                    
                if field_name in raw_results:
                    result = raw_results[field_name]
                    value = result.get("value")
                    confidence = result.get("confidence", 0.0)
                    citations = result.get("citations", [])
                    field_values.append({
                        "value": value,
                        "confidence": confidence,
                        "citations": citations,
                        "model": model_name
                    })
            
            if not field_values:
                # No model extracted this field
                merged[field_name] = {
                    "value": None,
                    "confidence": 0.0,
                    "citations": [],
                    "model_source": "none"
                }
                continue
            
            if len(field_values) == 1:
                # Only one model provided this field
                fv = field_values[0]
                merged[field_name] = {
                    "value": fv["value"],
                    "confidence": fv["confidence"],
                    "citations": fv["citations"],
                    "model_source": fv["model"]
                }
                continue
            
            # Multiple models provided values - resolve conflict
            if conflict_resolution == "highest_confidence":
                # Use value with highest confidence
                best = max(field_values, key=lambda x: x["confidence"])
                merged[field_name] = {
                    "value": best["value"],
                    "confidence": best["confidence"],
                    "citations": best["citations"],
                    "model_source": best["model"]
                }
                
            elif conflict_resolution == "vote":
                # Use most common value (simple voting)
                value_counts = {}
                for fv in field_values:
                    v = str(fv["value"])
                    if v not in value_counts:
                        value_counts[v] = {"count": 0, "best_fv": fv}
                    value_counts[v]["count"] += 1
                    if fv["confidence"] > value_counts[v]["best_fv"]["confidence"]:
                        value_counts[v]["best_fv"] = fv
                
                winner = max(value_counts.values(), key=lambda x: (x["count"], x["best_fv"]["confidence"]))
                best = winner["best_fv"]
                merged[field_name] = {
                    "value": best["value"],
                    "confidence": best["confidence"],
                    "citations": best["citations"],
                    "model_source": f"vote:{best['model']}"
                }
                
            elif conflict_resolution == "average":
                # Average numeric values, take highest confidence for non-numeric
                numeric_values = []
                for fv in field_values:
                    try:
                        numeric_values.append((float(fv["value"]), fv["confidence"]))
                    except (TypeError, ValueError):
                        pass
                
                if numeric_values and len(numeric_values) == len(field_values):
                    # All values are numeric, average them
                    avg_value = sum(v for v, _ in numeric_values) / len(numeric_values)
                    avg_conf = sum(c for _, c in numeric_values) / len(numeric_values)
                    merged[field_name] = {
                        "value": avg_value,
                        "confidence": avg_conf,
                        "citations": field_values[0]["citations"],  # Use first model's citations
                        "model_source": "average"
                    }
                else:
                    # Non-numeric, fall back to highest confidence
                    best = max(field_values, key=lambda x: x["confidence"])
                    merged[field_name] = {
                        "value": best["value"],
                        "confidence": best["confidence"],
                        "citations": best["citations"],
                        "model_source": best["model"]
                    }
                    
            else:  # flag_for_review or default
                # Take highest confidence but flag for review if values differ
                values_agree = len(set(str(fv["value"]) for fv in field_values)) == 1
                best = max(field_values, key=lambda x: x["confidence"])
                
                merged[field_name] = {
                    "value": best["value"],
                    "confidence": best["confidence"],
                    "citations": best["citations"],
                    "model_source": best["model"],
                    "needs_review": not values_agree,
                    "review_reason": "Models disagree" if not values_agree else None,
                    "all_values": [{"model": fv["model"], "value": fv["value"], "confidence": fv["confidence"]} for fv in field_values]
                }
        
        return merged

    def _map_to_output_schema(
        self,
        raw_results: Dict[str, Any],
        schema_version: DocumentTypeVersion,
        model_source: str
    ) -> List[ExtractedField]:
        """
        Map raw extraction results to output schema format.
        
        Args:
            raw_results: Raw results from model adapter or merged multi-model results
            schema_version: Schema defining output structure
            model_source: Default model name (used if not in result)
        
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
            
            # Get model source from result (for multi-model), fallback to default
            field_model_source = field_result.get("model_source", model_source)
            
            # Check for multi-model review flags
            needs_review = field_result.get("needs_review", False)
            review_reason = field_result.get("review_reason")
            
            # Additional review checks
            if value is None and not needs_review:
                needs_review = True
                review_reason = "Field not found in document"
            elif confidence < schema_version.confidence_threshold and not needs_review:
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
                model_source=field_model_source
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
            print(f"\n[_evaluate_extraction] Adapter check:")
            print(f"  adapter is None: {adapter is None}")
            print(f"  adapter has get_ocr_text: {hasattr(adapter, 'get_ocr_text') if adapter else 'N/A'}")
            
            if adapter and hasattr(adapter, 'get_ocr_text'):
                source_text = adapter.get_ocr_text()
                print(f"  adapter.get_ocr_text() returned: {len(source_text) if source_text else 'None/empty'} chars")
                if source_text:
                    ocr_source = "adapter_cache"
                    logger.info(f"[Evaluation] Using cached OCR text from extraction adapter ({len(source_text)} chars)")
            
            # Fallback to extracting text from document
            if not source_text:
                ocr_source = "document_extraction"
                logger.info("[Evaluation] No cached OCR text, extracting from document...")
                print(f"  Falling back to document extraction...")
                source_text = self._extract_text_from_document(document_content)
                print(f"  Extracted from document: {len(source_text) if source_text else 0} chars")
                logger.info(f"[Evaluation] Extracted {len(source_text)} chars from document")
            
            print(f"  Final source_text length: {len(source_text) if source_text else 0}")
            # Only print first 100 chars to avoid flooding logs
            sample = source_text[:100].replace('\n', ' ') if source_text else 'EMPTY'
            print(f"  Source sample (first 100 chars): {sample}...")
            
            # Prepare fields for evaluation with page info from citations
            fields_to_evaluate = []
            
            print(f"\n[_evaluate_extraction] Fields to evaluate:")
            print(f"  extraction.fields count: {len(extraction.fields)}")
            
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
                # Print each field being evaluated
                val_preview = str(field.value)[:50] if field.value else "None"
                print(f"    - {field.field_name}: '{val_preview}'")
            
            print(f"  Total fields: {len(fields_to_evaluate)}")
            
            if not fields_to_evaluate:
                logger.warning("[Evaluation] No fields to evaluate")
                return None
            
            logger.info(f"[Evaluation] Evaluating {len(fields_to_evaluate)} fields using {ocr_source} text source")
            
            # Run batch evaluation with both correctness and completeness
            print(f"\n[_evaluate_extraction] Calling evaluate_batch...")
            eval_results = self.evaluation_service.evaluate_batch(
                fields=fields_to_evaluate,
                source_text=source_text,
                evaluators=["correctness", "completeness"]
            )
            
            # Log individual field results
            print(f"\n[_evaluate_extraction] Evaluation Results:")
            if eval_results and 'results' in eval_results:
                print(f"  Total results: {len(eval_results['results'])}")
                for field_result in eval_results['results']:
                    field_name = field_result.get('field_name')
                    correctness_eval = field_result.get('evaluations', {}).get('correctness', {})
                    score = correctness_eval.get('score', 'N/A')
                    fuzzy = correctness_eval.get('fuzzy_score', 'N/A')
                    correct = correctness_eval.get('extraction_correct', False)
                    print(f"    - {field_name}: score={score}, fuzzy={fuzzy}, correct={correct}")
                
                # Print aggregate
                agg = eval_results.get('aggregate_summary', {})
                print(f"\n  Aggregate Summary:")
                print(f"    average_correctness_score: {agg.get('average_correctness_score', 'N/A')}")
                print(f"    fields_correct: {agg.get('fields_correct', 0)}/{eval_results.get('total_fields', len(fields_to_evaluate))}")
            else:
                print(f"  WARNING: No results returned!")
                print(f"  eval_results keys: {eval_results.keys() if eval_results else 'None'}")
            
            return eval_results
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            print(f"[_evaluate_extraction] ERROR: {e}")
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
