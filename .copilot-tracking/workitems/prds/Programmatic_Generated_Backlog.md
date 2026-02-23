# Programmatically Generated Backlog

Date (UTC): 2025-11-19

Source transcripts: Transcript1, Transcript2, Transcript3, Transcript4, Transcript5

Confidence: Draft – requires stakeholder validation.

## Detected Themes (Heuristic)

- Document Classification
- Financial Analysis
- Fraud / Malicious Detection
- Handwritten Layout Handling
- Identity Verification
- Medical Report Processing
- Model Governance
- Quality Metrics
- Regional Compliance
- Signature Verification
- UI/UX Workflow
- Underwriting Summarization

## Next Steps (Aggregated)

- [Transcript2] Josh to check and share the Excel file containing document details with the Microsoft team.
- [Transcript2] Josh to check if dummy document samples can be shared with the Microsoft team.
- [Transcript2] Cherry to summarize document types and information requirements in a table and share with the Microsoft team.
- [Transcript2] Microsoft ISE team to connect with other ISE team members who work with different insurance customers to gather learnings on similar use cases.
- [Transcript2] Microsoft team to understand the minimum quality requirements for scanned documents.
- [Transcript2] Josh to continue the discussion on POC prompts and extractions in the next meeting before moving to UI discussions.
- [Transcript3] Josh to share the Excel file containing the list of documents with Lukasz's team.
- [Transcript3] Josh and Lukasz to schedule the next meeting for Thursday of the following week.
- [Transcript3] Microsoft team to explore solutions for signature extraction in Azure without requiring Contoso to provide training data.
- [Transcript3] Josh's team to test the Python layout approach suggested by Vikesh for handling text written across multiple columns/lines.
- [Transcript3] Tanveer to get statistics from underwriters on how frequently the issue of text written across lines/columns occurs in documents.
- [Transcript3] Esra and Tanveer to consider scheduling a separate discussion about redesigning the overall workflow for underwriting.
- [Transcript3] Summary
- [Transcript3] AI Document Processing POC Review
- [Transcript3] The team discussed a POC for document processing using AI models, focusing on extracting information from underwriting documents. Josh explained they tested 6-10 document types using generic models without custom training, processing items like medical reports and application forms. Joe was tasked with presenting sample results to demonstrate the system's capabilities and challenges, particularly around signature verification where they currently use Tesseract due to its flexibility. The team also discussed the need for further testing with Hong Kong data, which cannot be sent to US servers, and the comparison between models with different context windows.
- [Transcript4] Josh to share the Excel file containing the list of documents with Lukasz's team.
- [Transcript4] Josh and Lukasz to schedule the next meeting for Thursday of the following week.
- [Transcript4] Microsoft team to explore solutions for signature extraction in Azure without requiring Contoso to provide training data.
- [Transcript4] Josh's team to test the Python layout approach suggested by Vikesh for handling text written across multiple columns/lines.
- [Transcript4] Tanveer to get statistics from underwriters on how frequently the issue of text written across lines/columns occurs in documents.
- [Transcript4] Esra and Tanveer to consider scheduling a separate discussion about redesigning the overall workflow for underwriting.
- [Transcript4] Summary
- [Transcript4] AI Document Processing POC Review
- [Transcript4] The team discussed a POC for document processing using AI models, focusing on extracting information from underwriting documents. Josh explained they tested 6-10 document types using generic models without custom training, processing items like medical reports and application forms. Joe was tasked with presenting sample results to demonstrate the system's capabilities and challenges, particularly around signature verification where they currently use Tesseract due to its flexibility. The team also discussed the need for further testing with Hong Kong data, which cannot be sent to US servers, and the comparison between models with different context windows.

## Action Items (Actor → Action)

