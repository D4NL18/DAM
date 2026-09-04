# Checklist da Tarefa: US-09 Conversor e Manipulador Universal de Arquivos e Documentos

- **ID da Tarefa:** `TASK-US09-001`
- **Domínio:** 5. Domínio: Utilitários & Segurança
- **Status:** Em Andamento

---

## 🎯 Descrição Funcional
Disponibilizar uma suíte completa de conversão e manipulação de arquivos no DAM para atender demandas rotineiras com agilidade máxima diretamente pelo WhatsApp ou pela API REST do Dashboard. As operações incluem:
1. Converter Imagens (JPG, PNG, WEBP) para documento PDF unificado.
2. Transcodificar imagens entre formatos (PNG <-> JPG <-> WEBP).
3. Juntar múltiplos arquivos PDF em um único documento mantendo a ordem especificada.
4. Dividir/fatiar PDF por intervalos de páginas (ex: `1-5, 8`).
5. Extrair texto puro de arquivos PDF para leitura rápida.
6. Converter PDF para Word (.docx) preservando estrutura e tabelas.
7. Converter Word (.docx) para PDF determinístico.
8. Extrair páginas de PDF como imagens PNG/JPG em alta resolução.

---

## 📋 Critérios de Aceite (Acceptance Criteria)
1. **CA-01 (Conversões de Imagens e Gráficos):**
   - Suporta unir uma ou mais imagens em um único PDF mantendo proporções sem distorção.
   - Suporta conversão entre formatos de imagem (PNG, JPG, WEBP) com parâmetro de compressão/qualidade.
2. **CA-02 (Fusão e Fatiamento de PDFs):**
   - `merge_pdfs` combina 2 ou mais PDFs em bytes válidos sem perda de páginas ou rotação.
   - `split_pdf` extrai apenas as páginas indicadas (ex: páginas 1 a 3 de um PDF de 10 páginas) e gera um novo PDF válido.
   - Rejeita intervalos fora do limite do documento (ex: página 99 em PDF de 5 páginas).
3. **CA-03 (Conversão de Documentos de Escritório):**
   - `pdf_to_docx` gera arquivo DOCX válido e legível.
   - `docx_to_pdf` gera arquivo PDF legível a partir de parágrafos e tabelas do DOCX.
   - `pdf_to_images` extrai páginas como imagens nítidas (150 DPI).
4. **CA-04 (Segurança e Isolamento):**
   - Rejeição imediata de arquivos maiores que 25 MB.
   - Arquivos temporários removidos 100% após a operação.
   - Registro de telemetria em `file_conversions` no Firestore isolado por `user_id`.
   - Tratamento de PDFs com senha e arquivos inválidos.
5. **CA-05 (Integração WhatsApp & API):**
   - Endpoints REST `/api/files/convert` e `/api/files/conversions/history` funcionais.
   - Envio de documento de volta ao usuário via `WhatsAppService.send_document`.

---

## 📝 Checklist de Implementação
- [x] Passo 1: Quebra de Escopo no ROADMAP.md (PO)
- [x] Passo 2: Especificação de Regras de Negócio P-0901 a P-0906 (Analista)
- [x] Passo 3: Contrato de API e Arquitetura técnica (Arquiteto & Designer)
- [x] Passo 4: Modelagem Firestore NoSQL de `file_conversions` (DBA)
- [x] Passo 5: Planejamento detalhado da tarefa (Arquiteto)
- [x] Passo 6: Criação da suíte TDD `test_file_converter.py` (Tester)
- [x] Passo 7: Implementação do motor de conversão, repositório, router, tool e WhatsApp integration (Desenvolvedor)
- [x] Passo 8: Code Review e inspeção de Clean Code (Reviewer)
- [x] Passo 9: UX Review de experiência conversacional e retorno no WhatsApp (UX Reviewer)
- [x] Passo 10: Execução dos testes e verificação de regressão zero (Tester)
- [x] Passo 11: Auditoria de segurança SecOps (SecOps)
- [x] Passo 12: Preparação de PR e release em `feature/US-09-conversao-arquivos` (DevOps)

