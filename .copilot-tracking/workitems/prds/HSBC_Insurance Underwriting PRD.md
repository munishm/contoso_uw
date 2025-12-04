## HNW Insurance Underwriting Process

### Overall goal of the HSBC UW Engagement is entailed below

- Reduction in manual underwriting processing time to lower than 3 hours per case
- Establish a standardized case management framework that ensures consistency and auditability across all cases, with full traceability back to source documents to strengthen compliance, transparency, and decision-making integrity.
- Establish a robust document ingestion and preprocessing capability that standardizes incoming data by cleaning text and optimizing OCR outputs, enabling accurate document classification
- Implement an intelligent document classification system that automatically identifies document types and validates completeness against mandatory information requirements, ensuring accuracy
- Benchmarked accuracy levels with citations for the summaries generated at each document and logically grouped set of documents
- Support multi-language (English, Traditional Chinese, Simplified Chinese) understanding often within the same document with ability to relate entities across multiple multi-lingual document
- Component Level Evaluation with Human in the loop verification
- Document Extraction for Underwriting Platform Approach with ability to extract key entities for underwriting (The goal is to create a pattern which applies to credit underwriting scenarios as well)
- Enhance underwriting integrity by implementing advanced fraud and malicious document detection mechanisms to ensure only authentic, accurate, and compliant documents are processed, reducing financial risk and safeguarding against fraudulent claims

### Business Success Criteria

- Significant reduction in Underwriting Processing Time currently measured at 3–4 hours per case per day
- Significant reduction in process inefficiencies often take days to ensure completeness of mandatory documents and information

| Goal #   | **Business Goal**                                 | **AS-IS State**           | **Success Criteria (TO-BE state)**                                                                 | **Roadmap Alignment**           | **MosCoW**           |
|----------|---------------------------------------------------|---------------------------|----------------------------------------------------------------------------------------------------|-------------------------------|----------------------|
| BG-001   | Processing Time Reduction in Manual Underwriting  | 3 – 4 hours per case      | < 3 hours per case (To be validated)                                                               | North Star                    | Must-Have            |
| BG-002   | Document Versioning or Lifecycle Management       | Unknown                   | Multiple versions of the same documents should be versioned with details to enable UW to choose    | MVP Release (April – May 2026) | Must-Have            |
| BG-003   | Document Ingestion and Pre-processing             | Multi-Channel lacking a unified approach to ingestion | Fully Automated | MVP Release (April – May 2026) | Must-Have            |
| BG-004   | Document Classification                           | Manual Classification     | Fully Automated                                                                                     |                               | Must-Have            |
| BG-005   | Add Citations within Summary for traceability     | Done manually             | Citations should be embedded within the summaries generated. To be established (Consider 95% accuracy of citation) 100% Correct UW Decision backed by Audit | TBD                          | Must-Have            |
| BG-006   | Summarization (Single and Multiple Documents)     | Done Manually             | Fully Automated                                                                                     | MVP Release (April – May 2026) | Must-Have            |
| BG-007   | Component Level Evaluation                        | Partial Automation        | Fully Automated                                                                                     | TBD                          | Must-Have            |
| BG-008   | Multi-language Support                            | Done Manually             | Fully Automated                                                                                     | MVP Release (April – May 2026) | Must-Have            |
| BG-009   | Fraud and Malicious Document Detection and Safety | Done Manually             | Fully Automated                                                                                     | TBD                          | Nice to have         |
| BG-010   | Document Extraction for Underwriting – Platform First Approach | NA                        | NA                                                                                                 | TBD                          | Must-Have (ISE Led)  |

#### Comments

- Vikesh Singh Baghel: Not sure if we want to fraud here as there shall be a separate process
- Debleena Banerjee: Based on my conversations with Tanvir this is in the customer roadmap. Now, do we want to take it up is subject to further decisions

### For Phase 1 of the release below are high level focus areas for the project

- If customer data is made available, understand the distribution of documents and identify distinct patterns which can create the sample set of documents for subsequent MVEs
- This sample set should be representative of the document structural patterns for the sample set selected for Phase 1 release for HSBC
- In the absence of customer data, synthetic data generation needs to be considered
- Synthetic Data Generation for specific document types including application form, medical lab reports and individual ID cards to be considered
- Finalize the approach for Synthetic Data Generation for Documents
- Document Ingestion:
  - Document Classification
  - Meta-Data Tagging
  - Completeness of Information within the document
- Document Classification Module is key to enable Underwriters with the ability to understand the comprehensiveness of the documents subsequently also checking for frauds within
- Summary at document level and overall summary is a must-have requirement with citations
- Evaluation of Pre-Trained Models for Entity Extraction from the selected documents
- Pattern First approach – Document Extraction Platform for Underwriting
- For Phase 1, the components built should have enough flexibility and configurability to enable capabilities which can extend to other business domains of underwriting including credit
- Each Business Requirement will break down into multiple functional requirements which will result in user stories and tasks for Phase 1 of the project:

| **Goal #**         | **FR #**   | **FR Title**                  | **Description**                                                                                   | **Acceptance Criteria**                                                                 | **MosCoW**           |
|--------------------|------------|-------------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|----------------------|
| **BG-001 and BG-003** | FR-001     | Document Ingestion            | The system should automatically ingest the incoming documents through a unified automated pipeline | Accuracy levels > X% for detecting the document type and have a relevance score, completion and coverage score for the content of the document | Must-Have            |
| **BG-002**         | FR-002     | Document Classification [Document Intake] |                                                                                                   |                                                                                        |                      |

#### Comments

- Vikesh Singh Baghel: The relevance score shall give us directional metrics. We can also include completeness score which can be measured by whether all necessary fields from a document are included in the summary. Also, we can include statistical metrics like ROUGE score to compare LLM generated summaries with human written summaries
