<!--
Sync Impact Report - Constitution v1.1.0
════════════════════════════════════════

Version Change: 1.0.0 → 1.1.0
Type: MINOR (Scope clarification and technology stack specification)

Modified Principles:
  - Principle 4: Updated to POC scope (2 English forms only, multi-language deferred)
  - Principle 6: Updated performance targets to POC-appropriate levels
  - Principle 8: Added Azure-only architecture constraint

Added Sections:
  - POC Phase scope clarification
  - Azure technology stack specification
  - Updated success criteria for POC

Templates Requiring Updates:
  ✅ Plan template - aligned with POC scope
  ✅ Spec template - includes Azure services
  ✅ Tasks template - reflects POC priorities
  ⚠ Commands (speckit.constitution) - initial version, will evolve

Follow-up TODOs:
  - Define specific team owner/lead (marked TBD)
  - Secure Azure AI Document Intelligence access
  - Provision Azure OpenAI Service with quota
  - Define 2 specific application forms for POC
  - Define 5-6 extraction fields per document

Generated: 2025-12-11
-->

# HSBC Insurance Underwriting Automation Project Constitution

**Version:** 1.1.0  
**Ratification Date:** 2025-12-11  
**Last Amended:** 2025-12-11  
**Status:** Active  
**Scope:** HSBC HNW Insurance Underwriting Process Automation (POC Phase)

---

## Project Identity & Mission

### Project Name
HSBC High Net Worth (HNW) Insurance Underwriting Process Automation Platform

### Mission Statement
Validate the technical and business viability of AI-powered document processing for insurance underwriting through a focused proof-of-concept, demonstrating accurate classification, extraction, and summarization on 2 English application forms, thereby establishing the foundation for full-scale automation.

### Project Vision
Establish the industry-leading intelligent document processing platform for insurance underwriting that:
- Delivers consistent, explainable AI-driven insights to underwriters
- Ensures complete auditability and regulatory compliance
- Scales to handle growing case volumes without proportional headcount increases
- Creates reusable patterns applicable to credit underwriting and beyond

### Strategic Context
This POC phase addresses the need to validate AI capabilities before full-scale investment. The proof-of-concept focuses on:
- **Document Scope**: 2 English-language application forms
- **Field Extraction**: 5-6 key fields per document type
- **Technology Stack**: Azure-only services (Azure AI Document Intelligence, Azure OpenAI, Azure ML)
- **Timeline**: 8-12 weeks
- **Validation Goals**: Prove >95% classification accuracy, >90% extraction completeness, quality summaries with citations
- **Foundation Building**: Establish reusable patterns, data contracts, and architecture for production scaling

### Success Criteria (POC Phase)
- **Classification Accuracy:** >95% precision/recall on test set with confusion matrix validation
- **Extraction Quality:** >90% completeness and correctness for 5-6 fields per document
- **Summary Quality:** Benchmarked against manual summaries, with proper citations to source text
- **Technical Proof:** OCR accuracy >98% for typed text using Azure AI Document Intelligence
- **Architecture Validation:** Reusable patterns, data contracts, and schemas documented
- **Stakeholder Approval:** Demo completed, business case validated, production funding secured

---

## Core Principles

These principles are **NON-NEGOTIABLE** and MUST guide all decisions, implementations, and operations throughout the project lifecycle.

### Principle 1: Compliance & Regulatory Adherence First

**Statement:**  
All system capabilities, data handling, and AI outputs MUST comply with applicable insurance regulations, data privacy laws (GDPR, CCPA, HIPAA where applicable), and HSBC internal policies before any feature is deployed to production.

**Rationale:**  
Processing highly sensitive financial and medical data for insurance underwriting carries severe regulatory and reputational risk. Non-compliance can result in fines, legal action, license revocation, and loss of customer trust. Regulatory requirements are table stakes—not optional enhancements.

**Implementation Requirements:**
- Legal/compliance review MUST be completed before any PII/PHI processing capability goes live
- All data storage MUST use AES-256 encryption at rest and TLS 1.3+ in transit
- Audit logs MUST be immutable, tamper-proof, and retained per regulatory requirements
- Data residency MUST comply with regional laws (define regions before deployment)
- AI decision explanations MUST be traceable to source documents (page-level citations)
- Right to deletion and data retention policies MUST be implemented and configurable

