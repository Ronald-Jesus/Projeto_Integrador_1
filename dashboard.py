"""
╔══════════════════════════════════════════════════════════════════════╗
║  SAPA — Sistema de Autoconhecimento Psicológico Automatizado         ║
║  Dashboard Interativo — Projeto Integrador I | CEUB | Aula 15        ║
║  Profa. Kadidja Valéria | 25/05/2026                                 ║
╚══════════════════════════════════════════════════════════════════════╝

Como rodar:
    pip install streamlit pandas plotly openpyxl
    python -m streamlit run dashboard.py
"""

import os
import sqlite3
import random
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# 0. CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SAPA – Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

CORES = {
    "primaria":   "#D6006E",
    "secundaria": "#8B5CF6",
    "terciaria":  "#C4B5FD",
    "fundo":      "#F5F0FA",
    "texto":      "#1E1B2E",
    "sucesso":    "#10B981",
    "alerta":     "#F59E0B",
    "card_bg":    "#FFFFFF",
    "borda":      "#E9D5F5",
}

PALETA_EMOCOES = px.colors.qualitative.Vivid
PALETA_REGIOES = px.colors.qualitative.Pastel

st.markdown(f"""
<style>
    /* Fundo geral */
    .stApp {{ background-color: {CORES['fundo']}; }}

    /* Cards KPI */
    .kpi-card {{
        background: {CORES['card_bg']};
        border-left: 5px solid {CORES['primaria']};
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 2px 12px rgba(214,0,110,0.08);
        margin-bottom: 10px;
    }}
    .kpi-value {{
        font-size: 2rem;
        font-weight: 800;
        color: {CORES['primaria']};
        line-height: 1.1;
    }}
    .kpi-label {{
        font-size: 0.82rem;
        color: #6B7280;
        margin-top: 4px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    /* Títulos de seção */
    .section-title {{
        font-size: 1.25rem;
        font-weight: 700;
        color: {CORES['texto']};
        border-bottom: 3px solid {CORES['primaria']};
        padding-bottom: 6px;
        margin: 20px 0 16px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #2D1B4E 0%, #1a0533 100%);
    }}
    section[data-testid="stSidebar"] * {{ color: white !important; }}

    /* Esconder menu e footer */
    #MainMenu, footer {{ visibility: hidden; }}

    /* Subheaders mais limpos */
    h3 {{ color: {CORES['texto']} !important; font-size: 1rem !important; font-weight: 700 !important; }}

    /* Corrigir st.metric — label e valor visíveis no fundo claro */
    [data-testid="stMetric"] {{
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        border-left: 4px solid {CORES['secundaria']};
        box-shadow: 0 2px 8px rgba(139,92,246,0.08);
    }}
    [data-testid="stMetricLabel"] {{ color: #374151 !important; font-weight: 600 !important; font-size: 0.85rem !important; }}
    [data-testid="stMetricValue"] {{ color: {CORES['primaria']} !important; font-weight: 800 !important; font-size: 1.6rem !important; }}

    /* Expander header legível */
    [data-testid="stExpander"] summary {{
        color: {CORES['texto']} !important;
        font-weight: 600;
    }}

    /* Captions e textos menores */
    .stCaption, [data-testid="stCaptionContainer"] {{
        color: #6B7280 !important;
    }}

    /* Separadores */
    hr {{ border-color: {CORES['borda']}; margin: 16px 0; }}

    /* Chips de info */
    .info-chip {{
        display: inline-block;
        background: #EDE9FE;
        color: #5B21B6;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 2px;
    }}

    /* Aviso de dados ausentes */
    .missing-data {{
        background: #FEF3C7;
        border: 1px solid #FCD34D;
        border-radius: 8px;
        padding: 10px 16px;
        font-size: 0.85rem;
        color: #92400E;
    }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 1. CARREGAMENTO DE DADOS
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _encontrar_banco():
    candidatos = [
        "saude_mental.db",
        os.path.join(os.path.dirname(__file__), "saude_mental.db"),
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "saude_mental.db"),
        os.path.join(os.path.dirname(__file__), "data", "processed", "saude_mental.db"),
    ]
    for c in candidatos:
        if os.path.exists(c):
            return os.path.abspath(c)
    return None


@st.cache_data(show_spinner=False)
def carregar_do_sqlite(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = [row[0] for row in cursor.fetchall()]
    dados = {}
    for t in tabelas:
        try:
            dados[t] = pd.read_sql(f"SELECT * FROM {t}", conn)
        except Exception:
            pass
    conn.close()
    return dados


@st.cache_data(show_spinner=False)
def gerar_dados_demo():
    rng = np.random.default_rng(42)
    n = 500
    emocoes_lista    = ["Feliz", "Triste", "Ansioso", "Calmo", "Irritado",
                        "Motivado", "Cansado", "Esperançoso"]
    atividades_lista = ["Corrida", "Yoga", "Natação", "Musculação", "Caminhada",
                        "Ciclismo", "Meditação", "Dança"]
    sono_lista       = ["Ótimo", "Bom", "Regular", "Ruim", "Péssimo"]
    datas = [datetime(2024, 1, 1) + timedelta(days=int(d))
             for d in rng.integers(0, 365, n)]

    emocoes_atividades = pd.DataFrame({
        "id_registro":               range(1, n + 1),
        "id_fonte":                  1,
        "data_registro":             [d.strftime("%Y-%m-%d") for d in datas],
        "emocao_principal":          rng.choice(emocoes_lista, n),
        "humor_score":               rng.integers(1, 11, n),
        "atividade":                 rng.choice(atividades_lista, n),
        "duracao_min":               rng.integers(15, 120, n),
        "calorias":                  rng.integers(80, 800, n),
        "frequencia_cardiaca_media": rng.integers(60, 160, n),
        "qualidade_sono":            rng.choice(sono_lista, n),
        "nivel_estresse":            rng.integers(1, 11, n),
    })

    emocoes_diario = ["Joy", "Sadness", "Fear", "Anger", "Surprise",
                      "Disgust", "Trust", "Anticipation"]
    textos_exemplo = [
        "Hoje me senti muito bem com minhas decisões.",
        "Tive um dia difícil mas consegui me manter focado.",
        "A ansiedade bateu forte, mas pratiquei respiração.",
        "Sinto que estou progredindo no meu autoconhecimento.",
        "Refleti bastante sobre meus hábitos e padrões.",
    ]
    n2 = 300
    diarios_emocoes = pd.DataFrame({
        "id_entrada":        range(1, n2 + 1),
        "id_fonte":          2,
        "data_entrada":      [(datetime(2024, 1, 1) + timedelta(days=int(d))).strftime("%Y-%m-%d")
                              for d in rng.integers(0, 365, n2)],
        "texto_entrada":     rng.choice(textos_exemplo, n2),
        "emocao_rotulada":   rng.choice(emocoes_diario, n2),
        "comprimento_texto": rng.integers(30, 500, n2),
    })

    ufs = ["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
           "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"]
    regioes_map = {
        "AC":"Norte","AL":"Nordeste","AM":"Norte","AP":"Norte","BA":"Nordeste",
        "CE":"Nordeste","DF":"Centro-Oeste","ES":"Sudeste","GO":"Centro-Oeste",
        "MA":"Nordeste","MG":"Sudeste","MS":"Centro-Oeste","MT":"Centro-Oeste",
        "PA":"Norte","PB":"Nordeste","PE":"Nordeste","PI":"Nordeste","PR":"Sul",
        "RJ":"Sudeste","RN":"Nordeste","RO":"Norte","RR":"Norte","RS":"Sul",
        "SC":"Sul","SE":"Nordeste","SP":"Sudeste","TO":"Norte"
    }
    faixas = ["Até 2 SM", "2-5 SM", "5-10 SM", "10-20 SM", "Acima de 20 SM"]
    n3 = 800
    uf_col    = rng.choice(ufs, n3)
    desp_med  = rng.uniform(50,  1500, n3).round(2)
    desp_cons = rng.uniform(100, 3000, n3).round(2)
    desp_plan = rng.uniform(0,   2500, n3).round(2)
    desp_ment = rng.uniform(0,    800, n3).round(2)
    total     = (desp_med + desp_cons + desp_plan + desp_ment).round(2)
    pct_ment  = (desp_ment / total * 100).round(2)

    def perfil(t):
        if t < 1000: return "Baixo"
        if t < 3000: return "Médio"
        if t < 5000: return "Alto"
        return "Muito Alto"

    despesas_saude_pof = pd.DataFrame({
        "id_registro":          range(1, n3 + 1),
        "id_fonte":             3,
        "ano_referencia":       rng.choice([2017, 2018], n3),
        "uf":                   uf_col,
        "regiao":               [regioes_map[u] for u in uf_col],
        "faixa_renda_familiar": rng.choice(faixas, n3),
        "despesa_medicamentos": desp_med,
        "despesa_consultas":    desp_cons,
        "despesa_plano_saude":  desp_plan,
        "despesa_saude_mental": desp_ment,
        "total_despesa_saude":  total,
        "pct_saude_mental":     pct_ment,
        "perfil_gasto":         [perfil(t) for t in total],
    })

    paises = ["Brazil", "World", "United States", "Portugal"]
    anos   = list(range(1990, 2024))
    linhas = []
    base   = {"Brazil": 3.5, "World": 4.4, "United States": 5.9, "Portugal": 6.2}
    for p in paises:
        for i, a in enumerate(anos):
            linhas.append({
                "pais":                  p,
                "codigo":                {"Brazil":"BRA","World":"WLD","United States":"USA","Portugal":"PRT"}[p],
                "ano":                   a,
                "prevalencia_depressao": round(base[p] + i * 0.04 + rng.uniform(-0.1, 0.1), 3),
                "id_fonte":              7,
            })
    prevalencia_depressao_global = pd.DataFrame(linhas)

    return {
        "emocoes_atividades":           emocoes_atividades,
        "diarios_emocoes":              diarios_emocoes,
        "despesas_saude_pof":           despesas_saude_pof,
        "prevalencia_depressao_global": prevalencia_depressao_global,
    }


@st.cache_data(show_spinner=False)
def carregar_dados():
    db = _encontrar_banco()
    if db:
        dados = carregar_do_sqlite(db)
        return dados, f"✅ Banco real carregado:\n`{os.path.basename(db)}`"
    else:
        dados = gerar_dados_demo()
        return dados, "⚠️ Usando dados de demonstração."


# ─────────────────────────────────────────────────────────────────────────────
# 2. HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def kpi(label, valor, sufixo="", delta=None):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{valor}{sufixo}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def titulo(icone, texto):
    st.markdown(f'<div class="section-title">{icone} {texto}</div>', unsafe_allow_html=True)


def aviso_coluna(col_nome):
    st.markdown(f"""
    <div class="missing-data">
        ⚠️ A coluna <b>{col_nome}</b> não está disponível no dataset real —
        este gráfico usa o dataset de demonstração.
    </div>
    """, unsafe_allow_html=True)


def amostrar(df, max_pts=3000):
    """Retorna amostra aleatória para gráficos pesados."""
    if len(df) > max_pts:
        return df.sample(max_pts, random_state=42)
    return df


LAYOUT_BASE = dict(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family="Inter, sans-serif", size=12, color="#374151"),
    margin=dict(l=0, r=0, t=30, b=0),
)


# ─────────────────────────────────────────────────────────────────────────────
# 3. PÁGINAS
# ─────────────────────────────────────────────────────────────────────────────

def pagina_visao_geral(dados):
    titulo("🏠", "Visão Geral do SAPA")

    df  = dados.get("emocoes_atividades", pd.DataFrame())
    df2 = dados.get("diarios_emocoes", pd.DataFrame())
    df3 = dados.get("despesas_saude_pof", pd.DataFrame())
    df7 = dados.get("prevalencia_depressao_global", pd.DataFrame())

    total_registros = sum(len(dados.get(t, pd.DataFrame())) for t in dados)
    humor_medio     = round(df["humor_score"].mean(), 1) if not df.empty and "humor_score" in df and df["humor_score"].sum() > 0 else "—"
    estresse_medio  = round(df["nivel_estresse"].mean(), 1) if not df.empty and "nivel_estresse" in df and df["nivel_estresse"].sum() > 0 else "—"
    emocao_top      = df["emocao_principal"].mode()[0] if not df.empty and "emocao_principal" in df else "—"

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Total de Registros", f"{total_registros:,}")
    with c2: kpi("Humor Médio", humor_medio, sufixo="/10")
    with c3: kpi("Estresse Médio", estresse_medio, sufixo="/10")
    with c4: kpi("Emoção Mais Frequente", emocao_top)

    st.markdown("---")
    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.subheader("📈 Evolução do Humor ao Longo do Tempo")
        if not df.empty and "data_registro" in df and "humor_score" in df:
            df_t = df.copy()
            df_t["data_registro"] = pd.to_datetime(df_t["data_registro"], errors="coerce")
            df_t = df_t.dropna(subset=["data_registro"])
            # Filtrar datas inválidas (antes de 2000 = dado corrompido)
            df_t = df_t[df_t["data_registro"] >= pd.Timestamp("2000-01-01")]
            # Agrupar por semana para performance com datasets grandes
            if len(df_t) > 5000:
                df_t["periodo"] = df_t["data_registro"].dt.to_period("W").apply(lambda r: r.start_time)
            else:
                df_t["periodo"] = df_t["data_registro"]
            df_media = df_t.groupby("periodo")["humor_score"].mean().reset_index()
            df_media.columns = ["data", "humor"]
            df_media["media_movel"] = df_media["humor"].rolling(4, min_periods=1).mean()

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_media["data"], y=df_media["humor"],
                mode="lines", name="Humor médio",
                line=dict(color=CORES["terciaria"], width=1.5), opacity=0.6,
            ))
            fig.add_trace(go.Scatter(
                x=df_media["data"], y=df_media["media_movel"],
                mode="lines", name="Média móvel",
                line=dict(color=CORES["primaria"], width=2.5),
            ))
            fig.update_layout(**LAYOUT_BASE,
                xaxis_title="Período", yaxis_title="Score (1–10)",
                yaxis=dict(range=[0, 11]),
                legend=dict(orientation="h", y=1.12),
                height=310,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados de humor não disponíveis.")

    with col_b:
        st.subheader("🎭 Distribuição de Emoções")
        if not df.empty and "emocao_principal" in df:
            contagem = df["emocao_principal"].value_counts().head(12).reset_index()
            contagem.columns = ["emocao", "total"]
            fig = px.pie(contagem, names="emocao", values="total",
                         color_discrete_sequence=PALETA_EMOCOES, hole=0.42)
            fig.update_traces(textinfo="percent", textfont_size=11)
            fig.update_layout(**LAYOUT_BASE,
                showlegend=True,
                legend=dict(orientation="v", x=1.0, font=dict(size=10)),
                height=310,
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📦 Fontes de Dados Conectadas")
    fontes = [
        ("🏋️ FitLife / Kaggle",  len(df),  "Emoções e atividades físicas"),
        ("📓 Diários / Kaggle",   len(df2), "Entradas rotuladas por emoção"),
        ("🏥 IBGE POF",           len(df3), "Despesas de saúde por estado"),
        ("🌍 OWID Depressão",     len(df7), "Prevalência global de depressão"),
    ]
    cols = st.columns(4)
    for col, (nome, qtd, desc) in zip(cols, fontes):
        with col:
            st.metric(label=nome, value=f"{qtd:,}", help=desc)


def pagina_emocoes_atividades(dados):
    titulo("🎭", "Emoções & Atividades Físicas")

    df_orig = dados.get("emocoes_atividades", pd.DataFrame())
    if df_orig.empty:
        st.warning("Tabela `emocoes_atividades` não disponível.")
        return

    df = df_orig.copy()

    # Tentar converter datas — ignorar se inválidas
    df["data_registro"] = pd.to_datetime(df["data_registro"], errors="coerce")
    tem_datas_validas = df["data_registro"].notna().any() and \
                        (df["data_registro"].dropna() >= pd.Timestamp("2000-01-01")).any()
    if tem_datas_validas:
        df = df[df["data_registro"].isna() | (df["data_registro"] >= pd.Timestamp("2000-01-01"))]

    # ── Filtros ───────────────────────────────────────────────────────────────
    with st.expander("🔍 Filtros", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            emocoes_disp = sorted(df["emocao_principal"].dropna().unique())
            sel_emocoes  = st.multiselect("Emoções", emocoes_disp, default=emocoes_disp[:6])
        with col2:
            atividades_disp = sorted(df["atividade"].dropna().unique())
            sel_atividades  = st.multiselect("Atividades", atividades_disp, default=atividades_disp[:8] if len(atividades_disp) > 8 else atividades_disp)
        with col3:
            if tem_datas_validas:
                df_datas = df.dropna(subset=["data_registro"])
                min_d = df_datas["data_registro"].min().date()
                max_d = df_datas["data_registro"].max().date()
                intervalo = st.date_input("Período", value=(min_d, max_d), min_value=min_d, max_value=max_d)
            else:
                st.caption("📅 Datas não disponíveis neste dataset")
                intervalo = None

    mask = df["emocao_principal"].isin(sel_emocoes) & df["atividade"].isin(sel_atividades)
    if intervalo is not None and isinstance(intervalo, (tuple, list)) and len(intervalo) == 2:
        mask &= (df["data_registro"] >= pd.Timestamp(intervalo[0])) & \
                (df["data_registro"] <= pd.Timestamp(intervalo[1]))
    df = df[mask]

    if df.empty:
        st.info("Nenhum registro encontrado com esses filtros.")
        return

    n_total = len(df_orig)
    n_filtrado = len(df)
    st.markdown(f"""
    <span class="info-chip">📊 {n_filtrado:,} registros filtrados</span>
    <span class="info-chip">📁 {n_total:,} registros totais</span>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # ── Gráficos principais ───────────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("😊 Humor Médio por Emoção")
        humor_emocao = df.groupby("emocao_principal")["humor_score"].mean().sort_values().reset_index()
        fig = px.bar(humor_emocao, x="humor_score", y="emocao_principal",
                     orientation="h", color="humor_score",
                     color_continuous_scale=[[0, "#FF6B9D"], [0.5, "#8B5CF6"], [1, "#4B0082"]],
                     labels={"humor_score": "Score médio", "emocao_principal": "Emoção"},
                     text_auto=".1f")
        fig.update_layout(**LAYOUT_BASE,
            coloraxis_showscale=False,
            xaxis=dict(range=[0, 10]),
            height=360,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("😤 Distribuição do Nível de Estresse")
        fig = px.histogram(df, x="nivel_estresse", nbins=10,
                           color_discrete_sequence=[CORES["secundaria"]],
                           labels={"nivel_estresse": "Nível de Estresse (1–10)", "count": "Frequência"})
        fig.update_layout(**LAYOUT_BASE,
            bargap=0.08,
            xaxis=dict(tickmode="linear", tick0=1, dtick=1),
            height=360,
        )
        st.plotly_chart(fig, use_container_width=True)

    col_c, col_d = st.columns(2)

    # Verificar se tem dados reais de calorias
    tem_calorias = "calorias" in df.columns and df["calorias"].sum() > 0
    tem_sono     = "qualidade_sono" in df.columns and (df["qualidade_sono"] != "Não Informado").any()

    with col_c:
        if tem_calorias:
            st.subheader("🏃 Calorias Médias por Atividade")
            cal_ativ = df.groupby("atividade")["calorias"].mean().sort_values().reset_index()
            fig = px.bar(cal_ativ, x="calorias", y="atividade",
                         orientation="h", color="calorias",
                         color_continuous_scale=[[0, "#C4B5FD"], [1, CORES["primaria"]]],
                         labels={"calorias": "Calorias médias", "atividade": "Atividade"},
                         text_auto=".0f")
            fig.update_layout(**LAYOUT_BASE,
                coloraxis_showscale=False, height=360)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.subheader("⏱️ Duração Média por Atividade")
            dur_ativ = df.groupby("atividade")["duracao_min"].mean().sort_values().reset_index()
            fig = px.bar(dur_ativ, x="duracao_min", y="atividade",
                         orientation="h", color="duracao_min",
                         color_continuous_scale=[[0, "#C4B5FD"], [1, CORES["primaria"]]],
                         labels={"duracao_min": "Duração média (min)", "atividade": "Atividade"},
                         text_auto=".0f")
            fig.update_layout(**LAYOUT_BASE,
                coloraxis_showscale=False, height=360)
            st.plotly_chart(fig, use_container_width=True)

    with col_d:
        if tem_sono:
            st.subheader("😴 Qualidade do Sono vs Humor")
            ordem_sono = ["Ótimo", "Bom", "Regular", "Ruim", "Péssimo"]
            vals_presentes = [s for s in ordem_sono if s in df["qualidade_sono"].unique()]
            sono_humor = df.groupby("qualidade_sono")["humor_score"].mean().reindex(vals_presentes).reset_index()
            fig = px.bar(sono_humor, x="qualidade_sono", y="humor_score",
                         color="humor_score",
                         color_continuous_scale=[[0, "#FCA5A5"], [1, "#34D399"]],
                         labels={"qualidade_sono": "Qualidade do Sono", "humor_score": "Humor Médio"},
                         text_auto=".1f")
            fig.update_layout(**LAYOUT_BASE, coloraxis_showscale=False, height=360)
            st.plotly_chart(fig, use_container_width=True)
        elif "frequencia_cardiaca_media" in df.columns and df["frequencia_cardiaca_media"].sum() > 0:
            st.subheader("❤️ Frequência Cardíaca Média por Emoção")
            fc_emocao = df.groupby("emocao_principal")["frequencia_cardiaca_media"].mean().sort_values().reset_index()
            fig = px.bar(fc_emocao, x="frequencia_cardiaca_media", y="emocao_principal",
                         orientation="h", color="frequencia_cardiaca_media",
                         color_continuous_scale=[[0, "#FCA5A5"], [1, "#DC2626"]],
                         labels={"frequencia_cardiaca_media": "BPM médio", "emocao_principal": "Emoção"},
                         text_auto=".0f")
            fig.update_layout(**LAYOUT_BASE, coloraxis_showscale=False, height=360)
            st.plotly_chart(fig, use_container_width=True)
        else:
            col_int = next((c for c in ["intensity", "Intensity"] if c in df.columns), None)
            if col_int:
                st.subheader("📊 Emoção por Intensidade de Treino")
                sample_int = amostrar(df, 5000)
                contagem_int = sample_int.groupby([col_int, "emocao_principal"]).size().reset_index(name="total")
                fig = px.bar(contagem_int, x=col_int, y="total", color="emocao_principal",
                             color_discrete_sequence=PALETA_EMOCOES,
                             labels={col_int: "Intensidade", "total": "Frequência", "emocao_principal": "Emoção"})
                fig.update_layout(**LAYOUT_BASE, height=360,
                    legend=dict(orientation="h", y=-0.25, font=dict(size=9)))
                st.plotly_chart(fig, use_container_width=True)

    # ── Scatter com amostragem ────────────────────────────────────────────────
    st.subheader("🔗 Relação: Humor × Nível de Estresse por Emoção")
    df_scatter = amostrar(df, max_pts=1500)
    if len(df) > 1500:
        st.caption(f"⚡ Exibindo amostra de 1.500 pontos de {len(df):,} para melhor performance.")

    fig = px.scatter(df_scatter,
                     x="humor_score", y="nivel_estresse",
                     color="emocao_principal",
                     color_discrete_sequence=PALETA_EMOCOES,
                     opacity=0.65,
                     hover_data=["atividade"] if "atividade" in df_scatter.columns else None,
                     labels={"humor_score": "Humor (1–10)",
                             "nivel_estresse": "Estresse (1–10)",
                             "emocao_principal": "Emoção"})
    fig.update_traces(marker=dict(size=5))
    fig.update_layout(**LAYOUT_BASE,
        height=420,
        xaxis=dict(range=[0, 11]),
        yaxis=dict(range=[0, 11]),
        legend=dict(orientation="h", y=-0.18, font=dict(size=11)),
    )
    st.plotly_chart(fig, use_container_width=True)


def pagina_diarios(dados):
    titulo("📓", "Diários Emocionais")

    df = dados.get("diarios_emocoes", pd.DataFrame())
    if df.empty:
        st.warning("Tabela `diarios_emocoes` não disponível.")
        return

    # Detectar coluna de emoção
    col_emocao = None
    for c in ["emocao_rotulada", "emocao_principal", "emotion", "label"]:
        if c in df.columns:
            col_emocao = c
            break

    if col_emocao is None:
        st.info("Estrutura dos diários ainda não mapeada para exibição visual.")
        st.dataframe(df.head(20))
        return

    col1, _ = st.columns([2, 3])
    with col1:
        emocoes_disp = sorted(df[col_emocao].dropna().unique())
        sel = st.multiselect("Filtrar por emoção", emocoes_disp, default=emocoes_disp)
    df = df[df[col_emocao].isin(sel)]

    st.markdown(f'<span class="info-chip">📊 {len(df):,} entradas filtradas</span>', unsafe_allow_html=True)
    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("📊 Distribuição de Emoções nos Diários")
        contagem = df[col_emocao].value_counts().reset_index()
        contagem.columns = ["emocao", "total"]
        fig = px.bar(contagem, x="emocao", y="total",
                     color="emocao", color_discrete_sequence=PALETA_EMOCOES,
                     labels={"emocao": "Emoção", "total": "Nº de Entradas"},
                     text_auto=True)
        fig.update_layout(**LAYOUT_BASE,
            showlegend=False, height=370,
            xaxis_tickangle=-30,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        col_texto = None
        for c in ["comprimento_texto", "text_length", "char_count"]:
            if c in df.columns:
                col_texto = c
                break
        if col_texto:
            st.subheader("📝 Comprimento dos Textos por Emoção")
            fig = px.box(df, x=col_emocao, y=col_texto,
                         color=col_emocao, color_discrete_sequence=PALETA_EMOCOES,
                         labels={col_emocao: "Emoção", col_texto: "Caracteres"},
                         points="outliers")
            fig.update_layout(**LAYOUT_BASE,
                showlegend=False, height=370,
                xaxis_tickangle=-30,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.subheader("📊 Top 10 Emoções")
            top10 = df[col_emocao].value_counts().head(10).reset_index()
            top10.columns = ["emocao", "total"]
            fig = px.pie(top10, names="emocao", values="total",
                         color_discrete_sequence=PALETA_EMOCOES, hole=0.4)
            fig.update_layout(**LAYOUT_BASE, height=370)
            st.plotly_chart(fig, use_container_width=True)

    # Timeline se tiver coluna de data
    col_data = None
    for c in ["data_entrada", "date", "data_registro"]:
        if c in df.columns:
            col_data = c
            break

    if col_data:
        st.subheader("📅 Emoções ao Longo do Tempo")
        df_t = df.copy()
        df_t[col_data] = pd.to_datetime(df_t[col_data], errors="coerce")
        df_t = df_t.dropna(subset=[col_data])
        df_t["mes"] = df_t[col_data].dt.to_period("M").astype(str)
        grupo = df_t.groupby(["mes", col_emocao]).size().reset_index(name="total")
        fig = px.area(grupo, x="mes", y="total", color=col_emocao,
                      color_discrete_sequence=PALETA_EMOCOES,
                      labels={"mes": "Mês", "total": "Entradas", col_emocao: "Emoção"})
        fig.update_layout(**LAYOUT_BASE, height=360,
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig, use_container_width=True)


def pagina_saude_brasil(dados):
    titulo("🇧🇷", "Saúde Mental no Brasil — IBGE POF")

    df = dados.get("despesas_saude_pof", pd.DataFrame())
    if df.empty:
        st.warning("Tabela `despesas_saude_pof` não disponível.")
        return

    with st.expander("🔍 Filtros", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            regioes   = sorted(df["regiao"].dropna().unique()) if "regiao" in df else []
            sel_reg   = st.multiselect("Região", regioes, default=regioes)
        with col2:
            ordem_renda = ["Até 2 SM", "2-5 SM", "5-10 SM", "10-20 SM", "Acima de 20 SM"]
            faixas_disp = [f for f in ordem_renda if f in df["faixa_renda_familiar"].unique()] \
                          if "faixa_renda_familiar" in df else []
            sel_faixa = st.multiselect("Faixa de Renda", faixas_disp, default=faixas_disp)

    if sel_reg and sel_faixa:
        df = df[df["regiao"].isin(sel_reg) & df["faixa_renda_familiar"].isin(sel_faixa)]

    st.markdown(f'<span class="info-chip">📊 {len(df):,} registros filtrados</span>', unsafe_allow_html=True)
    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("💰 Gasto Médio em Saúde Mental por Região")
        reg = df.groupby("regiao")["despesa_saude_mental"].mean().sort_values(ascending=False).reset_index()
        fig = px.bar(reg, x="regiao", y="despesa_saude_mental",
                     color="regiao", color_discrete_sequence=PALETA_REGIOES,
                     text_auto=".0f",
                     labels={"regiao": "Região", "despesa_saude_mental": "R$ Médio/Mês"})
        fig.update_layout(**LAYOUT_BASE,
            showlegend=False, height=360)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("📊 % Saúde Mental no Gasto Total por Renda")
        ordem = [f for f in ordem_renda if f in df["faixa_renda_familiar"].unique()]
        renda = df.groupby("faixa_renda_familiar")["pct_saude_mental"].mean().reindex(ordem).reset_index()
        fig = px.bar(renda, x="faixa_renda_familiar", y="pct_saude_mental",
                     color="pct_saude_mental",
                     color_continuous_scale=[[0, "#C4B5FD"], [1, CORES["primaria"]]],
                     text_auto=".1f",
                     labels={"faixa_renda_familiar": "Faixa de Renda", "pct_saude_mental": "% Saúde Mental"})
        fig.update_layout(**LAYOUT_BASE,
            coloraxis_showscale=False,
            xaxis_tickangle=-20,
            height=360,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("🗺️ Gasto Total Médio por Estado (UF)")
    uf_media = df.groupby("uf")["total_despesa_saude"].mean().sort_values(ascending=False).reset_index()
    fig = px.bar(uf_media, x="uf", y="total_despesa_saude",
                 color="total_despesa_saude", color_continuous_scale="RdPu",
                 text_auto=".0f",
                 labels={"uf": "Estado (UF)", "total_despesa_saude": "R$ Total Médio/Mês"})
    fig.update_layout(**LAYOUT_BASE, height=380)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📦 Composição do Gasto em Saúde por Faixa de Renda")
    cols_d = ["despesa_medicamentos", "despesa_consultas", "despesa_plano_saude", "despesa_saude_mental"]
    if all(c in df.columns for c in cols_d):
        comp = df.groupby("faixa_renda_familiar")[cols_d].mean().reindex(
            [f for f in ordem_renda if f in df["faixa_renda_familiar"].unique()]
        ).reset_index()
        comp_long = comp.melt(id_vars="faixa_renda_familiar", var_name="Tipo", value_name="Valor (R$)")
        comp_long["Tipo"] = comp_long["Tipo"].str.replace("despesa_", "").str.replace("_", " ").str.title()
        fig = px.bar(comp_long, x="faixa_renda_familiar", y="Valor (R$)",
                     color="Tipo", barmode="stack",
                     color_discrete_sequence=PALETA_REGIOES,
                     labels={"faixa_renda_familiar": "Faixa de Renda"})
        fig.update_layout(**LAYOUT_BASE,
            height=390,
            xaxis_tickangle=-20,
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig, use_container_width=True)


def pagina_tendencias_globais(dados):
    titulo("🌍", "Tendências Globais de Depressão")

    df = dados.get("prevalencia_depressao_global", pd.DataFrame())
    if df.empty:
        st.warning("Tabela `prevalencia_depressao_global` não disponível.")
        return

    # Detectar colunas
    col_pais  = next((c for c in ["pais", "country", "location", "Entity"] if c in df.columns), None)
    col_ano   = next((c for c in ["ano", "year", "Year"]                   if c in df.columns), None)
    col_prev  = next((c for c in ["prevalencia_depressao", "prevalence", "Value",
                                   "Depressive disorders (share of population) - Sex: Both - Age: Age-standardized"]
                      if c in df.columns), None)

    if not all([col_pais, col_ano, col_prev]):
        st.info("Estrutura dos dados globais não reconhecida.")
        st.dataframe(df.head(10))
        return

    df = df.rename(columns={col_pais: "pais", col_ano: "ano", col_prev: "prevalencia_depressao"})
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    df["prevalencia_depressao"] = pd.to_numeric(df["prevalencia_depressao"], errors="coerce")
    df = df.dropna(subset=["ano", "prevalencia_depressao"])

    col1, col2 = st.columns([2, 3])
    with col1:
        paises_disp = sorted(df["pais"].dropna().unique())
        # Sugerir países relevantes por padrão
        default_paises = [p for p in ["Brazil", "World", "United States", "Portugal", "Argentina"]
                          if p in paises_disp][:5] or paises_disp[:5]
        sel_paises = st.multiselect("Países / Regiões", paises_disp, default=default_paises)
    with col2:
        anos_disp = sorted(df["ano"].dropna().unique())
        intervalo_anos = st.slider("Período", int(min(anos_disp)), int(max(anos_disp)),
                                   (int(min(anos_disp)), int(max(anos_disp))))

    df = df[df["pais"].isin(sel_paises) & df["ano"].between(intervalo_anos[0], intervalo_anos[1])]
    st.markdown(f'<span class="info-chip">📊 {len(df):,} pontos filtrados</span>', unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("📈 Prevalência de Depressão ao Longo do Tempo (%)")
    fig = px.line(df, x="ano", y="prevalencia_depressao", color="pais",
                  markers=True,
                  color_discrete_sequence=px.colors.qualitative.Bold,
                  labels={"ano": "Ano", "prevalencia_depressao": "Prevalência (%)", "pais": "País"})
    fig.update_traces(marker=dict(size=5))
    fig.update_layout(**LAYOUT_BASE,
        legend=dict(orientation="h", y=-0.18),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    ultimo_ano = int(df["ano"].max())

    with col_a:
        st.subheader(f"🌍 Ranking em {ultimo_ano}")
        snap = df[df["ano"] == ultimo_ano].sort_values("prevalencia_depressao", ascending=True)
        fig = px.bar(snap, x="prevalencia_depressao", y="pais", orientation="h",
                     color="prevalencia_depressao",
                     color_continuous_scale=[[0, "#C4B5FD"], [1, CORES["primaria"]]],
                     text_auto=".2f",
                     labels={"prevalencia_depressao": "Prevalência (%)", "pais": "País"})
        fig.update_layout(**LAYOUT_BASE,
            coloraxis_showscale=False, height=310)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("📊 Variação Acumulada no Período")
        if intervalo_anos[0] != intervalo_anos[1]:
            ini = df[df["ano"] == intervalo_anos[0]].set_index("pais")["prevalencia_depressao"]
            fim = df[df["ano"] == intervalo_anos[1]].set_index("pais")["prevalencia_depressao"]
            var = ((fim - ini) / ini * 100).dropna().reset_index()
            var.columns = ["pais", "variacao_pct"]
            var = var.sort_values("variacao_pct")
            cores_v = [CORES["sucesso"] if v < 0 else CORES["primaria"] for v in var["variacao_pct"]]
            fig = go.Figure(go.Bar(
                x=var["variacao_pct"], y=var["pais"], orientation="h",
                marker_color=cores_v,
                text=var["variacao_pct"].round(1).astype(str) + "%",
                textposition="outside",
            ))
            fig.update_layout(**LAYOUT_BASE,
                xaxis_title="Variação (%)",
                height=310,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Selecione um intervalo de anos para ver a variação acumulada.")


# ─────────────────────────────────────────────────────────────────────────────
# 4. MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── Sidebar ───────────────────────────────────────────────────────────────
    st.sidebar.markdown("""
    <div style="text-align:center; padding: 20px 0 10px;">
        <div style="font-size:2.8rem">🧠</div>
        <div style="font-size:1.4rem; font-weight:800; letter-spacing:2px;">SAPA</div>
        <div style="font-size:0.75rem; opacity:0.7; margin-top:4px; line-height:1.5;">
            Sistema de Autoconhecimento<br>Psicológico Automatizado
        </div>
    </div>
    <hr style="border-color:rgba(255,255,255,0.15); margin:10px 0 18px;">
    """, unsafe_allow_html=True)

    with st.spinner("Carregando dados..."):
        dados, msg_status = carregar_dados()

    paginas = {
        "🏠 Visão Geral":          pagina_visao_geral,
        "🎭 Emoções & Atividades": pagina_emocoes_atividades,
        "📓 Diários Emocionais":   pagina_diarios,
        "🇧🇷 Saúde no Brasil":      pagina_saude_brasil,
        "🌍 Tendências Globais":   pagina_tendencias_globais,
    }

    st.sidebar.markdown('<div style="font-size:0.7rem; opacity:0.6; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">Navegação</div>', unsafe_allow_html=True)
    escolha = st.sidebar.radio("", list(paginas.keys()), label_visibility="collapsed")
    st.sidebar.markdown("---")

    tabelas_disp = list(dados.keys())
    total_registros = sum(len(dados[t]) for t in tabelas_disp)
    st.sidebar.markdown(f"""
    <div style="font-size:0.75rem; background:rgba(255,255,255,0.1);
         border-radius:8px; padding:10px 12px; margin-bottom:10px; line-height:1.6;">
        {msg_status}<br>
        <b>{total_registros:,}</b> registros totais
    </div>
    <div style="font-size:0.73rem; opacity:0.75; line-height:1.7;">
        📦 <b>{len(tabelas_disp)}</b> tabelas:<br>
        {"<br>".join(f"&nbsp;&nbsp;• {t}" for t in tabelas_disp)}
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style="font-size:0.7rem; opacity:0.55; text-align:center; line-height:1.7;">
        CEUB · Projeto Integrador I<br>
        Profa. Kadidja Valéria<br>
        Aula 15 · 25/05/2026
    </div>
    """, unsafe_allow_html=True)

    # ── Header principal ──────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {CORES['primaria']} 0%, {CORES['secundaria']} 100%);
         border-radius: 16px; padding: 24px 32px; margin-bottom: 28px; color: white;
         box-shadow: 0 4px 20px rgba(214,0,110,0.25);">
        <div style="font-size: 1.7rem; font-weight: 900; letter-spacing: 0.5px;">
            🧠 SAPA — Painel Interativo
        </div>
        <div style="font-size: 0.9rem; opacity: 0.88; margin-top: 6px;">
            Projeto Integrador I &nbsp;·&nbsp; CEUB &nbsp;·&nbsp; Ciência da Computação
            &nbsp;·&nbsp; {escolha.split(' ', 1)[-1]}
        </div>
    </div>
    """, unsafe_allow_html=True)

    paginas[escolha](dados)


if __name__ == "__main__":
    main()
