# ClaimSync Solution — Full Component Extraction Inventory

**Generated:** 2026-06-25  
**Scope:** READ-ONLY extraction of all agent configs, RPA workflows, BPMN orchestration, and dependency maps  
**Status:** COMPLETE

---

## Table of Contents
1. [Agent Inventory](#1-agent-inventory)
2. [RPA Workflow Inventory](#2-rpa-workflow-inventory)
3. [BPMN Orchestration Map](#3-bpmn-orchestration-map)
4. [Stage-to-Component Mapping](#4-stage-to-component-mapping)
5. [Gateway Dependency Map](#5-gateway-dependency-map)
6. [Knowledge Base Dependency Map](#6-knowledge-base-dependency-map)
7. [Data Flow / Variable Contract](#7-data-flow--variable-contract)
8. [Final Assessment](#8-final-assessment)

---

## 1. Agent Inventory

### AG_Claim_Analysis_Core
| Attribute | Value |
|-----------|-------|
| **Model** | gpt-4o-2024-11-20 |
| **Purpose** | Primary claim analysis — categorization, eligibility, document completeness |
| **Input Schema** | claim_id (string), document_text_bundle (string), extracted_data (string), claim_category_hint (string, optional) |
| **Output Schema** (10 fields) | category, category_confidence, eligible, eligibility_reason, documents_complete, missing_documents (list), request_message, claim_summary, key_document_facts, analysis_confidence |
| **Logic Pattern** | KB-first grounding → dual-signal confidence (category + eligibility) → deduction-from-1.0 scoring |
| **KB Files** | 00_ClaimSync_Master_KB.docx, 02_Claim_Categories_KB.docx, 03_Document_Requirements_KB.docx |
| **Process Key** | Solution.agent.AG_Claim_Analysis_Core |

### AG_Fraud_Risk
| Attribute | Value |
|-----------|-------|
| **Model** | gpt-5.4 |
| **Purpose** | Fraud risk assessment with signal-based corroboration |
| **Input Schema** | claim_id, document_text_bundle, extracted_data, analysis_result, validation_result |
| **Output Schema** (nested object) | fraudRisk: { level, score, score_confidence, signals (list), corroborating_signals (list), reasoning, recommended_action } |
| **Logic Pattern** | 7 built-in signals + BV corroboration → weighted scoring → level mapping |
| **KB Files** | 00_ClaimSync_Master_KB.docx, 01_Fraud_Detection_KB.docx, 04_Historical_Cases_KB.docx |
| **Process Key** | Fraud_Risk_Agent.agent.Agent |

### AG_Decision_Support
| Attribute | Value |
|-----------|-------|
| **Model** | gpt-4o-2024-11-20 |
| **Purpose** | Priority-ranked decision recommendation |
| **Input Schema** | claim_id, analysis_result, fraud_result, validation_result, extracted_data |
| **Output Schema** (6 fields) | decision, decision_confidence, reasoning, recommended_action, missing_documents (list), request_message |
| **Logic Pattern** | First-match priority: P1 Request Docs → P2 Reject Ineligible → P3 Reject High Fraud → P4 Partial Medium → P5 Partial Low Conf → P6 Approve |
| **KB Files** | 00_ClaimSync_Master_KB.docx, 01_Fraud_Detection_KB.docx, 02_Claim_Categories_KB.docx, 05_Decision_Guidelines_KB.docx |

### AG_Final_Summary
| Attribute | Value |
|-----------|-------|
| **Model** | gpt-5.4 |
| **Purpose** | Audit-trail generation and summary alignment |
| **Input Schema** | claim_id, analysis_result, fraud_result, validation_result, decision_support, reviewer_decision |
| **Output Schema** (3 fields) | summary_report, audit_trail (8 steps), processing_metadata |
| **Logic Pattern** | 8-step audit trail + alignment/override detection |
| **KB Files** | 00_ClaimSync_Master_KB.docx, 06_Summary_Templates_KB.docx |

### AG_PDF_Extraction
| Attribute | Value |
|-----------|-------|
| **Model** | gpt-5.4 |
| **Purpose** | PDF text extraction fallback (invoked by WF_Read_And_Extract_Document_Text) |
| **Input Schema** | claim_id, pdf_file_name, pdf_file_path_or_reference, claim_folder_context, extraction_request_notes |
| **Output Schema** (6 fields) | pdf_text, pdf_status, pdf_notes, extracted_amount, extracted_date, extracted_identifier |
| **Invocation** | Called via `uasj:RunJob` from WF_Read_And_Extract_Document_Text |

---

## 2. RPA Workflow Inventory

### WF_Monitor_Claim_Intake
| Attribute | Value |
|-----------|-------|
| **Purpose** | Discover claim folders from a root directory |
| **Inputs** | in_rootFolderPath (String) |
| **Outputs** | out_claimFolderPath (String), out_claimId (String) |
| **Internal Variables** | claimFolders (Object), firstFolder (String) |
| **Logic** | 1) GetDirectories on root → 2) If empty, log warn → 3) Else take first folder → 4) out_claimFolderPath = firstFolder, out_claimId = Path.GetFileName(firstFolder) |
| **Error Handling** | TryCatch around entire logic; exception logged as Error |
| **BPMN Stage** | Stage 1 — Intake |

### WF_Initialize_Claim_Record
| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate deterministic claim ID from folder path |
| **Inputs** | in_claim_folder_path (String) |
| **Outputs** | out_claim_id (String) |
| **Internal Variables** | timestamp_part, random_part, safe_folder_name |
| **Logic** | 1) If path empty → INVALID_CLAIM_ + timestamp → 2) Else CLM- + timestamp + safe_folder_name + 4-char GUID suffix → 3) Final safety fallback |
| **BPMN Stage** | Stage 2 — Initialization |

### WF_Read_And_Extract_Document_Text
| Attribute | Value |
|-----------|-------|
| **Purpose** | Read all files in claim folder, extract text, bundle output, deterministic parsing |
| **Inputs** | in_claimFolderPath (String), in_claimId (String), in_expectedFileTypes (String, default="pdf,txt,docx,jpg,jpeg,png") |
| **Outputs** | out_documentTextBundle (String), out_documentNames (String), out_extractedData (String), out_extractionSuccess (Boolean), out_extractionNotes (String) |
| **Internal Variables** | filesList, currentFileName, currentExtension, currentExtractedText, allTextParts, allDocNames, notesLog, parsedAmount, parsedDate, parsedIdentifier, rxAmount, rxDate, rxId, supportedExtensions, joinedNotes, pdfText, pdfStatus, pdfNotes, earlyExit, textOk |
| **Logic** | STEP 1: Init outputs → STEP 2: Guard empty path → STEP 3: Resolve supported extensions → STEP 4: Enumerate files (filtered by extension) → STEP 5: Guard no files → STEP 6: ForEach file: extract by type (TXT=ReadAllText, PDF=invoke AG_PDF_Extraction, JPG/JPEG/PNG=log OCR unavailable, DOCX=ReadAllText with catch, unsupported=skip) → Quality gate (>20 chars) → Regex parse amount/date/identifier → STEP 7: Build bundle, names, extracted_data, notes → STEP 8: Set success |
| **Regex Patterns** | Amount: `\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b` — Date: `\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{4}\b` — Identifier: `\b[A-Z]{2,5}-\d{4,10}\b` |
| **Error Handling** | Per-file TryCatch; earlyExit flag prevents processing if preconditions fail; never fails whole workflow on single file error |
| **BPMN Stage** | Stage 3 — Document Extraction |

### WF_Load_Agent_Knowledge
| Attribute | Value |
|-----------|-------|
| **Purpose** | Load knowledge base files per agent, bundle with size cap |
| **Inputs** | in_agent_name (String), in_kb_base_path (String, optional) |
| **Outputs** | out_knowledge_bundle (String), out_knowledge_load_status (String), out_knowledge_quality_hint (String) |
| **Internal Variables** | resolved_kb_path, kb_files, file_texts, single_content, raw_bundle, MAX_KB_CHARS=80000 |
| **Logic** | 1) Resolve KB path (input → env var CLAIMSYNC_KB_PATH → Desktop default) → 2) Switch on agent_name to select KB file list → 3) ForEach KB file: invoke WF_Load_Knowledge_File → 4) Join with `---` separator → 5) Apply 80K char cap → 6) Determine status (failed/partial/success) |
| **Agent KB Mappings** | AG_Claim_Analysis_Core → [00,02,03] — AG_Fraud_Risk → [00,01,04] — AG_Decision_Support → [00,01,02,05] — AG_Final_Summary → [00,06] — Default → [00] + warn |
| **BPMN Stage** | Stage 4 — Knowledge Loading (parallel with Stage 3) |

