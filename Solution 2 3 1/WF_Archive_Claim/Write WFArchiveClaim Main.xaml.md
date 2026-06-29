# WF_Archive_Claim.xaml Implementation

## Steps

### Step 1: Write WF_Archive_Claim Main.xaml
Overwrite `C:\Users\mrinal.kant\Documents\Usecase\Solution 2\WF_Archive_Claim\Main.xaml` with the complete CrossPlatform workflow XAML that:

- Declares argument `in_claimFolderPath` (InArgument String)
- Declares variables: `archiveRoot` (String), `folderName` (String), `archivePath` (String), `v_dummy` (Object)
- Uses the same namespace set and assembly references as sibling workflows (mirrors `WF_Monitor_Claim_Intake` exactly, plus adds `xmlns:sio` for `System.IO` to support `TargetType` on `InvokeMethod`)
- Root Sequence `DisplayName="WF_Archive_Claim"` contains:
  - **STEP 1** — Assign `archiveRoot = "Archive"`
  - **STEP 2** — Assign `folderName = New DirectoryInfo(in_claimFolderPath).Name` (handles trailing separators correctly)
  - **STEP 3** — Assign `archivePath = System.IO.Path.Combine(archiveRoot, folderName)`
  - **STEP 4** — `TryCatch`:
    - **Try** → inner Sequence:
      - `If Not Directory.Exists(archiveRoot)` → Assign `v_dummy = Directory.CreateDirectory(archiveRoot)` (returns DirectoryInfo, discarded)
      - `InvokeMethod` with `TargetType="{x:Type sio:Directory}"`, `MethodName="Move"`, args `in_claimFolderPath` + `archivePath`
      - `ui:LogMessage Level="Info"` → `"Claim archived successfully"`
    - **Catch** `s:Exception` as `ex` → Sequence → `ui:LogMessage Level="Error"` → `"[WF_Archive_Claim] Archive failed: " + ex.Message`

### Step 2: Verify file written correctly
Read back `Main.xaml` and confirm: argument declared, all 4 variables present, TryCatch structure intact, both LogMessage activities present, no truncation.
