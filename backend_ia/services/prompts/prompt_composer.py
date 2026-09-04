from datetime import datetime
from services.prompts.system_base import get_system_base_prompt
from services.prompts.financial_rules import get_financial_prompt
from services.prompts.mobility_rules import get_mobility_prompt
from services.prompts.anime_rules import get_anime_prompt
from services.prompts.briefing_rules import get_briefing_prompt
from services.prompts.billing_rules import get_billing_prompt
from services.prompts.nutrition_rules import get_nutrition_prompt

class PromptComposer:
    """
    Compositor modular de prompts de sistema.
    Permite compor, cachear e otimizar as instruções mestras sem monolitos estáticos.
    """

    @staticmethod
    def compose_system_instruction(data_hora_atual: str = None) -> str:
        """
        Monta a instrução de sistema consolidada estruturada por domínios funcionais.
        """
        if not data_hora_atual:
            data_hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M")

        secoes = [
            get_system_base_prompt(data_hora_atual),
            get_financial_prompt(),
            get_mobility_prompt(),
            get_anime_prompt(),
            get_briefing_prompt(),
            get_billing_prompt(),
            get_nutrition_prompt()
        ]

        return "\n".join(secoes)
