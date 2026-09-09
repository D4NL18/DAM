import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel
from config import firebase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/finance", tags=["Finance"])

DEFAULT_CATEGORIES = [
    {"id": "cat-mercado", "name": "Mercado", "color": "#2563eb"},
    {"id": "cat-carro", "name": "Carro", "color": "#eab308"},
    {"id": "cat-oliver", "name": "Oliver", "color": "#86efac"},
    {"id": "cat-casa", "name": "Casa", "color": "#15803d"},
    {"id": "cat-familia", "name": "Família", "color": "#22c55e"},
    {"id": "cat-farmacia", "name": "Farmácia", "color": "#a855f7"},
    {"id": "cat-karen", "name": "Karen", "color": "#f472b6"},
    {"id": "cat-gatos", "name": "Gatos", "color": "#7e22ce"},
    {"id": "cat-lazer", "name": "Lazer", "color": "#06b6d4"},
    {"id": "cat-mercadinho", "name": "Mercadinho", "color": "#f97316"},
    {"id": "cat-ifood", "name": "iFood", "color": "#ef4444"},
    {"id": "cat-receitas", "name": "Receitas", "color": "#10b981"},
    {"id": "cat-outros", "name": "Outros", "color": "#64748b"}
]

DEFAULT_CARDS = [
    {"id": "card-credito-pessoal", "name": "Cartão de Crédito Pessoal", "type": "credito"},
    {"id": "card-credito-secundario", "name": "Cartão de Crédito Secundário", "type": "credito"},
    {"id": "card-debito-pix", "name": "Cartão de Débito / Pix", "type": "debito"}
]

class TransactionCreateDTO(BaseModel):
    description: str
    amount: float
    category: str
    type: Optional[str] = "expense_variable"
    paymentMethod: Optional[str] = "Cartão de Crédito Pessoal"
    installment: Optional[str] = None
    owner: Optional[str] = None
    date: Optional[str] = None