### WF_Load_Knowledge_File
| Attribute | Value |
|-----------|-------|
| **Purpose** | Simple file reader utility invoked by WF_Load_Agent_Knowledge |
| **Inputs** | in_filePath (String) |
| **Outputs** | out_fileContent (String) |
| **Logic** | 1) Guard empty path → 2) Check File.Exists → 3) ReadAllText → 4) Trim |
| **Error Handling** | Returns `[ERROR: ...]` strings for missing/empty path |
| **Invocation** | Called via `InvokeWorkflowFile` from WF_Load_Agent_Knowledge |

### WF_Run_Business_Validations
| Attribute | Value |
|-----------|-------|
| **Purpose** | Deterministic validation of claim data quality |
| **Inputs** | in_claimId (String), in_documentTextBundle (String), in_documentNames (String) |
| **Outputs** | out_validationResults (String), out_validationPassed (Boolean) |
| **Internal Variables** | textLength, docCount |
| **Logic** | 1) Validate ClaimID → 2) Validate text bundle (present + >50 chars) → 3) Validate document names (present + count >0) → 4) Serialize results as `Key=Value;...` → 5) Determine pass/fail based on Missing/TooShort/NoDocuments markers |
| **BPMN Stage** | Stage 5 — Business Validations |

### WF_Prepare_Reviewer_Package
| Attribute | Value |
|-----------|-------|
| **Purpose** | Aggregate all intermediate results into reviewer-facing package |
| **Inputs** | in_claimId, in_validationResults, in_validationPassed, in_analysisResult, in_fraudResult, in_decisionSupport |
| **Outputs** | out_reviewerPackage (String) |
| **Internal Variables** | packageParts |
| **Logic** | 1) Add ClaimID → 2) Add Validation → 3) Add ValidationPassed → 4) Add Analysis → 5) Add FraudRisk → 6) Add Recommendation → 7) Join with newlines |
| **BPMN Stage** | Stage 13 — Reviewer Package (before HITL) |

