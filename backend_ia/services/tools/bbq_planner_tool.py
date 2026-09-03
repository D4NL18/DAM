import math
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

def calcular_churrasco(
    adultos_que_bebem: int,
    adultos_que_nao_bebem: int,
    criancas: int,
    duracao_horas: int = 4,
    tipos_carne: Optional[List[str]] = None
) -> str:
    """
    Calculadora Inteligente de Churrasco e Eventos.
    Aplica regras consagradas per capita ajustadas pela duração do evento.
    
    Args:
        adultos_que_bebem: Número de adultos que consomem bebidas alcoólicas.
        adultos_que_nao_bebem: Número de adultos que não bebem álcool.
        criancas: Número de crianças participantes.
        duracao_horas: Duração estimada da festa em horas (padrão 4h).
        tipos_carne: Lista opcional com cortes desejados (ex: ['picanha', 'linguiça', 'frango']).
    """
    adultos_total = max(0, adultos_que_bebem) + max(0, adultos_que_nao_bebem)
    criancas_total = max(0, criancas)
    total_pessoas = adultos_total + criancas_total

    if total_pessoas == 0:
        return "Por favor, informe a quantidade de convidados (adultos e/ou crianças) para realizar o cálculo do churrasco."

    duracao = max(1, duracao_horas)

    # 1. CÁLCULO DE CARNES PER CAPITA
    # Base: 450g por adulto para 4h. Se a festa for mais longa, ajusta ~8% por hora adicional.
    fator_tempo_adulto = 1.0 + (duracao - 4) * 0.08
    fator_tempo_adulto = max(0.8, min(1.6, fator_tempo_adulto))
    gramas_por_adulto = 450 * fator_tempo_adulto

    # Crianças consomem cerca de 200g (ajustado também pela duração)
    fator_tempo_crianca = 1.0 + (duracao - 4) * 0.05
    fator_tempo_crianca = max(0.75, min(1.4, fator_tempo_crianca))
    gramas_por_crianca = 200 * fator_tempo_crianca

    peso_total_carne_kg = ((adultos_total * gramas_por_adulto) + (criancas_total * gramas_por_crianca)) / 1000.0

    # Distribuição das carnes
    distribuicao_carnes = []
    if not tipos_carne:
        # Padrão tradicional brasileiro: 50% bovina, 25% linguiça, 25% frango
        peso_bovina = peso_total_carne_kg * 0.50
        peso_linguica = peso_total_carne_kg * 0.25
        peso_frango = peso_total_carne_kg * 0.25
        distribuicao_carnes = [
            f"  • 🥩 Carne Bovina (Picanha/Maminha/Alcatra): *{peso_bovina:.2f} kg*",
            f"  • 🌭 Linguiça (Toscana/Calabresa): *{peso_linguica:.2f} kg*",
            f"  • 🍗 Frango (Coxinha da asa/Tulipa): *{peso_frango:.2f} kg*"
        ]
    else:
        qtd_cortes = len(tipos_carne)
        peso_por_corte = peso_total_carne_kg / qtd_cortes
        for corte in tipos_carne:
            nome_corte = corte.strip().title()
            distribuicao_carnes.append(f"  • 🥩 {nome_corte}: *{peso_por_corte:.2f} kg*")

    # 2. CÁLCULO DE BEBIDAS ALCOÓLICAS
    # Base: 1.75L por adulto que bebe para 4h (~5 latas de 350ml).
    litros_cerveja = 0.0
    latas_cerveja = 0
    fardos_12 = 0
    if adultos_que_bebem > 0:
        fator_cerveja = duracao / 4.0
        litros_por_bebedor = 1.75 * fator_cerveja
        litros_cerveja = adultos_que_bebem * litros_por_bebedor
        latas_cerveja = math.ceil(litros_cerveja / 0.350)
        fardos_12 = math.ceil(latas_cerveja / 12)

    # 3. CÁLCULO DE BEBIDAS NÃO ALCOÓLICAS
    # 1L de refrigerante/suco e 500ml de água por pessoa total
    litros_refri_suco = total_pessoas * 1.0
    garrafas_pet_2l = math.ceil(litros_refri_suco / 2.0)

    litros_agua = total_pessoas * 0.5
    garrafas_agua_1_5l = math.ceil(litros_agua / 1.5)

    # 4. CARVÃO
    # 1kg para cada 1kg a 1.2kg de carne
    kg_carvao = peso_total_carne_kg * 1.1
    sacos_carvao_4kg = math.ceil(kg_carvao / 4.0)

    # 5. GELO
    # 1 saco de 5kg para cada 3 a 4 pessoas
    sacos_gelo_5kg = math.ceil(total_pessoas / 3.5)
    if adultos_que_bebem > 0:
        sacos_gelo_5kg = max(sacos_gelo_5kg, math.ceil(latas_cerveja / 24) + 1)

    # 6. ACOMPANHAMENTOS & GUARIÇÕES
    # Pão de alho: ~2.5 unidades por pessoa
    paes_alho_unidades = math.ceil(total_pessoas * 2.5)
    pct_pao_alho = math.ceil(paes_alho_unidades / 5)

    # Queijo coalho: ~1.5 espetinhos por pessoa
    queijo_coalho_unidades = math.ceil(total_pessoas * 1.5)
    pct_queijo_coalho = math.ceil(queijo_coalho_unidades / 7)

    # Farofa pronta: 50g por pessoa
    farofa_gramas = total_pessoas * 50
    pct_farofa = math.ceil(farofa_gramas / 500)

    # Vinagrete: ~60g por pessoa
    vinagrete_gramas = total_pessoas * 60

    # Sal grosso: 1 pacote de 1kg para até 10kg de carne
    pct_sal_grosso = max(1, math.ceil(peso_total_carne_kg / 10.0))

    # FORMATAÇÃO DO CHECKLIST PARA WHATSAPP
    linhas = [
        "🍖 *LISTA DE COMPRAS PARA O CHURRASCO* 🍻",
        "",
        "📋 *Resumo do Evento:*",
        f"  • 🍻 Adultos que bebem: *{adultos_que_bebem}*",
        f"  • 🥤 Adultos que não bebem: *{adultos_que_nao_bebem}*",
        f"  • 🧒 Crianças: *{criancas_total}*",
        f"  • 👥 Total de convidados: *{total_pessoas} pessoas*",
        f"  • ⏱ Duração estimada: *{duracao} horas*",
        "",
        f"🥩 *CARNES & PROTEÍNAS* (Total: *{peso_total_carne_kg:.2f} kg*):",
    ]
    linhas.extend(distribuicao_carnes)
    linhas.append("")

    if adultos_que_bebem > 0:
        linhas.append("🍺 *BEBIDAS ALCOÓLICAS*:")
        linhas.append(f"  • Cerveja: *{litros_cerveja:.1f} L* (~*{latas_cerveja} latas* de 350ml | *{fardos_12} fardo(s)* de 12 latas)")
        linhas.append("")

    linhas.append("🥤 *BEBIDAS NÃO ALCOÓLICAS*:")
    linhas.append(f"  • Refrigerante / Suco: *{litros_refri_suco:.1f} L* (~*{garrafas_pet_2l} garrafas* de 2L)")
    linhas.append(f"  • Água Mineral: *{litros_agua:.1f} L* (~*{garrafas_agua_1_5l} garrafas* de 1.5L)")
    linhas.append("")

    linhas.append("🥖 *ACOMPANHAMENTOS & GUARNIÇÕES*:")
    linhas.append(f"  • Pão de Alho: *{paes_alho_unidades} unidades* (~*{pct_pao_alho} pacote(s)*)")
    linhas.append(f"  • Queijo Coalho: *{queijo_coalho_unidades} espetos* (~*{pct_queijo_coalho} pacote(s)*)")
    linhas.append(f"  • Farofa Pronta: *{farofa_gramas}g* (~*{pct_farofa} pacote(s)* de 500g)")
    linhas.append(f"  • Vinagrete: *~{vinagrete_gramas}g* (tomates, cebolas e cheiro-verde)")
    linhas.append(f"  • Sal Grosso: *{pct_sal_grosso} pacote(s)* de 1kg")
    linhas.append("")

    linhas.append("🔥 *INSUMOS & DESCARTÁVEIS*:")
    linhas.append(f"  • Carvão: *{kg_carvao:.1f} kg* (~*{sacos_carvao_4kg} saco(s)* de 4kg/5kg)")
    linhas.append(f"  • Gelo em Cubos/Escama: *{sacos_gelo_5kg} saco(s)* de 5kg")
    linhas.append("  • Descartáveis: Copos (300ml/500ml), pratinhos, garfos e guardanapos de papel")
    linhas.append("")
    linhas.append("💡 *Dica do Mestre Churrasqueiro:*")
    linhas.append("Acenda o carvão cerca de 45 minutos antes de colocar as primeiras carnes. O braseiro perfeito é vermelho e sem labaredas.")

    return "\n".join(linhas)
