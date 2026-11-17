# Modelagem de Dados: Catálogo Nutricional Dietbox (SB-04)

## 1. Dicionário de Grupos Calóricos

| ID do Grupo | Nome Oficial do Grupo | Média Calórica (Kcal) | Total de Itens |
| :--- | :--- | :--- | :--- |
| `carboidratos` | Carboidratos | 150 Kcal | 13 |
| `carnes_e_ovos` | Carnes e Ovos | 190 Kcal | 17 |
| `frutas` | Frutas | 70 Kcal | 33 |
| `laticinios` | Laticínios | 120 Kcal | 17 |
| `legumes_e_verduras` | Legumes e Verduras | 15 Kcal | 36 |
| `leguminosas` | Leguminosas | 55 Kcal | 6 |
| `oleos_e_gorduras` | Óleos e Gorduras | 73 Kcal | 10 |
| **Total Geral** | **7 Grupos** | - | **132 Alimentos** |

---

## 2. Estrutura do Registro de Alimento (Schema)

```json
{
  "id": "alimento_slug",
  "nome_oficial": "Nome do Alimento Conforme Dietbox",
  "grupo_id": "slug_do_grupo",
  "grupo_nome": "Nome do Grupo",
  "media_calorica_kcal": 150.0,
  "medida_caseira": "4 Colheres de Sopa",
  "quantidade_g_ml": 100.0,
  "unidade": "g",
  "aliases": ["arroz", "arroz cozido", "arroz branco"],
  "tags": ["carboidrato_complexo", "cozido"]
}
```

---

## 3. Prevenção de Perda de Dados e Imutabilidade
- Os dados da lista prescrita do Dietbox são imutáveis por padrão.
- A consulta é otimizada com normalização textual (`unicodedata.normalize('NFKD')`, lowercase, remoção de caracteres especiais).