### WF_Send_Missing_Document_Request
| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate missing document request message |
| **Inputs** | in_claimId (String), in_missingDocuments (List<String>) |
| **Outputs** | out_requestMessage (String) |
| **Internal Variables** | status |
| **Logic** | 1) Build message: "Missing documents for claim <id>: <list>" → 2) Set internal status = pending_documents |
| **BPMN Stage** | Stage 9 — Missing Document Request |

### WF_Update_Claim_Record
| Attribute | Value |
|-----------|-------|
| **Purpose** | Aggregate ALL stage outputs into final claim record |
| **Inputs** | in_claimId, in_validationResults, in_analysisResult, in_fraudResult, in_decisionSupport, in_reviewerDecision, in_finalSummary |
| **Outputs** | out_claimRecord (String) |
| **Internal Variables** | recordParts |
| **Logic** | 1) Add ClaimID → 2) Add Validation → 3) Add Analysis → 4) Add FraudRisk → 5) Add Recommendation → 6) Add ReviewerDecision → 7) Add FinalSummary → 8) Join with newlines |
| **BPMN Stage** | Stage 16 — Update Record |

### WF_Archive_Claim
| Attribute | Value |
|-----------|-------|
| **Purpose** | Move claim folder to Archive directory |
| **Inputs** | in_claimFolderPath (String) |
| **Outputs** | (none — side effect only) |
| **Internal Variables** | archiveRoot, folderName, archivePath, v_dummy |
| **Logic** | 1) Set archiveRoot = "Archive" → 2) Extract folderName → 3) Compute archivePath = Archive/<folderName> → 4) Create Archive dir if missing → 5) Directory.Move → 6) Log success |
| **Error Handling** | TryCatch around move operation; logs error on failure |
| **BPMN Stage** | Stage 17 — Archive |

