import logging
import re
from typing import Optional, Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)

# Base gastronômica rica com pratos internacionais icônicos, preparo, ingredientes, analogias e alérgenos
GASTRONOMY_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "boeuf bourguignon": {
        "nome_pt": "Boeuf Bourguignon (Carne Ensopada ao Vinho Tinto)",
        "idioma": "Francês",
        "ingredientes": ["Carne bovina (músculo ou acém)", "Vinho tinto da Borgonha", "Bacon", "Cogumelos paris", "Cebolas pérola", "Cenouras", "Alho e bouquet garni"],
        "preparo": "Cozimento lento (braseado) por várias horas em panela de ferro com vinho tinto até a carne desmanchar e o molho reduzir.",
        "analogia_br": "Lembra muito o clássico picadinho brasileiro com legumes ou uma vaca atolada, porém cozida em um rico molho de vinho tinto francês.",
        "alergenos": ["glúten (farinha na redução)", "álcool (reduzido)"],
        "tipo_dieta": ["carne vermelha", "porco (bacon)"]
    },
    "confit de canard": {
        "nome_pt": "Confit de Canard (Coxa de Pato Confitada)",
        "idioma": "Francês",
        "ingredientes": ["Coxa e sobrecoxa de pato", "Gordura de pato", "Alho", "Tomilho", "Sal grosso"],
        "preparo": "Cozimento lento em imersão de gordura (confit) em temperatura baixa (< 90°C) por várias horas, seguido de douração em forno ou frigideira para pele crocante.",
        "analogia_br": "Lembra a tradicional carne de lata brasileira (conservada e cozida na banha) ou um pato assado bem suculento com pele pururuca.",
        "alergenos": [],
        "tipo_dieta": ["aves", "gordura animal"]
    },
    "soupe a l'oignon": {
        "nome_pt": "Soupe à l'Oignon (Sopa de Cebola Gratinada)",
        "idioma": "Francês",
        "ingredientes": ["Cebolas amarelas caramelizadas", "Caldo de carne", "Vinho branco", "Fatias de pão baguete tostado", "Queijo Gruyère ralado"],
        "preparo": "Caramelização lenta das cebolas no fogo baixo, adição de caldo de carne e gratinada no forno com pão e queijo até formar crosta dourada.",
        "analogia_br": "Lembra caldos e sopas caseiras brasileiras bem encorpadas servidas com torradas e queijo coalho ou minas gratinado por cima.",
        "alergenos": ["lactose (queijo gruyère)", "glúten (pão)"],
        "tipo_dieta": ["caldo de carne bovina", "laticínios"]
    },
    "coq au vin": {
        "nome_pt": "Coq au Vin (Frango Cozido ao Vinho Tinto)",
        "idioma": "Francês",
        "ingredientes": ["Frango ou galo caipira", "Vinho tinto seco", "Bacon em cubos", "Cogumelos", "Cebolas pérola", "Alho e ervas"],
        "preparo": "Frango marinado no vinho tinto e braseado lentamente com bacon e cogumelos até amaciar.",
        "analogia_br": "Lembra um frango ensopado de panela ou galinhada sofisticada feita com redução de vinho tinto e tempero caseiro.",
        "alergenos": ["álcool (reduzido)", "glúten (na redução)"],
        "tipo_dieta": ["frango/aves", "porco (bacon)"]
    },
    "ratatouille": {
        "nome_pt": "Ratatouille (Ensopado Provençal de Legumes)",
        "idioma": "Francês",
        "ingredientes": ["Berinjela", "Abobrinha", "Pimentões", "Tomates maduros", "Cebola", "Alho", "Azeite de oliva", "Ervas de Provence"],
        "preparo": "Legumes laminados ou em cubos refogados lentamente no azeite de oliva com alho e ervas frescas até ficarem macios e caramelizados.",
        "analogia_br": "Lembra uma caponata de legumes ou um refogado caseiro brasileiro de chuchu, berinjela e tomate bem temperado no azeite.",
        "alergenos": [],
        "tipo_dieta": ["vegano", "vegetariano", "sem glúten", "sem lactose"]
    },
    "creme brulee": {
        "nome_pt": "Crème Brûlée (Creme Queimado com Baunilha)",
        "idioma": "Francês",
        "ingredientes": ["Gemas de ovos", "Creme de leite fresco", "Açúcar", "Fava de baunilha natural"],
        "preparo": "Cozimento em banho-maria em baixa temperatura até consistência cremosa, resfriado e finalizado com açúcar maçaricado formando casquinha crocante.",
        "analogia_br": "Lembra nosso pudim de leite ou quindim cremoso, porém sem leite condensado e com uma fina casca crocante de caramelo que quebra na colher.",
        "alergenos": ["lactose (creme de leite)", "ovos"],
        "tipo_dieta": ["vegetariano (com ovos e leite)"]
    },
    "quiche lorraine": {
        "nome_pt": "Quiche Lorraine (Torta Salgada de Bacon e Queijo)",
        "idioma": "Francês",
        "ingredientes": ["Massa podre amanteigada (pâte brisée)", "Bacon frito em cubos", "Ovos", "Creme de leite", "Queijo gruyère ou emmental", "Noz-moscada"],
        "preparo": "Massa assada cega e depois preenchida com o creme de ovos batidos com creme de leite, bacon e queijo, dourando até inflar levemente.",
        "analogia_br": "Lembra o empadão aberto ou torta de liquidificador de queijo e bacon das padarias brasileiras.",
        "alergenos": ["glúten (massa)", "lactose (creme e queijo)", "ovos"],
        "tipo_dieta": ["porco (bacon)", "laticínios"]
    },
    "ossobuco alla milanese": {
        "nome_pt": "Ossobuco alla Milanese (Ossobuco Braseado com Risoto de Açafrão)",
        "idioma": "Italiano",
        "ingredientes": ["Corte transversal de perna de vitela/boi com osso e tutano", "Vinho branco", "Cenoura", "Salsão", "Gremolata (alho, salsinha, raspas de limão)"],
        "preparo": "Carne braseada em fogo baixo por horas com caldo e vinho até quase soltar do osso, preservando o tutano central cremoso.",
        "analogia_br": "Equivalente ao ossobuco de panela de pressão com polenta ou arroz ensopado brasileiro, com o saboroso tutano no meio do osso.",
        "alergenos": [],
        "tipo_dieta": ["carne vermelha"]
    },
    "spaghetti alla carbonara": {
        "nome_pt": "Spaghetti alla Carbonara (Massa Carbonara Autêntica)",
        "idioma": "Italiano",
        "ingredientes": ["Massa de grano duro", "Guanciale (bochecha de porco curada)", "Gemas de ovos frescos", "Queijo Pecorino Romano", "Pimenta-do-reino preta"],
        "preparo": "Massa cozida al dente misturada fora do fogo com a gordura do guanciale crocante e uma emulsão cremosa de gemas e queijo pecorino (sem creme de leite!).",
        "analogia_br": "Lembra um macarrão cremoso com bacon e ovos fritos, mas sem adição de creme de leite.",
        "alergenos": ["glúten (massa)", "ovos (gemas cruas temperadas)", "lactose (pecorino)"],
        "tipo_dieta": ["porco (guanciale)", "laticínios"]
    },
    "cacio e pepe": {
        "nome_pt": "Cacio e Pepe (Massa com Queijo Pecorino e Pimenta)",
        "idioma": "Italiano",
        "ingredientes": ["Massa tonnarelli ou espaguete", "Queijo Pecorino Romano envelhecido", "Pimenta-do-reino moída na hora"],
        "preparo": "Pimenta tostada a seco na frigideira, misturada com água do cozimento rica em amido e queijo pecorino ralado fino para formar um creme aveludado sem gordura extra.",
        "analogia_br": "Lembra um macarrão simples ao alho e óleo com bastante queijo ralado da roça e pimenta preta bem aromática.",
        "alergenos": ["glúten (massa)", "lactose (queijo pecorino)"],
        "tipo_dieta": ["vegetariano (com leite)"]
    },
    "risotto ai funghi porcini": {
        "nome_pt": "Risotto ai Funghi Porcini (Risoto de Cogumelos Porcini)",
        "idioma": "Italiano",
        "ingredientes": ["Arroz arbóreo ou carnaroli", "Cogumelos porcini secos e frescos", "Caldo de legumes", "Vinho branco", "Manteiga", "Parmesão ralado"],
        "preparo": "Arroz tostado no azeite, cozimento lento adicionando caldo fervente concha a concha e finalizado com mantecatura (manteiga gelada e parmesão vigorosamente mexidos).",
        "analogia_br": "Lembra um arroz cremoso de festa brasileiro feito com caldo denso e queijo, super reconfortante.",
        "alergenos": ["lactose (manteiga e parmesão)"],
        "tipo_dieta": ["vegetariano"]
    },
    "tiramisu": {
        "nome_pt": "Tiramisù Tradicional Italiano",
        "idioma": "Italiano",
        "ingredientes": ["Biscoitos savoiardi (champanhe)", "Café espresso forte", "Queijo mascarpone", "Gemas de ovos", "Açúcar", "Cacau em pó 100%"],
        "preparo": "Camadas intercaladas de biscoitos embebidos no café espresso e creme aveludado de mascarpone com gemas batidas, polvilhado com cacau fino.",
        "analogia_br": "É o equivalente italiano direto ao nosso pavê brasileiro de café com creme e chocolate.",
        "alergenos": ["glúten (biscoitos)", "lactose (mascarpone)", "ovos"],
        "tipo_dieta": ["vegetariano (com ovos e leite)"]
    },
    "tonkatsu": {
        "nome_pt": "Tonkatsu (Bife de Porco Empanado na Farinha Panko)",
        "idioma": "Japonês",
        "ingredientes": ["Lombo ou copa-lombo de porco", "Farinha de trigo", "Ovo batido", "Farinha panko japonesa", "Molho agridoce tonkatsu", "Repolho fatiado bem fino"],
        "preparo": "Carne temperada, empanada na técnica japonesa com panko e frita por imersão em óleo quente até obter crocância extrema sem encharcar.",
        "analogia_br": "Exatamente igual ao bife de porco à milanesa de boteco, porém com empanamento muito mais leve e crocante (panko).",
        "alergenos": ["glúten (farinha e panko)", "ovos", "soja (molho tonkatsu)"],
        "tipo_dieta": ["carne de porco"]
    },
    "ramen": {
        "nome_pt": "Ramen / Lámen Tradicional Japonês",
        "idioma": "Japonês",
        "ingredientes": ["Massa artesanal alcalina", "Caldo tonkotsu (ossos de porco cozidos por 12h) ou caldo shoyu", "Chashu (fatias de porco enrolado)", "Ovo marinado ajitsuke tamago", "Alga nori", "Cebolinha"],
        "preparo": "Caldo emulsionado e reduzido por até 16 horas, servido fervendo sobre o macarrão fresco, carne marinada e ovo com gema mole.",
        "analogia_br": "Lembra uma canja de galinha ou mocotó brasileiro bem concentrado e rico em colágeno, servido com macarrão caseiro.",
        "alergenos": ["glúten (macarrão)", "ovos (ovo marinado)", "soja (molho shoyu)"],
        "tipo_dieta": ["carne de porco"]
    },
    "tempura": {
        "nome_pt": "Tempurá (Camarões e Legumes Empanados)",
        "idioma": "Japonês",
        "ingredientes": ["Camarões frescos limpos", "Legumes (abóbora kabocha, cenoura, batata doce)", "Farinha especial e água gelada/gasosa", "Molho tentsuyu"],
        "preparo": "Massa ultraleve batida rapidamente com água gelada para evitar desenvolvimento de glúten e frita instantaneamente em óleo limpo.",
        "analogia_br": "Lembra o peixinho da horta frito ou os pasteizinhos e camarões empanados de praia brasileira, mas com casquinha mais leve e crocante.",
        "alergenos": ["glúten (massa)", "crustáceos/frutos do mar (camarão)", "soja (molho dip)"],
        "tipo_dieta": ["frutos do mar", "peixes"]
    },
    "okonomiyaki": {
        "nome_pt": "Okonomiyaki (Panqueca Japonesa de Repolho e Carnes)",
        "idioma": "Japonês",
        "ingredientes": ["Repolho fatiado", "Massa com farinha e dashi", "Ovos", "Fatias finas de barriga de porco ou frutos do mar", "Molho okonomi", "Maionese japonesa", "Katsuobushi (flocos de peixe seco bonito)"],
        "preparo": "Grelhado na chapa de ferro (teppan), coberto com molho escuro doce, maionese em zigue-zague e flocos de peixe que dançam com o calor.",
        "analogia_br": "Lembra uma torta de frigideira ou um omeletão brasileiro recheado com repolho, linguiça e queijo.",
        "alergenos": ["glúten (massa)", "ovos", "peixe (katsuobushi)", "soja (molhos)"],
        "tipo_dieta": ["porco", "frutos do mar", "peixe"]
    },
    "paella valenciana": {
        "nome_pt": "Paella Valenciana (Arroz Espanhol na Paellera)",
        "idioma": "Espanhol",
        "ingredientes": ["Arroz bomba espanhol", "Frango e coelho", "Feijão verde (bajoqueta)", "Garrofó (feijão branco grande)", "Tomate ralado", "Açafrão legítimo", "Azeite e alecrim"],
        "preparo": "Cozimento lento em paellera aberta com caldo aromático e açafrão, formando a famosa crosta de arroz tostado no fundo (socarrat).",
        "analogia_br": "Primo direto da nossa galinhada caipira com açafrão da terra ou do arroz de carreteiro do sul.",
        "alergenos": [],
        "tipo_dieta": ["aves", "carne de caça"]
    },
    "pulpo a la gallega": {
        "nome_pt": "Pulpo a la Gallega / Polbo à Feira",
        "idioma": "Espanhol",
        "ingredientes": ["Polvo inteiro cozido", "Batatas cozidas cortadas em rodelas (cachelos)", "Páprica doce e picante (pimentón)", "Azeite de oliva extravirgem", "Sal grosso em flocos"],
        "preparo": "Polvo mergulhado ('assustado') em água fervente 3 vezes e cozido até a maciez ideal, fatiado sobre batatas e regado com azeite quente e páprica.",
        "analogia_br": "Lembra um vinagrete morno ou salada brasileira de frutos do mar com batata cozida e azeite generoso.",
        "alergenos": ["moluscos / frutos do mar (polvo)"],
        "tipo_dieta": ["pescetariano", "frutos do mar"]
    },
    "gazpacho": {
        "nome_pt": "Gazpacho Andaluz (Sopa Fria de Tomate)",
        "idioma": "Espanhol",
        "ingredientes": ["Tomates maduros selecionados", "Pepino", "Pimentão verde", "Alho", "Azeite de oliva extravirgem", "Vinagre de Jerez"],
        "preparo": "Ingredientes crus batidos vigorosamente até formar uma emulsão refrescante, aveludada e gelada, servida com cubos de vegetais.",
        "analogia_br": "Lembra nosso vinagrete brasileiro de churrasco batido no liquidificador e servido bem gelado.",
        "alergenos": [],
        "tipo_dieta": ["vegano", "vegetariano", "sem glúten", "sem lactose"]
    },
    "tortilla espanola": {
        "nome_pt": "Tortilla de Patatas (Omelete Espanhola de Batatas)",
        "idioma": "Espanhol",
        "ingredientes": ["Batatas laminadas", "Ovos caipiras", "Cebola (opcional)", "Azeite de oliva extravirgem abundante", "Sal"],
        "preparo": "Batatas e cebolas confitadas no azeite em fogo médio até derreterem de macias, misturadas aos ovos batidos e seladas na frigideira com centro cremoso.",
        "analogia_br": "Lembra uma torta de frigideira ou omelete alta de batata e ovos da cozinha das avós brasileiras.",
        "alergenos": ["ovos"],
        "tipo_dieta": ["vegetariano"]
    },
    "wiener schnitzel": {
        "nome_pt": "Wiener Schnitzel (Escalope de Vitela Empanado)",
        "idioma": "Alemão / Austríaco",
        "ingredientes": ["Fatia fina de vitela", "Farinha de trigo", "Ovos batidos", "Farinha de rosca artesanal", "Manteiga clarificada para fritar", "Limão siciliano"],
        "preparo": "Carne batida com martelo até ficar ultrafina, passada na farinha, ovos e rosca com cuidado para a casca ondular ao flutuar na manteiga quente.",
        "analogia_br": "Exatamente o nosso tradicional bife bovino à milanesa servido com limão para espremer na hora.",
        "alergenos": ["glúten (farinha)", "ovos", "lactose (manteiga)"],
        "tipo_dieta": ["carne vermelha (vitela)"]
    },
    "sauerbraten": {
        "nome_pt": "Sauerbraten (Assado de Panela Alemão Marinado)",
        "idioma": "Alemão",
        "ingredientes": ["Carne bovina", "Marinada de vinagre de maçã, vinho e especiarias (cravo, louro, zimbro)", "Legumes", "Pão de especiarias (lebkuchen) para engrossar o molho"],
        "preparo": "Carne marinada no vinagre e especiarias por 3 a 5 dias antes de ser braseada lentamente no forno até ficar tenra e com molho agridoce.",
        "analogia_br": "Lembra a nossa carne assada de panela com vinagrete e especiarias ou um lagarto recheado de festa com toque agridoce.",
        "alergenos": ["glúten (espessante do molho)"],
        "tipo_dieta": ["carne vermelha"]
    },
    "currywurst": {
        "nome_pt": "Currywurst (Salsicha Alemã com Molho de Curry)",
        "idioma": "Alemão",
        "ingredientes": ["Salsicha de porco bratwurst", "Molho de tomate temperado com páprica e especiarias", "Curry em pó abundante", "Batatas fritas para acompanhar"],
        "preparo": "Salsicha grelhada ou frita, fatiada em rodelas, banhada em molho quente de tomate agridoce e polvilhada com curry indiano aromático.",
        "analogia_br": "Lembra um petisco de linguiça calabresa ou salsicha no molho de cachorro-quente bem temperado.",
        "alergenos": [],
        "tipo_dieta": ["carne de porco"]
    },
    "shepherd's pie": {
        "nome_pt": "Shepherd's Pie / Cottage Pie (Torta de Carne com Purê Gratinado)",
        "idioma": "Inglês",
        "ingredientes": ["Carne de cordeiro moída (Shepherd's) ou bovina (Cottage)", "Cenoura", "Ervilhas", "Cebola", "Molho inglês", "Purê de batatas com manteiga e queijo"],
        "preparo": "Carne refogada com legumes e molho encorpado, coberta por generosa camada de purê de batatas cremoso e levada ao forno para gratinar.",
        "analogia_br": "Irmão gêmeo britânico do nosso escondidinho brasileiro (a diferença é que usa purê de batata inglesa em vez de mandioca/aipim).",
        "alergenos": ["lactose (purê de batatas)", "glúten (molho inglês/caldo)"],
        "tipo_dieta": ["carne vermelha"]
    },
    "fish and chips": {
        "nome_pt": "Fish and Chips (Peixe Empanado na Cerveja com Batata Frita)",
        "idioma": "Inglês",
        "ingredientes": ["Filé de peixe branco (bacalhau fresco/haddock)", "Massa aerada com cerveja (beer batter)", "Batatas cortadas grossas", "Purê de ervilhas (mushy peas)", "Molho tártaro"],
        "preparo": "Filé de peixe mergulhado na massa com cerveja e frito por imersão até formar uma casca dourada inflada e crocante.",
        "analogia_br": "Idêntico ao clássico filé de peixe frito com batata frita e limão servido nos quiosques de praia brasileiros.",
        "alergenos": ["peixe", "glúten (massa de cerveja e trigo)"],
        "tipo_dieta": ["pescetariano", "peixes"]
    },
    "beef wellington": {
        "nome_pt": "Beef Wellington (Filé Mignon Folhado)",
        "idioma": "Inglês",
        "ingredientes": ["Filé mignon de corte alto", "Duxelles de cogumelos picadinhos", "Presunto de parma (prosciutto)", "Massa folhada amanteigada", "Mostarda dijon"],
        "preparo": "Filé selado e pincelado com mostarda, envolvido em cogumelos refogados e presunto cru, envolto em massa folhada e assado no forno até o ponto rosado.",
        "analogia_br": "Lembra um rocambole de carne ou empadão folhado nobre de festa de casamento.",
        "alergenos": ["glúten (massa folhada)", "lactose (manteiga da massa)", "ovos (pincelamento)"],
        "tipo_dieta": ["carne vermelha", "porco (prosciutto)"]
    },
    "clam chowder": {
        "nome_pt": "Clam Chowder (Sopa Cremosa de Mariscos com Batata)",
        "idioma": "Inglês / Americano",
        "ingredientes": ["Mariscos/vôngoles frescos (clams)", "Batatas em cubos", "Bacon em cubinhos", "Creme de leite espesso", "Cebola", "Salsão", "Caldo de mariscos"],
        "preparo": "Ensopado espesso e aveludado cozido lentamente com caldo do cozimento dos mariscos, batatas macias e finalizado com creme de leite fresco.",
        "analogia_br": "Lembra uma moqueca cremosa com leite de coco ou um bobó de mariscos bem aveludado e reconfortante.",
        "alergenos": ["frutos do mar / moluscos (mariscos)", "lactose (creme de leite)", "glúten (espessante)"],
        "tipo_dieta": ["frutos do mar", "porco (bacon)"]
    }
}

