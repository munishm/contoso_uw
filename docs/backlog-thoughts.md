---
marp: true
title: Underwriting Automation Pilot Plan
theme: default
paginate: true
---

## Document boundry

* How to detect multiple files belong to same document?
* Detect duplicate files or near duplicate documents?
-   What if both are ingested and conflict downstream?
-Distinction: Document vs data
---

## OCR 

* What if OCR confidence is high with in correct value? e.g. 10,00,000 mapping to 100,000 or o mapping to 0

* Table extraction issues, 
-   column repeat for better OCR
-   Partial tables
-   fall back?
-   Orientation Issues

---

## Classification

* One file with multiple documemts
- Jumbled pages
- Incomplete document
- Misleading titles
    - Proposal mislabelled as Quotation
- What to rely on? Tile, content pattern, file metadata, score?

---

## Extraction

* Field present but sematically different meaning
    - e.g. 
* Schema flat or need context awareness
* ambiguity issues
* Same field appears multiple times
    - Dettecting winner
* field detected but present only in annexure
* Document quality issue?

---

## Open ended extraction

* hallucination
* rewording issue and loosing important information
* Over generalization


---

## Summarization

* In case of renewals, Nothing changed is still important as renewal requires the old information access.
