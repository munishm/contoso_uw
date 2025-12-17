---
description: "Detailed customer discovery questions for platform design discussion"
---

# Customer Discovery Questions - HNW Underwriting Platform

**Purpose:** Deep-dive questions for customer discussion to refine platform design post-POC  
**Date:** 2025-12-12  
**Status:** Draft - Ready for customer meeting

---

## Executive Summary

This document contains detailed discovery questions organized across 5 critical areas to help design a production-ready platform based on POC learnings. The questions are designed for customers who have completed a POC and come with informed opinions about the solution.

**Focus Areas:**
1. **POC Validation & Learnings** (14 question groups)
2. **Cost & ROI Considerations** (6 question groups)
3. **Parallel Processing & Concurrency** (6 question groups)
4. **Quality, Auditing & Compliance** (10 question groups)
5. **Gaps & Underspecified Areas** (10 question groups)

---

## 1. POC Validation & Learnings (Deep Dive)

### Technical Performance

#### 1.1 OCR Quality
- What was your measured OCR character accuracy for English vs. Simplified Chinese sections?
- Were there specific sections where OCR consistently failed (handwriting, stamps, signatures, checkboxes)?
- How did OCR perform on tables vs. free-form text vs. checkboxes?
- Did the Layout API correctly identify table structures, or were there row/column misalignments?
- Were there any pages that required manual intervention or re-processing?

#### 1.2 Field Extraction Accuracy
For each of the 7 fields, what was the extraction completeness rate?
- **Family Name:** ___%
- **Given Name:** ___%
- **Address:** ___%
- **Date of Birth:** ___%
- **Place of Birth:** ___%
- **Health Details:** ___%
- **Financial Information:** ___%

**Follow-up questions:**
- Which field had the highest error rate and why (format variations, location inconsistency, ambiguous labeling)?
- Were there cases where fields were present but not detected? Vice versa (false positives)?
- How often did the bilingual nature cause confusion (e.g., extracting Chinese characters when English was expected)?

#### 1.3 Summarization Quality
- How did underwriters rate the summary quality (if you had a rating system)?
- Were citations accurate and helpful, or did they point to wrong pages/sections?
- Did summaries capture all critical information (health risks, financial red flags)?
- Were summaries too verbose, too terse, or about right?
- Did any summaries hallucinate information not present in the source document?
- How did bilingual summarization work—did it maintain both languages or translate?

#### 1.4 Processing Speed
What was the average processing time per 30-page document (end-to-end)?
- **OCR phase:** ___ minutes
- **Extraction phase:** ___ seconds
- **Summarization phase:** ___ seconds
- **Total:** ___ minutes

**Follow-up questions:**
- Did processing times vary significantly between documents? If yes, what caused variability?
- Were there timeout issues with Azure OpenAI (given 120 TPM quota)?

#### 1.5 User Experience & Workflow
- What did underwriters like most about the POC interface?
- What frustrated them most?
- Did the side-by-side view (document + extracted data) work well?
- How often did underwriters need to click citations to verify information?
- Were there missing features that users immediately requested?

### Failure Modes & Edge Cases

#### 1.6 Processing Failures
- What percentage of documents failed processing completely?
- What were the top 3 reasons for processing failures?
- Were there any document characteristics that always caused issues (specific layouts, poor scan quality, annotations)?
- How did the system handle pages with stamps, signatures, or redactions overlaying text?
- Were there documents with unexpected languages or mixed scripts that caused problems?

#### 1.7 Model Behavior
- Did you notice any patterns in low-confidence extractions (certain pages, certain fields)?
- How often did you need to adjust prompts to improve extraction/summarization quality?
- Did GPT-4o's output format remain consistent, or did it occasionally deviate from the requested JSON structure?
- Were there examples where the model "understood" context better than expected (e.g., inferring missing information)?

---

## 2. Cost & ROI Considerations (Deep Dive)