ALLERGEN_KEYWORDS = {
    "glúten": ["trigo", "farinha", "glúten", "gluten", "massa", "pão", "panko", "baguete", "cerveja", "cevada", "savoiardi"],
    "lactose / laticínios": ["leite", "creme de leite", "queijo", "manteiga", "gruyère", "parmesão", "pecorino", "mascarpone", "gorgonzola", "iogurte"],
    "ovos": ["ovo", "ovos", "gema", "gemas", "clara", "maionese"],
    "frutos do mar / crustáceos": ["camarão", "lagosta", "caranguejo", "siri", "marisco", "vôngole", "ostra", "polvo", "lula", "frutos do mar"],
    "peixes": ["peixe", "atum", "salmão", "bacalhau", "katsuobushi", "bonito", "anchova"],
    "nozes / amendoim": ["amendoim", "noz", "nozes", "castanha", "amêndoa", "pistache", "avelã"],
    "soja": ["soja", "shoyu", "tofu", "miso", "dashi de soja", "molho tonkatsu", "tonkatsu"]
}

DIET_CONFLICT_RULES = {
    "vegano": ["carne", "porco", "bacon", "bovina", "frango", "pato", "vitela", "cordeiro", "ovo", "ovos", "gema", "leite", "queijo", "manteiga", "lactose", "mel", "peixe", "frutos do mar", "camarão", "polvo"],
    "vegetariano": ["carne", "porco", "bacon", "bovina", "frango", "pato", "vitela", "cordeiro", "peixe", "frutos do mar", "camarão", "polvo"],
    "sem gluten": ["glúten", "gluten", "trigo", "farinha", "pão", "panko", "baguete", "cerveja", "massa", "espaguete", "macarrão", "massa folhada"],
    "celiaco": ["glúten", "gluten", "trigo", "farinha", "pão", "panko", "baguete", "cerveja", "massa", "espaguete", "macarrão", "massa folhada"],
    "sem lactose": ["lactose", "leite", "creme de leite", "queijo", "manteiga", "gruyère", "parmesão", "pecorino", "mascarpone", "gorgonzola"],
    "intolerante a lactose": ["lactose", "leite", "creme de leite", "queijo", "manteiga", "gruyère", "parmesão", "pecorino", "mascarpone", "gorgonzola"],
    "sem frutos do mar": ["frutos do mar", "camarão", "lagosta", "marisco", "ostra", "polvo", "lula", "crustáceos", "moluscos"],
    "alergia a frutos do mar": ["frutos do mar", "camarão", "lagosta", "marisco", "ostra", "polvo", "lula", "crustáceos", "moluscos"],
    "sem porco": ["porco", "bacon", "guanciale", "pancetta", "salsicha", "chashu", "prosciutto", "presunto"],
    "halal": ["porco", "bacon", "guanciale", "álcool", "vinho", "cerveja"],
    "kosher": ["porco", "bacon", "camarão", "polvo", "marisco", "frutos do mar"]
}