- [Transcript1] Expected to be implemented in Agentic AI solution pattern with reusable components to be shared across the insurance / credit underwriting and the insurance claims use cases
- [Transcript1] Agreed to start with the insurance underwriting use case first and then the credit underwriting use case
- [Transcript2] Josh to check and share the Excel file containing document details with the Microsoft team
- [Transcript2] Josh to check if dummy document samples can be shared with the Microsoft team
- [Transcript2] Cherry to summarize document types and information requirements in a table and share with the Microsoft team
- [Transcript2] Josh to continue the discussion on POC prompts and extractions in the next meeting before moving to UI discussions
- [Transcript3] Josh to share the Excel file containing the list of documents with Lukasz's team
- [Transcript3] Tanveer to get statistics from underwriters on how frequently the issue of text written across lines/columns occurs in documents
- [Transcript4] Josh to share the Excel file containing the list of documents with Lukasz's team
- [Transcript4] Tanveer to get statistics from underwriters on how frequently the issue of text written across lines/columns occurs in documents

## Pipeline / Ordered Steps

- [Transcript5] 1. Takes up to a few hours for the underwriters to process each case with 30+ documents with some
- [Transcript5] 2. Potential risks of overlooking key information for the underwriting assessment because of the
- [Transcript5] 3. In some cases, can involve high number of turnarounds of supplementing documents
- [Transcript5] 4. Can only support a very low % of manual audit of the accuracy of the underwriting assessment
- [Transcript5] 1. Document classification
- [Transcript5] 2. Document image quality check
- [Transcript5] 3. Document criteria check / malicious document check
- [Transcript5] 4. Document checklist verification
- [Transcript5] 5. Document level summary per document (no fixed list of fields per document considering the
- [Transcript5] 6. ID and signature verification
- [Transcript5] 7. Overall case level summary and assessment
- [Transcript5] 8. Generation of the quality metrics (relevancy, consistency, fluency, coherence, etc) for the case
- [Transcript5] 1. Document list showing list of documents classified, the image quality of those documents,
- [Transcript5] 2. AI-generated document level summary with the corresponding preview of the original document
- [Transcript5] 3. AI verification of the ID and signature across the documents where the user will provide feedback
- [Transcript5] 4. AI-generated case level underwriting summary, together with the quality metric of the summary
- [Transcript5] 5. User will assign an overall user satisfaction score at a case level based on the quality of the AI
- [Transcript5] 6. Ideally, between versions, there can be a summary of what are the additional documents in the

## Preliminary Epics Derived From Themes

### Document Classification

Placeholder user story: As an underwriter, I need document classification capabilities to accelerate and improve underwriting accuracy.

### Financial Analysis

Placeholder user story: As an underwriter, I need financial analysis capabilities to accelerate and improve underwriting accuracy.

### Fraud / Malicious Detection

Placeholder user story: As an underwriter, I need fraud / malicious detection capabilities to accelerate and improve underwriting accuracy.

### Handwritten Layout Handling

Placeholder user story: As an underwriter, I need handwritten layout handling capabilities to accelerate and improve underwriting accuracy.

### Identity Verification

Placeholder user story: As an underwriter, I need identity verification capabilities to accelerate and improve underwriting accuracy.

### Medical Report Processing

Placeholder user story: As an underwriter, I need medical report processing capabilities to accelerate and improve underwriting accuracy.

### Model Governance

Placeholder user story: As an underwriter, I need model governance capabilities to accelerate and improve underwriting accuracy.

### Quality Metrics

Placeholder user story: As an underwriter, I need quality metrics capabilities to accelerate and improve underwriting accuracy.

### Regional Compliance

Placeholder user story: As an underwriter, I need regional compliance capabilities to accelerate and improve underwriting accuracy.

### Signature Verification

Placeholder user story: As an underwriter, I need signature verification capabilities to accelerate and improve underwriting accuracy.

### UI/UX Workflow

Placeholder user story: As an underwriter, I need ui/ux workflow capabilities to accelerate and improve underwriting accuracy.

### Underwriting Summarization

Placeholder user story: As an underwriter, I need underwriting summarization capabilities to accelerate and improve underwriting accuracy.


## Notes

- This file was generated automatically via heuristic parsing.

- Improve by integrating structured annotation or LLM extraction with JSON schema.

- Consider mapping actions to Azure DevOps work items next.