### POC Cost Breakdown

#### 2.1 Azure Service Costs (Measured)
What was your total Azure AI Document Intelligence (Layout API) cost for processing ~X documents?
- **Per document cost:** $___ 
- **Total OCR cost:** $___

What was your Azure OpenAI (GPT-4o) cost breakdown?
- **Extraction cost per document:** $___
- **Summarization cost per document:** $___
- **Total LLM cost:** $___

- **Storage costs (Blob + Cosmos DB):** $___
- **Total POC infrastructure cost:** $___

#### 2.2 Token Usage Patterns
- Average tokens consumed per document for extraction: ___
- Average tokens consumed per document for summarization: ___
- Did you hit the 120 TPM quota limit? If yes, how often and what was the impact?
- What's your estimated token cost per document at scale (100 docs/month, 1000 docs/month)?

#### 2.3 Time Savings Analysis
How long does a human underwriter take to manually process one 30-page application?
- **Reading + extracting key fields:** ___ minutes
- **Creating summary memo:** ___ minutes
- **Total manual effort:** ___ minutes/hours per document

How long did the POC system take (including review/correction time)?
- **AI processing:** ___ minutes
- **Human review/correction:** ___ minutes
- **Net time savings:** ___ minutes (___%)

What's the value of that time savings (underwriter hourly rate × time saved)?

#### 2.4 Accuracy vs. Manual Cost Trade-off
- At what accuracy threshold does AI become cost-effective vs. manual processing?
- If extraction is 90% accurate, how long does it take to correct the remaining 10%?
- Is "AI-assisted" mode (human validates everything) acceptable, or must it be "AI-autonomous"?

#### 2.5 Production Scale Projections
- **Current monthly volume:** ~100 documents
- **Projected volume after full rollout (40-50 document types):** ___ documents/month
- **Estimated monthly infrastructure cost at production scale:** $___
- **Estimated annual FTE savings (hours saved ÷ 2080 hours/year):** ___ FTEs
- **ROI timeline:** When would cost savings offset development investment?

#### 2.6 Cost Optimization Opportunities
- Could you use GPT-4o-mini for simpler extraction tasks to reduce costs?
- Could you use Azure AI Document Intelligence Prebuilt models instead of Layout API for some documents?
- Would batch processing (vs. real-time) reduce costs?
- Could you cache common extractions to avoid re-processing similar documents?

---

## 3. Parallel Processing & Concurrency (Deep Dive)

### Current POC Behavior

#### 3.1 Concurrency Implementation
Did you implement concurrent processing in the POC? If yes:
- How many documents could process simultaneously?
- Did you use async/await, thread pools, or task queues?
- Were there race conditions or resource contention issues?

If no, why not (simplicity, quota limits, other constraints)?

#### 3.2 Azure Service Limits
Given 120 TPM for GPT-4o:
- How many documents can realistically process concurrently without throttling?
- Did you encounter 429 (rate limit) errors? How often?
- What was your retry strategy when throttled?

Azure AI Document Intelligence limits:
- What's your concurrent OCR limit (transactions per second)?
- Did you hit this limit during testing?

#### 3.3 Production Requirements
- What's your expected peak concurrency (e.g., Monday morning rush, month-end batch)?
- Should the system support batch uploads (e.g., 50 documents at once)?
- What's acceptable queuing delay (e.g., if 50 docs submitted, last one starts processing after ___ minutes)?
- Do you need prioritization (urgent applications jump the queue)?

### Task Queue Design

#### 3.4 Queue Implementation
- Should you use Azure Queue Storage, Azure Service Bus, or another solution?
- What's the desired queue behavior:
  - FIFO (first-in-first-out)?
  - Priority-based?
  - Fair-share (distribute across users)?
- How should the system handle queue failures (e.g., worker crashes mid-processing)?
- Should users see their queue position and estimated wait time?