**Validation:**
- Compliance audit sign-off required before production deployment
- Quarterly compliance reviews scheduled post-launch
- Automated compliance validation in CI/CD pipeline

---

### Principle 2: Human-in-the-Loop (HITL) is Mandatory for Critical Decisions

**Statement:**  
No automated underwriting decision or high-risk determination SHALL be executed without human validation. AI outputs MUST serve as decision support tools, not autonomous decision-makers.

**Rationale:**  
Insurance underwriting involves complex risk assessment with significant financial and personal impact. Fully automated decisions without human oversight create unacceptable liability, ethical concerns, and regulatory violations. HITL ensures accountability, allows for context-aware judgment, and builds trust in AI systems.

**Implementation Requirements:**
- All AI-generated summaries, entity extractions, and risk assessments MUST be reviewable by underwriters
- System MUST provide confidence scores and explanations for all AI outputs
- Underwriters MUST have ability to accept, modify, or reject AI recommendations
- Correction feedback MUST be captured and used for model improvement
- Final underwriting decisions MUST be explicitly confirmed by licensed underwriters
- Component-level evaluation interface MUST enable quality monitoring

**Validation:**
- HITL validation workflows tested in UAT
- Feedback collection mechanisms verified
- Underwriter training completion confirmed before rollout

---

### Principle 3: Full Auditability & Source Traceability

**Statement:**  
Every data point, AI output, summary, and decision MUST be traceable to its source document with page-level precision. All user actions and system events MUST be logged in immutable audit trails.

**Rationale:**  
Regulatory compliance, dispute resolution, quality assurance, and continuous improvement all depend on complete traceability. Without source citations, AI outputs are unverifiable black boxes. Audit trails are essential for compliance investigations, fraud detection, and accountability.

**Implementation Requirements:**
- All extracted entities MUST include source document ID and page number
- All summary statements MUST cite source documents with page references
- All user actions (view, edit, approve, reject) MUST be timestamped and logged
- All AI model predictions MUST include version, confidence, and input references
- Audit logs MUST be write-only (immutable) with cryptographic integrity protection
- Case history MUST provide complete chronological record of all activities

**Validation:**
- Audit trail completeness tested across all workflows
- Source citation accuracy validated in acceptance testing
- Compliance audit verifies traceability meets regulatory standards

---

### Principle 4: Scalable Architecture with Multi-Language Readiness

**Statement:**  
The POC MUST validate AI capabilities on English documents while designing architecture to support multi-language expansion (Traditional Chinese, Simplified Chinese, code-switching) in production without major re-architecture.

**Rationale:**  
The POC focuses on English-only documents to reduce scope and accelerate validation, but the production system will require multi-language support. Architecture decisions made during POC must accommodate future language expansion to avoid technical debt.

**Implementation Requirements (POC Phase):**
- Azure AI Document Intelligence MUST demonstrate >98% OCR accuracy for English typed text
- Entity extraction MUST use language-agnostic patterns where possible
- Data schemas MUST support language metadata fields for future use
- Azure OpenAI prompts MUST be designed for easy localization
- Document classification architecture MUST support taxonomy expansion
- UI design SHOULD consider internationalization (i18n) best practices

**Implementation Requirements (Production - Deferred):**
- Multi-language OCR with >90% accuracy for handwritten text
- Cross-language entity linking (>85% accuracy)
- Code-switching handling within single documents
- Language-specific UI support

**Validation:**
- POC architecture reviewed for multi-language extensibility
- Language metadata fields included in data contracts
- Azure AI Document Intelligence tested with multi-language samples (optional)

---

### Principle 5: Security by Design & Zero Trust Architecture

**Statement:**  
Security controls MUST be embedded at every layer (data, network, application, identity). No component SHALL assume trust without verification. All sensitive data MUST be encrypted, access-controlled, and monitored.

**Rationale:**  
The platform processes highly sensitive PII, financial data, and medical records—prime targets for cyberattacks and insider threats. Security breaches result in regulatory penalties, legal liability, customer harm, and reputational damage. Security cannot be bolted on; it must be architected from day one.

