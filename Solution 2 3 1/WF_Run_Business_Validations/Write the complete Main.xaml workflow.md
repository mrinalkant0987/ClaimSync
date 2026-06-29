## WF_Run_Business_Validations — Build Plan

**File:** `C:\Users\mrinal.kant\Documents\Usecase\Solution 2\WF_Run_Business_Validations\Main.xaml`

## Steps

### Step 1: Write the complete Main.xaml workflow
Replace the current stub (which only contains a `ManualTrigger`) with the full workflow XAML. The file will contain:

- **5 arguments** — `in_claim_id`, `in_document_text_bundle`, `in_document_names` (In/String), `out_validation_results` (Out/String), `out_validation_passed` (Out/Boolean)
- **3 variables** — `validation_messages` (List\<String\>), `text_length` (Int32), `doc_count` (Int32)
- **Activity tree:**
  - 5× `Assign` — initialize all outputs and variables to safe defaults
  - `If` — Step 2: Claim ID null check → `InvokeMethod Add("ClaimID=OK|Missing")`
  - `If` — Step 3: Text bundle null/whitespace check → nested `Assign text_length` + inner `If text_length > 50` → `InvokeMethod Add("TextQuality=OK|TextTooShort")`; Else → `Add("TextMissing")`
  - `If` — Step 4: Document names null/whitespace check → nested `Assign doc_count` + inner `If doc_count > 0` → `InvokeMethod Add("DocumentsPresent=OK|NoDocumentsFound")`; Else → `Add("DocumentNamesMissing")`
  - `Assign` — Step 5: `String.Join("; ", validation_messages)` → `out_validation_results`
  - `If` — Step 6: condition checks for "Missing"/"TooShort"/"NoDocuments" → sets `out_validation_passed = False/True`
  - `If` — Step 7: safety guard — if `out_validation_results` is empty → override with fallback message + set `False`

All namespaces and assembly references are preserved exactly from the existing file. No new packages added.

### Step 2: Verify the written XAML
Read the file back and confirm structural integrity — all 7 steps present, all 5 arguments defined, all OUT arguments always assigned, no null-unsafe expressions.
