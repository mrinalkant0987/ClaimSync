## WF_Prepare_Reviewer_Package — Build Plan

### Inspection Summary
| Area | Status | Detail |
|---|---|---|
| Arguments (7 in + 1 out) | ❌ Missing | No `x:Members` block at all |
| Variable `package_parts` | ❌ Missing | No `Sequence.Variables` block |
| Initialize section | ❌ Missing | Only a `ManualTrigger` placeholder |
| ClaimID conditional add | ❌ Missing | No logic |
| Validation / Flag / Analysis / Fraud / Recommendation adds | ❌ Missing | No logic |
| `String.Join` final build | ❌ Missing | No logic |
| Safety guard | ❌ Missing | No logic |

**Decision → Full rebuild** (stub only; nothing to preserve).

---

## Steps

### Step 1: Write the complete WF_Prepare_Reviewer_Package XAML

Overwrite `Main.xaml` with the full implementation matching the project's CrossPlatform XAML patterns (same namespace headers, references, and activity style as sibling workflows). The new file will contain:

- **`x:Members`** block — 6 `InArgument` + 1 `OutArgument` as specified
- **`Sequence.Variables`** — `package_parts` typed `scg:List(x:String)`
- **Step 2 — Initialize** — two `Assign` activities: `out_reviewer_package = ""` and `package_parts = New List(Of String)()`
- **Step 3 — Build package** — seven activities in exact order:
  - `If` guard for ClaimID (conditional `InvokeMethod Add`)
  - Five unconditional `InvokeMethod Add` calls for Validation, ValidationPassed, Analysis, FraudRisk, Recommendation — each using `String.IsNullOrEmpty` guards with `"NotAvailable"` fallback
- **Step 4 — Final string** — `Assign` using `String.Join(Environment.NewLine, package_parts)` with `"ReviewerPackageEmpty"` fallback
- **Step 5 — Safety** — `If String.IsNullOrEmpty(out_reviewer_package)` → `Assign "ReviewerPackageGenerationFailed"`
- All activities carry unique `sap2010:WorkflowViewState.IdRef` values