**Implementation Requirements:**
- All data encrypted at rest (AES-256) and in transit (TLS 1.3+)
- Role-Based Access Control (RBAC) enforced with least privilege principle
- Multi-Factor Authentication (MFA) required for all users
- Secrets managed via secure vault (Azure Key Vault, AWS Secrets Manager, etc.)
- Network segmentation and firewall rules limit lateral movement
- Security monitoring, anomaly detection, and automated alerting active
- Penetration testing and vulnerability scanning conducted before launch
- Incident response plan documented and tested

**Validation:**
- Security audit sign-off before production deployment
- Penetration testing results reviewed and remediated
- Access control policies tested and validated

---

### Principle 6: Performance & Scalability Targets are Commitments

**Statement:**  
The POC MUST demonstrate acceptable processing performance (<5 minutes per document) and establish performance baselines for production. The architecture MUST be designed to scale to 10+ concurrent cases and 1000+ cases per month in production.

**Rationale:**  
POC performance targets validate that AI processing is faster than manual review, proving efficiency gains. While production-grade performance is not required for POC, the architecture must be capable of scaling without major re-work. Performance measurements during POC establish baselines for production SLAs.

**Implementation Requirements (POC Phase):**
- Azure AI Document Intelligence processing MUST complete <1 minute per 10-page document
- Document classification MUST respond within reasonable time (<30 seconds acceptable for POC)
- Full document processing (upload → classification → extraction → summaries) MUST complete <5 minutes
- Performance metrics MUST be captured and documented as baseline
- Azure infrastructure MUST be sized appropriately for POC load (single-user or small team)
- Basic monitoring dashboards MUST track processing times

**Implementation Requirements (Production - Deferred):**
- Full case processing <30 minutes
- 10+ concurrent case handling
- Auto-scaling infrastructure
- Load testing and stress testing
- SLA monitoring and alerting

**Validation:**
- POC performance benchmarks documented
- Azure service performance validated with sample documents
- Architecture reviewed for production scalability

---

### Principle 7: Continuous Model Monitoring & Improvement

**Statement:**  
AI model performance MUST be continuously monitored in production. Model drift, accuracy degradation, or bias MUST trigger alerts and retraining workflows. User corrections MUST feed back into model improvement.

**Rationale:**  
AI models degrade over time as data distributions shift (model drift). Without monitoring, accuracy silently erodes, leading to poor decisions and lost trust. Continuous improvement ensures the system remains valuable and adapts to changing document formats, regulations, and business needs.

**Implementation Requirements:**
- Model performance metrics (accuracy, precision, recall, F1) MUST be tracked per component
- Baseline accuracy benchmarks established and monitored monthly
- HITL corrections captured and stored for retraining
- Automated retraining pipelines triggered when accuracy drops below thresholds
- A/B testing capability for evaluating new models before deployment
- Bias detection and fairness metrics monitored (especially for fraud detection)
- Model versioning and rollback capability maintained

**Validation:**
- Model monitoring dashboards operational at launch
- Retraining pipeline tested and validated
- Baseline accuracy benchmarks documented

---

### Principle 8: Reusable Patterns & Extensibility

**Statement:**  
All architecture, data models, extraction patterns, and workflows MUST be designed for reusability beyond insurance underwriting. The platform MUST be extensible to credit underwriting and other document-intensive processes without major re-architecture.

**Rationale:**  
HSBC's investment in this platform should yield returns across multiple business domains. Siloed, domain-specific implementations create technical debt and limit ROI. Reusable patterns enable faster expansion, consistent quality, and shared learnings across underwriting domains.

**Implementation Requirements:**
- Extraction patterns MUST be configurable via metadata/rules (not hardcoded)
- Document taxonomy MUST support custom document types and attributes
- Data models MUST use extensible schemas (allow new fields without breaking changes)
- APIs MUST be domain-agnostic and versioned
- Architecture documentation MUST explicitly identify reusable components
- Code MUST follow SOLID principles and avoid tight coupling to insurance-specific logic

**Validation:**
- Architecture review confirms extensibility design
- Reusable patterns documented in technical guidelines
- Cross-domain applicability validated in design reviews

---

### Principle 9: Azure-Native Architecture (POC Constraint)