def _limpar_texto(t: str) -> str:
    """Remove pontuações e acentuações para busca normalizada."""
    t = t.lower()
    t = re.sub(r'[àáâãä]', 'a', t)
    t = re.sub(r'[éèêë]', 'e', t)
    t = re.sub(r'[íìîï]', 'i', t)
    t = re.sub(r'[óòôõö]', 'o', t)
    t = re.sub(r'[úùûü]', 'u', t)
    t = re.sub(r'[ç]', 'c', t)
    t = re.sub(r'[\'\"’\-]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def _verificar_conflitos_alimentares(
    texto_analisado: str,
    lista_ingredientes: list,
    restricoes_usuario: Optional[str],
    alergenos_detectados: Optional[list] = None
) -> list:
    """Identifica conflitos entre a restrição alimentar informada e os ingredientes do prato."""
    if not restricoes_usuario:
        return []

    restricoes_norm = _limpar_texto(restricoes_usuario)
    corpo_completo = _limpar_texto(texto_analisado + " " + " ".join(lista_ingredientes))
    conflitos = []

    # 1. Checagem direta de palavras-chave proibidas
    for chave_regra, proibidos in DIET_CONFLICT_RULES.items():
        if chave_regra in restricoes_norm:
            for proibido in proibidos:
                if re.search(r'\b' + re.escape(proibido) + r'\b', corpo_completo):
                    alerta = f"Conflito com '{chave_regra}': contém '{proibido}'."
                    if alerta not in conflitos:
                        conflitos.append(alerta)

    # 2. Checagem com alérgenos já identificados no prato
    if alergenos_detectados:
        alergenos_texto = " ".join(alergenos_detectados).lower()
        if ("celiaco" in restricoes_norm or "gluten" in restricoes_norm) and ("glúten" in alergenos_texto or "gluten" in alergenos_texto):
            alerta = "Conflito com 'celíaco / sem glúten': prato contém glúten."
            if alerta not in conflitos:
                conflitos.append(alerta)
        if "lactose" in restricoes_norm and ("lactose" in alergenos_texto or "laticínios" in alergenos_texto):
            alerta = "Conflito com 'lactose': prato contém lactose / laticínios."
            if alerta not in conflitos:
                conflitos.append(alerta)
        if ("frutos do mar" in restricoes_norm or "crustaceos" in restricoes_norm) and ("frutos do mar" in alergenos_texto or "crustáceos" in alergenos_texto or "moluscos" in alergenos_texto):
            alerta = "Conflito com 'frutos do mar': prato contém frutos do mar / crustáceos."
            if alerta not in conflitos:
                conflitos.append(alerta)

    return conflitos