#### 3.5 Worker Scaling
- How many worker instances should run concurrently (consider quota limits)?
- Should workers auto-scale based on queue depth?
- What's the cost trade-off between faster processing (more workers) vs. lower cost (fewer workers)?

#### 3.6 Failure & Retry in Concurrent Context
- If one document in a batch fails, should processing continue for others?
- Should failed documents automatically retry, or require manual intervention?
- How should the system notify users of failures in a batch (individual emails, batch summary)?

---

## 4. Quality, Auditing & Compliance (Deep Dive)

### Quality Assurance

#### 4.1 Confidence Thresholds
What confidence score should trigger automatic approval vs. manual review?
- Per field (e.g., if Date of Birth confidence <90%, flag for review)?
- Document-level (e.g., if any field <80%, entire document needs review)?

**Follow-up questions:**
- How should the UI surface low-confidence extractions (visual highlighting, warnings)?
- Can underwriters override AI extractions inline, or must they use a separate correction flow?

#### 4.2 Ground Truth & Validation
- Do you have a "gold standard" dataset of manually validated documents for ongoing evaluation?
- How often should you re-evaluate accuracy as new documents are processed?
- Who is responsible for creating/maintaining ground truth data (underwriters, data scientists)?

#### 4.3 Human-in-the-Loop (HITL)
What's the desired HITL workflow:
- AI processes → human reviews all outputs (assisted mode)?
- AI processes → human reviews only low-confidence outputs (hybrid mode)?
- AI processes → human spot-checks random sample (autonomous mode)?

**Follow-up questions:**
- What percentage of documents should be sampled for quality audits?
- How should corrections feed back into model improvement (active learning)?

#### 4.4 Error Categorization
When errors occur, how should they be categorized for analysis:
- OCR errors (misread text)?
- Extraction errors (correct text, wrong field assignment)?
- Validation errors (extracted value violates business rules)?
- Summarization errors (incorrect/missing information)?

Who reviews error patterns and decides on corrective actions?

### Audit Trail & Compliance

#### 4.5 Audit Requirements
What must be logged for regulatory compliance:
- Who uploaded the document?
- When was it processed?
- Which model versions were used (OCR, extraction, summarization)?
- What were the original extracted values before human corrections?
- Who made corrections and when?
- What was the final approved output?

**Follow-up questions:**
- How long must audit logs be retained (months/years)?
- Must audit logs be immutable (tamper-proof)?

#### 4.6 Data Lineage
- Can you trace every extracted value back to the exact source location (page, line, bounding box)?
- Can you reproduce historical extractions (re-run old model versions on old documents)?
- How do you handle schema migrations (e.g., adding new fields, renaming fields)?

#### 4.7 Model Versioning & Rollback
- If a model update degrades accuracy, can you instantly rollback to the previous version?
- How do you A/B test model changes (route 10% of traffic to new model, compare results)?
- Should users be notified when model versions change?

#### 4.8 Data Privacy & Security
- Are there PII (Personally Identifiable Information) redaction requirements?
- Should certain fields (e.g., medical conditions, financial data) have restricted access?
- Do you need role-based access control (RBAC) for different user types?
- Are there data residency requirements (must data stay in specific Azure region)?
- How long should documents be retained before automatic deletion?

### Explainability & Transparency

#### 4.9 Model Explainability
- Do underwriters need to understand *why* the AI extracted a particular value?
- Should the system show alternative interpretations (e.g., "This could be Date of Birth OR Policy Start Date")?
- How much detail is useful vs. overwhelming (e.g., attention weights, token probabilities)?

#### 4.10 Bias & Fairness
- Are there concerns about bias in OCR/extraction (e.g., lower accuracy for certain names, addresses, languages)?
- Should you monitor accuracy across demographic groups (if detectable from documents)?
- How should you handle "unfair" failures (e.g., system consistently struggles with Chinese names)?

---

## 5. Gaps & Underspecified Areas (Detailed)

