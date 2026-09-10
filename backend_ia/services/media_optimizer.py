"""
MediaOptimizer — Otimizador Multimodal de Mídias (PC-11 / P-1103, P-1104, P-1106)
Reduz o consumo de tokens visuais e de documentos através de downsampling de imagens (Pillow),
extração digital local de texto de PDFs (PyMuPDF) e hashing criptográfico SHA-256 para cache.
"""
import io
import base64
import hashlib
import logging
from typing import Optional, Tuple
from PIL import Image

logger = logging.getLogger(__name__)


class MediaOptimizer:
    """
    Serviço centralizado de pré-processamento e compressão de mídias multimodais.
    """

    @staticmethod
    def compute_media_hash(media_base64: str) -> str:
        """
        P-1106: Gera o hash SHA-256 do binário de mídia para indexação de cache.
        """
        if not media_base64:
            return ""
        clean_b64 = media_base64
        if "," in clean_b64:
            clean_b64 = clean_b64.split(",", 1)[1]
        clean_b64 = clean_b64.strip().replace("\n", "").replace("\r", "")
        try:
            raw_bytes = base64.b64decode(clean_b64)
            return hashlib.sha256(raw_bytes).hexdigest()
        except Exception as e:
            logger.warning(f"[MEDIA OPTIMIZER] Falha ao computar hash de mídia: {e}")
            return hashlib.sha256(clean_b64.encode("utf-8")).hexdigest()

    @staticmethod
    def optimize_image(
        media_base64: str, 
        media_mimetype: str = "image/jpeg", 
        max_dimension: int = 1024,
        quality: int = 80
    ) -> Tuple[str, str]:
        """
        P-1103: Redimensiona proporcionalmente imagens que excederem max_dimension,
        converte para RGB JPEG com fator de qualidade especificado.
        Retorna (base64_otimizado, mimetype_otimizado).
        """
        try:
            clean_b64 = media_base64
            if "," in clean_b64:
                clean_b64 = clean_b64.split(",", 1)[1]
            clean_b64 = clean_b64.strip().replace("\n", "").replace("\r", "")
            img_bytes = base64.b64decode(clean_b64)

            image = Image.open(io.BytesIO(img_bytes))
            orig_w, orig_h = image.size

            # Se for imagem com transparência (RGBA/LA/P), converte para RGB
            if image.mode in ("RGBA", "LA", "P"):
                image = image.convert("RGB")

            # Verifica se precisa de downscale
            needs_resize = orig_w > max_dimension or orig_h > max_dimension
            if needs_resize:
                # Calcula proporção respeitando o maior lado
                ratio = min(max_dimension / orig_w, max_dimension / orig_h)
                new_w = int(orig_w * ratio)
                new_h = int(orig_h * ratio)
                image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
                logger.info(f"[MEDIA OPTIMIZER] Downsampling de imagem: {orig_w}x{orig_h} ➔ {new_w}x{new_h}")

            out_buf = io.BytesIO()
            image.save(out_buf, format="JPEG", quality=quality, optimize=True)
            optimized_bytes = out_buf.getvalue()

            opt_b64 = base64.b64encode(optimized_bytes).decode("utf-8")
            orig_kb = len(img_bytes) / 1024
            opt_kb = len(optimized_bytes) / 1024
            logger.info(f"[MEDIA OPTIMIZER] Compressão de imagem: {orig_kb:.1f} KB ➔ {opt_kb:.1f} KB (Salvos {orig_kb - opt_kb:.1f} KB)")

            return opt_b64, "image/jpeg"
        except Exception as e:
            logger.warning(f"[MEDIA OPTIMIZER] Falha ao otimizar imagem: {e}. Mantendo imagem original.")
            return media_base64, media_mimetype

    @staticmethod
    def extract_text_from_pdf(media_base64: str, max_pages: int = 15) -> Optional[str]:
        """
        P-1104: Tenta extrair o texto limpo de um PDF digitalmente via PyMuPDF ou PyPDF.
        Se o PDF possuir conteúdo textual legível, retorna o texto extraído para
        inclusão direta no prompt, suprimindo o envio de mídia binária multimodal.
        """
        try:
            clean_b64 = media_base64
            if "," in clean_b64:
                clean_b64 = clean_b64.split(",", 1)[1]
            clean_b64 = clean_b64.strip().replace("\n", "").replace("\r", "")
            pdf_bytes = base64.b64decode(clean_b64)

            extracted_chunks = []
            total_chars = 0

            # 1. Tentativa primária com PyMuPDF / fitz
            try:
                try:
                    import pymupdf as fitz
                except ImportError:
                    import fitz

                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                total_pages = min(len(doc), max_pages)

                for page_idx in range(total_pages):
                    page = doc[page_idx]
                    page_text = page.get_text("text").strip()
                    if page_text:
                        extracted_chunks.append(f"--- [Página {page_idx + 1}] ---\n{page_text}")
                        total_chars += len(page_text)
                doc.close()
            except ImportError:
                # 2. Fallback secundário com pypdf
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                total_pages = min(len(reader.pages), max_pages)
                for page_idx in range(total_pages):
                    page = reader.pages[page_idx]
                    page_text = (page.extract_text() or "").strip()
                    if page_text:
                        extracted_chunks.append(f"--- [Página {page_idx + 1}] ---\n{page_text}")
                        total_chars += len(page_text)

            # Se houver texto substancial (> 20 caracteres), consideramos sucesso na extração
            if total_chars > 20:
                full_text = "\n\n".join(extracted_chunks)
                logger.info(f"[MEDIA OPTIMIZER] Texto extraído localmente de PDF ({total_chars} caracteres em {len(extracted_chunks)} páginas). Despacho direto como texto!")
                return full_text

            logger.info("[MEDIA OPTIMIZER] PDF digital não contém texto extraível suficiente (possível PDF escaneado/imagem). Mantendo envio multimodal.")
            return None
        except Exception as e:
            logger.warning(f"[MEDIA OPTIMIZER] Falha ao extrair texto do PDF: {e}")
            return None