class TransactionUpdateDTO(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    type: Optional[str] = None
    paymentMethod: Optional[str] = None
    installment: Optional[str] = None
    owner: Optional[str] = None
    date: Optional[str] = None

class CategoryDTO(BaseModel):
    name: str
    color: str

class CardDTO(BaseModel):
    name: str
    type: str

def _get_category_color(category_name: str, custom_categories: List[Dict[str, Any]]) -> str:
    for cat in custom_categories:
        if cat.get("name", "").lower() == category_name.lower():
            return cat.get("color", "#64748b")
    for cat in DEFAULT_CATEGORIES:
        if cat.get("name", "").lower() == category_name.lower():
            return cat.get("color", "#64748b")
    return "#64748b"

@router.get("/dashboard")
def get_finance_dashboard(
    year: int = Query(default=datetime.now().year),
    month: int = Query(default=datetime.now().month),
    type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> Dict[str, Any]:
    """Retorna dados agregados para o dashboard avançado de finanças."""
    effective_user = x_user_id.strip() if x_user_id else "daniel"
    total_income = 0.0
    total_fixed = 0.0
    total_variable = 0.0
    
    category_map: Dict[str, float] = {}
    transactions: List[Dict[str, Any]] = []

    # Busca categorias customizadas do usuário para mapear cores
    user_cats = []
    if firebase.db is not None:
        try:
            cat_docs = firebase.db.collection("finance_categories").stream()
            for cd in cat_docs:
                cdata = cd.to_dict() or {}
                if (cdata.get("userId") or "daniel") == effective_user:
                    user_cats.append({
                        "id": cd.id,
                        "name": cdata.get("name", ""),
                        "color": cdata.get("color", "#64748b")
                    })
        except Exception as e:
            logger.warning(f"Erro ao buscar categorias customizadas: {e}")

    all_categories = user_cats if user_cats else DEFAULT_CATEGORIES

    if firebase.db is not None:
        try:
            docs = firebase.db.collection("finances").stream()
            for doc in docs:
                data = doc.to_dict() or {}
                doc_user = data.get("userId") or data.get("user_id") or "daniel"
                if doc_user != effective_user:
                    continue

                date_str = data.get("date") or data.get("created_at") or ""
                valido = True
                dt_obj = None
                if date_str:
                    try:
                        clean_date = date_str.replace("Z", "+00:00")
                        dt_obj = datetime.fromisoformat(clean_date)
                        if dt_obj.year != year or dt_obj.month != month:
                            valido = False
                    except Exception:
                        pass

                if not valido:
                    continue

                amount = float(data.get("amount") or 0.0)
                tx_type = data.get("type") or "expense_variable"
                cat = data.get("category") or "Outros"

                if tx_type == "income":
                    total_income += amount
                elif tx_type == "expense_fixed":
                    total_fixed += amount
                else:
                    total_variable += amount

                # Verifica se deve incluir na listagem e no gráfico da aba ativa
                incluir = True
                if type and type != "total" and tx_type != type:
                    incluir = False
                if category and cat.lower() != category.lower():
                    incluir = False

                if incluir:
                    if type == "income":
                        if tx_type == "income":
                            category_map[cat] = category_map.get(cat, 0.0) + amount
                    elif type == "total" or not type:
                        category_map[cat] = category_map.get(cat, 0.0) + amount
                    else:
                        if tx_type != "income":
                            category_map[cat] = category_map.get(cat, 0.0) + amount

                    transactions.append({
                        "id": doc.id,
                        "date": date_str or datetime.now(timezone.utc).isoformat(),
                        "description": data.get("description") or "Sem descrição",
                        "amount": amount,
                        "category": cat,
                        "categoryColor": _get_category_color(cat, all_categories),
                        "type": tx_type,
                        "paymentMethod": data.get("payment_method") or data.get("paymentMethod") or "Cartão de Crédito Pessoal",
                        "installment": data.get("installment"),
                        "owner": (data.get("owner") or "") if (data.get("owner") or "") != "Christian" else ""
                    })
        except Exception as e:
            logger.error(f"Erro ao processar finanças no Firestore: {e}")

    # Ordenar transações mais recentes primeiro
    transactions.sort(key=lambda x: x.get("date", ""), reverse=True)

    total_spent = total_fixed + total_variable
    balance = total_income - total_spent

    # Soma da base para percentuais do gráfico
    target_sum = sum(category_map.values()) or 1.0

    expenses_by_category = [
        {
            "category": cat_name,
            "amount": round(val, 2),
            "percentage": round((val / target_sum) * 100.0, 1),
            "color": _get_category_color(cat_name, all_categories)
        }
        for cat_name, val in sorted(category_map.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "totalSpent": round(total_spent, 2),
        "totalIncome": round(total_income, 2),
        "totalFixed": round(total_fixed, 2),
        "totalVariable": round(total_variable, 2),
        "balance": round(balance, 2),
        "currency": "BRL",
        "expensesByCategory": expenses_by_category,
        "transactions": transactions
    }

@router.post("/transactions", status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreateDTO,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> Dict[str, Any]:
    effective_user = x_user_id.strip() if x_user_id else "daniel"
    tx_id = str(uuid.uuid4())
    date_val = payload.date if payload.date else datetime.now(timezone.utc).isoformat()

    doc_data = {
        "id": tx_id,
        "userId": effective_user,
        "user_id": effective_user,
        "description": payload.description,
        "amount": payload.amount,
        "category": payload.category,
        "type": payload.type or "expense_variable",
        "payment_method": payload.paymentMethod or "Cartão de Crédito Pessoal",
        "installment": payload.installment,
        "owner": payload.owner if payload.owner and payload.owner != "Christian" else None,
        "date": date_val,
        "timestamp": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    if firebase.db is not None:
        try:
            _, ref = firebase.db.collection("finances").add(doc_data)
            doc_data["id"] = ref.id
        except Exception as e:
            logger.error(f"Erro ao salvar transação: {e}")
            raise HTTPException(status_code=500, detail="Erro ao gravar transação no banco de dados.")

    return doc_data

@router.put("/transactions/{tx_id}")
def update_transaction(
    tx_id: str,
    payload: TransactionUpdateDTO,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> Dict[str, Any]:
    update_data: Dict[str, Any] = {}
    if payload.description is not None:
        update_data["description"] = payload.description
    if payload.amount is not None:
        update_data["amount"] = payload.amount
    if payload.category is not None:
        update_data["category"] = payload.category
    if payload.type is not None:
        update_data["type"] = payload.type
    if payload.paymentMethod is not None:
        update_data["payment_method"] = payload.paymentMethod
    if payload.installment is not None:
        update_data["installment"] = payload.installment
    if payload.owner is not None:
        update_data["owner"] = payload.owner
    if payload.date is not None:
        update_data["date"] = payload.date

    if firebase.db is not None:
        try:
            firebase.db.collection("finances").document(tx_id).update(update_data)
        except Exception as e:
            logger.error(f"Erro ao atualizar transação {tx_id}: {e}")

    return {"success": True, "id": tx_id, **update_data}

@router.delete("/transactions/{tx_id}")
def delete_transaction(
    tx_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> Dict[str, Any]:
    if firebase.db is not None:
        try:
            firebase.db.collection("finances").document(tx_id).delete()
        except Exception as e:
            logger.error(f"Erro ao deletar transação {tx_id}: {e}")

    return {"success": True, "id": tx_id}

# --- Gestão de Categorias ---

@router.get("/categories")
def get_categories(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> List[Dict[str, Any]]:
    effective_user = x_user_id.strip() if x_user_id else "daniel"
    user_cats = []

    if firebase.db is not None:
        try:
            docs = firebase.db.collection("finance_categories").where("userId", "==", effective_user).stream()
            for doc in docs:
                data = doc.to_dict() or {}
                # Filtrar qualquer remanescente de 'Christian'
                if str(data.get("name", "")).strip().lower() == "christian":
                    doc.reference.delete()
                    continue
                user_cats.append({
                    "id": doc.id,
                    "name": data.get("name", ""),
                    "color": data.get("color", "#64748b")
                })
        except Exception as e:
            logger.error(f"Erro ao ler categorias no Firestore: {e}")

    # Se o usuário ainda não tem categorias salvas, semear defaults limpos (sem Christian)
    if not user_cats and firebase.db is not None:
        try:
            settings_ref = firebase.db.collection("finance_user_settings").document(effective_user)
            settings_doc = settings_ref.get()
            is_initialized = settings_doc.exists and settings_doc.to_dict().get("categories_initialized")
            if not is_initialized:
                batch = firebase.db.batch()
                for def_cat in DEFAULT_CATEGORIES:
                    if def_cat["name"].lower() == "christian":
                        continue
                    doc_ref = firebase.db.collection("finance_categories").document()
                    cat_item = {
                        "id": doc_ref.id,
                        "userId": effective_user,
                        "name": def_cat["name"],
                        "color": def_cat["color"],
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    batch.set(doc_ref, cat_item)
                    user_cats.append({
                        "id": doc_ref.id,
                        "name": def_cat["name"],
                        "color": def_cat["color"]
                    })
                settings_ref.set({"categories_initialized": True}, merge=True)
                batch.commit()
        except Exception as e:
            logger.error(f"Erro ao semear categorias padrão: {e}")

    return user_cats if user_cats else [c for c in DEFAULT_CATEGORIES if c["name"].lower() != "christian"]

@router.post("/categories", status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryDTO,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> Dict[str, Any]:
    effective_user = x_user_id.strip() if x_user_id else "daniel"
    doc_data = {
        "userId": effective_user,
        "name": payload.name.strip(),
        "color": payload.color.strip(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    if firebase.db is not None:
        try:
            doc_ref = firebase.db.collection("finance_categories").document()
            doc_data["id"] = doc_ref.id
            doc_ref.set(doc_data)
            firebase.db.collection("finance_user_settings").document(effective_user).set(
                {"categories_initialized": True}, merge=True
            )
        except Exception as e:
            logger.error(f"Erro ao adicionar categoria: {e}")
            raise HTTPException(status_code=500, detail="Erro ao adicionar categoria.")

    return doc_data

@router.put("/categories/{cat_id}")
def update_category(
    cat_id: str,
    payload: CategoryDTO,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> Dict[str, Any]:
    update_data = {
        "name": payload.name.strip(),
        "color": payload.color.strip()
    }

    if firebase.db is not None:
        try:
            firebase.db.collection("finance_categories").document(cat_id).update(update_data)
        except Exception as e:
            logger.error(f"Erro ao atualizar categoria {cat_id}: {e}")

    return {"success": True, "id": cat_id, **update_data}

@router.delete("/categories/{cat_id}")
def delete_category(
    cat_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> Dict[str, Any]:
    effective_user = x_user_id.strip() if x_user_id else "daniel"
    deleted_names = []

    if firebase.db is not None:
        try:
            # 1. Tentar deletar diretamente pelo ID do documento
            doc_ref = firebase.db.collection("finance_categories").document(cat_id)
            doc_snap = doc_ref.get()
            if doc_snap.exists:
                deleted_names.append(doc_snap.to_dict().get("name", ""))
                doc_ref.delete()

            # 2. Se não encontrou ou era id legado (ex: 'cat-christian'), procurar na coleção do usuário
            clean_name = cat_id.replace("cat-", "").strip().lower()
            query_docs = firebase.db.collection("finance_categories").where("userId", "==", effective_user).stream()
            for doc in query_docs:
                data = doc.to_dict() or {}
                d_id = str(data.get("id", "")).lower()
                d_name = str(data.get("name", "")).lower()
                if doc.id == cat_id or d_id == cat_id.lower() or d_name == clean_name or (cat_id == "cat-christian" and d_name == "christian"):
                    deleted_names.append(data.get("name", ""))
                    doc.reference.delete()

            # 3. Garantir flag categories_initialized para não ressemear categorias deletadas
            firebase.db.collection("finance_user_settings").document(effective_user).set(
                {"categories_initialized": True}, merge=True
            )

            # 4. Migrar despesas associadas para "Outros"
            for cat_name in deleted_names:
                if cat_name and cat_name != "Outros":
                    tx_docs = firebase.db.collection("finances").where("userId", "==", effective_user).where("category", "==", cat_name).stream()
                    for tx_doc in tx_docs:
                        tx_doc.reference.update({"category": "Outros"})
        except Exception as e:
            logger.error(f"Erro ao deletar categoria {cat_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Erro ao deletar categoria: {str(e)}")

    return {"success": True, "id": cat_id, "deleted_names": deleted_names}

# --- Gestão de Cartões ---

@router.get("/cards")
def get_cards(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> List[Dict[str, Any]]:
    effective_user = x_user_id.strip() if x_user_id else "daniel"
    user_cards = []

    if firebase.db is not None:
        try:
            docs = firebase.db.collection("finance_cards").where("userId", "==", effective_user).stream()
            for doc in docs:
                data = doc.to_dict() or {}
                user_cards.append({
                    "id": doc.id,
                    "name": data.get("name", ""),
                    "type": data.get("type", "credito")
                })
        except Exception as e:
            logger.error(f"Erro ao ler cartões no Firestore: {e}")

    # Inicializar cartões padrão se usuário não tiver nenhum salvo
    if not user_cards and firebase.db is not None:
        try:
            settings_ref = firebase.db.collection("finance_user_settings").document(effective_user)
            settings_doc = settings_ref.get()
            is_initialized = settings_doc.exists and settings_doc.to_dict().get("cards_initialized")
            if not is_initialized:
                batch = firebase.db.batch()
                for def_card in DEFAULT_CARDS:
                    doc_ref = firebase.db.collection("finance_cards").document()
                    card_item = {
                        "id": doc_ref.id,
                        "userId": effective_user,
                        "name": def_card["name"],
                        "type": def_card["type"],
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    batch.set(doc_ref, card_item)
                    user_cards.append({
                        "id": doc_ref.id,
                        "name": def_card["name"],
                        "type": def_card["type"]
                    })
                settings_ref.set({"cards_initialized": True}, merge=True)
                batch.commit()
        except Exception as e:
            logger.error(f"Erro ao inicializar cartões padrão: {e}")

    return user_cards if user_cards else DEFAULT_CARDS

@router.post("/cards", status_code=status.HTTP_201_CREATED)
def create_card(
    payload: CardDTO,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> Dict[str, Any]:
    effective_user = x_user_id.strip() if x_user_id else "daniel"
    doc_data = {
        "userId": effective_user,
        "name": payload.name.strip(),
        "type": payload.type.strip(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    if firebase.db is not None:
        try:
            doc_ref = firebase.db.collection("finance_cards").document()
            doc_data["id"] = doc_ref.id
            doc_ref.set(doc_data)
            firebase.db.collection("finance_user_settings").document(effective_user).set(
                {"cards_initialized": True}, merge=True
            )
        except Exception as e:
            logger.error(f"Erro ao cadastrar cartão: {e}")
            raise HTTPException(status_code=500, detail="Erro ao cadastrar cartão.")

    return doc_data

@router.put("/cards/{card_id}")
def update_card(
    card_id: str,
    payload: CardDTO,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> Dict[str, Any]:
    update_data = {
        "name": payload.name.strip(),
        "type": payload.type.strip()
    }

    if firebase.db is not None:
        try:
            firebase.db.collection("finance_cards").document(card_id).update(update_data)
        except Exception as e:
            logger.error(f"Erro ao atualizar cartão {card_id}: {e}")

    return {"success": True, "id": card_id, **update_data}

@router.delete("/cards/{card_id}")
def delete_card(
    card_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> Dict[str, Any]:
    effective_user = x_user_id.strip() if x_user_id else "daniel"
    if firebase.db is not None:
        try:
            doc_ref = firebase.db.collection("finance_cards").document(card_id)
            if doc_ref.get().exists:
                doc_ref.delete()
            else:
                clean_name = card_id.replace("card-", "").strip().lower()
                query_docs = firebase.db.collection("finance_cards").where("userId", "==", effective_user).stream()
                for doc in query_docs:
                    data = doc.to_dict() or {}
                    d_id = str(data.get("id", "")).lower()
                    d_name = str(data.get("name", "")).lower()
                    if doc.id == card_id or d_id == card_id.lower() or d_name == clean_name:
                        doc.reference.delete()

            firebase.db.collection("finance_user_settings").document(effective_user).set(
                {"cards_initialized": True}, merge=True
            )
        except Exception as e:
            logger.error(f"Erro ao deletar cartão {card_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Erro ao deletar cartão: {str(e)}")

    return {"success": True, "id": card_id}

# --- Evolução Temporal e Tendências (FG-07) ---

MONTH_NAMES_SHORT = [
    "", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez"
]

@router.get("/trends")
def get_finance_trends(
    period: str = Query(default="12m"),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> Dict[str, Any]:
    """Retorna séries históricas mensais de receitas e gastos para o período solicitado."""
    effective_user = x_user_id.strip() if x_user_id else "daniel"
    now = datetime.now(timezone.utc)

    if period == "current_month":
        num_months = 1
        period_label = "Mês atual"
    elif period == "3m":
        num_months = 3
        period_label = "Últimos 3 meses"
    elif period == "6m":
        num_months = 6
        period_label = "Últimos 6 meses"
    else:  # default "12m" ou custom
        num_months = 12
        period_label = "Últimos 12 meses"

    # Monta a série cronológica de meses (do mais antigo para o atual)
    series_map: Dict[str, Dict[str, Any]] = {}
    series_list: List[Dict[str, Any]] = []

    for i in range(num_months - 1, -1, -1):
        y = now.year
        m = now.month - i
        while m <= 0:
            m += 12
            y -= 1
        key = f"{y}-{m:02d}"
        label = f"{MONTH_NAMES_SHORT[m]} {y}"
        item = {
            "label": label,
            "year": y,
            "month": m,
            "income": 0.0,
            "expenses": 0.0,
            "balance": 0.0
        }
        series_map[key] = item
        series_list.append(item)

    # Período anterior para comparação
    prev_series_keys = set()
    for i in range(num_months * 2 - 1, num_months - 1, -1):
        y = now.year
        m = now.month - i
        while m <= 0:
            m += 12
            y -= 1
        prev_series_keys.add(f"{y}-{m:02d}")

    total_income = 0.0
    total_expenses = 0.0
    prev_income = 0.0
    prev_expenses = 0.0

    if firebase.db is not None:
        try:
            docs = firebase.db.collection("finances").stream()
            for doc in docs:
                data = doc.to_dict() or {}
                if (data.get("userId") or data.get("user_id") or "daniel") != effective_user:
                    continue

                date_str = data.get("date") or data.get("created_at") or ""
                if not date_str:
                    continue

                try:
                    dt_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    doc_key = f"{dt_obj.year}-{dt_obj.month:02d}"
                except Exception:
                    continue

                amount = float(data.get("amount") or 0.0)
                tx_type = data.get("type") or "expense_variable"

                # Período corrente da série
                if doc_key in series_map:
                    if tx_type == "income":
                        series_map[doc_key]["income"] += amount
                        total_income += amount
                    else:
                        series_map[doc_key]["expenses"] += amount
                        total_expenses += amount

                # Período comparativo anterior
                elif doc_key in prev_series_keys:
                    if tx_type == "income":
                        prev_income += amount
                    else:
                        prev_expenses += amount

        except Exception as e:
            logger.error(f"Erro ao agregar tendências financeiras no Firestore: {e}")

    for item in series_list:
        item["income"] = round(item["income"], 2)
        item["expenses"] = round(item["expenses"], 2)
        item["balance"] = round(item["income"] - item["expenses"], 2)

    total_income = round(total_income, 2)
    total_expenses = round(total_expenses, 2)
    period_balance = round(total_income - total_expenses, 2)

    has_prev = prev_income > 0 or prev_expenses > 0
    income_change = round(((total_income - prev_income) / prev_income) * 100, 1) if prev_income > 0 else 0.0
    expense_change = round(((total_expenses - prev_expenses) / prev_expenses) * 100, 1) if prev_expenses > 0 else 0.0

    return {
        "period": period,
        "periodLabel": period_label,
        "totalIncome": total_income,
        "totalExpenses": total_expenses,
        "periodBalance": period_balance,
        "currency": "BRL",
        "comparison": {
            "hasPreviousPeriod": has_prev,
            "incomeChangePct": income_change,
            "expenseChangePct": expense_change,
            "comparisonText": f"comparado com os {num_months} meses anteriores" if has_prev else "Sem período anterior"
        },
        "series": series_list
    }

