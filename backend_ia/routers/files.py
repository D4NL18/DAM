import io
import json
import time
import logging
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Response, Depends

from services.file_converter_service import FileConverterService
from repositories.file_conversion_repository import FileConversionRepository
from services.user_context import UserContext

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/files", tags=["File Conversions"])


@router.get("/supported-formats")
async def get_supported_formats():
    """
    Retorna a lista completa de formatos e operações de conversão suportadas.
    """
    return {
        "supported_conversions": [
            {
                "type": "img_to_pdf",
                "name": "Imagens para PDF",
                "from_formats": ["jpg", "jpeg", "png", "webp", "bmp"],
                "to_format": "pdf",
                "description": "Combina uma ou varias fotos em um único arquivo PDF."
            },
            {
                "type": "merge_pdfs",
                "name": "Juntar PDFs",
                "from_formats": ["pdf"],
                "to_format": "pdf",
                "description": "Funde dois ou mais arquivos PDF em ordem sequencial."
            },
            {
                "type": "split_pdf",
                "name": "Dividir PDF",
                "from_formats": ["pdf"],
                "to_format": "pdf",
                "description": "Extrai páginas específicas (ex: '1-3, 5') de um PDF."
            },
            {
                "type": "pdf_to_docx",
                "name": "PDF para Word",
                "from_formats": ["pdf"],
                "to_format": "docx",
                "description": "Converte PDF para documento Word (.docx) editável."
            },
            {
                "type": "docx_to_pdf",
                "name": "Word para PDF",
                "from_formats": ["docx"],
                "to_format": "pdf",
                "description": "Converte arquivo DOCX em PDF limpo e formatado."
            },
            {
                "type": "pdf_to_images",
                "name": "PDF para Imagens",
                "from_formats": ["pdf"],
                "to_format": "png",
                "description": "Renderiza páginas do PDF como imagens PNG de alta resolução."
            },
            {
                "type": "image_convert",
                "name": "Conversão de Formato de Imagem",
                "from_formats": ["png", "jpg", "jpeg", "webp", "bmp"],
                "to_format": "jpeg | png | webp",
                "description": "Altera o formato e compressão de imagens."
            },
            {
                "type": "pdf_to_text",
                "name": "Extrair Texto de PDF",
                "from_formats": ["pdf"],
                "to_format": "txt",
                "description": "Extrai todo o texto legível do arquivo PDF."
            }
        ],
        "max_file_size_mb": 25,
        "max_merge_total_mb": 50
    }


@router.get("/conversions/history")
async def get_conversion_history(limit: int = 10):
    """
    Retorna o histórico das conversões recentes do usuário ativo.
    """
    user_id = UserContext.get_user_id()
    history = FileConversionRepository.get_user_conversions(user_id=user_id, limit=limit)
    return {"user_id": user_id, "history": history}


