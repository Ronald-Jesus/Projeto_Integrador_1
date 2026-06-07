"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  SAPA — Sistema de Autoconhecimento Psicológico Automatizado                 ║
║  Algoritmo Analítico com Regras de Negócio                                   ║
║  Módulo 4 · Aula 16 · 01/06/2026                                             ║
║  Profª Kadidja Valéria · CEUB · Ciência da Computação · Projeto Integrador I ║
╚══════════════════════════════════════════════════════════════════════════════╝

PROBLEMA DE NEGÓCIO
───────────────────
Identificar, de forma automatizada, usuários do SAPA que apresentam padrões
de risco emocional — combinando humor, estresse, qualidade do sono e
frequência cardíaca — e gerar recomendações personalizadas antes que o quadro
se agrave.

LÓGICA DO ALGORITMO
────────────────────
1. Carrega os dados de emoções e atividades (SQLite ou demo)
2. Calcula métricas individuais por usuário (janela de 7 dias)
3. Aplica regras de negócio para gerar um SCORE DE RISCO (0–100)
4. Classifica em 3 níveis: 🟢 Saudável / 🟡 Atenção / 🔴 Crítico
5. Gera recomendações acionáveis para cada perfil
6. Exporta relatório em CSV e exibe análise textual

COMO RODAR
──────────
    pip install pandas numpy
    python algoritmo_analitico_sapa.py
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

VERSAO_ALGORITMO = "1.0.0"
DATA_EXECUCAO = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Pesos das métricas no score final (somam 100)
PESOS = {
    "humor":              30,   # peso mais alto — indicador direto do estado emocional
    "estresse":           30,   # peso alto — correlação forte com transtornos
    "sono":               25,   # muito relevante — sono ruim agrava quadros
    "freq_cardiaca":      15,   # indicador fisiológico de ansiedade
}

# Limiares para classificação de risco
LIMIAR_SAUDAVEL =  40   # score 0–39  → 🟢 Saudável
LIMIAR_ATENCAO  =  70   # score 40–69 → 🟡 Atenção
                        # score 70–100 → 🔴 Crítico

# ─────────────────────────────────────────────────────────────────────────────
# 1. CARREGAMENTO DE DADOS
# ─────────────────────────────────────────────────────────────────────────────

def encontrar_banco():
    """Busca saude_mental.db em locais padrão do projeto."""
    candidatos = [
        "saude_mental.db",
        os.path.join(os.path.dirname(__file__), "saude_mental.db"),
        os.path.join(os.path.dirname(__file__), "data", "processed", "saude_mental.db"),
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "saude_mental.db"),
    ]
    for c in candidatos:
        if os.path.exists(c):
            return os.path.abspath(c)
    return None


