from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from config import DOCUMENTS_DIR
from rag.ingestor import VALID_DOMAINS, ingest_domain
from rag.pipeline import refresh_domain_state

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


def _safe_filename(name: str) -> str:
    raw = (name or "").strip()
    if not raw:
        return "uploaded_document.pdf"
    return Path(raw).name


@router.post("/api/admin/ingest")
async def admin_ingest(
    domain: str = Form(...),
    file: UploadFile = File(...),
):
    normalized_domain = domain.strip().lower()
    if normalized_domain not in VALID_DOMAINS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid domain. Use one of: {', '.join(sorted(VALID_DOMAINS))}.",
        )

    safe_name = _safe_filename(file.filename)
    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use .pdf, .txt, or .md.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    target_dir = DOCUMENTS_DIR / normalized_domain
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / safe_name
    target_path.write_bytes(file_bytes)

    try:
        summary = await ingest_domain(normalized_domain)
        refresh_domain_state(normalized_domain)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    return {
        "status": "done",
        "message": "Ingestion completed successfully.",
        "domain": normalized_domain,
        "file": safe_name,
        "chunks_indexed": summary["chunks"],
    }