@router.post("/convert")
async def convert_file(
    file: UploadFile = File(...),
    additional_files: List[UploadFile] = File(default=[]),
    conversion_type: str = Form(...),
    options: Optional[str] = Form(default=None)
):
    """
    Executa a conversão do arquivo enviado e retorna o binário pronto para download.
    """
    user_id = UserContext.get_user_id()
    start_time = time.time()

    conv_type = conversion_type.strip().lower()
    parsed_options = {}
    if options:
        try:
            parsed_options = json.loads(options)
        except Exception:
            pass

    content = await file.read()
    file_size = len(content)

    if file_size > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo excede o limite máximo permitido de 25 MB ({file_size / (1024*1024):.2f} MB)."
        )

    try:
        if conv_type in ("img_to_pdf", "images_to_pdf", "fotos_para_pdf"):
            images_list = [content]
            for add_f in additional_files:
                images_list.append(await add_f.read())
            output_bytes = FileConverterService.images_to_pdf(images_list)
            output_filename = "documento_fotos.pdf"
            media_type = "application/pdf"
            source_fmt = "image"
            target_fmt = "pdf"

        elif conv_type in ("merge_pdfs", "juntar_pdfs", "merge"):
            pdfs_list = [content]
            for add_f in additional_files:
                pdfs_list.append(await add_f.read())
            output_bytes = FileConverterService.merge_pdfs(pdfs_list)
            output_filename = "documento_unificado.pdf"
            media_type = "application/pdf"
            source_fmt = "pdf"
            target_fmt = "pdf"

        elif conv_type in ("split_pdf", "dividir_pdf"):
            pages_range = parsed_options.get("pages", "1")
            output_bytes = FileConverterService.split_pdf(content, pages_range=pages_range)
            output_filename = f"pdf_dividido_paginas_{pages_range.replace(' ', '')}.pdf"
            media_type = "application/pdf"
            source_fmt = "pdf"
            target_fmt = "pdf"

        elif conv_type in ("pdf_to_docx", "pdf_para_word"):
            output_bytes = FileConverterService.pdf_to_docx(content)
            output_filename = "documento_convertido.docx"
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            source_fmt = "pdf"
            target_fmt = "docx"

        elif conv_type in ("docx_to_pdf", "word_para_pdf"):
            output_bytes = FileConverterService.docx_to_pdf(content)
            output_filename = "documento_convertido.pdf"
            media_type = "application/pdf"
            source_fmt = "docx"
            target_fmt = "pdf"

        elif conv_type in ("image_convert", "converter_imagem"):
            target_fmt = parsed_options.get("target_format", "JPEG").upper()
            quality = int(parsed_options.get("quality", 85))
            output_bytes = FileConverterService.convert_image(content, target_format=target_fmt, quality=quality)
            ext = "jpg" if target_fmt == "JPEG" else target_fmt.lower()
            output_filename = f"imagem_convertida.{ext}"
            media_type = f"image/{ext}"
            source_fmt = "image"

        elif conv_type in ("pdf_to_text", "extrair_texto"):
            text_result = FileConverterService.pdf_to_text(content)
            output_bytes = text_result.encode("utf-8")
            output_filename = "texto_extraido.txt"
            media_type = "text/plain; charset=utf-8"
            source_fmt = "pdf"
            target_fmt = "txt"

        elif conv_type in ("pdf_to_images", "pdf_para_fotos"):
            # Renderiza a primeira página ou retorna zip se múltiplas
            images = FileConverterService.pdf_to_images(content, dpi=150)
            if not images:
                raise ValueError("Nenhuma imagem gerada do PDF.")
            output_bytes = images[0][1]
            output_filename = images[0][0]
            media_type = "image/png"
            source_fmt = "pdf"
            target_fmt = "png"

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de conversão não suportado: '{conv_type}'."
            )

        duration_ms = int((time.time() - start_time) * 1000)

        # Auditoria no repositório
        FileConversionRepository.save_conversion(
            user_id=user_id,
            conversion_type=conv_type,
            source_format=source_fmt,
            target_format=target_fmt,
            file_size_bytes=file_size,
            output_size_bytes=len(output_bytes),
            status="success",
            execution_time_ms=duration_ms
        )

        return Response(
            content=output_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{output_filename}"',
                "X-Execution-Time-Ms": str(duration_ms)
            }
        )

    except HTTPException:
        raise
    except ValueError as ve:
        duration_ms = int((time.time() - start_time) * 1000)
        FileConversionRepository.save_conversion(
            user_id=user_id,
            conversion_type=conv_type,
            source_format="unknown",
            target_format="unknown",
            file_size_bytes=file_size,
            status="failed",
            execution_time_ms=duration_ms,
            error_message=str(ve)
        )
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Erro interno na conversão {conv_type}: {e}", exc_info=True)
        FileConversionRepository.save_conversion(
            user_id=user_id,
            conversion_type=conv_type,
            source_format="unknown",
            target_format="unknown",
            file_size_bytes=file_size,
            status="failed",
            execution_time_ms=duration_ms,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Erro interno na conversão: {str(e)}")