def carregar_dados():
    """Carrega emocoes_atividades do SQLite ou gera dados demo."""
    db = encontrar_banco()

    if db:
        print(f"  ✅ Banco real encontrado: {db}")
        conn = sqlite3.connect(db)
        df = pd.read_sql("SELECT * FROM emocoes_atividades", conn)
        conn.close()
        fonte = "SQLite (saude_mental.db)"
    else:
        print("  ⚠️  saude_mental.db não encontrado — gerando dados de demonstração.")
        df = _gerar_demo()
        fonte = "Dados de demonstração"

    df["data_registro"] = pd.to_datetime(df["data_registro"])

    # Garante que colunas numéricas são numéricas
    for col in ["humor_score", "nivel_estresse", "frequencia_cardiaca_media", "duracao_min", "calorias"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Mapeia qualidade_sono para valor numérico (para cálculos)
    mapa_sono = {"Ótimo": 5, "Bom": 4, "Regular": 3, "Ruim": 2, "Péssimo": 1}
    if "qualidade_sono" in df.columns:
        df["sono_num"] = df["qualidade_sono"].map(mapa_sono).fillna(3)

    print(f"  📊 {len(df)} registros carregados | Fonte: {fonte}")
    return df


def _gerar_demo():
    """Gera 200 registros simulando 10 usuários com perfis diferentes."""
    rng = np.random.default_rng(42)
    n_usuarios = 10
    n_por_usuario = 20

    emocoes   = ["Feliz", "Triste", "Ansioso", "Calmo", "Irritado",
                 "Motivado", "Cansado", "Esperançoso"]
    atividades = ["Corrida", "Yoga", "Natação", "Musculação", "Caminhada",
                  "Ciclismo", "Meditação", "Dança"]
    sono_opts = ["Ótimo", "Bom", "Regular", "Ruim", "Péssimo"]

    # Perfis de risco por usuário (para dados realistas)
    perfis_humor = {
        1: (8, 1),  2: (7, 1),  3: (6, 2),  4: (5, 2),  5: (4, 2),
        6: (3, 2),  7: (2, 1),  8: (6, 1),  9: (5, 3),  10: (4, 3),
    }

    linhas = []
    base_data = datetime(2024, 1, 1)

    for uid in range(1, n_usuarios + 1):
        mu_humor, sigma = perfis_humor[uid]
        for d in range(n_por_usuario):
            humor = int(np.clip(rng.normal(mu_humor, sigma), 1, 10))
            estresse = int(np.clip(11 - humor + rng.integers(-2, 3), 1, 10))
            fc = int(rng.normal(70 + estresse * 5, 10))
            sono_idx = max(0, min(4, int(rng.normal((humor / 2), 1))))

            linhas.append({
                "id_registro":             (uid - 1) * n_por_usuario + d + 1,
                "id_fonte":                1,
                "id_usuario":              uid,
                "data_registro":           (base_data + timedelta(days=d * 2)).strftime("%Y-%m-%d"),
                "emocao_principal":        rng.choice(emocoes),
                "humor_score":             humor,
                "atividade":               rng.choice(atividades),
                "duracao_min":             int(rng.integers(15, 90)),
                "calorias":                int(rng.integers(80, 600)),
                "frequencia_cardiaca_media": fc,
                "qualidade_sono":          sono_opts[sono_idx],
                "nivel_estresse":          estresse,
            })

    return pd.DataFrame(linhas)


# ─────────────────────────────────────────────────────────────────────────────
# 2. CÁLCULO DE MÉTRICAS POR USUÁRIO
# ─────────────────────────────────────────────────────────────────────────────

def calcular_metricas(df):
    """
    Calcula métricas agregadas por usuário.
    Se não houver coluna id_usuario, trata todos como um único perfil.
    """
    if "id_usuario" not in df.columns:
        df = df.copy()
        df["id_usuario"] = 1  # dataset sem ID individual → analisa como grupo

    grupos = []

    for uid, grupo in df.groupby("id_usuario"):
        grupo = grupo.sort_values("data_registro")
        n = len(grupo)

        # ── Médias ────────────────────────────────────────────────────────────
        humor_medio      = grupo["humor_score"].mean()
        estresse_medio   = grupo["nivel_estresse"].mean()
        fc_media         = grupo["frequencia_cardiaca_media"].mean() if "frequencia_cardiaca_media" in grupo else 80
        sono_medio       = grupo["sono_num"].mean() if "sono_num" in grupo else 3

        # ── Tendência (últimos 7 registros vs anteriores) ─────────────────────
        if n >= 4:
            metade = max(1, n // 2)
            humor_recente  = grupo["humor_score"].tail(metade).mean()
            humor_anterior = grupo["humor_score"].head(metade).mean()
            tendencia_humor = humor_recente - humor_anterior   # negativo = piorando
        else:
            tendencia_humor = 0

        # ── Emoção dominante ──────────────────────────────────────────────────
        emocao_dom = grupo["emocao_principal"].mode()[0] if "emocao_principal" in grupo else "—"

        # ── Frequência de emoções negativas ───────────────────────────────────
        emocoes_neg = {"Triste", "Ansioso", "Irritado", "Cansado"}
        pct_neg = grupo["emocao_principal"].isin(emocoes_neg).mean() * 100 if "emocao_principal" in grupo else 0

        # ── Dias com qualidade de sono ruim ───────────────────────────────────
        pct_sono_ruim = (grupo["sono_num"] <= 2).mean() * 100 if "sono_num" in grupo else 0

        # ── Consistência de exercícios (% dias com atividade registrada) ─────
        pct_ativo = (grupo["duracao_min"] >= 30).mean() * 100 if "duracao_min" in grupo else 0

        grupos.append({
            "id_usuario":       uid,
            "n_registros":      n,
            "humor_medio":      round(humor_medio, 2),
            "estresse_medio":   round(estresse_medio, 2),
            "fc_media":         round(fc_media, 1),
            "sono_medio":       round(sono_medio, 2),
            "tendencia_humor":  round(tendencia_humor, 2),
            "emocao_dominante": emocao_dom,
            "pct_emocoes_neg":  round(pct_neg, 1),
            "pct_sono_ruim":    round(pct_sono_ruim, 1),
            "pct_ativo":        round(pct_ativo, 1),
            "data_inicio":      grupo["data_registro"].min().strftime("%Y-%m-%d"),
            "data_fim":         grupo["data_registro"].max().strftime("%Y-%m-%d"),
        })

    return pd.DataFrame(grupos)


# ─────────────────────────────────────────────────────────────────────────────
# 3. REGRAS DE NEGÓCIO — SCORE DE RISCO
# ─────────────────────────────────────────────────────────────────────────────

def calcular_score_risco(row):
    """
    REGRAS DE NEGÓCIO DO SAPA
    ─────────────────────────
    Cada dimensão gera uma sub-pontuação de risco (0–100) que é depois
    ponderada pelo PESOS dict para compor o score final.

    ┌─────────────────────┬──────────────────────────────────────────────────┐
    │ Dimensão            │ Lógica                                           │
    ├─────────────────────┼──────────────────────────────────────────────────┤
    │ Humor               │ Inverte a escala: humor 1 = risco 100,           │
    │                     │ humor 10 = risco 0. Penaliza tendência negativa. │
    ├─────────────────────┼──────────────────────────────────────────────────┤
    │ Estresse            │ Proporcional: estresse 10 = risco 100.           │
    │                     │ Faixa crítica: estresse >= 8.                    │
    ├─────────────────────┼──────────────────────────────────────────────────┤
    │ Sono                │ Inverte escala (sono 1 = risco 100).             │
    │                     │ % de noites ruins amplia o risco.                │
    ├─────────────────────┼──────────────────────────────────────────────────┤
    │ Freq. Cardíaca      │ FC > 100 = risco alto (indicador de ansiedade).  │
    │                     │ FC 60–80 = saudável.                             │
    └─────────────────────┴──────────────────────────────────────────────────┘
    """
    detalhes = {}

    # ── Sub-score: Humor (0–100, onde 100 = máximo risco) ─────────────────────
    risco_humor_base = ((10 - row["humor_medio"]) / 9) * 100
    # Penalidade por tendência negativa (piora recente amplifica o risco)
    penalidade_tendencia = max(0, -row["tendencia_humor"]) * 8
    # Penalidade por alto % de emoções negativas
    penalidade_emocoes = row["pct_emocoes_neg"] * 0.3
    risco_humor = min(100, risco_humor_base + penalidade_tendencia + penalidade_emocoes)
    detalhes["risco_humor"] = round(risco_humor, 1)

    # ── Sub-score: Estresse (0–100) ────────────────────────────────────────────
    risco_estresse_base = ((row["estresse_medio"] - 1) / 9) * 100
    # Bônus de risco se estresse >= 8 (zona crítica clínica)
    bonus_critico = 15 if row["estresse_medio"] >= 8 else 0
    risco_estresse = min(100, risco_estresse_base + bonus_critico)
    detalhes["risco_estresse"] = round(risco_estresse, 1)

    # ── Sub-score: Sono (0–100) ────────────────────────────────────────────────
    risco_sono_base = ((5 - row["sono_medio"]) / 4) * 100
    # Penalidade por % de noites ruins
    penalidade_sono = row["pct_sono_ruim"] * 0.4
    risco_sono = min(100, risco_sono_base + penalidade_sono)
    detalhes["risco_sono"] = round(risco_sono, 1)

    # ── Sub-score: Frequência Cardíaca (0–100) ─────────────────────────────────
    fc = row["fc_media"]
    if fc < 60:                   # bradicardia — risco moderado
        risco_fc = 40
    elif fc <= 80:                # zona saudável
        risco_fc = max(0, (fc - 60) / 20 * 20)   # 0–20
    elif fc <= 100:               # elevada — atenção
        risco_fc = 20 + (fc - 80) / 20 * 40      # 20–60
    else:                         # acima de 100 — zona crítica de ansiedade
        risco_fc = min(100, 60 + (fc - 100) / 40 * 40)
    detalhes["risco_fc"] = round(risco_fc, 1)

    # ── Score Final Ponderado ──────────────────────────────────────────────────
    score_final = (
        risco_humor    * PESOS["humor"]       / 100 +
        risco_estresse * PESOS["estresse"]    / 100 +
        risco_sono     * PESOS["sono"]        / 100 +
        risco_fc       * PESOS["freq_cardiaca"] / 100
    )

    # Bônus de proteção: usuário ativo regularmente reduz o risco em até 8 pontos
    bonus_atividade = min(8, row["pct_ativo"] / 100 * 8)
    score_final = max(0, min(100, score_final - bonus_atividade))

    detalhes["bonus_atividade"] = round(bonus_atividade, 1)
    detalhes["score_final"]     = round(score_final, 1)

    return detalhes


# ─────────────────────────────────────────────────────────────────────────────
# 4. CLASSIFICAÇÃO E RECOMENDAÇÕES
# ─────────────────────────────────────────────────────────────────────────────

RECOMENDACOES = {
    "🟢 Saudável": [
        "Continue com sua rotina atual — ela está funcionando!",
        "Mantenha a frequência de registros no SAPA para monitoramento contínuo.",
        "Explore o módulo de hábitos avançados para potencializar seu bem-estar.",
        "Considere partilhar sua jornada com um profissional de psicologia.",
    ],
    "🟡 Atenção": [
        "Seu padrão emocional recente merece atenção. Não ignore os sinais.",
        "Pratique técnicas de respiração ou meditação por 10 minutos diários.",
        "Revise sua qualidade de sono — o SAPA identificou noites problemáticas.",
        "Reduza estímulos estressores quando possível nas próximas semanas.",
        "Considere uma consulta de acompanhamento com psicólogo ou terapeuta.",
    ],
    "🔴 Crítico": [
        "⚠️  Padrão de risco elevado identificado — ação imediata recomendada.",
        "Procure um profissional de saúde mental o quanto antes.",
        "Ative a rede de suporte: familiares, amigos próximos, colegas de confiança.",
        "Evite isolamento social — ele amplifica os quadros depressivos.",
        "CVV (Centro de Valorização da Vida): ligue 188 ou acesse cvv.org.br",
        "CAPS (Centro de Atenção Psicossocial): serviço gratuito pelo SUS na sua cidade.",
    ],
}


def classificar_e_recomendar(score):
    """Retorna nível de risco e lista de recomendações."""
    if score < LIMIAR_SAUDAVEL:
        nivel = "🟢 Saudável"
    elif score < LIMIAR_ATENCAO:
        nivel = "🟡 Atenção"
    else:
        nivel = "🔴 Crítico"
    return nivel, RECOMENDACOES[nivel]


def identificar_fator_principal(detalhes):
    """Identifica qual dimensão mais contribuiu para o risco."""
    mapa = {
        "risco_humor":    "Humor emocional",
        "risco_estresse": "Nível de estresse",
        "risco_sono":     "Qualidade do sono",
        "risco_fc":       "Frequência cardíaca",
    }
    scores_dim = {k: detalhes[k] for k in mapa}
    fator_key  = max(scores_dim, key=scores_dim.get)
    return mapa[fator_key], scores_dim[fator_key]


# ─────────────────────────────────────────────────────────────────────────────
# 5. RELATÓRIO FINAL
# ─────────────────────────────────────────────────────────────────────────────

def gerar_relatorio(metricas_df):
    """Aplica o algoritmo a todos os usuários e gera o relatório."""
    resultados = []

    for _, row in metricas_df.iterrows():
        detalhes = calcular_score_risco(row)
        score    = detalhes["score_final"]
        nivel, recomendacoes = classificar_e_recomendar(score)
        fator_principal, fator_score = identificar_fator_principal(detalhes)

        resultados.append({
            **row.to_dict(),
            **detalhes,
            "nivel_risco":       nivel,
            "fator_principal":   fator_principal,
            "fator_score":       fator_score,
            "recomendacoes":     " | ".join(recomendacoes),
        })

    return pd.DataFrame(resultados)


def imprimir_relatorio(df_resultado):
    """Exibe o relatório formatado no terminal."""
    sep = "=" * 72

    print(f"\n{sep}")
    print(f"  🧠 SAPA — RELATÓRIO DE ANÁLISE DE RISCO EMOCIONAL")
    print(f"  Versão do Algoritmo : {VERSAO_ALGORITMO}")
    print(f"  Executado em        : {DATA_EXECUCAO}")
    print(f"  Usuários analisados : {len(df_resultado)}")
    print(sep)

    # ── Estatísticas Gerais ───────────────────────────────────────────────────
    contagem = df_resultado["nivel_risco"].value_counts()
    print("\n📊 DISTRIBUIÇÃO DE RISCO:")
    for nivel in ["🟢 Saudável", "🟡 Atenção", "🔴 Crítico"]:
        n = contagem.get(nivel, 0)
        pct = n / len(df_resultado) * 100
        barra = "█" * int(pct / 5)
        print(f"   {nivel:<20} {n:>3} usuários  ({pct:4.1f}%)  {barra}")

    print(f"\n   Score médio geral   : {df_resultado['score_final'].mean():.1f}/100")
    print(f"   Score mais alto     : {df_resultado['score_final'].max():.1f} "
          f"(Usuário {df_resultado.loc[df_resultado['score_final'].idxmax(), 'id_usuario']})")
    print(f"   Score mais baixo    : {df_resultado['score_final'].min():.1f} "
          f"(Usuário {df_resultado.loc[df_resultado['score_final'].idxmin(), 'id_usuario']})")

    # ── Fator de Risco Predominante ────────────────────────────────────────────
    print("\n🔍 FATOR DE RISCO MAIS FREQUENTE:")
    fator_freq = df_resultado["fator_principal"].value_counts()
    for fator, n in fator_freq.items():
        print(f"   • {fator:<25} → {n} usuário(s)")

    # ── Detalhamento por Usuário ──────────────────────────────────────────────
    print(f"\n{'-' * 72}")
    print("  DETALHAMENTO POR USUÁRIO")
    print(f"{'-' * 72}")

    for _, row in df_resultado.sort_values("score_final", ascending=False).iterrows():
        print(f"\n  👤 Usuário #{int(row['id_usuario'])}  |  {row['nivel_risco']}  |  Score: {row['score_final']:.0f}/100")
        print(f"     Período analisado : {row['data_inicio']} → {row['data_fim']}  ({int(row['n_registros'])} registros)")
        print(f"     Humor médio       : {row['humor_medio']:.1f}/10"
              f"  (tendência: {'+' if row['tendencia_humor'] >= 0 else ''}{row['tendencia_humor']:.1f})")
        print(f"     Estresse médio    : {row['estresse_medio']:.1f}/10")
        print(f"     Sono médio        : {row['sono_medio']:.1f}/5  ({row['pct_sono_ruim']:.0f}% de noites ruins)")
        print(f"     FC média          : {row['fc_media']:.0f} bpm")
        print(f"     Emoções negativas : {row['pct_emocoes_neg']:.1f}%  |  Ativo: {row['pct_ativo']:.0f}% dos dias")
        print(f"     ⚠️  Fator principal: {row['fator_principal']} (sub-score: {row['fator_score']:.0f}/100)")
        print(f"\n     💡 Recomendações:")
        for rec in RECOMENDACOES[row["nivel_risco"]]:
            print(f"        → {rec}")

    print(f"\n{sep}")


def exportar_csv(df_resultado, caminho="relatorio_risco_sapa.csv"):
    """Exporta o relatório completo para CSV."""
    # Remove coluna de recomendações longas do CSV principal (fica no JSON)
    cols_csv = [c for c in df_resultado.columns if c != "recomendacoes"]
    df_resultado[cols_csv].to_csv(caminho, index=False, encoding="utf-8-sig", sep=";")
    print(f"\n  💾 Relatório CSV exportado: {caminho}")


def exportar_json_resumo(df_resultado, caminho="resumo_risco_sapa.json"):
    """Exporta um resumo JSON com alertas críticos — ideal para integração com APIs."""
    criticos = df_resultado[df_resultado["nivel_risco"] == "🔴 Crítico"]
    atencao  = df_resultado[df_resultado["nivel_risco"] == "🟡 Atenção"]

    resumo = {
        "versao_algoritmo":  VERSAO_ALGORITMO,
        "data_execucao":     DATA_EXECUCAO,
        "total_usuarios":    len(df_resultado),
        "distribuicao_risco": df_resultado["nivel_risco"].value_counts().to_dict(),
        "score_medio":       round(df_resultado["score_final"].mean(), 1),
        "alertas_criticos":  criticos[["id_usuario", "score_final", "fator_principal"]].to_dict("records"),
        "alertas_atencao":   atencao[["id_usuario", "score_final", "fator_principal"]].to_dict("records"),
    }

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)

    print(f"  💾 Resumo JSON exportado : {caminho}")


# ─────────────────────────────────────────────────────────────────────────────
# 6. PONTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 72)
    print("  🧠 SAPA — ALGORITMO ANALÍTICO v1.0.0")
    print("  Módulo 4 · Aula 16 · Projeto Integrador I · CEUB")
    print("=" * 72)

    # Passo 1: Carregar dados
    print("\n📥 [1/4] Carregando dados...")
    df = carregar_dados()

    # Passo 2: Calcular métricas
    print("\n📐 [2/4] Calculando métricas por usuário...")
    metricas = calcular_metricas(df)
    print(f"  {len(metricas)} perfil(is) gerado(s).")

    # Passo 3: Aplicar regras de negócio e gerar relatório
    print("\n⚙️  [3/4] Aplicando regras de negócio...")
    resultado = gerar_relatorio(metricas)
    print(f"  Algoritmo aplicado com sucesso.")

    # Passo 4: Exibir e exportar
    print("\n📄 [4/4] Gerando relatório...")
    imprimir_relatorio(resultado)
    exportar_csv(resultado)
    exportar_json_resumo(resultado)

    print("\n✅ Algoritmo finalizado com sucesso!")
    print(f"   Arquivos gerados:")
    print(f"   • relatorio_risco_sapa.csv  — análise completa (abrir no Excel)")
    print(f"   • resumo_risco_sapa.json    — alertas para integração com API")
    print("=" * 72)


if __name__ == "__main__":
    main()
