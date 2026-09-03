import logging
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Normalização de Nomes e Abreviações das Unidades
UNIT_ALIASES = {
    # Distância
    "mi": "mi", "milha": "mi", "milhas": "mi", "mile": "mi", "miles": "mi",
    "km": "km", "quilometro": "km", "quilometros": "km", "quilômetro": "km", "quilômetros": "km", "kilometer": "km", "kilometers": "km",
    "m": "m", "metro": "m", "metros": "m", "meter": "m", "meters": "m",
    "cm": "cm", "centimetro": "cm", "centimetros": "cm", "centímetro": "cm", "centímetros": "cm", "centimeter": "cm", "centimeters": "cm",
    "ft": "ft", "pe": "ft", "pes": "ft", "pé": "ft", "pés": "ft", "foot": "ft", "feet": "ft",
    "in": "in", "pol": "in", "polegada": "in", "polegadas": "in", "inch": "in", "inches": "in",
    "yd": "yd", "jarda": "yd", "jardas": "yd", "yard": "yd", "yards": "yd",

    # Temperatura
    "f": "f", "fahrenheit": "f", "ºf": "f", "°f": "f",
    "c": "c", "celsius": "c", "centigrados": "c", "centígrados": "c", "ºc": "c", "°c": "c",
    "k": "k", "kelvin": "k", "kelvins": "k",

    # Peso / Massa
    "lb": "lb", "lbs": "lb", "libra": "lb", "libras": "lb", "pound": "lb", "pounds": "lb",
    "kg": "kg", "quilo": "kg", "quilos": "kg", "quilograma": "kg", "quilogramas": "kg", "kilo": "kg", "kilos": "kg", "kilogram": "kg", "kilograms": "kg",
    "g": "g", "grama": "g", "gramas": "g", "gram": "g", "grams": "g",
    "oz": "oz", "onca": "oz", "oncas": "oz", "onça": "oz", "onças": "oz", "ounce": "oz", "ounces": "oz",

    # Volume / Culinária
    "gal": "gal", "galao": "gal", "galão": "gal", "galoes": "gal", "galões": "gal", "gallon": "gal", "gallons": "gal",
    "l": "l", "litro": "l", "litros": "l", "liter": "l", "liters": "l",
    "ml": "ml", "mililitro": "ml", "mililitros": "ml", "milliliter": "ml", "milliliters": "ml",
    "fl oz": "fl_oz", "floz": "fl_oz", "fl_oz": "fl_oz", "onça fluida": "fl_oz", "onças fluidas": "fl_oz", "fluid ounce": "fl_oz", "fluid ounces": "fl_oz",
    "cup": "cup", "cups": "cup", "xicara": "cup", "xicaras": "cup", "xícara": "cup", "xícaras": "cup",
    "tbsp": "tbsp", "colher de sopa": "tbsp", "colheres de sopa": "tbsp", "colher sopa": "tbsp", "colheres sopa": "tbsp", "tablespoon": "tbsp", "tablespoons": "tbsp",
    "tsp": "tsp", "colher de cha": "tsp", "colheres de cha": "tsp", "colher de chá": "tsp", "colheres de chá": "tsp", "colher cha": "tsp", "colheres cha": "tsp", "colher chá": "tsp", "colheres chá": "tsp", "teaspoon": "tsp", "teaspoons": "tsp"
}

# Relações de base para cálculo determinístico
# Distância: base em metros (m)
DISTANCE_TO_M = {
    "m": 1.0,
    "km": 1000.0,
    "cm": 0.01,
    "mi": 1609.344,
    "ft": 0.3048,
    "in": 0.0254,
    "yd": 0.9144
}

# Massa: base em gramas (g)
MASS_TO_G = {
    "g": 1.0,
    "kg": 1000.0,
    "lb": 453.59237,
    "oz": 28.349523125
}

# Volume: base em mililitros (ml)
VOLUME_TO_ML = {
    "ml": 1.0,
    "l": 1000.0,
    "gal": 3785.411784,
    "fl_oz": 29.5735295625,
    "cup": 240.0,
    "tbsp": 15.0,
    "tsp": 5.0
}