def _detectar_alergenos(texto: str, ingredientes: list) -> list:
    """Verifica alérgenos conhecidos presentes nos ingredientes ou texto descritivo."""
    texto_norm = _limpar_texto(texto + " " + " ".join(ingredientes))
    alergenos_detectados = []

    for alergeno, keywords in ALLERGEN_KEYWORDS.items():
        for kw in keywords:
            kw_norm = _limpar_texto(kw)
            if re.search(r'\b' + re.escape(kw_norm) + r'\b', texto_norm):
                if alergeno not in alergenos_detectados:
                    alergenos_detectados.append(alergeno)
                break
    return alergenos_detectados


def _analise_local_gastronomica(texto_cardapio: str, idioma_origem: str = "auto", restricoes_alimentares: Optional[str] = None) -> Optional[str]:
    """Busca na base de dados gastronômica especializada e gera o relatório completo."""
    texto_limpo = _limpar_texto(texto_cardapio)

    # Busca o prato mais correspondente
    melhor_match = None
    for chave, dados in GASTRONOMY_KNOWLEDGE_BASE.items():
        chave_limpa = _limpar_texto(chave)
        # Verifica se o nome da chave está contido no texto ou vice-versa
        if chave_limpa in texto_limpo or all(w in texto_limpo for w in chave_limpa.split() if len(w) > 2):
            melhor_match = dados
            break

    if not melhor_match:
        return None

    # Monta a ficha gastronômica detalhada
    nome_pt = melhor_match["nome_pt"]
    idioma = melhor_match["idioma"] if idioma_origem == "auto" else idioma_origem
    ingredientes_str = ", ".join(melhor_match["ingredientes"])
    preparo = melhor_match["preparo"]
    analogia = melhor_match["analogia_br"]

    # Alérgenos: combina os definidos na base curada + detecção dinâmica
    base_alergenos = list(melhor_match.get("alergenos", []))
    detectados = _detectar_alergenos(preparo + " " + ingredientes_str, melhor_match["ingredientes"])
    todos_alergenos = list(dict.fromkeys(base_alergenos + detectados))
    alergenos_str = ", ".join(todos_alergenos) if todos_alergenos else "Nenhum dos principais alérgenos comuns identificado na receita padrão."

    # Checagem de Restrições Informadas
    conflitos = _verificar_conflitos_alimentares(
        preparo + " " + ingredientes_str,
        melhor_match["ingredientes"],
        restricoes_alimentares,
        todos_alergenos
    )

    bloco_conflito = ""
    if restricoes_alimentares:
        if conflitos:
            detalhes = " | ".join(conflitos)
            bloco_conflito = (
                f"\n\n🚨 **ATENÇÃO / CONFLITO DE RESTRIÇÃO ALIMENTAR**:\n"
                f"Você especificou a restrição: '{restricoes_alimentares}'.\n"
                f"⚠️ **Alerta:** Este prato NÃO é recomendado para você devido a: {detalhes}"
            )
        else:
            bloco_conflito = (
                f"\n\n✅ **Compatibilidade com sua Restrição:**\n"
                f"Não foram identificados conflitos evidentes com '{restricoes_alimentares}' na receita padrão deste prato."
            )

    resultado = (
        f"🍽️ **Guia Gastronômico de Cardápio:** {nome_pt}\n\n"
        f"🌍 **Origem Cultural / Idioma:** {idioma}\n"
        f"🥣 **Ingredientes Principais:** {ingredientes_str}\n"
        f"👨‍🍳 **Modo de Preparo e Técnica Culinária:** {preparo}\n"
        f"🇧🇷 **Analogia Brasileira:** {analogia}\n"
        f"⚠️ **Alérgenos Conhecidos:** {alergenos_str}"
        f"{bloco_conflito}"
    )
    return resultado