### Field-Level Specifications

#### 5.1 Family Name & Given Name
- **Format:** Single line vs. multi-word (e.g., "Van Der Berg")?
- **Validation:** Allow special characters (hyphens, apostrophes, Chinese characters)?
- **Max length:** ___ characters?
- **Required:** Always, or optional if applicant is a trust/entity?

#### 5.2 Address
- **Format:** Free-form text, structured (street/city/zip), or geocoded?
- **Validation:** Must match known addresses, or free-form acceptable?
- **International addresses:** How to handle non-standard formats (Hong Kong, Mainland China)?
- **P.O. Boxes:** Allowed or prohibited?

#### 5.3 Date of Birth
- **Format:** MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD, or flexible?
- **Validation:** Must be adult (age >18), or allow minors?
- **Ambiguous dates:** How to resolve "05/06/1990" (May 6 vs. June 5)?
- **Partial dates:** Accept "1990" alone, or require full date?

#### 5.4 Place of Birth
- **Granularity:** Country only, city/state/country, or hospital name?
- **Format:** Standardized (ISO country codes), or free-form text?
- **Historical names:** Accept "USSR" or convert to current country?

#### 5.5 Health Details
- **Extraction scope:** Full text extraction, specific conditions only (diabetes, cancer, heart disease), or summary?
- **Structured vs. unstructured:** Extract as free-form text or map to ICD-10 codes?
- **Sensitivity:** Are there conditions that should be flagged for special review?
- **Negations:** How to handle "No history of diabetes" (don't extract "diabetes")?

#### 5.6 Financial Information (Marked as Required)
Specific fields to extract within this section:
- **Annual income:** $___
- **Net worth:** $___
- **Liquid assets:** $___
- **Existing insurance coverage:** $___
- **Requested policy amount:** $___
- **Source of funds:** (employment, inheritance, business, investments)?

**Validation questions:**
- **Currency:** USD assumed, or mixed currencies (HKD, CNY)?
- **Validation:** Income must match net worth (e.g., income >10% of net worth)?
- **Ranges:** Accept ranges ("$500K-$1M"), or require exact values?

### ISO Standards Clarification

#### 5.7 Date Formats (ISO 8601)
- Do you want strict ISO 8601 (YYYY-MM-DD), or accept common variants?
- **Time zones:** Relevant (documents timestamped with time zones), or dates only?
- **Durations:** Relevant (e.g., policy term "P5Y" for 5 years)?

#### 5.8 Currency Formats (ISO 4217)
- **Currency codes:** Use ISO codes (USD, HKD, CNY) or symbols ($, HK$, ¥)?
- **Precision:** Store cents ($1,234.56) or round to dollars ($1,235)?
- **Localization:** Display format 1,234.56 (US) vs. 1.234,56 (EU)?

### Validation Rules (Marked "I don't know")

#### 5.9 Validation Rule Priorities
- Should I propose validation rules based on domain best practices, or defer until you gather requirements?
- Are there existing underwriting guidelines that define acceptable ranges (e.g., max policy amount $50M, min age 18)?
- Which fields have cross-field dependencies (e.g., if health condition = "terminal illness", requested policy amount must <$X)?

#### 5.10 Validation Enforcement
- Should validation errors block document acceptance (hard validation)?
- Or should they generate warnings but allow processing (soft validation)?
- Who resolves validation conflicts (automated overrides, underwriter decision, escalation to manager)?

---

## Key Clarifications Needed Before Implementation

Based on the POC experience and current documentation, these critical gaps must be addressed:

### 1. Validation Rules (Priority: HIGH)
**Status:** Marked "I don't know" in requirements  
**Options:**
- **Option A:** Draft proposed validation rules based on insurance industry standards for review
- **Option B:** Schedule session with underwriting SMEs to define business-specific rules
- **Option C:** Start with minimal validation, add rules iteratively based on production data

**Recommendation:** Schedule 2-hour workshop with underwriting SMEs to define field-level validation rules, then implement in phases (critical rules first).

---

### 2. Financial Information Granularity (Priority: HIGH)
**Status:** Marked "required" but no sub-fields specified  
**Proposed Sub-fields:**
1. Annual income (validated range: $50K - $50M)
2. Net worth (validated range: $100K - $500M)
3. Liquid assets (validated: ≤ net worth)
4. Existing insurance coverage (validated: ≥ $0)
5. Requested policy amount (validated: ≤ 50× annual income)
6. Source of funds (validated: enum: employment | inheritance | business | investments | other)

**Question:** Should all 6 sub-fields be extracted, or subset sufficient?

---

### 3. Parallel Processing Strategy (Priority: MEDIUM)
**Status:** Spec mentions "up to 10 simultaneous" but unclear if achievable with 120 TPM quota  
**Analysis:**
- 30-page document → ~8,000 tokens (OCR text)
- Extraction prompt + response: ~3,000 tokens
- Summarization prompt + response: ~4,000 tokens
- **Total per document:** ~15,000 tokens
- **Processing time:** ~2 minutes (at 120 TPM)
- **Max concurrency without throttling:** ~2-3 documents

**Options:**
- **Option A:** Sequential processing (safest, simplest)
- **Option B:** Limited concurrency (2-3 workers) with exponential backoff retry
- **Option C:** Request TPM quota increase to 600+ (support 10 concurrent)

**Recommendation:** Start with Option B (2-3 concurrent workers), monitor throttling, request quota increase if needed.

---

### 4. Cost Model & ROI Targets (Priority: HIGH)
**Status:** No cost constraints specified  
**Questions:**
- What's the maximum acceptable per-document processing cost (e.g., must be <$5 per document)?
- What's the ROI hurdle rate (must save X hours or $Y per document)?
- What's the budget for production infrastructure (monthly Azure spend limit)?

**Action:** Define cost ceiling before scaling to production (40-50 document types).

---

## Discussion Flow Recommendation

### Pre-Meeting Preparation
1. Share this document with customer 48 hours before meeting
2. Ask customer to pre-populate quantitative answers (extraction accuracy %, processing times, costs)
3. Request POC metrics dashboard/logs be available during meeting

### Meeting Agenda (2-3 hours)

**Part 1: POC Retrospective (45 min)**
- Review measured metrics (Section 1.1-1.5)
- Discuss failure modes and edge cases (Section 1.6-1.7)
- Capture "what worked well" vs. "what needs improvement"

**Part 2: Production Requirements (60 min)**
- Scale and concurrency needs (Section 3)
- Cost model and ROI expectations (Section 2)
- Quality thresholds and HITL workflow (Section 4.1-4.4)

**Part 3: Technical Gaps (45 min)**
- Field-level specifications (Section 5.1-5.6)
- Validation rules and enforcement (Section 5.9-5.10)
- Compliance and audit requirements (Section 4.5-4.8)

**Part 4: Action Items & Next Steps (15 min)**
- Assign owners for each open question
- Set deadlines for answers (target: 1 week)
- Schedule follow-up for detailed design review

---

## Appendix: Reference Documents

| Document | Purpose | Location |
|----------|---------|----------|
| PRD v1.0 | Product requirements | `docs/prds/hnw-underwriting-poc.md` |
| Feature Spec v1.0 | Technical specification | `docs/specs/feature-spec-poc.md` |
| Underspecified Areas | Known gaps analysis | `docs/specs/underspecified-areas.md` |
| Sample Document | HNW CMB APP 2 form | `docs/sample_docs/HNW CMB APP 2.pdf` |

---

**Document Status:** Ready for customer meeting  
**Next Review:** After customer discussion (target: 2025-12-19)  
**Owner:** TBD  
**Last Updated:** 2025-12-12
