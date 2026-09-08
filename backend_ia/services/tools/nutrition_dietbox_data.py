import unicodedata
import re
from typing import Dict, List, Optional, Any

GRUPOS_ALIMENTARES: Dict[str, Dict[str, Any]] = {
    "carboidratos": {
        "nome": "Carboidratos",
        "media_calorica_kcal": 150.0,
        "descricao": "Fontes de energia primária, ricos em amido e fibras."
    },
    "carnes_e_ovos": {
        "nome": "Carnes e Ovos",
        "media_calorica_kcal": 190.0,
        "descricao": "Fontes nobres de proteína de alto valor biológico e ferro."
    },
    "frutas": {
        "nome": "Frutas",
        "media_calorica_kcal": 70.0,
        "descricao": "Fontes naturais de frutose, fibras solúveis, vitaminas e minerais."
    },
    "laticinios": {
        "nome": "Laticínios",
        "media_calorica_kcal": 120.0,
        "descricao": "Fontes ricas em cálcio, proteínas lácteas e fósforo."
    },
    "legumes_e_verduras": {
        "nome": "Legumes e Verduras",
        "media_calorica_kcal": 15.0,
        "descricao": "Alimentos de baixa densidade calórica, ricos em micronutrientes e água."
    },
    "leguminosas": {
        "nome": "Leguminosas",
        "media_calorica_kcal": 55.0,
        "descricao": "Grãos ricos em fibras, amido resistente e proteínas vegetais."
    },
    "oleos_e_gorduras": {
        "nome": "Óleos e Gorduras",
        "media_calorica_kcal": 73.0,
        "descricao": "Lipídios essenciais para síntese hormonal e absorção de vitaminas lipossolúveis."
    }
}

