import os
import tempfile
from dataclasses import dataclass
from typing import Optional

import httpx

BUCKET_ID = 219103
BUCKET_NAME = "ClaimDocuments"


def download_from_storage(file_reference: str) -> Optional[str]:
    """Download a file from Orchestrator storage bucket via REST API."""
    base_url = os.environ.get("UIPATH_URL", "")
    auth_token = os.environ.get("UIPATH_ACCESS_TOKEN", "")
    folder_id = os.environ.get("UIPATH_FOLDER_ID", "3149885")

    if not base_url or not auth_token:
        return None

    # Ensure base_url has no trailing slash
    base_url = base_url.rstrip("/")

    # 1. Get presigned download URL
    get_url_endpoint = (
        f"{base_url}/orchestrator_/odata/Buckets({BUCKET_ID})"
        f"/UiPath.Server.Configuration.OData.GetReadUri"
        f"?path={file_reference.replace('/', '%2F')}"
    )

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "X-UIPATH-OrganizationUnitId": folder_id,
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(get_url_endpoint, headers=headers)
            if resp.status_code != 200:
                return f"ERROR: GetReadUri failed: {resp.status_code} {resp.text}"

            data = resp.json()
            presigned_url = data.get("Uri", "")
            if not presigned_url:
                return "ERROR: No presigned URL returned"

            # 2. Download file from presigned URL
            temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            download_resp = client.get(presigned_url)
            if download_resp.status_code != 200:
                temp_file.close()
                os.unlink(temp_file.name)
                return f"ERROR: Download failed: {download_resp.status_code}"

            temp_file.write(download_resp.content)
            temp_file.close()
            return temp_file.name

    except Exception as e:
        return f"ERROR: Download exception: {str(e)}"


def extract_pdf_text(file_path: str) -> str:
    """Extract text from a PDF file using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        return "ERROR: PyPDF2 not installed"

    if not os.path.exists(file_path):
        return f"ERROR: File not found: {file_path}"

    try:
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        extracted = "\n".join(text_parts)
        if not extracted.strip():
            return "WARNING: No text extracted (possibly scanned/image PDF)"
        return extracted
    except Exception as e:
        return f"ERROR: PDF extraction failed: {str(e)}"


@dataclass
class PdfExtractIn:
    claim_id: Optional[str] = None
    pdf_file_name: Optional[str] = None
    pdf_file_path_or_reference: Optional[str] = None
    claim_folder_context: Optional[str] = None
    extraction_request_notes: Optional[str] = None


@dataclass
class PdfExtractOut:
    pdf_text: str
    pdf_status: str
    pdf_notes: str


def main(input: PdfExtractIn) -> PdfExtractOut:
    file_reference = input.pdf_file_path_or_reference or ""
    if not file_reference:
        return PdfExtractOut(
            pdf_text="",
            pdf_status="failed",
            pdf_notes="No file reference provided",
        )

    # First try as local file path
    file_path = file_reference
    notes = []

    if not os.path.exists(file_path):
        # Construct bucket reference from claim_id + file_name
        bucket_ref = file_reference
        if input.claim_id and input.pdf_file_name:
            bucket_ref = f"{input.claim_id}/{input.pdf_file_name}"
        notes.append(f"Local file not found, trying storage bucket: {bucket_ref}")
        downloaded_path = download_from_storage(bucket_ref)

        if downloaded_path and not downloaded_path.startswith("ERROR:"):
            file_path = downloaded_path
            notes.append(f"Downloaded from storage to: {downloaded_path}")
        else:
            return PdfExtractOut(
                pdf_text="",
                pdf_status="failed",
                pdf_notes="; ".join(
                    notes + [f"Could not download from storage: {downloaded_path or file_reference}"]
                ),
            )

    # Extract text
    text = extract_pdf_text(file_path)

    # Clean up temp file if we downloaded it
    if file_path != file_reference and os.path.exists(file_path):
        try:
            os.unlink(file_path)
        except Exception:
            pass

    if text.startswith("ERROR:"):
        return PdfExtractOut(
            pdf_text="",
            pdf_status="failed",
            pdf_notes=text + ("; " + "; ".join(notes) if notes else ""),
        )
    elif text.startswith("WARNING:"):
        return PdfExtractOut(
            pdf_text=text,
            pdf_status="warning",
            pdf_notes=text + ("; " + "; ".join(notes) if notes else ""),
        )
    else:
        return PdfExtractOut(
            pdf_text=text,
            pdf_status="success",
            pdf_notes=f"Extracted {len(text)} characters from {input.pdf_file_name or file_reference}"
            + ("; " + "; ".join(notes) if notes else ""),
        )