---

## 3. BPMN Orchestration Map

### Process Structure
| Element | Count | IDs (selected) |
|---------|-------|----------------|
| startEvent | 1 | Start_ClaimSync |
| endEvent | 1 | End_ClaimSync |
| serviceTask (RPA jobs) | 13 | Task_WF_Monitor, Task_WF_Init, Task_WF_Extract, Task_WF_KB, Task_WF_Validate, Task_WF_Package, Task_WF_RequestDocs, Task_WF_Update, Task_WF_Archive, plus 4 more |
| serviceTask (Agent jobs) | 4 | Task_AG_Analysis, Task_AG_Fraud, Task_AG_Decision, Task_AG_Summary |
| userTask (HITL) | 4 | Task_HITL_Reviewer, Task_HITL_MissingDocs, plus 2 more |
| scriptTask | 4 | Task_Script_InitVars, Task_Script_BuildPayload, Task_Script_ParseResponse, Task_Script_SetStatus |
| exclusiveGateway | 18 | Gw_Validation, Gw_DocumentsComplete, Gw_FraudRisk, Gw_Decision, Gw_ReviewerOverride, plus 13 more |
| sequenceFlow | 48 | (various conditional and default) |
| BPMNShape | 72 | (diagram elements) |
| BPMNEdge | 82 | (diagram edges) |

### Stage Sequence (Preserved)
1. **Intake** → WF_Monitor_Claim_Intake
2. **Initialize** → WF_Initialize_Claim_Record
3. **Document Extraction** → WF_Read_And_Extract_Document_Text (parallel with KB loading)
4. **Knowledge Loading** → WF_Load_Agent_Knowledge
5. **Business Validations** → WF_Run_Business_Validations
6. **Analysis** → AG_Claim_Analysis_Core
7. **Validation Check** → Gateway: validation_passed?
8. **Missing Docs Branch** → WF_Send_Missing_Document_Request + HITL
9. **Fraud Assessment** → AG_Fraud_Risk
10. **Fraud Check** → Gateway: fraud_risk_level?
11. **Decision Support** → AG_Decision_Support
12. **Decision Check** → Gateway: decision?
13. **Reviewer Package** → WF_Prepare_Reviewer_Package
14. **Human Review** → HITL Reviewer Task
15. **Final Summary** → AG_Final_Summary
16. **Update Record** → WF_Update_Claim_Record
17. **Archive** → WF_Archive_Claim
18. **End**

---

## 4. Stage-to-Component Mapping

