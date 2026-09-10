import io
import base64
import pytest
from PIL import Image
from services.media_optimizer import MediaOptimizer
from services.cache_service import ConversationCacheService
from services.tools.gcp_billing_tool import calcular_finops_scorecard, consultar_gcp_billing
from services.user_context import UserContext


@pytest.fixture(autouse=True)
def setup_user():
    UserContext.set_user("daniel", "5571991269995")
    ConversationCacheService.clear_cache()


class TestMediaOptimizer:
    def test_downsample_large_image(self):
        """CA-02 & P-1103: Imagens maiores que 1024px devem ser redimensionadas para teto 1024px."""
        img = Image.new("RGB", (2048, 1536), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        b64_orig = base64.b64encode(buf.getvalue()).decode("utf-8")

        b64_opt, mime = MediaOptimizer.optimize_image(b64_orig, "image/jpeg", max_dimension=1024)
        assert mime == "image/jpeg"

        # Carrega a imagem otimizada
        opt_bytes = base64.b64decode(b64_opt)
        opt_img = Image.open(io.BytesIO(opt_bytes))
        assert max(opt_img.size) <= 1024
        assert opt_img.size == (1024, 768)
        assert len(opt_bytes) < len(buf.getvalue())

    def test_small_image_no_upscale(self):
        """CA-02: Imagens menores que 1024px não devem sofrer upscale indesejado."""
        img = Image.new("RGB", (400, 300), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        b64_orig = base64.b64encode(buf.getvalue()).decode("utf-8")

        b64_opt, _ = MediaOptimizer.optimize_image(b64_orig, "image/jpeg", max_dimension=1024)
        opt_bytes = base64.b64decode(b64_opt)
        opt_img = Image.open(io.BytesIO(opt_bytes))
        assert opt_img.size == (400, 300)

    def test_extract_text_from_clean_pdf(self):
        """CA-03 & P-1104: Deve extrair texto digital de PDF localmente via PyMuPDF/PyPDF."""
        from reportlab.pdfgen import canvas
        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        c.drawString(100, 750, "Relatório Mensal de Finanças DAM 2026")
        c.save()
        pdf_bytes = buf.getvalue()
        b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

        extracted_text = MediaOptimizer.extract_text_from_pdf(b64_pdf)
        assert extracted_text is not None
        assert "Relatório Mensal de Finanças DAM 2026" in extracted_text


class TestMultimodalCache:
    def test_cache_hit_with_identical_media(self):
        """CA-04 & P-1106: Mídia com mesmo conteúdo e texto deve retornar Cache Hit."""
        fake_media_b64 = base64.b64encode(b"fake_image_content_12345").decode("utf-8")
        user_jid = "5571991269995@s.whatsapp.net"
        query = "Onde assistir este filme do pôster?"

        saved = ConversationCacheService.save_response(
            remote_jid=user_jid,
            query=query,
            response_text="Disponível na Netflix e no Prime Video.",
            media_base64=fake_media_b64,
            custom_ttl=3600
        )
        assert saved is True

        cached = ConversationCacheService.get_cached_response(
            remote_jid=user_jid,
            query=query,
            media_base64=fake_media_b64
        )
        assert cached == "Disponível na Netflix e no Prime Video."


class TestFinOpsScorecard:
    def test_finops_scorecard_calculation(self):
        """CA-05: Scorecard FinOps de 5 pilares com pontuação global >= 4.7/5.0."""
        scorecard = calcular_finops_scorecard()
        assert "score_global" in scorecard
        assert scorecard["score_global"] >= 4.7
        assert "pilares" in scorecard
        assert len(scorecard["pilares"]) == 5

        relatorio = consultar_gcp_billing()
        assert "FinOps Scorecard" in relatorio or "Score FinOps" in relatorio
