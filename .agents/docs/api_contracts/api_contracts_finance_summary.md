# Contrato de Integração: FG-05 consultar_resumo_gastos

## Assinatura Python da Ferramenta

```python
def consultar_resumo_gastos(mes: Optional[int] = None, ano: Optional[int] = None, dias_retroativos: Optional[int] = None) -> str:
    """
    Consulta o resumo consolidado de gastos financeiros do usuário agrupados por cartão/método e por categoria.
    Use esta ferramenta quando o usuário perguntar 'como estão meus gastos esse mês?', 'quanto gastei?', 'resumo financeiro',
    'quanto gastei no cartão pessoal?', 'quais foram meus gastos por categoria?', etc.

    Args:
        mes (int, opcional): Número do mês (1 a 12). Padrão é o mês atual.
        ano (int, opcional): Ano com 4 dígitos (ex: 2026). Padrão é o ano atual.
        dias_retroativos (int, opcional): Número de dias para trás (ex: 7, 15, 30). Se omitido, usa o mês civil.
    """
```

## Resposta Estruturada
- Se houver dados:
  - Cabeçalho com mês/ano ou janela temporal.
  - Total geral e contagem de itens.
  - Subtotais por Cartão (`Cartão de Crédito Pessoal`, `Cartão de Crédito Secundário`, `Cartão de Débito`).
  - Subtotais por Categoria (ordenado decrescente).
  - Destaque das 3 maiores compras (descrição, valor, categoria e cartão).
- Se não houver dados:
  - Mensagem informativa de ausência de registros para o período.