| Stage # | Stage Name | Component Type | Component Name | Inputs | Outputs |
|---------|------------|---------------|----------------|--------|---------|
| 1 | Intake | RPA | WF_Monitor_Claim_Intake | in_rootFolderPath | out_claimFolderPath, out_claimId |
| 2 | Initialize | RPA | WF_Initialize_Claim_Record | in_claim_folder_path | out_claim_id |
| 3 | Document Extraction | RPA | WF_Read_And_Extract_Document_Text | in_claimFolderPath, in_claimId, in_expectedFileTypes | out_documentTextBundle, out_documentNames, out_extractedData, out_extractionSuccess, out_extractionNotes |
| 4 | Knowledge Loading | RPA | WF_Load_Agent_Knowledge | in_agent_name, in_kb_base_path | out_knowledge_bundle, out_knowledge_load_status, out_knowledge_quality_hint |
| 5 | Business Validations | RPA | WF_Run_Business_Validations | in_claimId, in_documentTextBundle, in_documentNames | out_validationResults, out_validationPassed |
| 6 | Analysis | Agent | AG_Claim_Analysis_Core | claim_id, document_text_bundle, extracted_data, claim_category_hint | category, eligible, documents_complete, missing_documents, claim_summary, analysis_confidence |
| 7 | Validation Gateway | Gateway | Gw_Validation | out_validationPassed | (branch) |
| 8 | Missing Docs Request | RPA | WF_Send_Missing_Document_Request | in_claimId, in_missingDocuments | out_requestMessage |
| 9 | Missing Docs HITL | HITL | Task_HITL_MissingDocs | (form) | reviewer_response |
| 10 | Fraud Assessment | Agent | AG_Fraud_Risk | claim_id, document_text_bundle, extracted_data, analysis_result, validation_result | fraudRisk.level, fraudRisk.score, fraudRisk.recommended_action |
| 11 | Fraud Gateway | Gateway | Gw_FraudRisk | fraudRisk.level | (branch: none/low/medium/high) |
| 12 | Decision Support | Agent | AG_Decision_Support | claim_id, analysis_result, fraud_result, validation_result, extracted_data | decision, decision_confidence, recommended_action, missing_documents |
| 13 | Decision Gateway | Gateway | Gw_Decision | decision | (branch: approve/reject/request_docs/escalate) |
| 14 | Reviewer Package | RPA | WF_Prepare_Reviewer_Package | in_claimId, in_validationResults, in_validationPassed, in_analysisResult, in_fraudResult, in_decisionSupport | out_reviewerPackage |
| 15 | Human Review | HITL | Task_HITL_Reviewer | (form with reviewerPackage) | reviewer_decision, reviewer_notes |
| 16 | Final Summary | Agent | AG_Final_Summary | claim_id, analysis_result, fraud_result, validation_result, decision_support, reviewer_decision | summary_report, audit_trail, processing_metadata |
| 17 | Update Record | RPA | WF_Update_Claim_Record | in_claimId, in_validationResults, in_analysisResult, in_fraudResult, in_decisionSupport, in_reviewerDecision, in_finalSummary | out_claimRecord |
| 18 | Archive | RPA | WF_Archive_Claim | in_claimFolderPath | (side effect: moves folder) |

---

## 5. Gateway Dependency Map

| Gateway ID | Decision Variable | Condition Branches | True Path | False/Default Path |
|------------|-------------------|-------------------|-----------|-------------------|
| Gw_Validation | Var_ValidationPassed | `== true` | → Analysis | → Missing Docs Request |
| Gw_DocumentsComplete | Var_DocumentsComplete | `== true` | → Fraud Assessment | → Missing Docs Request |
| Gw_FraudRisk | Var_FraudRiskLevel | `== "none"` | → Decision Support | → (low/medium/high branches) |
| Gw_FraudHigh | Var_FraudRiskLevel | `== "high"` | → Reject/Escalate | → Continue |
| Gw_Decision | Var_Decision | `== "approve"` | → Reviewer Package | → (reject/request/escalate) |
| Gw_ReviewerOverride | Var_ReviewerDecision | `== "override"` | → Re-process | → Final Summary |
| Gw_HasMissingDocs | Var_MissingDocuments | `.Count > 0` | → Request Docs | → Skip |
| Gw_ExtractionSuccess | Var_ExtractionSuccess | `== true` | → Continue | → End (no docs) |

---

## 6. Knowledge Base Dependency Map