UNIT_DISPLAY_NAMES = {
    "mi": "milhas", "km": "quilômetros", "m": "metros", "cm": "centímetros", "ft": "pés", "in": "polegadas", "yd": "jardas",
    "f": "°F", "c": "°C", "k": "K",
    "lb": "libras (lb)", "kg": "quilogramas (kg)", "g": "gramas (g)", "oz": "onças (oz)",
    "gal": "galões (gal)", "l": "litros (L)", "ml": "mililitros (ml)", "fl_oz": "onças fluidas (fl oz)",
    "cup": "xícaras (cups)", "tbsp": "colheres de sopa (tbsp)", "tsp": "colheres de chá (tsp)"
}


def _normalizar_unidade(unidade_str: str) -> Optional[str]:
    """Limpa e normaliza a string da unidade para o identificador canônico."""
    if not unidade_str:
        return None
    u = unidade_str.strip().lower()
    u = re.sub(r'[\'\"º°]', '', u)
    u = re.sub(r'\s+', ' ', u)
    return UNIT_ALIASES.get(u)


def _avaliar_destaque_forno(temp_celsius: float, temp_origem_f: Optional[float] = None) -> str:
    """Gera notas culinárias especializadas se a temperatura estiver na faixa de forno doméstico/profissional."""
    f_val = temp_origem_f if temp_origem_f is not None else (temp_celsius * 9 / 5 + 32)

    # Faixa culinária de forno: ~200°F a 550°F (~90°C a 290°C)
    if not (90 <= temp_celsius <= 290):
        return ""

    destaque = "\n\n🍳 **Destaque Culinário (Guia de Forno):**\n"
    if 115 <= temp_celsius <= 135 or (240 <= f_val <= 275):
        destaque += f"• **{f_val:.0f}°F (~{temp_celsius:.0f}°C):** Forno muito baixo / morno (ideal para merengues, suspiros, confit e desidratação)."
    elif 140 <= temp_celsius <= 165 or (280 <= f_val <= 330):
        destaque += f"• **{f_val:.0f}°F (~{temp_celsius:.0f}°C):** Forno baixo (ideal para pudins em banho-maria, carnes de cozimento lento e cheesecakes)."
    elif 170 <= temp_celsius <= 185 or (340 <= f_val <= 365):
        destaque += f"• **{f_val:.0f}°F (~{temp_celsius:.0f}°C):** Forno médio (a temperatura padrão clássica de confeitaria: bolos, tortas, biscoitos e assados gerais)."
    elif 186 <= temp_celsius <= 205 or (370 <= f_val <= 400):
        destaque += f"• **{f_val:.0f}°F (~{temp_celsius:.0f}°C):** Forno moderado a alto (ideal para dourar aves, peixes e massas folhadas)."
    elif 206 <= temp_celsius <= 230 or (405 <= f_val <= 445):
        destaque += f"• **{f_val:.0f}°F (~{temp_celsius:.0f}°C):** Forno bem alto (ideal para batatas rústicas crocantes, legumes tostados e carnes seladas)."
    elif 231 <= temp_celsius <= 280 or (450 <= f_val <= 550):
        destaque += f"• **{f_val:.0f}°F (~{temp_celsius:.0f}°C):** Forno muito quente / potência máxima (ideal para pizzas caseiras crocantes e pães rústicos de fermentação natural)."
    else:
        destaque += f"• **{f_val:.0f}°F (~{temp_celsius:.0f}°C):** Faixa de cozimento em forno culinário."

    return destaque


def _formatar_numero(valor: float) -> str:
    """Formata o número com alta precisão evitando notação científica desnecessária e zeros à direita."""
    if abs(valor) >= 1000:
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs(valor) >= 1:
        s = f"{valor:.4f}".rstrip('0').rstrip('.')
        return s.replace(".", ",")
    # Valores muito pequenos
    s = f"{valor:.6f}".rstrip('0').rstrip('.')
    return s.replace(".", ",")


