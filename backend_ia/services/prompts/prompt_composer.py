from typing import Optional, List
from datetime import datetime
from config.timezone import get_brasilia_now_str
from services.prompts.system_base import get_system_base_prompt
from services.prompts.financial_rules import get_financial_prompt
from services.prompts.mobility_rules import get_mobility_prompt
from services.prompts.anime_rules import get_anime_prompt
from services.prompts.briefing_rules import get_briefing_prompt
from services.prompts.billing_rules import get_billing_prompt
from services.prompts.nutrition_rules import get_nutrition_prompt
from services.prompts.translation_rules import get_translation_rules_prompt

class PromptComposer:
    """
    Compositor modular de prompts de sistema (P-1102).
    Permite compor, cachear e otimizar as instruções mestras sem monolitos estáticos,
    injetando regras de domínio estritamente sob demanda.
    """

    @staticmethod
    def compose_system_instruction(
        data_hora_atual: Optional[str] = None, 
        domains: Optional[List[str]] = None
    ) -> str:
        """
        Monta a instrução de sistema estruturada por domínios funcionais.
        Se domains for None, injeta todas as regras para compatibilidade retroativa.
        Se domains for uma lista, injeta unicamente as regras dos domínios especificados.
        """
        if not data_hora_atual:
            data_hora_atual = get_brasilia_now_str("%Y-%m-%d %H:%M")

        secoes = [get_system_base_prompt(data_hora_atual)]

        if domains is None:
            # Compatibilidade retroativa completa
            secoes.extend([
                get_financial_prompt(),
                get_mobility_prompt(),
                get_anime_prompt(),
                get_briefing_prompt(),
                get_billing_prompt(),
                get_nutrition_prompt(),
                get_translation_rules_prompt()
            ])
        else:
            # Injeção seletiva sob demanda (P-1102)
            dom_set = set(domains)
            if dom_set.intersection({"finance", "trip"}):
                secoes.append(get_financial_prompt())
            if dom_set.intersection({"mobility", "vehicle"}):
                secoes.append(get_mobility_prompt())
            if "anime" in dom_set:
                secoes.append(get_anime_prompt())
            if "briefing" in dom_set:
                secoes.append(get_briefing_prompt())
            if "billing" in dom_set:
                secoes.append(get_billing_prompt())
            if "nutrition" in dom_set:
                secoes.append(get_nutrition_prompt())
            if "translation" in dom_set:
                secoes.append(get_translation_rules_prompt())

        return "\n".join(secoes)