| KB File | Agents That Use It | RPA Workflows That Load It | Content Purpose |
|---------|---------------------|---------------------------|-----------------|
| 00_ClaimSync_Master_KB.docx | ALL 5 agents | WF_Load_Agent_Knowledge (all branches) | Master guidelines, process overview |
| 01_Fraud_Detection_KB.docx | AG_Fraud_Risk, AG_Decision_Support | WF_Load_Agent_Knowledge (fraud branch) | Fraud signals, detection rules |
| 02_Claim_Categories_KB.docx | AG_Claim_Analysis_Core, AG_Decision_Support | WF_Load_Agent_Knowledge (analysis branch) | Category definitions, eligibility criteria |
| 03_Document_Requirements_KB.docx | AG_Claim_Analysis_Core | WF_Load_Agent_Knowledge (analysis branch) | Required documents per claim type |
| 04_Historical_Cases_KB.docx | AG_Fraud_Risk | WF_Load_Agent_Knowledge (fraud branch) | Historical fraud patterns |
| 05_Decision_Guidelines_KB.docx | AG_Decision_Support | WF_Load_Agent_Knowledge (decision branch) | Decision priority matrix |
| 06_Summary_Templates_KB.docx | AG_Final_Summary | WF_Load_Agent_Knowledge (summary branch) | Summary format, audit trail template |

### KB Resolution Chain
```
WF_Load_Agent_Knowledge
  → Resolve path: input → env(CLAIMSYNC_KB_PATH) → Desktop default
  → Switch(agent_name) → select kb_files list
  → ForEach kb_file → Invoke WF_Load_Knowledge_File
    → File.ReadAllText(current_kb_file) → Trim
  → Append to file_texts with [KB: filename] header
  → Join with "---" separator
  → Apply MAX_KB_CHARS=80000 cap
  → Determine status: failed / partial / success
```

---

## 7. Data Flow / Variable Contract

### Key BPMN Variables
| Variable | Populated By | Consumed By | Type |
|----------|-------------|-------------|------|
| Var_ClaimId | WF_Initialize_Claim_Record | ALL downstream | String |
| Var_ClaimFolderPath | WF_Monitor_Claim_Intake | WF_Read_And_Extract_Document_Text, WF_Archive_Claim | String |
| Var_DocTextBundle | WF_Read_And_Extract_Document_Text | AG_Claim_Analysis_Core, AG_Fraud_Risk, WF_Run_Business_Validations | String |
| Var_DocumentNames | WF_Read_And_Extract_Document_Text | WF_Run_Business_Validations | String |
| Var_ExtractedData | WF_Read_And_Extract_Document_Text | AG_Claim_Analysis_Core, AG_Fraud_Risk | String |
| Var_ExtractionNotes | WF_Read_And_Extract_Document_Text | (logging) | String |
| Var_ExtractionSuccess | WF_Read_And_Extract_Document_Text | Gateway | Boolean |
| Var_KnowledgeBundle | WF_Load_Agent_Knowledge | AG_Claim_Analysis_Core, AG_Fraud_Risk, AG_Decision_Support, AG_Final_Summary | String |
| Var_ValidationResults | WF_Run_Business_Validations | AG_Decision_Support, WF_Prepare_Reviewer_Package, WF_Update_Claim_Record | String |
| Var_ValidationPassed | WF_Run_Business_Validations | Gateway, WF_Prepare_Reviewer_Package | Boolean |
| Var_AnalysisResult | AG_Claim_Analysis_Core | AG_Fraud_Risk, AG_Decision_Support, WF_Prepare_Reviewer_Package, WF_Update_Claim_Record | String |
| Var_FraudResult | AG_Fraud_Risk | AG_Decision_Support, WF_Prepare_Reviewer_Package, WF_Update_Claim_Record | String |
| Var_FraudRiskLevel | AG_Fraud_Risk | Gateway | String |
| Var_DecisionSupport | AG_Decision_Support | WF_Prepare_Reviewer_Package, WF_Update_Claim_Record | String |
| Var_Decision | AG_Decision_Support | Gateway | String |
| Var_ReviewerPackage | WF_Prepare_Reviewer_Package | HITL Reviewer Task | String |
| Var_ReviewerDecision | HITL Reviewer Task | AG_Final_Summary, WF_Update_Claim_Record | String |
| Var_FinalSummary | AG_Final_Summary | WF_Update_Claim_Record | String |
| Var_ClaimRecord | WF_Update_Claim_Record | (output) | String |

