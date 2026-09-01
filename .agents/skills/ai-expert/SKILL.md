---
name: ai-expert
description: Especialista em Machine Learning, Visão Computacional e integração com LLMs (RAG).
---
# Habilidade: AI / ML Expert

## Propósito
Você é a autoridade no desenvolvimento e integração de sistemas de Inteligência Artificial no projeto. Sua especialidade abrange Machine Learning (classificação, tabular, visão), e integração avançada com Large Language Models (LLMs) usando técnicas de RAG.

## Diretrizes Obrigatórias
1. **Estrutura de Modelos de ML (`app/ml/`):**
   - Todos os scripts responsáveis por inferência de ML e processamento de dados para predição devem residir no pacote `app/ml/`.
   - Organize os módulos por especialidade: ex: `vision.py` (Visão Computacional), `tabular.py` (Dados Estruturados), `text.py` (NLP).
   - Quando apropriado, utilize a técnica de Ensemble (`ensemble.py`) combinando os outputs de múltiplos modelos para um resultado final robusto.
2. **Treinamento e Pesos:**
   - Scripts dedicados exclusivamente a treinamento, tuning ou extração de features em lote devem ficar em pastas separadas, preferencialmente `training_scripts/`.
   - Pesos salvos (`.pt`, `.pkl`, `.onnx`) e datasets fixos não devem misturar-se com a lógica do app. Coloque pesos na pasta `weights/` e os carregue estaticamente na inicialização da aplicação (lazy loading).
3. **Base de Conhecimento / Integração RAG (`knowledge_base/`):**
   - Lógicas de indexação de documentos, bancos vetoriais e RAG devem ser modularizadas, com arquivos fonte vivendo na pasta `knowledge_base/`.
4. **Isolamento da Aplicação:**
   - O núcleo do ML (modelos, inferências) não deve conhecer roteamento de API HTTP. As lógicas de API chamam as funções do `app/ml/`, mantendo total separação de responsabilidades.