ALIMENTOS_DIETBOX: List[Dict[str, Any]] = [
    # ----------------- CARBOIDRATOS (150 Kcal) -----------------
    {
        "nome_oficial": "Arroz Branco Cozido",
        "grupo": "carboidratos",
        "medida_caseira": "4 Colheres de Sopa",
        "quantidade_g_ml": 100.0,
        "unidade": "g",
        "aliases": ["arroz branco", "arroz branco cozido", "arroz"]
    },
    {
        "nome_oficial": "Arroz Integral Cozido",
        "grupo": "carboidratos",
        "medida_caseira": "4 Colheres de Sopa",
        "quantidade_g_ml": 100.0,
        "unidade": "g",
        "aliases": ["arroz integral", "arroz integral cozido"]
    },
    {
        "nome_oficial": "Batata Doce Cozida",
        "grupo": "carboidratos",
        "medida_caseira": "2 Pedaços Médios",
        "quantidade_g_ml": 200.0,
        "unidade": "g",
        "aliases": ["batata doce", "batata doce cozida"]
    },
    {
        "nome_oficial": "Batata Inglesa Cozida",
        "grupo": "carboidratos",
        "medida_caseira": "1 Unidade e 1/2",
        "quantidade_g_ml": 300.0,
        "unidade": "g",
        "aliases": ["batata inglesa", "batata inglesa cozida", "batata cozida", "batata"]
    },
    {
        "nome_oficial": "Farinha de Mandioca",
        "grupo": "carboidratos",
        "medida_caseira": "2 Colheres de Sopa",
        "quantidade_g_ml": 45.0,
        "unidade": "g",
        "aliases": ["farinha de mandioca", "farofa de mandioca"]
    },
    {
        "nome_oficial": "Macarrão Cozido",
        "grupo": "carboidratos",
        "medida_caseira": "1 Pegador",
        "quantidade_g_ml": 110.0,
        "unidade": "g",
        "aliases": ["macarrao", "macarrao cozido", "massa"]
    },
    {
        "nome_oficial": "Mandioca Cozida",
        "grupo": "carboidratos",
        "medida_caseira": "3 Unidades Pequenas",
        "quantidade_g_ml": 120.0,
        "unidade": "g",
        "aliases": ["mandioca", "mandioca cozida", "aipim", "macaxeira"]
    },
    {
        "nome_oficial": "Pão de Centeio",
        "grupo": "carboidratos",
        "medida_caseira": "2 Fatias",
        "quantidade_g_ml": 50.0,
        "unidade": "g",
        "aliases": ["pao de centeio", "pao centeio"]
    },
    {
        "nome_oficial": "Pão de Forma Tradicional",
        "grupo": "carboidratos",
        "medida_caseira": "2 Fatias",
        "quantidade_g_ml": 50.0,
        "unidade": "g",
        "aliases": ["pao de forma", "pao de forma tradicional", "pao de sanduiche"]
    },
    {
        "nome_oficial": "Pão de Queijo",
        "grupo": "carboidratos",
        "medida_caseira": "4 Unidades Pequenas",
        "quantidade_g_ml": 40.0,
        "unidade": "g",
        "aliases": ["pao de queijo"]
    },
    {
        "nome_oficial": "Pão Francês",
        "grupo": "carboidratos",
        "medida_caseira": "1 Unidade Média",
        "quantidade_g_ml": 50.0,
        "unidade": "g",
        "aliases": ["pao frances", "pao de sal", "cacetinho"]
    },
    {
        "nome_oficial": "Polenta",
        "grupo": "carboidratos",
        "medida_caseira": "4 Colheres de Sopa",
        "quantidade_g_ml": 170.0,
        "unidade": "g",
        "aliases": ["polenta", "polenta cozida", "angu"]
    },
    {
        "nome_oficial": "Purê de Batata",
        "grupo": "carboidratos",
        "medida_caseira": "3 Colheres de Sopa",
        "quantidade_g_ml": 135.0,
        "unidade": "g",
        "aliases": ["pure de batata", "pure"]
    },

    # ----------------- CARNES E OVOS (190 Kcal) -----------------
    {
        "nome_oficial": "Atum em Lata",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "4 Colheres de Sopa",
        "quantidade_g_ml": 160.0,
        "unidade": "g",
        "aliases": ["atum", "atum em lata", "atum enlatado"]
    },
    {
        "nome_oficial": "Bife de Fígado",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "1 Unidade Média",
        "quantidade_g_ml": 90.0,
        "unidade": "g",
        "aliases": ["figado", "bife de figado", "figado bovino"]
    },
    {
        "nome_oficial": "Bife Grelhado",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "1 Unidade Média",
        "quantidade_g_ml": 100.0,
        "unidade": "g",
        "aliases": ["bife", "bife grelhado", "carne bovina grelhada"]
    },
    {
        "nome_oficial": "Camarão Cozido",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "15 Unidades",
        "quantidade_g_ml": 170.0,
        "unidade": "g",
        "aliases": ["camarao", "camarao cozido"]
    },
    {
        "nome_oficial": "Carne Assada",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "1 Fatia Média",
        "quantidade_g_ml": 100.0,
        "unidade": "g",
        "aliases": ["carne assada"]
    },
    {
        "nome_oficial": "Carne Moída Refogada",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "5 Colheres de Sopa",
        "quantidade_g_ml": 90.0,
        "unidade": "g",
        "aliases": ["carne moida", "carne moida refogada"]
    },
    {
        "nome_oficial": "Carne Seca",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "2 Unidades Pequenas",
        "quantidade_g_ml": 40.0,
        "unidade": "g",
        "aliases": ["carne seca", "charque", "jabá"]
    },
    {
        "nome_oficial": "Costela Bovina Assada",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "1 Pedaço",
        "quantidade_g_ml": 45.0,
        "unidade": "g",
        "aliases": ["costela", "costela bovina", "costela assada"]
    },
    {
        "nome_oficial": "Coxa Ou Sobrecoxa sem pele",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "2 Unidades",
        "quantidade_g_ml": 75.0,
        "unidade": "g",
        "aliases": ["coxa de frango", "sobrecoxa", "coxa ou sobrecoxa sem pele"]
    },
    {
        "nome_oficial": "Filé de Frango Grelhado",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "1 Filé Médio",
        "quantidade_g_ml": 120.0,
        "unidade": "g",
        "aliases": ["frango grelhado", "file de frango", "frango", "file de frango grelhado"]
    },
    {
        "nome_oficial": "Hamburguer Grelhado",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "1 Unidade",
        "quantidade_g_ml": 100.0,
        "unidade": "g",
        "aliases": ["hamburguer", "hamburguer grelhado"]
    },
    {
        "nome_oficial": "Linguiça de Porco Grelhada",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "4 Fatias Finas",
        "quantidade_g_ml": 60.0,
        "unidade": "g",
        "aliases": ["linguica", "linguica de porco", "linguica grelhada"]
    },
    {
        "nome_oficial": "Lombo de Porco Assado",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "2 Fatias Finas",
        "quantidade_g_ml": 90.0,
        "unidade": "g",
        "aliases": ["lombo", "lombo de porco", "lombo assado"]
    },
    {
        "nome_oficial": "Ovo Mexido/Cozido",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "3 Unidades",
        "quantidade_g_ml": 150.0,
        "unidade": "g",
        "aliases": ["ovo", "ovos", "ovo mexido", "ovo cozido", "ovo mexido/cozido"]
    },
    {
        "nome_oficial": "Peito de frango assado",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "1 Pedaço Médio",
        "quantidade_g_ml": 100.0,
        "unidade": "g",
        "aliases": ["peito de frango", "peito de frango assado"]
    },
    {
        "nome_oficial": "Peixe Assado",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "1 Filé",
        "quantidade_g_ml": 150.0,
        "unidade": "g",
        "aliases": ["peixe", "peixe assado", "file de peixe"]
    },
    {
        "nome_oficial": "Sardinha em Conserva",
        "grupo": "carnes_e_ovos",
        "medida_caseira": "1 Unidade",
        "quantidade_g_ml": 60.0,
        "unidade": "g",
        "aliases": ["sardinha", "sardinha em conserva", "sardinha em lata"]
    },

    # ----------------- FRUTAS (70 Kcal) -----------------
    {"nome_oficial": "Abacate", "grupo": "frutas", "medida_caseira": "2 Colheres de Sopa", "quantidade_g_ml": 64.0, "unidade": "g", "aliases": ["abacate"]},
    {"nome_oficial": "Abacaxi", "grupo": "frutas", "medida_caseira": "2 Fatias", "quantidade_g_ml": 150.0, "unidade": "g", "aliases": ["abacaxi"]},
    {"nome_oficial": "Acerola", "grupo": "frutas", "medida_caseira": "20 Unidades", "quantidade_g_ml": 240.0, "unidade": "g", "aliases": ["acerola"]},
    {"nome_oficial": "Ameixa-preta Seca", "grupo": "frutas", "medida_caseira": "6 Unidades", "quantidade_g_ml": 30.0, "unidade": "g", "aliases": ["ameixa preta", "ameixa preta seca", "ameixa seca"]},
    {"nome_oficial": "Ameixa-vermelha", "grupo": "frutas", "medida_caseira": "4 Unidades", "quantidade_g_ml": 168.0, "unidade": "g", "aliases": ["ameixa vermelha", "ameixa"]},
    {"nome_oficial": "Banana Nanica", "grupo": "frutas", "medida_caseira": "1 Unidade", "quantidade_g_ml": 70.0, "unidade": "g", "aliases": ["banana nanica", "banana d'agua"]},
    {"nome_oficial": "Banana Prata", "grupo": "frutas", "medida_caseira": "1 Unidade", "quantidade_g_ml": 85.0, "unidade": "g", "aliases": ["banana prata", "banana"]},
    {"nome_oficial": "Caju", "grupo": "frutas", "medida_caseira": "2 Unidades e Meia", "quantidade_g_ml": 150.0, "unidade": "g", "aliases": ["caju"]},
    {"nome_oficial": "Caqui", "grupo": "frutas", "medida_caseira": "1 Unidade", "quantidade_g_ml": 110.0, "unidade": "g", "aliases": ["caqui"]},
    {"nome_oficial": "Carambola", "grupo": "frutas", "medida_caseira": "2 Unidades", "quantidade_g_ml": 140.0, "unidade": "g", "aliases": ["carambola"]},
    {"nome_oficial": "Cereja", "grupo": "frutas", "medida_caseira": "16 Unidades", "quantidade_g_ml": 112.0, "unidade": "g", "aliases": ["cereja"]},
    {"nome_oficial": "Damasco Seco", "grupo": "frutas", "medida_caseira": "4 Unidades", "quantidade_g_ml": 30.0, "unidade": "g", "aliases": ["damasco", "damasco seco"]},
    {"nome_oficial": "Fruta do Conde", "grupo": "frutas", "medida_caseira": "1 Unidade", "quantidade_g_ml": 75.0, "unidade": "g", "aliases": ["fruta do conde", "ata", "pinha"]},
    {"nome_oficial": "Goiaba", "grupo": "frutas", "medida_caseira": "2 Unidades Pequenas", "quantidade_g_ml": 100.0, "unidade": "g", "aliases": ["goiaba"]},
    {"nome_oficial": "Jabuticaba", "grupo": "frutas", "medida_caseira": "20 Unidades", "quantidade_g_ml": 100.0, "unidade": "g", "aliases": ["jabuticaba", "jaboticaba"]},
    {"nome_oficial": "Jaca", "grupo": "frutas", "medida_caseira": "6 Bagos", "quantidade_g_ml": 72.0, "unidade": "g", "aliases": ["jaca"]},
    {"nome_oficial": "Kiwi", "grupo": "frutas", "medida_caseira": "2 Unidades Pequenas", "quantidade_g_ml": 115.0, "unidade": "g", "aliases": ["kiwi", "quivi"]},
    {"nome_oficial": "Laranja", "grupo": "frutas", "medida_caseira": "1 Unidade Média", "quantidade_g_ml": 160.0, "unidade": "g", "aliases": ["laranja"]},
    {"nome_oficial": "Limão", "grupo": "frutas", "medida_caseira": "4 Unidades", "quantidade_g_ml": 250.0, "unidade": "g", "aliases": ["limao"]},
    {"nome_oficial": "Maçã", "grupo": "frutas", "medida_caseira": "1 Unidade", "quantidade_g_ml": 130.0, "unidade": "g", "aliases": ["maca"]},
    {"nome_oficial": "Mamão Formosa", "grupo": "frutas", "medida_caseira": "1 Fatia", "quantidade_g_ml": 160.0, "unidade": "g", "aliases": ["mamao formosa", "mamao"]},
    {"nome_oficial": "Mamão Papaia", "grupo": "frutas", "medida_caseira": "1/2 Unidade", "quantidade_g_ml": 190.0, "unidade": "g", "aliases": ["mamao papaia", "papaia"]},
    {"nome_oficial": "Manga", "grupo": "frutas", "medida_caseira": "1 Unidade", "quantidade_g_ml": 110.0, "unidade": "g", "aliases": ["manga"]},
    {"nome_oficial": "Maracujá", "grupo": "frutas", "medida_caseira": "1 Copo", "quantidade_g_ml": 65.0, "unidade": "ml", "aliases": ["maracuja"]},
    {"nome_oficial": "Melancia", "grupo": "frutas", "medida_caseira": "1 Fatia", "quantidade_g_ml": 220.0, "unidade": "g", "aliases": ["melancia"]},
    {"nome_oficial": "Melão", "grupo": "frutas", "medida_caseira": "2 Fatias", "quantidade_g_ml": 200.0, "unidade": "g", "aliases": ["melao"]},
    {"nome_oficial": "Morango", "grupo": "frutas", "medida_caseira": "15 Unidades", "quantidade_g_ml": 240.0, "unidade": "g", "aliases": ["morango", "morangos"]},
    {"nome_oficial": "Nectarina", "grupo": "frutas", "medida_caseira": "3 Unidades", "quantidade_g_ml": 180.0, "unidade": "g", "aliases": ["nectarina"]},
    {"nome_oficial": "Pêra", "grupo": "frutas", "medida_caseira": "1 Unidade", "quantidade_g_ml": 130.0, "unidade": "g", "aliases": ["pera"]},
    {"nome_oficial": "Pêssego", "grupo": "frutas", "medida_caseira": "3 Unidades", "quantidade_g_ml": 180.0, "unidade": "g", "aliases": ["pessego"]},
    {"nome_oficial": "Tangerina", "grupo": "frutas", "medida_caseira": "1 Unidade", "quantidade_g_ml": 135.0, "unidade": "g", "aliases": ["tangerina", "mexerica", "bergamota"]},
    {"nome_oficial": "Uva", "grupo": "frutas", "medida_caseira": "15 Unidades", "quantidade_g_ml": 100.0, "unidade": "g", "aliases": ["uva", "uvas"]},
    {"nome_oficial": "Uva Passa", "grupo": "frutas", "medida_caseira": "1 e 1/2 Colher de Sopa", "quantidade_g_ml": 25.0, "unidade": "g", "aliases": ["uva passa", "passas"]},
    {"nome_oficial": "Uva Rubi", "grupo": "frutas", "medida_caseira": "1 Cacho Médio", "quantidade_g_ml": 150.0, "unidade": "g", "aliases": ["uva rubi"]},

    # ----------------- LATICÍNIOS (120 Kcal) -----------------
    {"nome_oficial": "Coalhada", "grupo": "laticinios", "medida_caseira": "1 Copo Americano", "quantidade_g_ml": 160.0, "unidade": "g", "aliases": ["coalhada"]},
    {"nome_oficial": "Iogurte Desnatado de Frutas", "grupo": "laticinios", "medida_caseira": "1 Copo Pequeno", "quantidade_g_ml": 120.0, "unidade": "g", "aliases": ["iogurte desnatado de frutas", "iogurte de frutas"]},
    {"nome_oficial": "Iogurte Desnatado Natural", "grupo": "laticinios", "medida_caseira": "1 Copo de Requeijão", "quantidade_g_ml": 200.0, "unidade": "g", "aliases": ["iogurte desnatado natural", "iogurte desnatado"]},
    {"nome_oficial": "Iogurte Integral Natural", "grupo": "laticinios", "medida_caseira": "1 Copo de Requeijão", "quantidade_g_ml": 200.0, "unidade": "g", "aliases": ["iogurte natural", "iogurte integral natural", "iogurte integral"]},
    {"nome_oficial": "Leite de Cabra Integral", "grupo": "laticinios", "medida_caseira": "2 Copos", "quantidade_g_ml": 190.0, "unidade": "ml", "aliases": ["leite de cabra"]},
    {"nome_oficial": "Leite Desnatado Longa Vida", "grupo": "laticinios", "medida_caseira": "2 Copos Americanos", "quantidade_g_ml": 350.0, "unidade": "ml", "aliases": ["leite desnatado", "leite desnatado longa vida"]},
    {"nome_oficial": "Leite em Pó Desnatado", "grupo": "laticinios", "medida_caseira": "3 Colheres de Sopa", "quantidade_g_ml": 35.0, "unidade": "g", "aliases": ["leite em po desnatado", "leite ninho desnatado"]},
    {"nome_oficial": "Leite em Pó Integral", "grupo": "laticinios", "medida_caseira": "2 Colheres de Sopa Rasas", "quantidade_g_ml": 25.0, "unidade": "g", "aliases": ["leite em po integral", "leite em po"]},
    {"nome_oficial": "Leite Integral Longa Vida", "grupo": "laticinios", "medida_caseira": "1 Copo Grande", "quantidade_g_ml": 200.0, "unidade": "ml", "aliases": ["leite integral", "leite integral longa vida", "leite"]},
    {"nome_oficial": "Leite Semi-desnatado Longa Vida", "grupo": "laticinios", "medida_caseira": "1 Copo Grande", "quantidade_g_ml": 300.0, "unidade": "ml", "aliases": ["leite semi-desnatado", "leite semidesnatado"]},
    {"nome_oficial": "Queijo Gorgonzola", "grupo": "laticinios", "medida_caseira": "1 Fatia", "quantidade_g_ml": 30.0, "unidade": "g", "aliases": ["gorgonzola", "queijo gorgonzola"]},
    {"nome_oficial": "Queijo Minas", "grupo": "laticinios", "medida_caseira": "2 Fatias", "quantidade_g_ml": 50.0, "unidade": "g", "aliases": ["queijo minas", "queijo branco", "queijo frescal"]},
    {"nome_oficial": "Queijo Mussarela", "grupo": "laticinios", "medida_caseira": "2 e 1/2 Fatias", "quantidade_g_ml": 37.0, "unidade": "g", "aliases": ["mussarela", "queijo mussarela", "mucarela"]},
    {"nome_oficial": "Queijo Parmesão Ralado", "grupo": "laticinios", "medida_caseira": "3 colheres de sopa", "quantidade_g_ml": 30.0, "unidade": "g", "aliases": ["queijo parmesao", "parmesao", "parmesao ralado"]},
    {"nome_oficial": "Queijo Prato", "grupo": "laticinios", "medida_caseira": "2 Fatias", "quantidade_g_ml": 40.0, "unidade": "g", "aliases": ["queijo prato"]},
    {"nome_oficial": "Queijo Provolone", "grupo": "laticinios", "medida_caseira": "1 e 1/2 Fatia", "quantidade_g_ml": 35.0, "unidade": "g", "aliases": ["provolone", "queijo provolone"]},
    {"nome_oficial": "Ricota", "grupo": "laticinios", "medida_caseira": "2 Fatias", "quantidade_g_ml": 70.0, "unidade": "g", "aliases": ["ricota", "queijo ricota"]},

    # ----------------- LEGUMES E VERDURAS (15 Kcal) -----------------
    {"nome_oficial": "Abóbora Cozida", "grupo": "legumes_e_verduras", "medida_caseira": "2 Colheres de Sopa", "quantidade_g_ml": 75.0, "unidade": "g", "aliases": ["abobora", "abobora cozida", "jerimum"]},
    {"nome_oficial": "Abobrinha Cozida", "grupo": "legumes_e_verduras", "medida_caseira": "4 Rodelas", "quantidade_g_ml": 72.0, "unidade": "g", "aliases": ["abobrinha", "abobrinha cozida"]},
    {"nome_oficial": "Acelga Cozida", "grupo": "legumes_e_verduras", "medida_caseira": "À vontade", "quantidade_g_ml": 120.0, "unidade": "g", "aliases": ["acelga cozida"]},
    {"nome_oficial": "Acelga Crua Picada", "grupo": "legumes_e_verduras", "medida_caseira": "À vontade", "quantidade_g_ml": 90.0, "unidade": "g", "aliases": ["acelga crua", "acelga"]},
    {"nome_oficial": "Agrião", "grupo": "legumes_e_verduras", "medida_caseira": "À vontade", "quantidade_g_ml": 70.0, "unidade": "g", "aliases": ["agriao"]},
    {"nome_oficial": "Aipo Cru", "grupo": "legumes_e_verduras", "medida_caseira": "À vontade", "quantidade_g_ml": 75.0, "unidade": "g", "aliases": ["aipo", "aipo cru", "salso"]},
    {"nome_oficial": "Alcachofra Cozida", "grupo": "legumes_e_verduras", "medida_caseira": "1/4 de Unidade", "quantidade_g_ml": 30.0, "unidade": "g", "aliases": ["alcachofra"]},
    {"nome_oficial": "Alface", "grupo": "legumes_e_verduras", "medida_caseira": "À vontade", "quantidade_g_ml": 120.0, "unidade": "g", "aliases": ["alface"]},
    {"nome_oficial": "Almeirão", "grupo": "legumes_e_verduras", "medida_caseira": "5 Folhas", "quantidade_g_ml": 25.0, "unidade": "g", "aliases": ["almeirao"]},
    {"nome_oficial": "Aspargo Cru", "grupo": "legumes_e_verduras", "medida_caseira": "6 Unidades", "quantidade_g_ml": 65.0, "unidade": "g", "aliases": ["aspargo cru", "aspargo"]},
    {"nome_oficial": "Aspargo em Conserva", "grupo": "legumes_e_verduras", "medida_caseira": "8 Unidades", "quantidade_g_ml": 75.0, "unidade": "g", "aliases": ["aspargo em conserva"]},
    {"nome_oficial": "Berinjela Cozida", "grupo": "legumes_e_verduras", "medida_caseira": "1 Colher de Servir", "quantidade_g_ml": 60.0, "unidade": "g", "aliases": ["berinjela", "berinjela cozida"]},
    {"nome_oficial": "Beterraba Cozida", "grupo": "legumes_e_verduras", "medida_caseira": "3 Fatias", "quantidade_g_ml": 35.0, "unidade": "g", "aliases": ["beterraba cozida", "beterraba"]},
    {"nome_oficial": "Beterraba Crua Ralada", "grupo": "legumes_e_verduras", "medida_caseira": "2 Colheres de Sopa", "quantidade_g_ml": 40.0, "unidade": "g", "aliases": ["beterraba crua", "beterraba ralada"]},
    {"nome_oficial": "Brócolis Cozido", "grupo": "legumes_e_verduras", "medida_caseira": "1 Ramo", "quantidade_g_ml": 60.0, "unidade": "g", "aliases": ["brocolis", "brocolis cozido"]},
    {"nome_oficial": "Broto de Alfafa Cru", "grupo": "legumes_e_verduras", "medida_caseira": "À vontade", "quantidade_g_ml": 65.0, "unidade": "g", "aliases": ["broto de alfafa", "alfafa"]},
    {"nome_oficial": "Broto de Feijão Cozido", "grupo": "legumes_e_verduras", "medida_caseira": "1/2 Colher de Servir", "quantidade_g_ml": 27.0, "unidade": "g", "aliases": ["broto de feijao", "moyashi"]},
    {"nome_oficial": "Cenoura Cozida", "grupo": "legumes_e_verduras", "medida_caseira": "1 Unidade Pequena", "quantidade_g_ml": 45.0, "unidade": "g", "aliases": ["cenoura cozida"]},
    {"nome_oficial": "Cenoura Crua Picada", "grupo": "legumes_e_verduras", "medida_caseira": "1 Unidade Pequena", "quantidade_g_ml": 40.0, "unidade": "g", "aliases": ["cenoura", "cenoura crua", "cenoura picada"]},
    {"nome_oficial": "Chuchu Cozido", "grupo": "legumes_e_verduras", "medida_caseira": "3 Colheres de Sopa", "quantidade_g_ml": 60.0, "unidade": "g", "aliases": ["chuchu", "chuchu cozido"]},
    {"nome_oficial": "Couve", "grupo": "legumes_e_verduras", "medida_caseira": "2 Folhas", "quantidade_g_ml": 60.0, "unidade": "g", "aliases": ["couve", "couve manteiga"]},
    {"nome_oficial": "Couve-Flor Cozido", "grupo": "legumes_e_verduras", "medida_caseira": "1 Ramo", "quantidade_g_ml": 70.0, "unidade": "g", "aliases": ["couve flor", "couve-flor", "couve flor cozida"]},
    {"nome_oficial": "Escarola", "grupo": "legumes_e_verduras", "medida_caseira": "À vontade", "quantidade_g_ml": 30.0, "unidade": "g", "aliases": ["escarola"]},
    {"nome_oficial": "Espinafre Cozido", "grupo": "legumes_e_verduras", "medida_caseira": "3 Colheres de Sopa", "quantidade_g_ml": 70.0, "unidade": "g", "aliases": ["espinafre", "espinafre cozido"]},
    {"nome_oficial": "Jiló Cozido", "grupo": "legumes_e_verduras", "medida_caseira": "1 Colher de Sopa", "quantidade_g_ml": 65.0, "unidade": "g", "aliases": ["jilo", "jilo cozido"]},
    {"nome_oficial": "Mostarda", "grupo": "legumes_e_verduras", "medida_caseira": "À vontade", "quantidade_g_ml": 100.0, "unidade": "g", "aliases": ["folha de mostarda", "mostarda verdura"]},
    {"nome_oficial": "Palmito em Conserva", "grupo": "legumes_e_verduras", "medida_caseira": "1 Unidade Pequena", "quantidade_g_ml": 55.0, "unidade": "g", "aliases": ["palmito", "palmito em conserva"]},
    {"nome_oficial": "Pepino", "grupo": "legumes_e_verduras", "medida_caseira": "1 Unidade", "quantidade_g_ml": 100.0, "unidade": "g", "aliases": ["pepino"]},
    {"nome_oficial": "Pimentão Cru", "grupo": "legumes_e_verduras", "medida_caseira": "1 Unidade", "quantidade_g_ml": 75.0, "unidade": "g", "aliases": ["pimentao", "pimentao cru"]},
    {"nome_oficial": "Quiabo Cozido", "grupo": "legumes_e_verduras", "medida_caseira": "2 Colheres de Sopa", "quantidade_g_ml": 80.0, "unidade": "g", "aliases": ["quiabo", "quiabo cozido"]},
    {"nome_oficial": "Rabanete", "grupo": "legumes_e_verduras", "medida_caseira": "4 Unidades", "quantidade_g_ml": 100.0, "unidade": "g", "aliases": ["rabanete"]},
    {"nome_oficial": "Repolho Cozido", "grupo": "legumes_e_verduras", "medida_caseira": "4 Colheres de Sopa", "quantidade_g_ml": 75.0, "unidade": "g", "aliases": ["repolho cozido"]},
    {"nome_oficial": "Repolho Cru", "grupo": "legumes_e_verduras", "medida_caseira": "6 Colheres de Sopa", "quantidade_g_ml": 60.0, "unidade": "g", "aliases": ["repolho", "repolho cru"]},
    {"nome_oficial": "Rúcula", "grupo": "legumes_e_verduras", "medida_caseira": "À vontade", "quantidade_g_ml": 70.0, "unidade": "g", "aliases": ["rucula"]},
    {"nome_oficial": "Salsão", "grupo": "legumes_e_verduras", "medida_caseira": "5 Colheres de Sopa Picado", "quantidade_g_ml": 95.0, "unidade": "g", "aliases": ["salsao", "salsao picado"]},
    {"nome_oficial": "Tomate", "grupo": "legumes_e_verduras", "medida_caseira": "5 Fatias", "quantidade_g_ml": 75.0, "unidade": "g", "aliases": ["tomate"]},
    {"nome_oficial": "Tomate Cereja", "grupo": "legumes_e_verduras", "medida_caseira": "7 Unidades", "quantidade_g_ml": 70.0, "unidade": "g", "aliases": ["tomate cereja"]},
    {"nome_oficial": "Vagem", "grupo": "legumes_e_verduras", "medida_caseira": "2 Colheres de Sopa", "quantidade_g_ml": 40.0, "unidade": "g", "aliases": ["vagem", "vagem cozida"]},

    # ----------------- LEGUMINOSAS (55 Kcal) -----------------
    {"nome_oficial": "Ervilha Em Conserva", "grupo": "leguminosas", "medida_caseira": "3 Colheres de Sopa", "quantidade_g_ml": 80.0, "unidade": "g", "aliases": ["ervilha", "ervilha em conserva", "ervilha em lata"]},
    {"nome_oficial": "Feijão Branco Cozido", "grupo": "leguminosas", "medida_caseira": "1 Colher de Sopa", "quantidade_g_ml": 35.0, "unidade": "g", "aliases": ["feijao branco", "feijao branco cozido"]},
    {"nome_oficial": "Feijão Preto Cozido", "grupo": "leguminosas", "medida_caseira": "1 Concha", "quantidade_g_ml": 65.0, "unidade": "g", "aliases": ["feijao", "feijao preto", "feijao preto cozido", "feijao carioca"]},
    {"nome_oficial": "Grão de Bico Cozido", "grupo": "leguminosas", "medida_caseira": "1 Colher de Sopa e Meia", "quantidade_g_ml": 30.0, "unidade": "g", "aliases": ["grao de bico", "grao de bico cozido"]},
    {"nome_oficial": "Lentilha Cozida", "grupo": "leguminosas", "medida_caseira": "1 Concha Pequena", "quantidade_g_ml": 60.0, "unidade": "g", "aliases": ["lentilha", "lentilha cozida"]},
    {"nome_oficial": "Proteína de Soja", "grupo": "leguminosas", "medida_caseira": "1 Colher de Sopa", "quantidade_g_ml": 30.0, "unidade": "g", "aliases": ["proteina de soja", "soja", "pts"]},

    # ----------------- ÓLEOS E GORDURAS (73 Kcal) -----------------
    {"nome_oficial": "Azeite de Dendê", "grupo": "oleos_e_gorduras", "medida_caseira": "1/2 Colher de Sopa", "quantidade_g_ml": 9.2, "unidade": "g", "aliases": ["azeite de dende", "dende"]},
    {"nome_oficial": "Azeite de Oliva", "grupo": "oleos_e_gorduras", "medida_caseira": "1 Colher de Sopa", "quantidade_g_ml": 8.0, "unidade": "g", "aliases": ["azeite", "azeite de oliva", "azeite extravirgem"]},
    {"nome_oficial": "Bacon (gordura)", "grupo": "oleos_e_gorduras", "medida_caseira": "1 Fatia", "quantidade_g_ml": 15.0, "unidade": "g", "aliases": ["bacon", "bacon gordura"]},
    {"nome_oficial": "Banha de Porco", "grupo": "oleos_e_gorduras", "medida_caseira": "1 Colher de Sopa Rasa", "quantidade_g_ml": 8.0, "unidade": "g", "aliases": ["banha", "banha de porco"]},
    {"nome_oficial": "Creme Vegetal/Margarina", "grupo": "oleos_e_gorduras", "medida_caseira": "1 Colher de Sopa", "quantidade_g_ml": 10.0, "unidade": "g", "aliases": ["margarina", "creme vegetal"]},
    {"nome_oficial": "Manteiga", "grupo": "oleos_e_gorduras", "medida_caseira": "1 Colher de Sopa", "quantidade_g_ml": 10.0, "unidade": "g", "aliases": ["manteiga"]},
    {"nome_oficial": "Óleo Vegetal de Canola", "grupo": "oleos_e_gorduras", "medida_caseira": "1 Colher de Sopa", "quantidade_g_ml": 8.0, "unidade": "g", "aliases": ["oleo de canola", "oleo vegetal de canola"]},
    {"nome_oficial": "Óleo Vegetal de Girassol", "grupo": "oleos_e_gorduras", "medida_caseira": "1 Colher de Sopa", "quantidade_g_ml": 8.0, "unidade": "g", "aliases": ["oleo de girassol", "oleo vegetal de girassol"]},
    {"nome_oficial": "Óleo Vegetal de Milho", "grupo": "oleos_e_gorduras", "medida_caseira": "1 Colher de Sopa", "quantidade_g_ml": 8.0, "unidade": "g", "aliases": ["oleo de milho", "oleo vegetal de milho"]},
    {"nome_oficial": "Óleo Vegetal de Soja", "grupo": "oleos_e_gorduras", "medida_caseira": "1 Colher de Sopa", "quantidade_g_ml": 8.0, "unidade": "g", "aliases": ["oleo de soja", "oleo vegetal de soja", "oleo"]}
]