**Statement:**  
The POC MUST use Azure-native services exclusively for all AI, storage, and compute capabilities. Multi-cloud or third-party services are out of scope for POC. This constraint ensures rapid provisioning, HSBC internal compliance, and simplified security review.

**Rationale:**  
Using HSBC's internal Azure subscription accelerates POC execution by leveraging pre-approved services, existing security controls, and enterprise agreements. Evaluating multiple cloud providers during POC adds unnecessary complexity and delays. Azure-native services provide sufficient capabilities to validate the approach.

**Implementation Requirements (POC Phase):**
- **OCR**: Azure AI Document Intelligence (formerly Form Recognizer) MUST be used exclusively
- **LLM**: Azure OpenAI Service MUST be used for extraction and summarization
- **Classification**: Azure OpenAI or Azure ML MUST be used
- **Storage**: Azure Blob Storage MUST be used for documents
- **Database**: Azure SQL Database or Azure Cosmos DB MUST be used for structured data
- **Model Registry**: Azure ML Model Registry MUST be used for model versioning
- **Infrastructure**: Internal HSBC Azure subscription MUST be used
- **Monitoring**: Azure Monitor and Application Insights MUST be used

**Implementation Requirements (Production - Deferred):**
- Multi-cloud strategy MAY be considered post-POC based on cost, performance, and vendor lock-in analysis
- Abstraction layers SHOULD be designed to support potential multi-cloud expansion

**Validation:**
- All services provisioned within HSBC Azure subscription
- Azure AI Document Intelligence access secured
- Azure OpenAI Service quota approved and provisioned
- Azure security baseline compliance validated

---

## Governance Framework

### Roles & Responsibilities

**Executive Sponsor:** TBD  
- Final authority on scope, budget, and strategic direction
- Resolves cross-functional conflicts and resource allocation
- Reviews and approves constitution amendments

**Product Owner:** TBD  
- Defines and prioritizes POC requirements
- Maintains product backlog and roadmap
- Accountable for POC delivery and success metrics
- Secures funding for production phase based on POC results

**Technical Lead / Architect:** TBD  
- Defines technical architecture and standards
- Reviews all design decisions for principle compliance
- Approves technical constitution amendments

**Security Lead:** TBD  
- Ensures security and privacy compliance
- Conducts security reviews and audits
- Veto authority on security-related decisions

**Compliance Officer:** TBD  
- Ensures regulatory compliance throughout lifecycle
- Reviews data handling, audit trails, and AI explainability
- Sign-off required for production deployment

**ML/AI Lead:** TBD  
- Defines AI/ML architecture and model selection
- Ensures model performance monitoring and improvement
- Accountable for accuracy benchmarks and HITL effectiveness

**Engineering Manager:** TBD  
- Manages development team and execution
- Ensures code quality, testing, and delivery
- Implements technical standards and best practices

**Underwriting SME / Business Lead:** TBD  
- Defines domain requirements and validates workflows
- Represents end users in design and testing
- Conducts user acceptance testing and training

### Decision-Making Authority

**Principle Violations:**  
Any team member MAY raise a principle violation concern. If unresolved, escalate to Technical Lead → Product Owner → Executive Sponsor. Principle violations MUST be resolved before proceeding.

**Architecture Decisions:**  
Technical Lead has final authority on architecture, subject to principle compliance. Architecture Decision Records (ADRs) SHOULD be maintained for major decisions.

**Scope Changes:**  
Product Owner has authority for minor scope adjustments. Major scope changes require Executive Sponsor approval.

**Security & Compliance:**  
Security Lead and Compliance Officer have veto authority on security/compliance matters. Disputes escalated to Executive Sponsor.

**Production Deployment:**  
Requires sign-off from: Technical Lead, Security Lead, Compliance Officer, Product Owner.

### Compliance Review Process

**Pre-POC Review:**  
Basic security review and HSBC development environment compliance MUST be completed before POC start. Use of anonymized/synthetic data preferred to minimize compliance requirements.

**POC Phase Reviews:**  
- **Weekly:** Progress review and blocker resolution (Product Owner, Technical Lead)
- **Bi-weekly:** Technical architecture and model performance review (ML/AI Lead, Technical Lead)
- **End-of-POC:** Comprehensive evaluation against success criteria, stakeholder demo, production funding decision

