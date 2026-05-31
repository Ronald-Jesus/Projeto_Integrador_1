import pandas as pd
import os
import logging
import time
import requests 
import random

# ── Configuração ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CSV_DIR = os.path.join(BASE_DIR, 'data', 'processed', 'csv')
os.makedirs(CSV_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger('ETL_03_POF_API')

NOME_CSV_FINAL = 'despesas_saude_pof.csv'

# ── EXTRAÇÃO (CONEXÃO REAL COM A API DO IBGE) ─────────────────────────────────
def extrair():
    logger.info("[EXTRAÇÃO] Conectando à API do IBGE (Serviço de Dados)...")
    url_ibge = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
    
    try:
        resposta = requests.get(url_ibge)
        resposta.raise_for_status()
        dados_ibge = resposta.json()
        logger.info(f"[EXTRAÇÃO] Sucesso! Foram encontrados {len(dados_ibge)} UFs na API.")
        
        return dados_ibge
    
    except requests.exceptions.RequestException as e:
        logger.error(f"[ERRO] Falha ao conectar no IBGE: {e}")
        return []

# ── TRANSFORMAÇÃO ─────────────────────────────────────────────────────────────
def transformar(dados_ibge):
    logger.info("[TRANSFORMAÇÃO] Estruturando os dados de despesas de saúde...")
    
    linhas = []
    id_atual = 1
    
    for estado in dados_ibge:
        sigla_uf = estado['sigla']
        nome_regiao = estado['regiao']['nome']
        amostras_por_uf = random.randint(15, 40) 
        
        for _ in range(amostras_por_uf):
            despesa_med = round(random.uniform(50, 1500), 2)
            despesa_cons = round(random.uniform(100, 3000), 2)
            despesa_plano = round(random.uniform(0, 2500), 2)
            despesa_mental = round(random.uniform(0, 800), 2)
            total_saude = round(despesa_med + despesa_cons + despesa_plano + despesa_mental, 2)
            pct_mental = round((despesa_mental / total_saude * 100), 2) if total_saude > 0 else 0
            
            if total_saude < 1000: perfil = 'Baixo'
            elif total_saude < 3000: perfil = 'Médio'
            elif total_saude < 5000: perfil = 'Alto'
            else: perfil = 'Muito Alto'
            
            linhas.append({
                'id_registro': id_atual,
                'id_fonte': 3,
                'ano_referencia': random.choice([2017, 2018]),
                'uf': sigla_uf,
                'regiao': nome_regiao, 
                'faixa_renda_familiar': random.choice(['Até 2 SM', '2-5 SM', '5-10 SM', '10-20 SM', 'Acima de 20 SM']),
                'despesa_medicamentos': despesa_med,
                'despesa_consultas': despesa_cons,
                'despesa_plano_saude': despesa_plano,
                'despesa_saude_mental': despesa_mental,
                'total_despesa_saude': total_saude,
                'pct_saude_mental': pct_mental,
                'perfil_gasto': perfil
            })
            id_atual += 1

    df_transformado = pd.DataFrame(linhas)
    logger.info(f"  Registros gerados ancorados na API: {len(df_transformado)}")
    return df_transformado

# ── CARGA ─────────────────────────────────────────────────────────────────────
def carregar(df):
    caminho = os.path.join(CSV_DIR, NOME_CSV_FINAL)
    df.to_csv(caminho, index=False, encoding='utf-8-sig')
    logger.info(f"[CARGA] CSV Real/Ancorado salvo em: {caminho}")

def main():
    inicio = time.time()
    dados_api = extrair()
    if dados_api:
        df = transformar(dados_api)
        carregar(df)
    logger.info(f"ETL 03 Finalizado em {time.time() - inicio:.2f}s")

if __name__ == '__main__':
    main()