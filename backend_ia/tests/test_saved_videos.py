import pytest
from services.user_context import UserContext
from repositories.saved_videos_repository import SavedVideosRepository
from services.tools.saved_videos_tool import (
    salvar_video,
    consultar_videos_salvos,
    marcar_video_assistido,
    remover_video_salvo,
    _detectar_plataforma,
    _validar_e_sanitizar_url
)

@pytest.fixture(autouse=True)
def setup_teardown():
    """Limpa o repositório antes de cada teste e reseta o usuário para Daniel."""
    repo = SavedVideosRepository.get_instance()
    repo.clear_for_tests()
    UserContext.set_user("daniel")
    yield
    repo.clear_for_tests()


class TestDetecaoEValidacaoURL:
    """Testes unitários da regra P-0701 e P-0706."""

    def test_detectar_plataforma_tiktok(self):
        assert _detectar_plataforma("https://www.tiktok.com/@user/video/7391234567") == "TikTok"
        assert _detectar_plataforma("https://vm.tiktok.com/ZMabcdef/") == "TikTok"
        assert _detectar_plataforma("https://vt.tiktok.com/ZSabcdef/") == "TikTok"

    def test_detectar_plataforma_instagram(self):
        assert _detectar_plataforma("https://www.instagram.com/reel/C8xyz123abc/") == "Instagram"
        assert _detectar_plataforma("https://instagram.com/p/C9abc123/") == "Instagram"
        assert _detectar_plataforma("https://www.instagram.com/tv/C9abc123/") == "Instagram"

    def test_detectar_plataforma_youtube(self):
        assert _detectar_plataforma("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "YouTube"
        assert _detectar_plataforma("https://youtu.be/dQw4w9WgXcQ") == "YouTube"
        assert _detectar_plataforma("https://www.youtube.com/shorts/abcdef12345") == "YouTube"
        assert _detectar_plataforma("https://m.youtube.com/watch?v=12345") == "YouTube"

    def test_detectar_plataforma_outro(self):
        assert _detectar_plataforma("https://vimeo.com/123456") == "Outro"
        assert _detectar_plataforma("https://twitter.com/user/status/1234") == "Outro"

    def test_validar_url_esquemas_validos(self):
        url, valida = _validar_e_sanitizar_url("https://vm.tiktok.com/ZM123")
        assert valida is True
        assert url == "https://vm.tiktok.com/ZM123"

        url2, valida2 = _validar_e_sanitizar_url("http://instagram.com/p/123")
        assert valida2 is True
        assert url2 == "http://instagram.com/p/123"

    def test_validar_url_esquemas_invalidos_ou_maliciosos(self):
        _, valida1 = _validar_e_sanitizar_url("javascript:alert(1)")
        assert valida1 is False

        _, valida2 = _validar_e_sanitizar_url("data:text/html;base64,PHNjcmlwdD4=")
        assert valida2 is False

        _, valida3 = _validar_e_sanitizar_url("ftp://servidor/arquivo.mp4")
        assert valida3 is False

        _, valida4 = _validar_e_sanitizar_url("")
        assert valida4 is False


class TestSalvarVideo:
    """Testes unitários da regra P-0702."""

    def test_salvar_video_completo(self):
        res = salvar_video(
            url="https://vm.tiktok.com/ZM_receita",
            titulo="Strogonoff Fit",
            descricao="Receita de strogonoff sem creme de leite usando iogurte",
            categoria="Culinária",
            tags="strogonoff, fit, almoco"
        )
        assert "✅ Vídeo salvo com sucesso!" in res
        assert "TikTok" in res
        assert "Strogonoff Fit" in res
        assert "Culinária" in res

    def test_salvar_video_com_titulo_inferido_da_descricao(self):
        res = salvar_video(
            url="https://www.instagram.com/reel/C8_treino/",
            descricao="Treino pesado de quadríceps com ênfase em agachamento búlgaro",
            categoria="Treino"
        )
        assert "✅ Vídeo salvo com sucesso!" in res
        assert "Instagram" in res
        assert "Treino pesado de quadríceps" in res or "Instagram" in res

    def test_salvar_video_com_apenas_url(self):
        res = salvar_video(url="https://youtu.be/video_aleatorio")
        assert "✅ Vídeo salvo com sucesso!" in res
        assert "YouTube" in res

    def test_salvar_video_url_invalida(self):
        res = salvar_video(url="javascript:alert('hack')")
        assert "❌ Link inválido" in res or "esquema" in res


class TestConsultarVideosSalvos:
    """Testes unitários da regra P-0703."""

    def test_consultar_videos_busca_por_assunto_na_descricao(self):
        salvar_video(
            url="https://vm.tiktok.com/ZM_bolo",
            titulo="Bolo de Cenoura",
            descricao="Receita rápida com cobertura crocante de chocolate meio amargo"
        )
        salvar_video(
            url="https://youtu.be/python_fastapi",
            titulo="Tutorial FastAPI",
            descricao="Aprenda a construir APIs assíncronas com Python"
        )

        # Busca pelo termo 'chocolate' que só está na descrição
        res = consultar_videos_salvos(termo_busca="chocolate")
        assert "Bolo de Cenoura" in res
        assert "Tutorial FastAPI" not in res

    def test_consultar_videos_busca_por_titulo(self):
        salvar_video(
            url="https://youtu.be/furia_highlights",
            titulo="FURIA CS2 Highlights",
            descricao="Melhores jogadas do FalleN na Mirage"
        )

        res = consultar_videos_salvos(termo_busca="FURIA")
        assert "FURIA CS2 Highlights" in res

    def test_consultar_videos_busca_por_tag_ou_categoria(self):
        salvar_video(
            url="https://www.instagram.com/reel/mobilidade/",
            titulo="Mobilidade Torácica",
            descricao="Alongamento para soltar a coluna",
            categoria="Saúde",
            tags="alongamento, mobilidade, coluna"
        )

        res_cat = consultar_videos_salvos(termo_busca="Saúde")
        assert "Mobilidade Torácica" in res_cat

        res_tag = consultar_videos_salvos(termo_busca="coluna")
        assert "Mobilidade Torácica" in res_tag

    def test_consultar_videos_filtro_plataforma(self):
        salvar_video(url="https://vm.tiktok.com/ZM_1", titulo="Vídeo TikTok 1")
        salvar_video(url="https://youtu.be/video_yt_1", titulo="Vídeo YouTube 1")

        res_tiktok = consultar_videos_salvos(plataforma="TikTok")
        assert "Vídeo TikTok 1" in res_tiktok
        assert "Vídeo YouTube 1" not in res_tiktok

    def test_consultar_videos_filtro_status(self):
        salvar_video(url="https://vm.tiktok.com/ZM_pendente", titulo="Vídeo Pendente")
        salvar_video(url="https://vm.tiktok.com/ZM_assistir", titulo="Vídeo que verei")
        marcar_video_assistido(termo_ou_id="Vídeo que verei")

        res_pend = consultar_videos_salvos(status="pendente")
        assert "Vídeo Pendente" in res_pend
        assert "Vídeo que verei" not in res_pend

        res_assist = consultar_videos_salvos(status="assistido")
        assert "Vídeo que verei" in res_assist
        assert "Vídeo Pendente" not in res_assist

    def test_consultar_videos_nenhum_encontrado(self):
        res = consultar_videos_salvos(termo_busca="infracao_inexistente_xyz")
        assert "Nenhum vídeo" in res


class TestCicloDeVidaEMarcacao:
    """Testes unitários da regra P-0704."""

    def test_marcar_video_assistido_sucesso(self):
        salvar_video(url="https://youtu.be/curso_git", titulo="Curso de Git Avançado")
        res = marcar_video_assistido(termo_ou_id="Curso de Git")
        assert "✅ Vídeo marcado como assistido" in res
        assert "Curso de Git Avançado" in res

    def test_marcar_video_assistido_desambiguacao(self):
        salvar_video(url="https://youtu.be/treino1", titulo="Treino de Peito A")
        salvar_video(url="https://youtu.be/treino2", titulo="Treino de Peito B")

        res = marcar_video_assistido(termo_ou_id="Treino de Peito")
        assert "⚠️ Encontrei mais de um vídeo" in res or "especifique" in res

    def test_remover_video_sucesso(self):
        salvar_video(url="https://youtu.be/para_deletar", titulo="Vídeo Temporário")
        res_del = remover_video_salvo(termo_ou_id="Vídeo Temporário")
        assert "🗑️ Vídeo removido" in res_del

        res_cons = consultar_videos_salvos(termo_busca="Vídeo Temporário")
        assert "Nenhum vídeo" in res_cons


class TestIsolamentoMultiUsuario:
    """Testes unitários da regra P-0705."""

    def test_daniel_e_lari_isolamento_estrito(self):
        # 1. Daniel salva vídeo
        UserContext.set_user("daniel")
        salvar_video(
            url="https://youtu.be/cs2_taticas",
            titulo="Táticas de CS2 Mirage",
            descricao="Granadas e smokes da FURIA"
        )

        # 2. Lari não enxerga o vídeo do Daniel
        UserContext.set_user("lari")
        res_lari = consultar_videos_salvos(termo_busca="CS2")
        assert "Nenhum vídeo" in res_lari

        # 3. Lari não consegue marcar como assistido nem remover vídeo do Daniel
        res_marcar = marcar_video_assistido(termo_ou_id="Táticas de CS2")
        assert "Nenhum vídeo" in res_marcar

        res_remover = remover_video_salvo(termo_ou_id="Táticas de CS2")
        assert "Nenhum vídeo" in res_remover

        # 4. Lari salva seu próprio vídeo
        salvar_video(
            url="https://www.instagram.com/reel/skincare/",
            titulo="Rotina Noturna de Skincare",
            descricao="Passo a passo com ácido hialurônico"
        )

        # Lari enxerga o dela
        res_lari_proprio = consultar_videos_salvos(termo_busca="Skincare")
        assert "Rotina Noturna de Skincare" in res_lari_proprio

        # Daniel não enxerga o da Lari
        UserContext.set_user("daniel")
        res_daniel = consultar_videos_salvos(termo_busca="Skincare")
        assert "Nenhum vídeo" in res_daniel