def converter_unidade(valor: float, unidade_origem: str, unidade_destino: str) -> str:
    """
    Cálculo determinístico com alta precisão matemática (sem alucinações de LLM)
    para conversão de unidades nas categorias de distância, temperatura, peso/massa e volume/culinária.

    Args:
        valor (float): O valor numérico a ser convertido.
        unidade_origem (str): Unidade inicial (ex: 'mi', 'ft', 'in', 'yd', 'F', 'K', 'lb', 'oz', 'gal', 'fl oz', 'xícara', 'colher de sopa').
        unidade_destino (str): Unidade desejada (ex: 'km', 'm', 'cm', 'C', 'kg', 'g', 'L', 'ml').

    Returns:
        str: Resultado determinístico exato com explicação de cálculo e destaques práticos culinários.
    """
    u_orig = _normalizar_unidade(unidade_origem)
    u_dest = _normalizar_unidade(unidade_destino)

    if not u_orig:
        return f"Unidade de origem '{unidade_origem}' não reconhecida. Suportamos distância (mi, km, ft, in, yd, m, cm), temperatura (F, C, K), peso (lb, kg, oz, g) e culinária/volume (gal, L, fl oz, xícara/cup, colher de sopa/tbsp, ml)."

    if not u_dest:
        return f"Unidade de destino '{unidade_destino}' não reconhecida. Verifique se digitou corretamente a unidade de destino."

    if u_orig == u_dest:
        return f"As unidades de origem e destino são iguais ({u_orig}). O valor é exatamente {_formatar_numero(valor)}."

    # 1. TEMPERATURA
    temp_units = {"c", "f", "k"}
    if u_orig in temp_units or u_dest in temp_units:
        if u_orig not in temp_units or u_dest not in temp_units:
            return f"Incompatibilidade de dimensões: não é possível converter temperatura ({u_orig}) para uma unidade que não seja de temperatura ({u_dest})."

        # Converte origem para Celsius
        if u_orig == "c":
            celsius = valor
        elif u_orig == "f":
            celsius = (valor - 32.0) * 5.0 / 9.0
        elif u_orig == "k":
            celsius = valor - 273.15

        # De Celsius para destino
        if u_dest == "c":
            resultado = celsius
        elif u_dest == "f":
            resultado = (celsius * 9.0 / 5.0) + 32.0
        elif u_dest == "k":
            resultado = celsius + 273.15

        orig_f_val = valor if u_orig == "f" else (resultado if u_dest == "f" else None)
        destaque_forno = _avaliar_destaque_forno(celsius, orig_f_val)

        val_orig_fmt = _formatar_numero(valor)
        res_fmt = _formatar_numero(resultado)
        nome_orig = UNIT_DISPLAY_NAMES[u_orig]
        nome_dest = UNIT_DISPLAY_NAMES[u_dest]

        return (
            f"🌡️ **Conversão de Temperatura:**\n"
            f"**{val_orig_fmt} {nome_orig}** = **{res_fmt} {nome_dest}**"
            f"{destaque_forno}"
        )

    # 2. DISTÂNCIA
    if u_orig in DISTANCE_TO_M or u_dest in DISTANCE_TO_M:
        if u_orig not in DISTANCE_TO_M or u_dest not in DISTANCE_TO_M:
            return f"Incompatibilidade de dimensões: não é possível converter distância ({u_orig}) para {u_dest}."

        em_metros = valor * DISTANCE_TO_M[u_orig]
        resultado = em_metros / DISTANCE_TO_M[u_dest]

        val_orig_fmt = _formatar_numero(valor)
        res_fmt = _formatar_numero(resultado)
        nome_orig = UNIT_DISPLAY_NAMES[u_orig]
        nome_dest = UNIT_DISPLAY_NAMES[u_dest]

        return (
            f"📏 **Conversão de Distância:**\n"
            f"**{val_orig_fmt} {nome_orig}** = **{res_fmt} {nome_dest}**"
        )

    # 3. PESO / MASSA
    if u_orig in MASS_TO_G or u_dest in MASS_TO_G:
        if u_orig not in MASS_TO_G or u_dest not in MASS_TO_G:
            return f"Incompatibilidade de dimensões: não é possível converter peso/massa ({u_orig}) para {u_dest}."

        em_gramas = valor * MASS_TO_G[u_orig]
        resultado = em_gramas / MASS_TO_G[u_dest]

        val_orig_fmt = _formatar_numero(valor)
        res_fmt = _formatar_numero(resultado)
        nome_orig = UNIT_DISPLAY_NAMES[u_orig]
        nome_dest = UNIT_DISPLAY_NAMES[u_dest]

        return (
            f"⚖️ **Conversão de Peso / Massa:**\n"
            f"**{val_orig_fmt} {nome_orig}** = **{res_fmt} {nome_dest}**"
        )

    # 4. VOLUME / CULINÁRIA
    if u_orig in VOLUME_TO_ML or u_dest in VOLUME_TO_ML:
        if u_orig not in VOLUME_TO_ML or u_dest not in VOLUME_TO_ML:
            return f"Incompatibilidade de dimensões: não é possível converter volume ({u_orig}) para {u_dest}."

        em_ml = valor * VOLUME_TO_ML[u_orig]
        resultado = em_ml / VOLUME_TO_ML[u_dest]

        val_orig_fmt = _formatar_numero(valor)
        res_fmt = _formatar_numero(resultado)
        nome_orig = UNIT_DISPLAY_NAMES[u_orig]
        nome_dest = UNIT_DISPLAY_NAMES[u_dest]

        return (
            f"🧪 **Conversão de Volume / Culinária:**\n"
            f"**{val_orig_fmt} {nome_orig}** = **{res_fmt} {nome_dest}**"
        )

    return "Não foi possível realizar a conversão com as unidades especificadas."