def traduzir_e_explicar_cardapio(
    texto_cardapio: str,
    idioma_origem: str = "auto",
    restricoes_alimentares: Optional[str] = None
) -> str:
    """
    Traduz pratos de cardápios internacionais (inglês, francês, italiano, japonês, espanhol, alemão),
    fornecendo descrição culinária detalhada (ingredientes principais, modo de preparo, ex: sous-vide,
    confit, flambado, ao molho gorgonzola, etc.), analogias claras com pratos conhecidos no Brasil e alertas
    pontuais caso contenha ingredientes alérgenos conhecidos ou conflitantes com restrições alimentares informadas.

    Args:
        texto_cardapio (str): Nome ou descrição do prato no cardápio (ex: 'Boeuf Bourguignon', 'Tonkatsu', 'Shepherd\'s Pie').
        idioma_origem (str, opcional): Idioma original do cardápio ('francês', 'inglês', 'italiano', 'japonês', 'espanhol', 'alemão', 'auto').
        restricoes_alimentares (str, opcional): Restrições do comensal (ex: 'vegano', 'sem glúten', 'intolerância a lactose', 'alergia a frutos do mar').

    Returns:
        str: Guia gastronômico completo e traduzido com analogias brasileiras e alertas de saúde.
    """
    if not texto_cardapio or not texto_cardapio.strip():
        return "Por favor, forneça o nome ou a foto/texto do prato que você deseja traduzir e entender."

    # 1. Tenta correspondência imediata com base gastronômica curada
    analise_local = _analise_local_gastronomica(texto_cardapio, idioma_origem, restricoes_alimentares)
    if analise_local:
        return analise_local

    # 2. Se não estiver na base local e houver API Key do Gemini, usa a IA generativa com prompt culinário de alto nível
    if settings.GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            prompt_culinario = (
                f"Você é um renomado Chef de Cozinha internacional e Guia Gastronômico brasileiro do DAM.\n"
                f"Analise o seguinte item de cardápio internacional: '{texto_cardapio}'.\n"
                f"Idioma indicado: '{idioma_origem}'.\n"
                f"Restrições alimentares informadas: '{restricoes_alimentares or 'Nenhuma'}'.\n\n"
                f"Estruture OBRIGATORIAMENTE a resposta no seguinte formato:\n"
                f"🍽️ **Guia Gastronômico de Cardápio:** [Nome do prato traduzido e original]\n\n"
                f"🌍 **Origem Cultural / Idioma:** [País/Cultura e idioma]\n"
                f"🥣 **Ingredientes Principais:** [Lista de ingredientes centrais]\n"
                f"👨‍🍳 **Modo de Preparo e Técnica Culinária:** [Explique técnicas como confit, sous-vide, flambado, redução, emulsão, etc.]\n"
                f"🇧🇷 **Analogia Brasileira:** [Faça uma analogia clara e afetuosa com pratos populares brasileiros que o usuário conheça]\n"
                f"⚠️ **Alérgenos Conhecidos:** [Liste glúten, lactose, ovos, frutos do mar, nozes, soja se houver]\n"
                f"🚨 **Alerta de Restrições:** [Se o usuário passou restrições, confirme se é seguro ou se há conflito]."
            )
            model = genai.GenerativeModel('gemini-2.5-flash')
            resp = model.generate_content(prompt_culinario)
            if resp and resp.text:
                return resp.text.strip()
        except Exception as e:
            logger.warning(f"Falha na tradução via Gemini: {e}")

    # 3. Fallback inteligente com inferência de ingredientes e termos técnicos culinários
    texto_lower = texto_cardapio.lower()
    idioma_detectado = idioma_origem if idioma_origem != "auto" else "Internacional"

    # Técnicas comuns
    tecnicas = []
    if "sous-vide" in texto_lower or "sous vide" in texto_lower:
        tecnicas.append("Cozimento a vácuo em baixa temperatura (Sous-vide)")
    if "confit" in texto_lower:
        tecnicas.append("Cozimento lento em imersão de gordura (Confit)")
    if "flamb" in texto_lower:
        tecnicas.append("Flambagem em bebida destilada")
    if "gorgonzola" in texto_lower:
        tecnicas.append("Molho cremoso à base de queijo gorgonzola/azul")
    if "smoke" in texto_lower or "defumad" in texto_lower or "fumee" in texto_lower:
        tecnicas.append("Defumação artesanal")
    if "gratin" in texto_lower:
        tecnicas.append("Gratinado ao forno com crosta dourada")

    tecnica_str = ", ".join(tecnicas) if tecnicas else "Preparo tradicional da culinária regional."

    alergenos = _detectar_alergenos(texto_cardapio, [])
    alergenos_str = ", ".join(alergenos) if alergenos else "Nenhum alérgeno evidente no nome do prato. Confirme com o garçom."

    conflitos = _verificar_conflitos_alimentares(texto_cardapio, [], restricoes_alimentares)
    bloco_conflito = ""
    if restricoes_alimentares:
        if conflitos:
            bloco_conflito = f"\n\n🚨 **ATENÇÃO DE RESTRIÇÃO ALIMENTAR**: Risco de incompatibilidade com '{restricoes_alimentares}'."
        else:
            bloco_conflito = f"\n\n✅ **Restrições:** Verifique os ingredientes detalhados no restaurante para garantir compatibilidade com '{restricoes_alimentares}'."

    return (
        f"🍽️ **Guia Gastronômico de Cardápio:** {texto_cardapio}\n\n"
        f"🌍 **Origem Cultural / Idioma:** {idioma_detectado}\n"
        f"🥣 **Ingredientes Principais:** Ingredientes típicos do prato '{texto_cardapio}'.\n"
        f"👨‍🍳 **Modo de Preparo e Técnica Culinária:** {tecnica_str}\n"
        f"🇧🇷 **Analogia Brasileira:** Prato culinário com textura e perfil aromático reconfortante similar aos assados e ensopados brasileiros.\n"
        f"⚠️ **Alérgenos Conhecidos:** {alergenos_str}"
        f"{bloco_conflito}"
    )
