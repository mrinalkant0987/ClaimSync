
## WF_Send_Missing_Document_Request — XAML Implementation

## Steps

### Step 1: Write the complete workflow XAML to Main.xaml
Overwrite `C:\Users\mrinal.kant\Documents\Usecase\Solution 2\WF_Send_Missing_Document_Request\Main.xaml` with the full implementation following the established solution pattern (matching `WF_Update_Claim_Record`'s namespace and reference layout), containing:
- `x:Members` declaring `in_claimId` (InArgument String), `in_missingDocuments` (InArgument List\<String\>), `out_requestMessage` (OutArgument String)
- A local `status` variable (String) inside the Sequence
- **STEP 0** — Assign: initialize `out_requestMessage = ""` immediately (guarantees output is always set before any logic)
- **STEP 1–2** — Assign: build message `"Missing documents for claim {id}: {list}"` with VB `String.Join(", ", in_missingDocuments)` and null/empty guards on both inputs; result goes directly to `out_requestMessage`
- **STEP 3** — `LogMessage` (Info): `"Requesting missing documents"`
- **STEP 4** — Assign: `status = "pending_documents"`
- **STEP 5** — `If` safety gate: if `out_requestMessage` is still empty after all steps, assign fallback `"MissingDocumentRequestFailed"`
