"""
Suíte de Testes Automatizados TDD First (FG-09)
Regras de Negócio P-0901, P-0902, P-0903 e P-0904
Governança de Categorias, Registro de Receitas/Reembolsos e Recorrência de Despesas Fixas
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from main import app
from services.user_context import UserContext

client = TestClient(app)

class TestFinanceCategoriesAndFixedExpenses:

    # =========================================================================
    # Helpers de Mocks
    # =========================================================================
    def _criar_mock_doc(self, doc_id, data):
        doc = MagicMock()
        doc.id = doc_id
        doc.to_dict.return_value = data
        doc.reference = MagicMock()
        return doc

    # =========================================================================
    # 1. P-0901: Normalização Taxonômica de Categorias & Anti-Alucinação
    # =========================================================================
    def test_obter_categorias_usuario_fallback_defaults(self):
        """P-0901: Usuário sem categorias customizadas deve receber as 13 DEFAULT_CATEGORIES."""
        # Arrange
        from services.tools.finance_tool import obter_categorias_usuario
        mock_db = MagicMock()
        mock_db.collection.return_value.where.return_value.stream.return_value = []
        mock_db.collection.return_value.stream.return_value = []

        # Act
        with patch("config.firebase.db", mock_db):
            categorias = obter_categorias_usuario("novo_usuario")

        # Assert
        assert len(categorias) >= 13
        nomes = [c["name"] for c in categorias]
        assert "Mercado" in nomes
        assert "Carro" in nomes
        assert "Casa" in nomes
        assert "Receitas" in nomes
        assert "Outros" in nomes
        assert "Reembolso" not in nomes

    def test_obter_categorias_usuario_customizadas(self):
        """P-0901: Categorias criadas pelo usuário no Firestore devem ser carregadas dinamicamente."""
        # Arrange
        from services.tools.finance_tool import obter_categorias_usuario
        mock_db = MagicMock()
        doc_custom = self._criar_mock_doc("cat_inv", {
            "userId": "daniel",
            "name": "Investimentos",
            "color": "#10B981"
        })
        mock_db.collection.return_value.where.return_value.stream.return_value = [doc_custom]

        # Act
        with patch("config.firebase.db", mock_db):
            categorias = obter_categorias_usuario("daniel")

        # Assert
        nomes = [c["name"] for c in categorias]
        assert "Investimentos" in nomes

    def test_normalizar_categoria_sinonimos_conhecidos(self):
        """P-0901: Termos correlatos conhecidos devem ser mapeados deterministicamente para categorias cadastradas."""
        # Arrange
        from services.tools.finance_tool import normalizar_categoria

        # Act & Assert
        # Mercado / Alimentação
        assert normalizar_categoria("supermercado") == "Mercado"
        assert normalizar_categoria("almoço") == "Mercado"
        assert normalizar_categoria("comida") == "Mercado"
        assert normalizar_categoria("açougue") == "Mercado"
        assert normalizar_categoria("padaria") == "Mercado"
        assert normalizar_categoria("delivery") == "iFood"
        assert normalizar_categoria("ifood") == "iFood"

        # Carro / Transporte
        assert normalizar_categoria("gasolina") == "Carro"
        assert normalizar_categoria("combustível") == "Carro"
        assert normalizar_categoria("uber") == "Carro"
        assert normalizar_categoria("estacionamento") == "Carro"
        assert normalizar_categoria("mecânico") == "Carro"

        # Farmácia / Saúde
        assert normalizar_categoria("farmácia") == "Farmácia"
        assert normalizar_categoria("remédio") == "Farmácia"
        assert normalizar_categoria("drogaria") == "Farmácia"
        assert normalizar_categoria("consulta médica") == "Farmácia"

        # Casa / Moradia
        assert normalizar_categoria("aluguel") == "Casa"
        assert normalizar_categoria("condomínio") == "Casa"
        assert normalizar_categoria("conta de luz") == "Casa"
        assert normalizar_categoria("energia") == "Casa"
        assert normalizar_categoria("água") == "Casa"
        assert normalizar_categoria("internet") == "Casa"

        # Lazer
        assert normalizar_categoria("cinema") == "Lazer"
        assert normalizar_categoria("jogos") == "Lazer"
        assert normalizar_categoria("games") == "Lazer"
        assert normalizar_categoria("churrasco") == "Lazer"
        assert normalizar_categoria("bar") == "Lazer"

    def test_normalizar_categoria_alucinacao_arbitraria_fallback_outros(self):
        """P-0901: Categorias arbitrárias/inventadas sem correspondência devem cair em 'Outros'."""
        # Arrange
        from services.tools.finance_tool import normalizar_categoria

        # Act & Assert
        assert normalizar_categoria("Presentes") == "Outros"
        assert normalizar_categoria("Assinaturas") == "Outros"
        assert normalizar_categoria("Comprei um telescópio espacial") == "Outros"
        assert normalizar_categoria("Vestuário aleatório") == "Outros"

    def test_proibicao_estrita_categoria_reembolso(self):
        """P-0901: O sistema é terminantemente proibido de atribuir a categoria 'Reembolso'."""
        # Arrange
        from services.tools.finance_tool import normalizar_categoria

        # Act & Assert
        cat = normalizar_categoria("Reembolso")
        assert cat != "Reembolso"
        assert cat in ["Receitas", "Outros"]

    def test_normalizar_categoria_case_insensitive_e_acentos(self):
        """P-0901: A normalização deve suportar variações de caixa, espaços e acentuação gráfica."""
        # Arrange
        from services.tools.finance_tool import normalizar_categoria

        # Act & Assert
        assert normalizar_categoria("   sUpErMeRcAdO   ") == "Mercado"
        assert normalizar_categoria("FARMACIA") == "Farmácia"
        assert normalizar_categoria("combustivel") == "Carro"
        assert normalizar_categoria("ÁGUA") == "Casa"

    def test_registrar_gasto_com_normalizacao_e_anti_alucinacao(self):
        """P-0901: Tool registrar_gasto normaliza a categoria antes de persistir no banco."""
        # Arrange
        from services.tools.finance_tool import registrar_gasto
        UserContext.set_user("daniel")

        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_db.collection.return_value = mock_col

        # Act
        with patch("config.firebase.db", mock_db):
            resposta = registrar_gasto(
                descricao="Abastecimento Posto Shell",
                valor=150.0,
                categoria="gasolina",
                metodo_pagamento="Cartão de Crédito Pessoal"
            )

        # Assert
        assert "Sucesso" in resposta
        assert mock_col.add.called
        saved_data = mock_col.add.call_args[0][0]
        assert saved_data["category"] == "Carro"
        assert saved_data["type"] == "expense_variable"
        assert saved_data["amount"] == 150.0

    # =========================================================================
    # 2. P-0902: Registro Nativo de Receitas e Reembolsos
    # =========================================================================
    def test_registrar_receita_sucesso_income(self):
        """P-0902: Tool registrar_receita persiste com type='income', category='Receitas', amount > 0."""
        # Arrange
        from services.tools.finance_tool import registrar_receita
        UserContext.set_user("daniel")

        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_db.collection.return_value = mock_col

        # Act
        with patch("config.firebase.db", mock_db):
            resposta = registrar_receita(
                descricao="Salário Mensal",
                valor=12000.0,
                metodo_recebimento="Pix"
            )

        # Assert
        assert "Sucesso" in resposta
        assert "12.000,00" in resposta or "12000" in resposta
        assert mock_col.add.called
        saved_data = mock_col.add.call_args[0][0]
        assert saved_data["type"] == "income"
        assert saved_data["category"] == "Receitas"
        assert saved_data["amount"] == 12000.0
        assert saved_data["userId"] == "daniel"
        assert saved_data["payment_method"] in ["Cartão de Débito", "Cartão de Débito / Pix"]

    def test_registrar_receita_converte_valor_negativo_para_positivo(self):
        """P-0902: Se informado valor negativo para receita/reembolso, o sistema converte para valor absoluto positivo."""
        # Arrange
        from services.tools.finance_tool import registrar_receita
        UserContext.set_user("daniel")

        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_db.collection.return_value = mock_col

        # Act
        with patch("config.firebase.db", mock_db):
            registrar_receita(
                descricao="Estorno Compra Cancelada",
                valor=-250.0,
                metodo_recebimento="Cartão de Débito"
            )

        # Assert
        saved_data = mock_col.add.call_args[0][0]
        assert saved_data["amount"] == 250.0
        assert saved_data["amount"] > 0
        assert saved_data["type"] == "income"
        assert saved_data["category"] == "Receitas"

    def test_registrar_receita_reembolso_gravado_como_income_receitas(self):
        """P-0902: Reembolsos de despesas são registrados contabilmente como Receitas e nunca como despesa com categoria 'Reembolso'."""
        # Arrange
        from services.tools.finance_tool import registrar_receita
        UserContext.set_user("daniel")

        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_db.collection.return_value = mock_col

        # Act
        with patch("config.firebase.db", mock_db):
            resposta = registrar_receita(
                descricao="Reembolso de Uber corporativo",
                valor=85.50
            )

        # Assert
        saved_data = mock_col.add.call_args[0][0]
        assert saved_data["type"] == "income"
        assert saved_data["category"] == "Receitas"
        assert saved_data["category"] != "Reembolso"

    def test_api_create_transaction_income_validation(self):
        """P-0902: Endpoint POST /transactions valida receitas e rejeita valores não-positivos (HTTP 422)."""
        mock_db = MagicMock()
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "new-income-id"
        mock_db.collection.return_value.add.return_value = (None, mock_doc_ref)

        with patch("config.firebase.db", mock_db):
            # 1. Criação com sucesso de receita
            payload_ok = {
                "description": "Pix Recebido Freela",
                "amount": 1500.00,
                "category": "Receitas",
                "type": "income",
                "paymentMethod": "Cartão de Débito / Pix"
            }
            res_ok = client.post("/api/v1/finance/transactions", json=payload_ok, headers={"X-User-Id": "daniel"})
            assert res_ok.status_code in [200, 201]
            data = res_ok.json()
            assert data["type"] == "income"
            assert data["amount"] == 1500.00

            # 2. Rejeição de amount negativo ou zero (HTTP 422)
            payload_invalido = {
                "description": "Reembolso Negativo Inválido",
                "amount": -50.00,
                "category": "Receitas",
                "type": "income"
            }
            res_bad = client.post("/api/v1/finance/transactions", json=payload_invalido, headers={"X-User-Id": "daniel"})
            assert res_bad.status_code in [400, 422]

    # =========================================================================
    # 3. P-0903: Saneamento Idempotente de Dados Legados
    # =========================================================================
    def test_sanear_transacoes_legadas_remedia_anomalias(self):
        """P-0903: Rotina de saneamento converte registros anômalos para type='income' e category='Receitas'."""
        # Arrange
        from services.finance_migration_service import sanear_transacoes_legadas

        # Doc 1: categoria 'Reembolso'
        doc1 = self._criar_mock_doc("doc1", {
            "userId": "daniel",
            "description": "Reembolso hotel",
            "amount": 300.0,
            "category": "Reembolso",
            "type": "expense_variable"
        })
        # Doc 2: valor negativo
        doc2 = self._criar_mock_doc("doc2", {
            "userId": "daniel",
            "description": "Estorno passagem",
            "amount": -150.0,
            "category": "Outros",
            "type": None
        })
        # Doc 3: transação sadia (não deve ser alterada)
        doc3 = self._criar_mock_doc("doc3", {
            "userId": "daniel",
            "description": "Mercado Pão de Açúcar",
            "amount": 250.0,
            "category": "Mercado",
            "type": "expense_variable"
        })

        mock_db = MagicMock()
        mock_db.collection.return_value.stream.return_value = [doc1, doc2, doc3]

        # Act
        with patch("config.firebase.db", mock_db):
            resultado = sanear_transacoes_legadas(user_id="daniel")

        # Assert
        assert resultado["totalScanned"] == 3
        assert resultado["remediated"] == 2
        assert resultado["alreadyClean"] == 1

        # Verifica chamadas de update nos documentos anômalos
        assert doc1.reference.update.called
        update_doc1 = doc1.reference.update.call_args[0][0]
        assert update_doc1["type"] == "income"
        assert update_doc1["category"] == "Receitas"
        assert update_doc1["amount"] == 300.0

        assert doc2.reference.update.called
        update_doc2 = doc2.reference.update.call_args[0][0]
        assert update_doc2["type"] == "income"
        assert update_doc2["category"] == "Receitas"
        assert update_doc2["amount"] == 150.0

        # O doc sadio não deve ter update chamado
        assert not doc3.reference.update.called

    def test_sanear_transacoes_legadas_idempotencia(self):
        """P-0903: Execução subsequente sobre dados já limpos não deve alterar nenhum documento."""
        # Arrange
        from services.finance_migration_service import sanear_transacoes_legadas

        doc_limpo1 = self._criar_mock_doc("doc1", {
            "userId": "daniel",
            "description": "Reembolso hotel",
            "amount": 300.0,
            "category": "Receitas",
            "type": "income"
        })
        doc_limpo2 = self._criar_mock_doc("doc2", {
            "userId": "daniel",
            "description": "Mercado",
            "amount": 250.0,
            "category": "Mercado",
            "type": "expense_variable"
        })

        mock_db = MagicMock()
        mock_db.collection.return_value.stream.return_value = [doc_limpo1, doc_limpo2]

        # Act
        with patch("config.firebase.db", mock_db):
            resultado = sanear_transacoes_legadas(user_id="daniel")

        # Assert
        assert resultado["remediated"] == 0
        assert resultado["alreadyClean"] == 2
        assert not doc_limpo1.reference.update.called
        assert not doc_limpo2.reference.update.called

    def test_api_maintenance_sanitize_endpoint(self):
        """P-0903: Endpoint REST POST /maintenance/sanitize executa saneamento e retorna status."""
        # Arrange
        doc_legado = self._criar_mock_doc("leg1", {
            "userId": "daniel",
            "description": "Reembolso antigo",
            "amount": 80.0,
            "category": "Reembolso",
            "type": "expense_variable"
        })
        mock_db = MagicMock()
        mock_db.collection.return_value.stream.return_value = [doc_legado]

        # Act
        with patch("config.firebase.db", mock_db):
            response = client.post("/api/v1/finance/maintenance/sanitize", headers={"X-User-Id": "daniel"})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "remediated" in data
        res_data = data.get("data", data)
        assert res_data["remediated"] == 1
        assert res_data["status"] == "COMPLETED"

    # =========================================================================
    # 4. P-0904: Recorrência Automática de Despesas Fixas no Dashboard
    # =========================================================================
    def test_dashboard_projecao_despesa_fixa_mes_seguinte(self):
        """P-0904: Despesa fixa de mês anterior é projetada dinamicamente para o mês consultado."""
        # Arrange
        mock_db = MagicMock()

        # Despesa Fixa cadastrada em Setembro/2026 (R$ 2.000 em Casa)
        doc_fixo_set = self._criar_mock_doc("fix_aluguel", {
            "userId": "daniel",
            "description": "Aluguel Apartamento",
            "amount": 2000.0,
            "category": "Casa",
            "type": "expense_fixed",
            "date": "2026-09-05T10:00:00Z",
            "payment_method": "Cartão de Débito / Pix"
        })

        # Despesa Variável cadastrada em Outubro/2026 (R$ 300 em Mercado)
        doc_var_out = self._criar_mock_doc("var_out", {
            "userId": "daniel",
            "description": "Mercado Semanal",
            "amount": 300.0,
            "category": "Mercado",
            "type": "expense_variable",
            "date": "2026-10-10T15:00:00Z"
        })

        mock_db.collection.return_value.stream.return_value = [doc_fixo_set, doc_var_out]

        # Act - Consulta o Dashboard de Outubro/2026 (onde não há Aluguel físico cadastrado)
        with patch("config.firebase.db", mock_db):
            response = client.get("/api/v1/finance/dashboard?year=2026&month=10", headers={"X-User-Id": "daniel"})

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Totais devem projetar a despesa fixa
        assert data["totalFixed"] == 2000.0
        assert data["totalVariable"] == 300.0
        assert data["totalSpent"] == 2300.0
        assert data["balance"] == -2300.0  # 0 receitas - 2300 despesas

        # Categoria 'Casa' deve aparecer no gráfico com 2000.0
        categorias = {c["category"]: c["amount"] for c in data["expensesByCategory"]}
        assert "Casa" in categorias
        assert categorias["Casa"] == 2000.0
        assert "Mercado" in categorias
        assert categorias["Mercado"] == 300.0

        # Lista de transações deve conter a transação projetada com isRecurring=True
        tx_descriptions = [t["description"] for t in data["transactions"]]
        assert "Aluguel Apartamento" in tx_descriptions

        tx_aluguel = next(t for t in data["transactions"] if t["description"] == "Aluguel Apartamento")
        assert tx_aluguel["isRecurring"] is True
        assert tx_aluguel["type"] == "expense_fixed"
        assert tx_aluguel["amount"] == 2000.0

    def test_dashboard_despesa_variavel_nao_projetada(self):
        """P-0904: Despesa variável de mês anterior NÃO deve ser projetada para meses seguintes."""
        # Arrange
        mock_db = MagicMock()
        doc_var_antigo = self._criar_mock_doc("var_passada", {
            "userId": "daniel",
            "description": "Jantar Especial",
            "amount": 400.0,
            "category": "Lazer",
            "type": "expense_variable",
            "date": "2026-08-15T20:00:00Z"
        })
        mock_db.collection.return_value.stream.return_value = [doc_var_antigo]

        # Act - Consulta Outubro/2026
        with patch("config.firebase.db", mock_db):
            response = client.get("/api/v1/finance/dashboard?year=2026&month=10", headers={"X-User-Id": "daniel"})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["totalSpent"] == 0.0
        assert len(data["transactions"]) == 0

    def test_dashboard_deduplicacao_despesa_fixa_ja_existente(self):
        """P-0904: Se o usuário já cadastrou fisicamente a despesa fixa no mês alvo, não duplica a projeção."""
        # Arrange
        mock_db = MagicMock()

        # Cadastrada originalmente em Setembro
        doc_set = self._criar_mock_doc("fix_orig", {
            "userId": "daniel",
            "description": "Internet Fibra",
            "amount": 150.0,
            "category": "Casa",
            "type": "expense_fixed",
            "date": "2026-09-01T10:00:00Z"
        })

        # Recadastrada fisicamente em Outubro (com mesmo id de origem ou descrição)
        doc_out = self._criar_mock_doc("fix_out_fisica", {
            "userId": "daniel",
            "originId": "fix_orig",
            "description": "Internet Fibra",
            "amount": 150.0,
            "category": "Casa",
            "type": "expense_fixed",
            "date": "2026-10-01T10:00:00Z"
        })

        mock_db.collection.return_value.stream.return_value = [doc_set, doc_out]

        # Act
        with patch("config.firebase.db", mock_db):
            response = client.get("/api/v1/finance/dashboard?year=2026&month=10", headers={"X-User-Id": "daniel"})

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Deve somar apenas 150.0, e não 300.0
        assert data["totalFixed"] == 150.0
        assert len([t for t in data["transactions"] if "Internet" in t["description"]]) == 1

    def test_dashboard_despesa_fixa_inativa_nao_projetada(self):
        """P-0904: Despesa fixa cancelada (active=False) não deve ser projetada para meses posteriores ao cancelamento."""
        # Arrange
        mock_db = MagicMock()
        doc_inativo = self._criar_mock_doc("fix_academia", {
            "userId": "daniel",
            "description": "Academia Cancelada",
            "amount": 120.0,
            "category": "Lazer",
            "type": "expense_fixed",
            "active": False,
            "date": "2026-07-01T10:00:00Z"
        })
        mock_db.collection.return_value.stream.return_value = [doc_inativo]

        # Act - Consulta Outubro/2026
        with patch("config.firebase.db", mock_db):
            response = client.get("/api/v1/finance/dashboard?year=2026&month=10", headers={"X-User-Id": "daniel"})

        # Assert
        data = response.json()
        assert data["totalFixed"] == 0.0
        assert len(data["transactions"]) == 0

    def test_dashboard_filtro_type_expense_fixed_com_projecao(self):
        """P-0904: Filtro por type=expense_fixed exibe transações fixas projetadas e mantém integridade."""
        # Arrange
        mock_db = MagicMock()
        doc_fixo = self._criar_mock_doc("fix_seguro", {
            "userId": "daniel",
            "description": "Seguro Carro",
            "amount": 350.0,
            "category": "Carro",
            "type": "expense_fixed",
            "date": "2026-05-10T10:00:00Z"
        })
        mock_db.collection.return_value.stream.return_value = [doc_fixo]

        # Act
        with patch("config.firebase.db", mock_db):
            response = client.get(
                "/api/v1/finance/dashboard?year=2026&month=10&type=expense_fixed",
                headers={"X-User-Id": "daniel"}
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 1
        assert data["transactions"][0]["description"] == "Seguro Carro"
        assert data["transactions"][0]["isRecurring"] is True

    # =========================================================================
    # 5. P-0904: Recorrência de Despesas Fixas em Séries Temporais (Trends)
    # =========================================================================
    def test_trends_projecao_despesas_fixas_na_serie(self):
        """P-0904: Endpoint /trends projeta despesas fixas para todos os meses correspondentes na série temporal."""
        # Arrange
        mock_db = MagicMock()

        # Fixa iniciada em Agosto/2026 (R$ 1.000)
        doc_fixo = self._criar_mock_doc("fix_condo", {
            "userId": "daniel",
            "description": "Condomínio",
            "amount": 1000.0,
            "category": "Casa",
            "type": "expense_fixed",
            "date": "2026-08-01T10:00:00Z"
        })

        mock_db.collection.return_value.stream.return_value = [doc_fixo]

        # Act - Consulta últimos 3 meses
        with patch("config.firebase.db", mock_db):
            response = client.get("/api/v1/finance/trends?period=3m", headers={"X-User-Id": "daniel"})

        # Assert
        assert response.status_code == 200
        data = response.json()
        series = data.get("data", data).get("series", [])
        assert len(series) == 3

        # Cada um dos meses da série deve conter ao menos os 1.000 da despesa fixa projetada
        for ponto in series:
            assert ponto["expenses"] >= 1000.0

    # =========================================================================
    # 6. Multi-Tenant e Isolamento de Usuários
    # =========================================================================
    def test_isolamento_multitenant_projecao_e_saneamento(self):
        """P-0901 a P-0904: Garante que dados de um usuário nunca são projetados ou afetados por outro."""
        # Arrange
        mock_db = MagicMock()
        doc_daniel = self._criar_mock_doc("fix_daniel", {
            "userId": "daniel",
            "description": "Aluguel Daniel",
            "amount": 2500.0,
            "category": "Casa",
            "type": "expense_fixed",
            "date": "2026-08-01T10:00:00Z"
        })
        doc_lari = self._criar_mock_doc("fix_lari", {
            "userId": "lari",
            "description": "Curso Lari",
            "amount": 400.0,
            "category": "Educação",
            "type": "expense_fixed",
            "date": "2026-08-01T10:00:00Z"
        })

        mock_db.collection.return_value.stream.return_value = [doc_daniel, doc_lari]

        # Act & Assert 1: Dashboard de Daniel não projeta Curso de Lari
        with patch("config.firebase.db", mock_db):
            res_daniel = client.get("/api/v1/finance/dashboard?year=2026&month=10", headers={"X-User-Id": "daniel"})
            data_d = res_daniel.json()
            assert data_d["totalFixed"] == 2500.0
            assert all("Lari" not in t["description"] for t in data_d["transactions"])

        # Act & Assert 2: Dashboard de Lari não projeta Aluguel de Daniel
        with patch("config.firebase.db", mock_db):
            res_lari = client.get("/api/v1/finance/dashboard?year=2026&month=10", headers={"X-User-Id": "lari"})
            data_l = res_lari.json()
            assert data_l["totalFixed"] == 400.0
            assert all("Daniel" not in t["description"] for t in data_l["transactions"])
