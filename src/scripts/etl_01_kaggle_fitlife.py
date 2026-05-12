import pandas as pd
import os
import sys
import logging
import time
import zipfile
import kaggle

# ── Configuração ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw') 
CSV_DIR = os.path.join(BASE_DIR, 'data', 'processed', 'csv')

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger('ETL_01_FitLife_REAL')

DATASET_KAGGLE = 'jijagallery/fitlife-emotions-mood-and-activity-dataset'
NOME_CSV_FINAL = 'emocoes_atividades.csv'

# ── EXTRAÇÃO (DOWNLOAD REAL DA API DO KAGGLE) ─────────────────────────────────
def extrair():
    logger.info("[EXTRAÇÃO] Conectando à API do Kaggle...")
    
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files(DATASET_KAGGLE, path=RAW_DIR, unzip=True)
    
    logger.info("[EXTRAÇÃO] Download concluído. Lendo o CSV original...")
    
    caminho_raw = os.path.join(RAW_DIR, 'fitlife_emotional_dataset.csv')
    
    df = pd.read_csv(caminho_raw)
    logger.info(f"  Registros reais extraídos: {len(df)}")
    return df

# ── TRANSFORMAÇÃO ─────────────────────────────────────────────────────────────
def transformar(df):
    logger.info("[TRANSFORMAÇÃO] Padronizando colunas reais do FitLife...")
    
    logger.info(f"Colunas que vieram do Kaggle: {list(df.columns)}")
    
    df.columns = [str(c).lower().strip() for c in df.columns]
    
    df_transformado = pd.DataFrame()
    
    if 'user_id' in df.columns:
        df_transformado['id_registro'] = df['user_id']
    else:
        df_transformado['id_registro'] = range(1, len(df) + 1)
        
    df_transformado['id_fonte'] = 1
    
    if 'date' in df.columns:
        df_transformado['data_registro'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    else:
        df_transformado['data_registro'] = pd.Timestamp.now().strftime('%Y-%m-%d')
        
    # 5. Mapeamento Dinâmico com .get()
    # Sintaxe: df.get('nome_da_coluna', valor_se_der_erro)
    df_transformado['emocao_principal'] = df.get('mood', 'Não Informado')
    df_transformado['humor_score'] = df.get('mood_score', 0)
    df_transformado['atividade'] = df.get('activity', 'Não Informado')
    df_transformado['duracao_min'] = df.get('duration_minutes', 0)
    df_transformado['calorias'] = df.get('calories_burned', 0)
    df_transformado['frequencia_cardiaca_media'] = df.get('heart_rate_avg', 0)
    df_transformado['qualidade_sono'] = df.get('sleep_quality', 'Não Informado')
    df_transformado['nivel_estresse'] = df.get('stress_level', 0)
    
    logger.info(f"  Registros transformados: {len(df_transformado)}")
    return df_transformado

# ── CARGA ─────────────────────────────────────────────────────────────────────
def carregar(df):
    caminho = os.path.join(CSV_DIR, NOME_CSV_FINAL)
    df.to_csv(caminho, index=False, encoding='utf-8-sig')
    logger.info(f"[CARGA] CSV Real salvo em: {caminho}")

def main():
    inicio = time.time()
    df = extrair()
    df = transformar(df)
    carregar(df)
    logger.info(f"ETL 01 Finalizado em {time.time() - inicio:.2f}s")

if __name__ == '__main__':
    main()