---

## 8. Final Assessment

### Fully Implemented Components (Logic Complete)
| # | Component | Status |
|---|-----------|--------|
| 1 | WF_Monitor_Claim_Intake | COMPLETE |
| 2 | WF_Initialize_Claim_Record | COMPLETE |
| 3 | WF_Read_And_Extract_Document_Text | COMPLETE |
| 4 | WF_Load_Knowledge_File | COMPLETE |
| 5 | WF_Load_Agent_Knowledge | COMPLETE |
| 6 | WF_Run_Business_Validations | COMPLETE |
| 7 | WF_Prepare_Reviewer_Package | COMPLETE |
| 8 | WF_Send_Missing_Document_Request | COMPLETE |
| 9 | WF_Update_Claim_Record | COMPLETE |
| 10 | WF_Archive_Claim | COMPLETE |
| 11 | AG_Claim_Analysis_Core | COMPLETE (config overwritten) |
| 12 | AG_Fraud_Risk | COMPLETE |
| 13 | AG_Decision_Support | COMPLETE |
| 14 | AG_Final_Summary | COMPLETE |
| 15 | AG_PDF_Extraction | COMPLETE |
| 16 | Process.bpmn | STRUCTURALLY COMPLETE (36 nodes, 48 flows) |

### Partially Implemented / Binding Gaps
| # | Component | Issue | Severity |
|---|-----------|-------|----------|
| 1 | All RPA serviceTasks in BPMN | releaseKey, folderId, folderPath are EMPTY — jobs cannot execute at runtime | BLOCKING |
| 2 | All HITL userTasks in BPMN | appId, appVersion, actions, key are EMPTY — forms cannot render | BLOCKING |
| 3 | Task_WF_Extract output mapping | Maps to generic Var_JobResponse; downstream expects Var_DocTextBundle, Var_ExtractionNotes, Var_ExtractedData | ERROR |
| 4 | Var_DocumentsComplete | Never populated by any task; Gateway Gw_DocumentsComplete will always take default branch | ERROR |
| 5 | Var_FraudRiskLevel | Never populated by fraud task output mapping; Gateway Gw_FraudRisk broken | ERROR |
| 6 | AG_Decision_Support, AG_Final_Summary | Process keys exist but not confirmed published to Orchestrator | WARNING |
| 7 | project.uiproj | MainFile is null | WARNING |
| 8 | IS Connections | None found — any IS connector nodes would fail | INFO |

### Missing Components
| # | Item | Needed For |
|---|------|-----------|
| 1 | Request_Missing_Documents_Task | HITL form for missing documents (referenced but not inspected) |
| 2 | Reviewer_Decision_Task | HITL form for human reviewer (referenced but not inspected) |
| 3 | bindings_v2.json enrichment | Runtime binding resolution for all serviceTask nodes |
| 4 | entry-points.json validation | Confirm entry point ID matches BPMN start event |

### Runtime Readiness
- **RPA Workflows:** 10/10 have complete XAML logic. Ready for Studio Web compilation once project.json dependencies are confirmed.
- **Agent Configs:** 5/5 have complete JSON configurations. Ready for deployment.
- **BPMN Orchestration:** Structure is complete but has 6 BLOCKING/ERROR-level binding gaps that prevent execution.
- **Knowledge Base:** 7 KB files referenced. Resolution chain is complete (path → env → default).

---

*End of Extraction Inventory*
