## Steps

### Step 1: Read the exact variable block and PDF branch for precise EditFile targets
Read lines 100–130 (Sequence.Variables block) and lines 255–285 (PDF If.Then block) from `Main.xaml` to capture exact whitespace and surrounding text needed for the two EditFile calls.

### Step 2: Add pdf_text, pdf_status, pdf_notes variables to Sequence.Variables
EditFile the variable block — insert the three new `String` variable declarations immediately before the closing `</Sequence.Variables>` tag, matching existing indentation style.

### Step 3: Replace the PDF branch If.Then with InvokeWorkflowFile + supporting activities
EditFile — replace the existing `<If.Then>` block (single AddToCollection warning) with a `<Sequence>` containing:
- `ui:InvokeWorkflowFile` mapping `current_file_path → in_pdf_file_path`, `pdf_text ← out_pdf_text`, `pdf_status ← out_pdfExtractionStatus`, `pdf_notes ← out_pdf_extraction_notes`, WorkflowFileName = `["..\WF_Extract_PDF_Text\Main.xaml"]`
- `Assign` setting `current_extracted_text = If(Not String.IsNullOrWhiteSpace(pdf_text), pdf_text, "")`
- `If` guarded `AddToCollection` for `pdf_notes` (only when non-empty)
- `If` guarded `AddToCollection` for error log (only when `pdf_status = "failed"`)

### Step 4: Verify the result
Run a PowerShell check confirming: old warning text is gone, `InvokeWorkflowFile` is present, all three new variables exist, file ends with `</Activity>`, no `pdf_text` null-unsafe raw usage.
