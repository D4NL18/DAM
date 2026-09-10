import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from services.translation_service import TranslationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/translate", tags=["Translation"])

class TranslationRequest(BaseModel):
    text: str = Field(..., description="Texto a ser traduzido", min_length=1)
    target_language: str = Field("pt", description="Código ISO ou nome do idioma de destino (ex: 'pt', 'en', 'es', 'ja')")
    source_language: Optional[str] = Field(None, description="Código ISO do idioma de origem (se omitido, detecção automática)")

class TranslationResponse(BaseModel):
    status: str
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    characters_count: int
    provider: str

class TranslationUsageResponse(BaseModel):
    month: str
    characters_used: int
    monthly_limit: int
    percentage_used: float
    requests_count: int
    free_tier_active: bool

@router.post("", response_model=TranslationResponse)
def translate_text(request: TranslationRequest):
    """
    P-1001 e P-1002: Endpoint RESTful para tradução universal any-to-any
    utilizando a Google Cloud Translation API v2 de forma gratuita.
    """
    clean_text = request.text.strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="Texto vazio para tradução.")

    result = TranslationService.translate_text(
        text=clean_text,
        target_language=request.target_language,
        source_language=request.source_language
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Erro ao processar tradução."))

    return TranslationResponse(
        status=result.get("status", "success"),
        original_text=result.get("original_text", clean_text),
        translated_text=result.get("translated_text", ""),
        source_language=result.get("source_language", "auto"),
        target_language=result.get("target_language", request.target_language),
        characters_count=result.get("characters_count", len(clean_text)),
        provider=result.get("provider", "google_cloud_translation_v2")
    )

@router.get("/usage", response_model=TranslationUsageResponse)
def get_translation_usage():
    """
    P-1002: Consulta a telemetria FinOps de consumo da cota gratuita mensal (500k caracteres).
    """
    usage = TranslationService.get_monthly_usage()
    return TranslationUsageResponse(
        month=usage["month"],
        characters_used=usage["characters_used"],
        monthly_limit=usage["monthly_limit"],
        percentage_used=usage["percentage_used"],
        requests_count=usage["requests_count"],
        free_tier_active=usage["free_tier_active"]
    )