**Production Planning (Post-POC):**  
- Full security audit, compliance validation, and legal review required before production
- Monthly model performance metrics review
- Quarterly compliance and security review
- Annual constitution review

**Incident Response:**  
Security or compliance incidents trigger immediate review. Root cause analysis and corrective action plan MUST be completed within 48 hours. Constitution amendments MAY be required based on findings.

---

## Amendment Procedures

### When Amendments Are Required

The constitution MUST be amended when:
- New regulatory requirements are introduced
- Principle violations are identified and require clarification
- Major scope changes impact core principles
- Lessons learned from production operation necessitate new principles
- Technology changes fundamentally alter architecture assumptions

The constitution SHOULD be amended when:
- Roles and responsibilities change
- Governance processes are optimized based on experience
- Additional principles are identified to improve project outcomes

### Amendment Process

1. **Proposal:** Any stakeholder MAY propose an amendment via formal written proposal including rationale, impact analysis, and affected sections.

2. **Review:** Technical Lead and Product Owner review for technical and business impact. Security Lead and Compliance Officer review for risk implications.

3. **Approval:** Amendments require unanimous approval from: Executive Sponsor, Product Owner, Technical Lead, Security Lead, Compliance Officer.

4. **Documentation:** Approved amendments MUST update version number per semantic versioning:
   - **MAJOR:** Backward-incompatible principle changes or removal
   - **MINOR:** New principle added or material expansion
   - **PATCH:** Clarifications, wording improvements, non-semantic changes

5. **Communication:** Amendments MUST be communicated to all team members with effective date. Training MAY be required for material changes.

6. **Template Updates:** All dependent templates (plan, spec, tasks, commands) MUST be reviewed and updated within 2 weeks of amendment ratification.

### Version History

| Version | Date | Type | Summary | Approved By |
|---------|------|------|---------|-------------|
| 1.0.0 | 2025-12-11 | MAJOR | Initial constitution establishment | Pending stakeholder approval |
| 1.1.0 | 2025-12-11 | MINOR | Updated for POC scope: 2 English forms, Azure-only architecture, POC-specific success criteria and performance targets | Pending stakeholder approval |

---

## Glossary

**HNW:** High Net Worth - referring to affluent insurance customers  
**POC:** Proof of Concept - limited pilot to validate approach before full production investment  
**HITL:** Human-in-the-Loop - workflow where humans validate AI outputs  
**OCR:** Optical Character Recognition - extracting text from images  
**PII:** Personally Identifiable Information  
**PHI:** Protected Health Information (medical data under HIPAA)  
**RBAC:** Role-Based Access Control  
**MFA:** Multi-Factor Authentication  
**ADR:** Architecture Decision Record  
**Azure AI Document Intelligence:** Azure service for OCR and document layout analysis (formerly Form Recognizer)  
**Azure OpenAI Service:** Azure-hosted OpenAI models (GPT-4, etc.) for LLM capabilities  
**P0/P1/P2:** Priority levels (P0 = highest, critical; P1 = high; P2 = medium/low)  
**UAT:** User Acceptance Testing  
**Model Drift:** Degradation of AI model accuracy over time due to data distribution changes  
**Code-Switching:** Using multiple languages within the same document (deferred to production)  
**Entity Linking:** Connecting related entities (e.g., person names) across documents  
**Source Traceability:** Ability to trace data/decisions back to original source documents with page numbers  
**Extractive Summary:** Summary created by selecting key sentences from source  
**Abstractive Summary:** Summary created by generating new text that captures meaning  
**Confusion Matrix:** Table showing classification accuracy (true/false positives/negatives)

---

## References

- [HNW Insurance Underwriting POC PRD](../docs/prds/hnw-underwriting-poc.md)
- [Business Requirements Document](../docs/01-requirement-specification/PRD-Phase1.0.md)
- [POC Scope Presentation](../docs/marp.md)
- [GitHub Repository](https://github.com/commercial-software-engineering/HSBC_IWPB_UW)

---

**Document Owner:** Product Owner (TBD)  
**Last Reviewed:** 2025-12-11  
**Next Review Due:** End of POC Phase (Week 12)

---

*This constitution is a living document. All team members are responsible for upholding these principles and raising concerns when they are violated.*
