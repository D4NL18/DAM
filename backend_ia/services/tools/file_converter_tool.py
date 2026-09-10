import logging
from typing import Optional
from services.user_context import UserContext
from repositories.file_conversion_repository import FileConversionRepository

logger = logging.getLogger(__name__)


class FileConverterTool:
    """
    Ferramenta de IA (Gemini Function Calling) para atendimento e orquestração de
    conversões de arquivos e documentos no ecossistema DAM (US-09).
    """

    FORMATOS_SUPORTADOS = [
        ("📄 PDF para Word (.docx)", "Converte documento PDF editável em Word preservando textos e tabelas."),
        ("📝 Word (.docx) para PDF", "Gera documento PDF formatado a partir de arquivos DOCX."),
        ("🖼️ Fotos para PDF", "Une uma ou várias fotos (JPG, PNG, WEBP) em um único arquivo PDF."),
        ("🔗 Juntar PDFs", "Funde múltiplos arquivos PDF em um único documento sequencial."),
        ("✂️ Dividir PDF", "Extrai páginas específicas ou intervalos (ex: '1-3, 5') de um documento PDF."),
        ("📸 PDF para Fotos", "Extrai todas as páginas de um PDF como imagens PNG de alta resolução."),
        ("🔄 Converter Imagens", "Transcodifica imagens entre formatos PNG, JPG e WEBP com compressão inteligente."),
        ("📋 Extrair Texto", "Extrai todo o texto contido no PDF para leitura rápida e sumarização.")
    ]

    @staticmethod
    def execute(
        acao: str = "listar_formatos",
        tipo_conversao: Optional[str] = None,
        parametros: Optional[str] = None
    ) -> str:
        """
        Executa a consulta de recursos ou orientação conversacional de arquivos.
        """
        user_name = UserContext.get_user_name()
        acao_lower = (acao or "listar_formatos").strip().lower()

        if acao_lower in ("listar_formatos", "formatos", "listar"):
            linhas = [
                f"📁 *Central de Conversão de Arquivos DAM*\n",
                f"Olá, {user_name}! Você pode me enviar seus arquivos diretamente aqui no WhatsApp que eu faço a conversão na hora.\n",
                "*Conversões Principais Disponíveis:*"
            ]
            for nome, desc in FileConverterTool.FORMATOS_SUPORTADOS:
                linhas.append(f"• *{nome}*: {desc}")

            linhas.extend([
                "\n⚙️ *Limites do Sistema:*",
                "• Tamanho máximo por arquivo: *25 MB*",
                "• Tamanho total para junção de PDFs: *50 MB*",
                "\n💡 *Como usar:* Basta me enviar o arquivo (PDF, Word ou Foto) e dizer o que deseja fazer com ele!"
            ])
            return "\n".join(linhas)

        elif acao_lower in ("instrucoes", "ajuda", "como_usar"):
            tipo = (tipo_conversao or "").strip().lower()

            if "word" in tipo or "doc" in tipo:
                return (
                    "📄 *Como converter PDF para Word ou Word para PDF:*\n\n"
                    "1. Anexe o documento aqui no chat (como Arquivo ou Documento).\n"
                    "2. Escreva na legenda ou na mensagem seguinte: *'converta para word'* ou *'converta para pdf'*.\n"
                    "3. Eu processarei o arquivo e te enviarei de volta pronto para download!"
                )
            elif "foto" in tipo or "imagem" in tipo or "img" in tipo:
                return (
                    "🖼️ *Como converter Fotos para PDF ou mudar formato:*\n\n"
                    "1. Envie uma ou mais fotos no chat.\n"
                    "2. Peça: *'junte essas fotos em pdf'* ou *'converta para PNG/JPG/WEBP'*.\n"
                    "3. Você receberá o documento PDF consolidado imediatamente."
                )
            elif "juntar" in tipo or "merge" in tipo:
                return (
                    "🔗 *Como juntar múltiplos PDFs:*\n\n"
                    "1. Envie os arquivos PDF em sequência que deseja unir.\n"
                    "2. Diga: *'junte esses PDFs em um só'*.\n"
                    "3. Eu unirei todos mantendo a ordem e a qualidade original."
                )
            elif "dividir" in tipo or "split" in tipo:
                return (
                    "✂️ *Como dividir ou fatiar PDF:*\n\n"
                    "1. Envie o PDF e informe as páginas desejadas.\n"
                    "2. Exemplo: *'extraia as páginas 1 a 3 e a 5 deste PDF'*.\n"
                    "3. Eu gerarei um novo PDF contendo apenas as páginas solicitadas."
                )
            else:
                return (
                    "📁 *Instruções de Conversão:*\n\n"
                    "Você pode me enviar qualquer PDF, Word ou Imagem diretamente aqui no WhatsApp e pedir a conversão desejada. "
                    "Se preferir, use o comando para listar todos os formatos suportados!"
                )

        elif acao_lower in ("historico", "ultimas_conversoes"):
            user_id = UserContext.get_user_id()
            history = FileConversionRepository.get_user_conversions(user_id=user_id, limit=5)
            if not history:
                return f"📁 {user_name}, você ainda não realizou nenhuma conversão de arquivos recentemente."

            linhas = [f"📊 *Suas Últimas Conversões de Arquivos:*\n"]
            for h in history:
                t = h.get("conversion_type", "conversão")
                status = "✅ Sucesso" if h.get("status") == "success" else "❌ Falha"
                ms = h.get("execution_time_ms", 0)
                linhas.append(f"• *{t}* — {status} ({ms}ms)")
            return "\n".join(linhas)

        else:
            return (
                f"📁 Para converter um arquivo, basta anexá-lo aqui no chat dizendo o que precisa "
                f"(ex: *'passa pra word'*, *'junta em pdf'*). Se quiser ver todas as opções, me peça para listar os formatos!"
            )


def gerenciar_arquivos(
    acao: str = "listar_formatos",
    tipo_conversao: Optional[str] = None,
    parametros: Optional[str] = None
) -> str:
    """
    Manage file and document conversions (PDF to Word, Word to PDF, merge, split, extract text).

    Args:
        acao: 'listar_formatos' for supported formats, 'instrucoes' for instructions, 'historico' for history.
        tipo_conversao: Specific conversion type for instructions.
        parametros: Additional parameters.
    """
    return FileConverterTool.execute(acao=acao, tipo_conversao=tipo_conversao, parametros=parametros)

