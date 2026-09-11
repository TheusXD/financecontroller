import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import os
import re
import io

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="Gestão Financeira Pessoal",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# ESTILOS VISUAIS PERSONALIZADOS (DARK THEME / GLASSMORPHISM)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Estilização geral */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0d1322 0%, #070a12 90%);
        color: #e2e8f0;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }
    
    /* Cards Métricos Customizados */
    .metric-card {
        background: rgba(21, 28, 46, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 4px;
    }
    .metric-sub {
        font-size: 0.82rem;
        color: #64748b;
    }
    .badge-positive {
        color: #10b981;
        font-weight: 600;
    }
    .badge-negative {
        color: #ef4444;
        font-weight: 600;
    }
    .badge-warning {
        color: #f59e0b;
        font-weight: 600;
    }

    /* Cards de Metas */
    .goal-card {
        background: rgba(17, 24, 39, 0.75);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 12px;
    }
    .goal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .goal-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #f1f5f9;
    }
    .goal-values {
        font-size: 0.88rem;
        font-weight: 500;
        color: #cbd5e1;
    }

    /* Caixa informativa de destaque */
    .info-box {
        background: rgba(30, 41, 59, 0.6);
        border-left: 4px solid #6366f1;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 12px 0;
    }

    /* Ocultar elementos desnecessários do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# AUTENTICAÇÃO E CONTROLE DE ACESSO (PIN / SENHA MESTRE)
# -----------------------------------------------------------------------------
def verificar_autenticacao():
    """Garante que apenas usuários autorizados com a senha mestre acessem o painel."""
    senha_correta = None
    if hasattr(st, "secrets") and "APP_PASSWORD" in st.secrets:
        senha_correta = str(st.secrets["APP_PASSWORD"])
    elif os.environ.get("APP_PASSWORD"):
        senha_correta = str(os.environ.get("APP_PASSWORD"))
    
    usando_senha_padrao = False
    if not senha_correta:
        senha_correta = "1234"
        usando_senha_padrao = True

    if st.session_state.get("autenticado", False):
        return True

    # Tela de Login Centralizada
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.4, 1])
    with col_l2:
        st.markdown("""
        <div style="background: rgba(21, 28, 46, 0.9); border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 18px; padding: 28px 24px 18px 24px; box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6); backdrop-filter: blur(14px); text-align: center;">
            <div style="font-size: 2.8rem; margin-bottom: 8px;">🔐</div>
            <h3 style="color: #ffffff; margin-bottom: 6px; font-weight: 700;">Painel Financeiro Protegido</h3>
            <p style="color: #94a3b8; font-size: 0.88rem; margin-bottom: 20px;">Acesso restrito. Digite a senha para visualizar suas finanças.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("form_login_app"):
            senha_digitada = st.text_input("Senha de Acesso", type="password", placeholder="Digite sua senha...")
            btn_entrar = st.form_submit_button("🔓 Desbloquear Painel", use_container_width=True, type="primary")
            if btn_entrar:
                if senha_digitada == senha_correta:
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta! Tente novamente.")
                    
        if usando_senha_padrao:
            st.caption("ℹ️ Senha inicial temporária: `1234`. Altere definindo `APP_PASSWORD = '...'` nos Secrets do Streamlit Cloud.")

    return False

# Bloqueia execução caso não esteja autenticado
if not verificar_autenticacao():
    st.stop()


# -----------------------------------------------------------------------------
# CONEXÃO COM O SUPABASE
# -----------------------------------------------------------------------------
@st.cache_resource
def get_supabase_client():
    """Inicializa e retorna o cliente Supabase lendo exclusivamente dos segredos."""
    url = None
    key = None

    if hasattr(st, "secrets"):
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")

    if not url:
        url = os.environ.get("SUPABASE_URL")
    if not key:
        key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        st.error("🔒 **Credenciais do Supabase não configuradas.**")
        st.info("Por segurança, as chaves não ficam armazenadas no código-fonte. "
                "Adicione `SUPABASE_URL` e `SUPABASE_KEY` na aba **Secrets** do Streamlit Cloud.")
        st.stop()

    try:
        from supabase import create_client
        return create_client(url, key)
    except ImportError:
        st.error("⚠️ Biblioteca `supabase` não encontrada. Adicione `supabase` ao seu requirements.txt.")
        return None
    except Exception as e:
        st.error(f"⚠️ Erro ao conectar ao Supabase: {str(e)}")
        return None


# -----------------------------------------------------------------------------
# OPERAÇÕES DE DADOS (CACHE & REQUISIÇÕES)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=30)
def carregar_configuracoes():
    """Carrega os parâmetros orçamentários do Supabase ou usa defaults de negócio."""
    defaults = {
        "renda_liquida": 3300.00,
        "custo_aluguel": 1200.00,
        "custo_energia": 100.00,
        "custo_agua": 0.00,
        "custo_seguro_carro": 168.00,
        "custo_parcela_divida": 150.00,
        "meta_reserva_emergencia": 5000.00,
        "aporte_mensal_reserva": 400.00,
        "teto_semanal_combustivel": 150.00,
        "teto_semanal_alimentacao": 200.00,
        "pluggy_item_id": ""
    }
    
    supabase = get_supabase_client()
    if not supabase:
        return defaults

    try:
        response = supabase.table("configuracoes_financeiras").select("*").eq("id", 1).execute()
        if response.data and len(response.data) > 0:
            row = response.data[0]
            for key in defaults.keys():
                if key in row and row[key] is not None:
                    if key == "pluggy_item_id":
                        defaults[key] = str(row[key])
                    else:
                        defaults[key] = float(row[key])
    except Exception:
        pass
        
    return defaults


# -----------------------------------------------------------------------------
# INTEGRAÇÃO OPEN FINANCE (PLUGGY.AI)
# -----------------------------------------------------------------------------
def pluggy_obter_api_key(client_id, client_secret):
    """Autentica na Pluggy e obtém o apiKey temporário."""
    import urllib.request
    import json
    url = "https://api.pluggy.ai/auth"
    payload = json.dumps({"clientId": client_id.strip(), "clientSecret": client_secret.strip()}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("apiKey")
    except Exception:
        return None

def pluggy_criar_connect_token(api_key):
    """Gera o token de conexão para abrir o widget do Pluggy Connect."""
    import urllib.request
    import json
    url = "https://api.pluggy.ai/connect_token"
    payload = json.dumps({}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "X-API-KEY": api_key})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("accessToken")
    except Exception:
        return None

def pluggy_consultar_item(api_key, item_id):
    """Consulta o status de um item (conexão bancária)."""
    import urllib.request
    import json
    url = f"https://api.pluggy.ai/items/{item_id.strip()}"
    req = urllib.request.Request(url, headers={"X-API-KEY": api_key})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

def pluggy_listar_contas(api_key, item_id):
    """Retorna as contas vinculadas ao item (conta e cartão)."""
    import urllib.request
    import json
    url = f"https://api.pluggy.ai/accounts?itemId={item_id.strip()}"
    req = urllib.request.Request(url, headers={"X-API-KEY": api_key})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("results", [])
    except Exception:
        return []

def pluggy_buscar_transacoes(api_key, account_id, data_inicio="2026-01-01"):
    """Busca transações de uma conta na Pluggy."""
    import urllib.request
    import json
    url = f"https://api.pluggy.ai/transactions?accountId={account_id}&from={data_inicio}&pageSize=500"
    req = urllib.request.Request(url, headers={"X-API-KEY": api_key})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("results", [])
    except Exception:
        return []


def salvar_configuracoes(novos_dados):
    """Atualiza as configurações orçamentárias no banco."""
    supabase = get_supabase_client()
    if not supabase:
        return False
    try:
        novos_dados["atualizado_em"] = datetime.utcnow().isoformat()
        supabase.table("configuracoes_financeiras").upsert({"id": 1, **novos_dados}).execute()
        carregar_configuracoes.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {e}")
        return False


@st.cache_data(ttl=20)
def carregar_transacoes():
    """Busca todas as transações cadastradas no Supabase."""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()

    try:
        response = supabase.table("transacoes").select("*").order("data_transacao", desc=True).execute()
        if not response.data:
            return pd.DataFrame(columns=["id", "data_transacao", "estabelecimento", "valor", "categoria", "tipo"])
        
        df = pd.DataFrame(response.data)
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
        df["data_transacao"] = pd.to_datetime(df["data_transacao"], errors="coerce", utc=True)
        # Converte para horário de Brasília e remove o fuso para evitar conflito de timezone no pandas
        try:
            df["data_transacao"] = df["data_transacao"].dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None)
        except Exception:
            df["data_transacao"] = df["data_transacao"].dt.tz_localize(None)
        # Preenche categorias vazias
        df["categoria"] = df["categoria"].fillna("Outros").replace("", "Outros")
        return df
    except Exception as e:
        st.error(f"Erro ao buscar transações: {e}")
        return pd.DataFrame()


def inserir_transacao_manual(estabelecimento, valor, categoria, tipo, data_hora):
    """Insere um lançamento manual no Supabase."""
    supabase = get_supabase_client()
    if not supabase:
        return False
    try:
        payload = {
            "estabelecimento": estabelecimento.strip(),
            "valor": float(valor),
            "tipo": tipo,
            "data_transacao": data_hora.isoformat()
        }
        if categoria and categoria != "Automática (Trigger)":
            payload["categoria"] = categoria
            
        supabase.table("transacoes").insert(payload).execute()
        carregar_transacoes.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir transação: {e}")
        return False


def inserir_transacoes_lote(lista_transacoes):
    """Insere múltiplas transações no Supabase com autocategorização automática via trigger."""
    supabase = get_supabase_client()
    if not supabase:
        return False, "Cliente Supabase não conectado"
    try:
        payloads = []
        for t in lista_transacoes:
            dt = t["data_transacao"]
            dt_str = dt.isoformat() if hasattr(dt, "isoformat") else str(dt)
            item = {
                "estabelecimento": str(t["estabelecimento"]).strip()[:200],
                "valor": float(t["valor"]),
                "tipo": str(t.get("tipo", "Extrato Importado")),
                "data_transacao": dt_str
            }
            if "categoria" in t and t["categoria"] and t["categoria"] != "Outros":
                item["categoria"] = t["categoria"]
            payloads.append(item)
            
        # Inserção em blocos de 50 registros para estabilidade
        total_inserido = 0
        for i in range(0, len(payloads), 50):
            lote = payloads[i:i + 50]
            supabase.table("transacoes").insert(lote).execute()
            total_inserido += len(lote)
            
        carregar_transacoes.clear()
        return True, total_inserido
    except Exception as e:
        return False, str(e)


def atualizar_categoria_transacao(transacao_id, nova_categoria):
    """Atualiza a categoria de uma transação existente."""
    supabase = get_supabase_client()
    if not supabase:
        return False
    try:
        supabase.table("transacoes").update({"categoria": nova_categoria}).eq("id", transacao_id).execute()
        carregar_transacoes.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar categoria: {e}")
        return False


def excluir_transacao(transacao_id):
    """Remove uma transação do banco de dados."""
    supabase = get_supabase_client()
    if not supabase:
        return False
    try:
        supabase.table("transacoes").delete().eq("id", transacao_id).execute()
        carregar_transacoes.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir transação: {e}")
        return False


# -----------------------------------------------------------------------------
# PARSERS DE EXTRATO (OFX & CSV DO NUBANK)
# -----------------------------------------------------------------------------
def parse_extrato_ofx(conteudo_texto):
    """Lê o conteúdo de um arquivo OFX do Nubank ou outros bancos e extrai as transações."""
    transacoes = []
    padrao_trn = re.compile(r"<STMTTRN>(.*?)(?:</STMTTRN>|(?=<STMTTRN>)|$)", re.DOTALL | re.IGNORECASE)
    blocos = padrao_trn.findall(conteudo_texto)
    
    for bloco in blocos:
        data_match = re.search(r"<DTPOSTED>(\d{8})", bloco, re.IGNORECASE)
        valor_match = re.search(r"<TRNAMT>([^\r\n<]+)", bloco, re.IGNORECASE)
        memo_match = re.search(r"<MEMO>([^\r\n<]+)", bloco, re.IGNORECASE)
        
        if valor_match and memo_match:
            try:
                val_raw = valor_match.group(1).strip().replace(",", ".")
                val_float = float(val_raw)
                valor = abs(val_float)
                if valor == 0:
                    continue
                
                descricao = memo_match.group(1).strip()
                # Limpa prefixos frequentes do extrato do Nubank
                estab_limpo = re.sub(
                    r"^(Compra no d[eé]bito\s*-\s*|Compra no cr[eé]dito\s*-\s*|Transfer[eê]ncia enviada\s*-\s*|Transfer[eê]ncia recebida\s*-\s*|Pagamento de fatura\s*-\s*)",
                    "", descricao, flags=re.IGNORECASE
                ).strip()
                if not estab_limpo:
                    estab_limpo = descricao
                
                dt_str = data_match.group(1) if data_match else datetime.now().strftime("%Y%m%d")
                dt = datetime.strptime(dt_str[:8], "%Y%m%d")
                
                tipo_trn = "Nubank Extrato (Débito)" if val_float < 0 else "Entrada / Receita"
                
                transacoes.append({
                    "data_transacao": dt,
                    "estabelecimento": estab_limpo,
                    "valor": valor,
                    "tipo": tipo_trn
                })
            except Exception:
                continue
                
    return transacoes


def parse_extrato_csv(arquivo_bytes):
    """Lê o extrato CSV do Nubank (conta corrente ou fatura de cartão) e padroniza."""
    try:
        df_csv = pd.read_csv(arquivo_bytes, sep=None, engine='python')
    except Exception:
        arquivo_bytes.seek(0)
        df_csv = pd.read_csv(arquivo_bytes, sep=';')
        
    cols_lower = {str(c).lower().strip(): c for c in df_csv.columns}
    transacoes = []
    
    # Formato Cartão de Crédito Nubank: date, category, title, amount
    if "title" in cols_lower and "amount" in cols_lower:
        col_title = cols_lower["title"]
        col_amount = cols_lower["amount"]
        col_date = cols_lower.get("date", None)
        col_cat = cols_lower.get("category", None)
        
        for _, row in df_csv.iterrows():
            try:
                estab = str(row[col_title]).strip()
                val = float(str(row[col_amount]).replace(",", "."))
                dt = pd.to_datetime(row[col_date]) if col_date and pd.notna(row[col_date]) else datetime.now()
                cat = str(row[col_cat]).strip() if col_cat and pd.notna(row[col_cat]) else "Outros"
                transacoes.append({
                    "data_transacao": dt,
                    "estabelecimento": estab,
                    "valor": abs(val),
                    "categoria": cat,
                    "tipo": "Nubank Cartão (CSV)"
                })
            except Exception:
                continue
                
    # Formato Conta Corrente Nubank: Data, Valor, Identificador, Descrição
    else:
        col_data = next((c for c in df_csv.columns if "data" in str(c).lower()), None)
        col_valor = next((c for c in df_csv.columns if "valor" in str(c).lower()), None)
        col_desc = next((c for c in df_csv.columns if any(x in str(c).lower() for x in ["descri", "identifica", "t[ií]tulo", "origem", "destino"])), None)
        
        if col_valor and col_desc:
            for _, row in df_csv.iterrows():
                try:
                    val_raw = str(row[col_valor]).replace("R$", "").strip().replace(".", "").replace(",", ".")
                    val = float(val_raw)
                    estab = str(row[col_desc]).strip()
                    dt = pd.to_datetime(row[col_data], dayfirst=True) if col_data and pd.notna(row[col_data]) else datetime.now()
                    
                    transacoes.append({
                        "data_transacao": dt,
                        "estabelecimento": estab,
                        "valor": abs(val),
                        "tipo": "Nubank Conta (CSV)"
                    })
                except Exception:
                    continue

    return transacoes


def filtrar_duplicadas(novas_transacoes, df_existentes):
    """Detecta transações já registradas no banco para evitar compras duplicadas."""
    if df_existentes.empty:
        return novas_transacoes, 0
        
    duplicadas = 0
    unicas = []
    
    chaves_existentes = set()
    for _, row in df_existentes.iterrows():
        try:
            dt_str = pd.to_datetime(row["data_transacao"]).strftime("%Y-%m-%d")
            estab = str(row["estabelecimento"]).lower().strip()
            val = round(float(row["valor"]), 2)
            chaves_existentes.add((dt_str, estab, val))
        except Exception:
            continue
            
    for t in novas_transacoes:
        try:
            dt_str = pd.to_datetime(t["data_transacao"]).strftime("%Y-%m-%d")
            estab = str(t["estabelecimento"]).lower().strip()
            val = round(float(t["valor"]), 2)
            if (dt_str, estab, val) in chaves_existentes:
                duplicadas += 1
            else:
                unicas.append(t)
                chaves_existentes.add((dt_str, estab, val))
        except Exception:
            unicas.append(t)
            
    return unicas, duplicadas


# -----------------------------------------------------------------------------
# CARREGAMENTO DE DADOS INICIAIS
# -----------------------------------------------------------------------------
config = carregar_configuracoes()
df_todas = carregar_transacoes()

LISTA_CATEGORIAS = [
    "Alimentação",
    "Transporte / Combustível",
    "Supermercado",
    "Saúde",
    "Lazer & Streaming",
    "Compras & Vestuário",
    "Moradia & Contas",
    "Reserva de Emergência",
    "Dívidas",
    "Outros"
]


# -----------------------------------------------------------------------------
# SIDEBAR: FILTROS, LANÇAMENTO MANUAL & AJUSTES
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 💳 **Gestão Financeira**")
    st.caption("100% Nuvem • Supabase • Open Finance")
    st.markdown("---")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Atualizar", use_container_width=True):
            carregar_transacoes.clear()
            carregar_configuracoes.clear()
            st.rerun()
    with col_btn2:
        if st.button("🔒 Bloquear", use_container_width=True):
            st.session_state["autenticado"] = False
            st.rerun()

    st.markdown("#### 📅 **Filtro de Período**")
    modo_periodo = st.radio(
        "Visualizar:",
        ["Mês Selecionado", "Todo o Histórico"],
        index=0,
        horizontal=True
    )

    data_atual = datetime.now()
    mes_selecionado = data_atual.month
    ano_selecionado = data_atual.year

    if modo_periodo == "Mês Selecionado":
        col_m, col_a = st.columns(2)
        meses_nomes = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        with col_m:
            mes_nome = st.selectbox("Mês", meses_nomes, index=data_atual.month - 1)
            mes_selecionado = meses_nomes.index(mes_nome) + 1
        with col_a:
            anos_disponiveis = [data_atual.year - 1, data_atual.year, data_atual.year + 1]
            ano_selecionado = st.selectbox("Ano", anos_disponiveis, index=1)

    st.markdown("---")

    # Formulário de Lançamento Manual
    with st.expander("➕ **Novo Lançamento Manual**", expanded=False):
        st.caption("Gastos em dinheiro, Pix avulso ou fora do Nubank")
        with st.form("form_novo_lancamento", clear_on_submit=True):
            novo_estab = st.text_input("Estabelecimento / Descrição*", placeholder="Ex: Feira de Domingo, Padaria")
            novo_valor = st.number_input("Valor (R$)*", min_value=0.01, step=1.00, format="%.2f")
            nova_cat = st.selectbox("Categoria", ["Automática (Trigger)"] + LISTA_CATEGORIAS)
            novo_tipo = st.selectbox("Tipo de Pagamento", ["Dinheiro Físico", "Pix Manual", "Cartão de Crédito", "Cartão de Débito", "Outro"])
            novo_data = st.date_input("Data da Transação", value=date.today())
            
            submetido = st.form_submit_button("💾 Salvar Lançamento", use_container_width=True)
            if submetido:
                if not novo_estab:
                    st.error("Informe o estabelecimento!")
                else:
                    data_hora = datetime.combine(novo_data, datetime.now().time())
                    if inserir_transacao_manual(novo_estab, novo_valor, nova_cat, novo_tipo, data_hora):
                        st.success(f"Transação de R$ {novo_valor:.2f} registrada com sucesso!")
                        st.rerun()

    # Parâmetros Orçamentários e Metas
    with st.expander("⚙️ **Ajustar Parâmetros & Metas**", expanded=False):
        st.caption("Altere a renda, custos fixos e tetos orçamentários")
        with st.form("form_parametros"):
            cfg_renda = st.number_input("Renda Líquida Mensal (R$)", value=float(config["renda_liquida"]), step=50.0)
            st.markdown("**Custos Fixos:**")
            cfg_aluguel = st.number_input("Aluguel (R$)", value=float(config["custo_aluguel"]), step=50.0)
            cfg_energia = st.number_input("Energia Elétrica (R$)", value=float(config["custo_energia"]), step=10.0)
            cfg_agua = st.number_input("Água (R$)", value=float(config["custo_agua"]), step=10.0)
            cfg_seguro = st.number_input("Seguro do Carro (R$)", value=float(config["custo_seguro_carro"]), step=10.0)
            cfg_divida = st.number_input("Parcelas de Dívidas (R$)", value=float(config["custo_parcela_divida"]), step=10.0)
            
            st.markdown("**Metas & Tetos:**")
            cfg_meta_reserva = st.number_input("Meta Reserva Emergência (R$)", value=float(config["meta_reserva_emergencia"]), step=500.0)
            cfg_aporte_reserva = st.number_input("Aporte Mensal Planejado (R$)", value=float(config["aporte_mensal_reserva"]), step=50.0)
            cfg_teto_combustivel = st.number_input("Teto Semanal Combustível (R$)", value=float(config["teto_semanal_combustivel"]), step=20.0)
            cfg_teto_alimentacao = st.number_input("Teto Semanal Alimentação (R$)", value=float(config["teto_semanal_alimentacao"]), step=20.0)

            if st.form_submit_button("Salvar Novos Parâmetros", use_container_width=True):
                novos_params = {
                    "renda_liquida": cfg_renda,
                    "custo_aluguel": cfg_aluguel,
                    "custo_energia": cfg_energia,
                    "custo_agua": cfg_agua,
                    "custo_seguro_carro": cfg_seguro,
                    "custo_parcela_divida": cfg_divida,
                    "meta_reserva_emergencia": cfg_meta_reserva,
                    "aporte_mensal_reserva": cfg_aporte_reserva,
                    "teto_semanal_combustivel": cfg_teto_combustivel,
                    "teto_semanal_alimentacao": cfg_teto_alimentacao
                }
                if salvar_configuracoes(novos_params):
                    st.success("Configurações salvas no Supabase!")
                    st.rerun()


# -----------------------------------------------------------------------------
# PROCESSAMENTO DOS DADOS PARA O PERÍODO SELECIONADO
# -----------------------------------------------------------------------------
renda_liquida = config["renda_liquida"]
total_custos_fixos = (
    config["custo_aluguel"] +
    config["custo_energia"] +
    config["custo_agua"] +
    config["custo_seguro_carro"] +
    config["custo_parcela_divida"]
)

if not df_todas.empty and "data_transacao" in df_todas.columns:
    if modo_periodo == "Mês Selecionado":
        df_periodo = df_todas[
            (df_todas["data_transacao"].dt.month == mes_selecionado) &
            (df_todas["data_transacao"].dt.year == ano_selecionado)
        ].copy()
    else:
        df_periodo = df_todas.copy()
else:
    df_periodo = pd.DataFrame(columns=["id", "data_transacao", "estabelecimento", "valor", "categoria", "tipo"])

df_gastos_variaveis = df_periodo[df_periodo["categoria"] != "Reserva de Emergência"] if not df_periodo.empty else df_periodo
total_variavel_gasto = df_gastos_variaveis["valor"].sum() if not df_gastos_variaveis.empty else 0.0
total_aporte_reserva_mes = df_periodo[df_periodo["categoria"] == "Reserva de Emergência"]["valor"].sum() if not df_periodo.empty else 0.0
total_reserva_acumulado = df_todas[df_todas["categoria"] == "Reserva de Emergência"]["valor"].sum() if not df_todas.empty else 0.0

saldo_restante = renda_liquida - total_custos_fixos - total_variavel_gasto
total_comprometido = total_custos_fixos + total_variavel_gasto
perc_comprometido = (total_comprometido / renda_liquida * 100) if renda_liquida > 0 else 0.0

periodo_str = f"{meses_nomes[mes_selecionado - 1]} de {ano_selecionado}" if modo_periodo == "Mês Selecionado" else "Todo o Histórico"


# -----------------------------------------------------------------------------
# CABEÇALHO DO DASHBOARD
# -----------------------------------------------------------------------------
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.markdown(f"## 📊 Painel de Controle Financeiro • **{periodo_str}**")
    st.markdown(
        f"<span style='color: #94a3b8;'>Hospedagem 100% Nuvem • "
        f"<b>{len(df_periodo)} transações</b> registradas no período.</span>",
        unsafe_allow_html=True
    )

with col_head2:
    if perc_comprometido <= 75:
        st.markdown("""
        <div style='background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; border-radius: 10px; padding: 10px; text-align: center;'>
            <span style='color: #10b981; font-weight: 700; font-size: 0.95rem;'>🟢 SAÚDE FINANCEIRA BOA</span><br>
            <span style='color: #cbd5e1; font-size: 0.78rem;'>Orçamento sob controle</span>
        </div>
        """, unsafe_allow_html=True)
    elif perc_comprometido <= 90:
        st.markdown("""
        <div style='background: rgba(245, 158, 11, 0.15); border: 1px solid #f59e0b; border-radius: 10px; padding: 10px; text-align: center;'>
            <span style='color: #f59e0b; font-weight: 700; font-size: 0.95rem;'>🟡 ATENÇÃO AO TETO</span><br>
            <span style='color: #cbd5e1; font-size: 0.78rem;'>Comprometimento elevado</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; border-radius: 10px; padding: 10px; text-align: center;'>
            <span style='color: #ef4444; font-weight: 700; font-size: 0.95rem;'>🔴 ALERTA DE DÉFICIT</span><br>
            <span style='color: #cbd5e1; font-size: 0.78rem;'>Limite mensal ultrapassado</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# NAVEGAÇÃO PRINCIPAL EM ABAS
# -----------------------------------------------------------------------------
tab_painel, tab_importar, tab_transacoes, tab_conexoes = st.tabs([
    "📊 Visão Geral & Métricas",
    "📥 Importar Extrato (Nubank OFX / CSV)",
    "📋 Extrato Detalhado & Ações",
    "🌐 Open Finance & Automações"
])


# =============================================================================
# ABA 1: VISÃO GERAL & MÉTRICAS
# =============================================================================
with tab_painel:
    # CARDS DE MÉTRICAS KPI (GRID COM 5 COLUNAS)
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">💵 Renda Líquida</div>
            <div class="metric-value">R$ {renda_liquida:,.2f}</div>
            <div class="metric-sub">Entrada fixa mensal</div>
        </div>
        """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🔒 Custos Fixos</div>
            <div class="metric-value">R$ {total_custos_fixos:,.2f}</div>
            <div class="metric-sub">Aluguel, Luz, Seguro, Dívida</div>
        </div>
        """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🛍️ Gastos Variáveis</div>
            <div class="metric-value">R$ {total_variavel_gasto:,.2f}</div>
            <div class="metric-sub">{len(df_gastos_variaveis)} compras efetuadas</div>
        </div>
        """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)

    with col4:
        saldo_class = "badge-positive" if saldo_restante >= 0 else "badge-negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">💰 Saldo Restante</div>
            <div class="metric-value {saldo_class}">R$ {saldo_restante:,.2f}</div>
            <div class="metric-sub">Livre para metas / poupar</div>
        </div>
        """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)

    with col5:
        pct_class = "badge-positive" if perc_comprometido <= 75 else ("badge-warning" if perc_comprometido <= 90 else "badge-negative")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📈 Comprometido</div>
            <div class="metric-value {pct_class}">{perc_comprometido:.1f}%</div>
            <div class="metric-sub">Do orçamento mensal</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # METAS ATIVAS & TETOS SEMANAIS
    st.markdown("### 🎯 **Metas Orçamentárias & Tetos de Gastos**")

    hoje = date.today()
    inicio_semana = pd.Timestamp(datetime.combine(hoje - timedelta(days=hoje.weekday()), datetime.min.time()))
    fim_semana = pd.Timestamp(inicio_semana + timedelta(days=6, hours=23, minutes=59, seconds=59))

    if not df_todas.empty and "data_transacao" in df_todas.columns:
        data_col = df_todas["data_transacao"]
        if hasattr(data_col.dt, "tz") and data_col.dt.tz is not None:
            data_col = data_col.dt.tz_localize(None)

        df_semana = df_todas[
            (data_col >= inicio_semana) &
            (data_col <= fim_semana)
        ]
        gasto_combustivel_semana = df_semana[df_semana["categoria"] == "Transporte / Combustível"]["valor"].sum()
        gasto_alimentacao_semana = df_semana[df_semana["categoria"] == "Alimentação"]["valor"].sum()
    else:
        gasto_combustivel_semana = 0.0
        gasto_alimentacao_semana = 0.0

    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)

    with col_meta1:
        meta_reserva = config["meta_reserva_emergencia"]
        prog_reserva = min(total_reserva_acumulado / meta_reserva, 1.0) if meta_reserva > 0 else 0.0
        st.markdown(f"""
        <div class="goal-card">
            <div class="goal-header">
                <span class="goal-title">🛡️ Reserva de Emergência</span>
                <span class="goal-values">{prog_reserva*100:.1f}%</span>
            </div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #6366f1;">
                R$ {total_reserva_acumulado:,.2f} <span style="font-size: 0.8rem; color: #94a3b8;">/ R$ {meta_reserva:,.2f}</span>
            </div>
            <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 4px;">
                Aporte este mês: <b>R$ {total_aporte_reserva_mes:,.2f}</b> (Meta: R$ {config['aporte_mensal_reserva']:,.2f})
            </div>
        </div>
        """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        st.progress(prog_reserva)

    with col_meta2:
        teto_comb = config["teto_semanal_combustivel"]
        prog_comb = min(gasto_combustivel_semana / teto_comb, 1.0) if teto_comb > 0 else 0.0
        cor_comb = "#10b981" if gasto_combustivel_semana <= teto_comb else "#ef4444"
        st.markdown(f"""
        <div class="goal-card">
            <div class="goal-header">
                <span class="goal-title">⛽ Teto Semanal: Combustível</span>
                <span class="goal-values" style="color: {cor_comb};">{(gasto_combustivel_semana/teto_comb*100):.0f}%</span>
            </div>
            <div style="font-size: 1.3rem; font-weight: 700; color: {cor_comb};">
                R$ {gasto_combustivel_semana:,.2f} <span style="font-size: 0.8rem; color: #94a3b8;">/ R$ {teto_comb:,.2f}</span>
            </div>
            <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 4px;">
                Semana: {inicio_semana.strftime('%d/%m')} a {fim_semana.strftime('%d/%m')}
            </div>
        </div>
        """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        st.progress(prog_comb)

    with col_meta3:
        teto_alim = config["teto_semanal_alimentacao"]
        prog_alim = min(gasto_alimentacao_semana / teto_alim, 1.0) if teto_alim > 0 else 0.0
        cor_alim = "#10b981" if gasto_alimentacao_semana <= teto_alim else "#ef4444"
        st.markdown(f"""
        <div class="goal-card">
            <div class="goal-header">
                <span class="goal-title">🍔 Teto Semanal: Alimentação</span>
                <span class="goal-values" style="color: {cor_alim};">{(gasto_alimentacao_semana/teto_alim*100):.0f}%</span>
            </div>
            <div style="font-size: 1.3rem; font-weight: 700; color: {cor_alim};">
                R$ {gasto_alimentacao_semana:,.2f} <span style="font-size: 0.8rem; color: #94a3b8;">/ R$ {teto_alim:,.2f}</span>
            </div>
            <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 4px;">
                Semana: {inicio_semana.strftime('%d/%m')} a {fim_semana.strftime('%d/%m')}
            </div>
        </div>
        """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        st.progress(prog_alim)

    with col_meta4:
        parcela_divida = config["custo_parcela_divida"]
        st.markdown(f"""
        <div class="goal-card">
            <div class="goal-header">
                <span class="goal-title">💳 Quitação de Dívidas</span>
                <span class="goal-values" style="color: #38bdf8;">Ativa</span>
            </div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #38bdf8;">
                R$ {parcela_divida:,.2f} <span style="font-size: 0.8rem; color: #94a3b8;">/ mês</span>
            </div>
            <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 4px;">
                Alocação fixa garantida no orçamento
            </div>
        </div>
        """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        st.progress(1.0)

    st.markdown("<br>", unsafe_allow_html=True)

    # GRÁFICOS ANALÍTICOS (PLOTLY INTERATIVO)
    st.markdown("### 📈 **Análise Visual de Gastos**")
    col_g1, col_g2 = st.columns([1, 1.2])

    with col_g1:
        st.markdown("##### 🍩 **Divisão de Gastos por Categoria**")
        if not df_gastos_variaveis.empty:
            df_cat = df_gastos_variaveis.groupby("categoria")["valor"].sum().reset_index()
            fig_donut = px.pie(
                df_cat,
                names="categoria",
                values="valor",
                hole=0.55,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_donut.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>(%{percent})<extra></extra>"
            )
            fig_donut.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#e2e8f0", size=12),
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=330
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("Nenhuma despesa variável registrada neste período para exibir o gráfico.")

    with col_g2:
        st.markdown("##### 📅 **Evolução Diária de Gastos no Mês**")
        if not df_gastos_variaveis.empty:
            df_dia = df_gastos_variaveis.copy()
            df_dia["dia"] = df_dia["data_transacao"].dt.date
            df_dia_grp = df_dia.groupby("dia")["valor"].sum().reset_index()

            fig_bar = px.bar(
                df_dia_grp,
                x="dia",
                y="valor",
                labels={"dia": "Data", "valor": "Total Gasto (R$)"},
                color_discrete_sequence=["#6366f1"]
            )
            fig_bar.update_traces(
                marker_line_width=0,
                hovertemplate="<b>%{x|%d/%m/%Y}</b><br>R$ %{y:,.2f}<extra></extra>"
            )
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#94a3b8"),
                xaxis=dict(showgrid=False, tickformat="%d/%m"),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
                margin=dict(t=10, b=10, l=10, r=10),
                height=330
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Nenhum dado diário disponível para o período selecionado.")


# =============================================================================
# ABA 2: IMPORTADOR DE EXTRATO (OFX / CSV DO NUBANK COM 1 CLIQUE)
# =============================================================================
with tab_importar:
    st.markdown("### 📥 **Importar Extrato do Nubank (100% Automático)**")
    
    st.markdown("""
    <div class="info-box">
        <b>💡 Como pegar o arquivo no app do Nubank (em 10 segundos):</b><br>
        1. Abra o app do <b>Nubank</b> no celular.<br>
        2. Toque na sua <b>Conta</b> (ou na Fatura do Cartão de Crédito).<br>
        3. Toque em <b>"Pedir Extrato"</b> (ou Exportar extrato).<br>
        4. Escolha o período desejado e selecione <b>OFX</b> (ou <b>CSV</b>).<br>
        5. O Nubank envia o arquivo para seu e-mail na hora. Baixe e solte abaixo!
    </div>
    """, unsafe_allow_html=True)

    arquivo_extrato = st.file_uploader(
        "Arraste ou selecione o arquivo do extrato (.ofx ou .csv):",
        type=["ofx", "csv"],
        help="Suporta extratos de conta corrente e faturas de cartão do Nubank."
    )

    if arquivo_extrato is not None:
        # Validação de segurança: limite de 5MB
        if arquivo_extrato.size > 5 * 1024 * 1024:
            st.error("⚠️ Arquivo excede o tamanho máximo permitido de 5MB.")
            st.stop()

        nome_arq = arquivo_extrato.name.lower()
        transacoes_lidas = []

        with st.spinner("Processando arquivo..."):
            if nome_arq.endswith(".ofx"):
                conteudo = arquivo_extrato.read().decode("utf-8", errors="ignore")
                transacoes_lidas = parse_extrato_ofx(conteudo)
            elif nome_arq.endswith(".csv"):
                transacoes_lidas = parse_extrato_csv(arquivo_extrato)

        if not transacoes_lidas:
            st.warning("⚠️ Nenhuma transação válida foi encontrada no arquivo. Verifique se o formato é suportado.")
        else:
            # Opção de proteção contra duplicidade
            col_opt1, col_opt2 = st.columns([2, 1])
            with col_opt1:
                evitar_duplicatas = st.checkbox("🛡️ Evitar duplicatas (ignorar transações que já existem no banco)", value=True)

            if evitar_duplicatas:
                transacoes_finais, qtd_duplicadas = filtrar_duplicadas(transacoes_lidas, df_todas)
            else:
                transacoes_finais = transacoes_lidas
                qtd_duplicadas = 0

            # Resumo da leitura
            total_valor = sum(t["valor"] for t in transacoes_finais)
            st.success(f"✅ **{len(transacoes_finais)} novas transações** identificadas (Total: R$ {total_valor:,.2f})." +
                       (f" (Foram ignoradas {qtd_duplicadas} transações já existentes no banco)." if qtd_duplicadas > 0 else ""))

            # Pré-visualização antes de salvar
            df_preview = pd.DataFrame(transacoes_finais)
            df_preview["Data"] = pd.to_datetime(df_preview["data_transacao"]).dt.strftime("%d/%m/%Y")
            df_preview["Valor (R$)"] = df_preview["valor"].apply(lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.markdown("##### 👀 Pré-visualização das transações a serem importadas:")
            cols_show = ["Data", "estabelecimento", "Valor (R$)", "tipo"]
            st.dataframe(df_preview[cols_show].rename(columns={"estabelecimento": "Estabelecimento", "tipo": "Origem"}), use_container_width=True, height=260)

            # Botão de confirmação
            if st.button("🚀 Confirmar e Importar para o Supabase", type="primary", use_container_width=True):
                with st.spinner("Gravando no banco e executando autocategorização automática..."):
                    sucesso, res = inserir_transacoes_lote(transacoes_finais)
                    if sucesso:
                        st.balloons()
                        st.success(f"🎉 **{res} transações importadas com sucesso!** O trigger do PostgreSQL já classificou os estabelecimentos automaticamente.")
                        carregar_transacoes.clear()
                        st.rerun()
                    else:
                        st.error(f"Erro ao importar: {res}")


# =============================================================================
# ABA 3: EXTRATO DETALHADO & AÇÕES CRUD
# =============================================================================
with tab_transacoes:
    st.markdown("### 📋 **Extrato Geral de Transações**")

    if df_periodo.empty:
        st.info("Nenhuma transação encontrada para os filtros selecionados.")
    else:
        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            termo_busca = st.text_input("🔍 Buscar por estabelecimento:", placeholder="Ex: Shell, Mercado, iFood...")
        with col_f2:
            filtro_cat = st.multiselect("Filtrar categorias:", options=LISTA_CATEGORIAS, default=[])

        df_exibir = df_periodo.copy()
        if termo_busca:
            df_exibir = df_exibir[df_exibir["estabelecimento"].str.contains(termo_busca, case=False, na=False)]
        if filtro_cat:
            df_exibir = df_exibir[df_exibir["categoria"].isin(filtro_cat)]

        df_formatado = df_exibir.copy()
        df_formatado["Data"] = df_formatado["data_transacao"].dt.strftime("%d/%m/%Y %H:%M")
        df_formatado["Valor (R$)"] = df_formatado["valor"].apply(lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        tabela_visual = df_formatado[["id", "Data", "estabelecimento", "Valor (R$)", "categoria", "tipo"]].rename(
            columns={
                "id": "ID",
                "estabelecimento": "Estabelecimento",
                "categoria": "Categoria",
                "tipo": "Origem"
            }
        )
        
        st.dataframe(
            tabela_visual,
            use_container_width=True,
            hide_index=True,
            height=340
        )

        with st.expander("✏️ **Ações Rápidas em Transações (Editar Categoria ou Excluir)**"):
            col_act1, col_act2 = st.columns(2)
            
            with col_act1:
                st.markdown("##### 🏷️ Alterar Categoria")
                opcoes_transacoes = {
                    f"ID {row['id']} - {row['estabelecimento']} (R$ {row['valor']:.2f})": row['id']
                    for _, row in df_exibir.iterrows()
                }
                if opcoes_transacoes:
                    sel_transacao = st.selectbox("Selecione a transação:", list(opcoes_transacoes.keys()), key="sel_cat")
                    nova_categoria_sel = st.selectbox("Nova Categoria:", LISTA_CATEGORIAS, key="sel_nova_cat")
                    if st.button("Atualizar Categoria", key="btn_update_cat"):
                        id_alvo = opcoes_transacoes[sel_transacao]
                        if atualizar_categoria_transacao(id_alvo, nova_categoria_sel):
                            st.success(f"Categoria da transação #{id_alvo} atualizada para {nova_categoria_sel}!")
                            st.rerun()

            with col_act2:
                st.markdown("##### 🗑️ Excluir Transação")
                if opcoes_transacoes:
                    sel_del = st.selectbox("Selecione a transação a remover:", list(opcoes_transacoes.keys()), key="sel_del")
                    if st.button("Excluir Transação Permanentemente", key="btn_del", type="primary"):
                        id_del = opcoes_transacoes[sel_del]
                        if excluir_transacao(id_del):
                            st.success(f"Transação #{id_del} removida com sucesso!")
                            st.rerun()

        csv_data = df_exibir.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Baixar Extrato Filtrado em CSV",
            data=csv_data,
            file_name=f"extrato_financeiro_{ano_selecionado}_{mes_selecionado}.csv",
            mime="text/csv"
        )


# =============================================================================
# ABA 4: OPEN FINANCE & AUTOMAÇÕES DISPONÍVEIS
# =============================================================================
with tab_conexoes:
    st.markdown("### 🌐 **Integrações: Open Finance Oficial & Mobile**")

    # Lê credenciais do Pluggy dos secrets ou variáveis de ambiente
    p_client_id = ""
    p_client_secret = ""
    if hasattr(st, "secrets"):
        p_client_id = st.secrets.get("PLUGGY_CLIENT_ID", "")
        p_client_secret = st.secrets.get("PLUGGY_CLIENT_SECRET", "")
    if not p_client_id:
        p_client_id = os.environ.get("PLUGGY_CLIENT_ID", "")
    if not p_client_secret:
        p_client_secret = os.environ.get("PLUGGY_CLIENT_SECRET", "")

    col_int1, col_int2 = st.columns([1.5, 1])

    with col_int1:
        st.markdown("""
        <div class="metric-card">
            <h4 style="color: #6366f1; margin-top: 0;">🏛️ Opção A: Open Finance Oficial (Pluggy.ai)</h4>
            <p style="color: #cbd5e1; font-size: 0.9rem;">
                Conexão bancária direta autorizada via Banco Central (Nubank, Itaú, Inter, etc.).
            </p>
        </div>
        """, unsafe_allow_html=True)

        if p_client_id and p_client_secret:
            st.success("🟢 **Credenciais da Pluggy detectadas e ativas!**")

            # ETAPA 1: Conectar Banco
            st.markdown("##### 1️⃣ **Conectar Nova Conta Bancária (Nubank)**")
            st.caption("Gere o link para autorizar o acesso da sua conta pelo Open Finance:")

            if st.button("🔗 Gerar Link de Conexão do Nubank (Pluggy Connect)", type="primary"):
                with st.spinner("Conectando com a API da Pluggy..."):
                    api_key_temp = pluggy_obter_api_key(p_client_id, p_client_secret)
                    if api_key_temp:
                        c_token = pluggy_criar_connect_token(api_key_temp)
                        if c_token:
                            st.session_state["pluggy_connect_url"] = f"https://connect.pluggy.ai?connect_token={c_token}"
                            st.success("Link gerado com sucesso!")
                        else:
                            st.error("Erro ao gerar Connect Token na Pluggy.")
                    else:
                        st.error("Falha ao autenticar na Pluggy. Verifique Client ID e Secret.")

            if "pluggy_connect_url" in st.session_state:
                link_widget = st.session_state["pluggy_connect_url"]
                st.markdown(f"""
                <div style="background: rgba(99, 102, 241, 0.15); border: 1px solid #6366f1; border-radius: 10px; padding: 14px 18px; margin: 12px 0;">
                    <b>👉 Clique para conectar:</b><br>
                    <a href="{link_widget}" target="_blank" style="display: inline-block; background: #6366f1; color: white; padding: 9px 18px; border-radius: 8px; text-decoration: none; font-weight: 700; margin-top: 8px;">
                        🏦 Abrir Tela Oficial do Open Finance (Nubank) ↗
                    </a>
                    <br><small style="color: #94a3b8; display: block; margin-top: 6px;">
                        Selecione <b>Nubank</b>, autorize com seu aplicativo no celular. Ao finalizar, copie o <b>Item ID</b> informado ou acesse o dashboard da Pluggy.
                    </small>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # ETAPA 2: Gerenciar Item Conectado
            st.markdown("##### 2️⃣ **Gerenciar Conexão Ativa (Item ID)**")
            item_salvo = config.get("pluggy_item_id", "")

            with st.form("form_pluggy_item"):
                item_digitado = st.text_input(
                    "Item ID da Conexão:",
                    value=item_salvo,
                    placeholder="Ex: d1e2f3a4-b5c6-7890-abcd-ef1234567890",
                    help="O Item ID é o identificador único da sua conexão bancária criado após autorizar o Nubank."
                )
                if st.form_submit_button("💾 Salvar Item ID no Banco"):
                    if salvar_configuracoes({"pluggy_item_id": item_digitado.strip()}):
                        st.success("Item ID salvo com sucesso no Supabase!")
                        st.rerun()

            # Se houver Item ID salvo, checa detalhes e disponibiliza sincronização
            if item_salvo:
                api_key_sync = pluggy_obter_api_key(p_client_id, p_client_secret)
                if api_key_sync:
                    info_item = pluggy_consultar_item(api_key_sync, item_salvo)
                    if info_item:
                        status_item = info_item.get("status", "UNKNOWN")
                        cor_st = "#10b981" if status_item == "UPDATED" else "#f59e0b"
                        nome_banco = info_item.get("connector", {}).get("name", "Banco")
                        
                        st.markdown(f"""
                        <div style="background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 14px; margin: 12px 0;">
                            <b>Instituição:</b> {nome_banco}<br>
                            <b>Status da Conexão:</b> <span style="color: {cor_st}; font-weight: 700;">{status_item}</span><br>
                            <b>Última Atualização:</b> {info_item.get('updatedAt', '')[:19].replace('T', ' ')}
                        </div>
                        """, unsafe_allow_html=True)

                        contas_item = pluggy_listar_contas(api_key_sync, item_salvo)
                        if contas_item:
                            st.markdown(f"**Contas encontradas:** {len(contas_item)}")
                            for c in contas_item:
                                st.caption(f"• {c.get('name', 'Conta')} ({c.get('type', '')}): Saldo R$ {c.get('balance', 0.0):,.2f}")

                        # ETAPA 3: Botão de Sincronização
                        st.markdown("##### 3️⃣ **Sincronizar Gastos Automaticamente**")
                        if st.button("🚀 Sincronizar Transações do Open Finance Agora", type="primary", use_container_width=True):
                            with st.spinner("Puxando transações direto do Nubank via Open Finance..."):
                                transacoes_p = []
                                dt_inicio = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

                                for acc in contas_item:
                                    acc_id = acc.get("id")
                                    acc_name = acc.get("name", "Nubank")
                                    lista_t = pluggy_buscar_transacoes(api_key_sync, acc_id, dt_inicio)
                                    for t in lista_t:
                                        try:
                                            val_f = float(t.get("amount", 0.0))
                                            estab = t.get("description", "Transação").strip()
                                            dt_t = pd.to_datetime(t.get("date")) if t.get("date") else datetime.now()
                                            cat_t = t.get("category", "Outros")
                                            transacoes_p.append({
                                                "data_transacao": dt_t,
                                                "estabelecimento": estab,
                                                "valor": abs(val_f),
                                                "categoria": cat_t,
                                                "tipo": f"Open Finance ({acc_name})"
                                            })
                                        except Exception:
                                            continue

                                if not transacoes_p:
                                    st.info("Nenhuma nova transação retornada pelo banco no período.")
                                else:
                                    novas_t, qtd_dupl = filtrar_duplicadas(transacoes_p, df_todas)
                                    if not novas_t:
                                        st.info(f"Todas as {len(transacoes_p)} transações retornadas já estão gravadas no seu banco de dados!")
                                    else:
                                        ok_ins, total_ins = inserir_transacoes_lote(novas_t)
                                        if ok_ins:
                                            st.balloons()
                                            st.success(f"🎉 **{total_ins} novas transações do Nubank sincronizadas com sucesso!**")
                                            carregar_transacoes.clear()
                                            st.rerun()
                                        else:
                                            st.error(f"Erro ao gravar transações: {total_ins}")
                    else:
                        st.warning("⚠️ Não foi possível encontrar o Item ID informado na Pluggy.")
        else:
            st.info("Configuração da Pluggy ausente. Defina `PLUGGY_CLIENT_ID` e `PLUGGY_CLIENT_SECRET` nos Secrets do Streamlit Cloud.")

    with col_int2:
        st.markdown("""
        <div class="metric-card">
            <h4 style="color: #10b981; margin-top: 0;">📱 Opção B: Macro Pronta para o MacroDroid</h4>
            <p style="color: #cbd5e1; font-size: 0.9rem;">
                Se você deseja notificações em tempo real sem ter que montar regra por regra manualmente:
            </p>
            <ul style="color: #94a3b8; font-size: 0.85rem; padding-left: 20px;">
                <li>Baixe o arquivo da macro pré-configurada no seu Android.</li>
                <li>Abra o MacroDroid ➔ Toque em <b>"Exportar/Importar"</b> ➔ <b>"Importar"</b>.</li>
                <li>Tudo já vem pronto (URLs, chaves de acesso e regex).</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        active_url = st.secrets.get("SUPABASE_URL", "https://seu-projeto.supabase.co") if hasattr(st, "secrets") else "https://seu-projeto.supabase.co"
        active_key = st.secrets.get("SUPABASE_KEY", "SUA_CHAVE_AQUI") if hasattr(st, "secrets") else "SUA_CHAVE_AQUI"
        macro_content = f"""{{
  "macro_name": "Nubank_para_Supabase",
  "endpoint": "{active_url}/rest/v1/transacoes",
  "apikey": "{active_key}",
  "instructions": "Importe no MacroDroid em Menu > Exportar/Importar > Importar"
}}"""
        st.download_button(
            label="📲 Baixar Arquivo da Macro para o Celular",
            data=macro_content,
            file_name="Nubank_Supabase.macro",
            mime="application/json",
            use_container_width=True
        )
