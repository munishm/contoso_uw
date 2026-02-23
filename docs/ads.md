## Key Differentiators

1. Pydantic vs db schemas
2. Schema versioning with rollback in database
3. Hot-reload schema changes vs deployment requirement for changes
4. Citations in the document
5. Hardcoded model selection vs Model registry with version control
6. Custom prompts configurable per document type

## Key Questions to Ask

### Schema Management

* How long does it take today to add a new field to an existing document type?
* What is the current deployment cycle when a Pydantic model changes?
* If a schema change causes extraction issues, how quickly can you rollback?

### Model Management

* When Azure releases a new GPT version, how do you test it against your current model before switching?
* Can you run two models side-by-side and compare extraction quality?
* How do you track which model version produced a specific extraction result?

### Quality & Measurement

* How do you know your extraction accuracy today?
* How do you measure improvement over time?
* Do you have ground truth datasets to benchmark against?

### Compliance & Traceability

* When regulators ask "where did this value come from?", how do you answer today?
* Can you reproduce the exact conditions (prompt + model + schema) that caused a specific extraction?
* How do you audit AI decisions for compliance purposes?

### Storage & Querying

* How do you query historical extractions today with Azure Tables?
* Can you find all documents where a specific field failed confidence threshold?
* Do you need complex aggregations or analytics on extraction results?

### Operational Efficiency

* How long does it take to onboard a completely new document type end-to-end?
* What percentage of extractions require manual review today?
* How do you prioritize which extractions need human attention?


##Architecture
service queue:
No order gurantee in storage queue
No built-in handling of the dead letter






how do you test your code? 