def normalizar_termo(texto: str) -> str:
    """Normaliza texto removendo acentos, pontuações e convertendo para minúsculas."""
    if not texto:
        return ""
    # Remover tags html ou comandos
    texto = re.sub(r"<[^>]+>", "", texto)
    texto = unicodedata.normalize('NFKD', texto)
    texto = "".join([c for c in texto if not unicodedata.combining(c)])
    texto = re.sub(r"[^a-zA-Z0-9\s]", " ", texto)
    return " ".join(texto.lower().split())

def buscar_alimento_dietbox(termo: str) -> Optional[Dict[str, Any]]:
    """Busca o alimento na lista oficial do Dietbox por nome oficial ou aliases com precisão."""
    termo_norm = normalizar_termo(termo)
    if not termo_norm:
        return None
    
    # 1. Busca exata no nome oficial normalizado
    for alimento in ALIMENTOS_DIETBOX:
        if normalizar_termo(alimento["nome_oficial"]) == termo_norm:
            return alimento
            
    # 2. Busca exata nos aliases
    for alimento in ALIMENTOS_DIETBOX:
        for alias in alimento.get("aliases", []):
            if normalizar_termo(alias) == termo_norm:
                return alimento

    # 3. Busca onde o nome oficial contém o termo digitado (ex: digitou 'arroz integral', acha 'arroz integral cozido')
    for alimento in ALIMENTOS_DIETBOX:
        nome_norm = normalizar_termo(alimento["nome_oficial"])
        if termo_norm in nome_norm:
            return alimento

    # 4. Busca onde o alias contém o termo digitado (ex: digitou 'frango', acha alias 'file de frango')
    for alimento in ALIMENTOS_DIETBOX:
        for alias in alimento.get("aliases", []):
            alias_norm = normalizar_termo(alias)
            if len(termo_norm) >= 4 and termo_norm in alias_norm:
                return alimento

    return None