def interpretar_e_converter(texto: str) -> str:
    """
    Parser inteligente que extrai valores e unidades de frases comuns do cotidiano e executa a conversão precisa.
    Exemplos:
    - '35 milhas em km'
    - '180 fahrenheit para celsius'
    - '150 libras em kg'
    - '350 F em C'
    - '2 xícaras em ml'
    - '3 colheres de sopa em ml'
    - '500g em oz'
    - 'quanto é 5 ft em cm?'
    """
    if not texto or not texto.strip():
        return "Por favor, forneça uma frase ou valor para conversão (ex: '35 milhas em km', '350 F para C', '150 libras em kg')."

    t = texto.strip().lower()

    # Normaliza separadores de decimal: 3,5 -> 3.5 se for número
    t_num_fixed = re.sub(r'(\d+),(\d+)', r'\1.\2', t)

    # Lista de preposições comuns de transição: 'em', 'para', 'to', 'em', 'pra', '->', '='
    # Padrão 1: "350 f para c", "35 milhas em km", "10.5 ft to m", "2 xicaras em ml"
    # Também suporta termos compostos como "colheres de sopa", "onça fluida", etc.
    padrao_frase = re.search(
        r'(\d+(?:\.\d+)?)\s*([a-záéíóúçº°\s_]+?)\s+(?:em|para|pra|to|equivale[am]?\s+a|->|=)\s+([a-záéíóúçº°\s_]+)',
        t_num_fixed
    )

    if padrao_frase:
        val_str, u_orig_raw, u_dest_raw = padrao_frase.groups()
        try:
            val = float(val_str)
            return converter_unidade(val, u_orig_raw.strip(), u_dest_raw.strip())
        except ValueError:
            pass

    # Padrão 2: "converter 350 f em c", "converta 5 ft para m"
    padrao_converter = re.search(
        r'(?:converter?|transformar?|passar?|quanto\s+(?:é|vale|da|dá))\s+(\d+(?:\.\d+)?)\s*([a-záéíóúçº°\s_]+?)\s+(?:em|para|pra|to)\s+([a-záéíóúçº°\s_]+)',
        t_num_fixed
    )
    if padrao_converter:
        val_str, u_orig_raw, u_dest_raw = padrao_converter.groups()
        try:
            val = float(val_str)
            return converter_unidade(val, u_orig_raw.strip(), u_dest_raw.strip())
        except ValueError:
            pass

    # Padrão 3: Valor colado na unidade: "500g em oz", "100km em mi", "350f em c"
    padrao_colado = re.search(
        r'(\d+(?:\.\d+)?)\s*([a-zº°]+)\s+(?:em|para|pra|to)\s+([a-záéíóúçº°\s_]+)',
        t_num_fixed
    )
    if padrao_colado:
        val_str, u_orig_raw, u_dest_raw = padrao_colado.groups()
        try:
            val = float(val_str)
            return converter_unidade(val, u_orig_raw.strip(), u_dest_raw.strip())
        except ValueError:
            pass

    return (
        "Não consegui identificar claramente os valores e as unidades para conversão.\n"
        "Exemplos de uso:\n"
        "• '35 milhas em km'\n"
        "• '350 fahrenheit para celsius'\n"
        "• '150 libras em kg'\n"
        "• '2 xícaras em ml'\n"
        "• '3 colheres de sopa em ml'\n"
        "• '500g em oz'"
    )