def buscar_alimentos_por_grupo(grupo_key: str) -> List[Dict[str, Any]]:
    """Retorna todos os alimentos de um grupo específico."""
    grupo_norm = normalizar_termo(grupo_key).replace(" ", "_")
    
    # Mapeamento de possíveis variações
    mapa_grupos = {
        "carboidrato": "carboidratos",
        "carboidratos": "carboidratos",
        "carne": "carnes_e_ovos",
        "carnes": "carnes_e_ovos",
        "carnes_e_ovos": "carnes_e_ovos",
        "ovo": "carnes_e_ovos",
        "ovos": "carnes_e_ovos",
        "fruta": "frutas",
        "frutas": "frutas",
        "laticinio": "laticinios",
        "laticinios": "laticinios",
        "leite": "laticinios",
        "queijo": "laticinios",
        "legume": "legumes_e_verduras",
        "legumes": "legumes_e_verduras",
        "verdura": "legumes_e_verduras",
        "verduras": "legumes_e_verduras",
        "legumes_e_verduras": "legumes_e_verduras",
        "leguminosa": "leguminosas",
        "leguminosas": "leguminosas",
        "feijao": "leguminosas",
        "oleo": "oleos_e_gorduras",
        "oleos": "oleos_e_gorduras",
        "gordura": "oleos_e_gorduras",
        "gorduras": "oleos_e_gorduras",
        "oleos_e_gorduras": "oleos_e_gorduras"
    }

    chave_final = mapa_grupos.get(grupo_norm, grupo_norm)
    return [a for a in ALIMENTOS_DIETBOX if a["grupo"] == chave_final]
