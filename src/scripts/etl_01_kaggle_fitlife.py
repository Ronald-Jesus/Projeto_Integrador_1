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
        
    # 5. Mapeamento corrigido para colunas reais do FitLife
    n = len(df)

    def col_str(candidates, default='Não Informado'):
        for c in candidates:
            if c in df.columns:
                return df[c].fillna(default)
        return pd.Series([default] * n, index=df.index)

    def col_num(candidates, default=0):
        for c in candidates:
            if c in df.columns:
                return pd.to_numeric(df[c], errors='coerce').fillna(default)
        return pd.Series([default] * n, index=df.index)

    df_transformado['emocao_principal']        = col_str(['primary emotion', 'mood'])
    df_transformado['humor_score']             = col_num(['mood before (1-10)', 'mood after (1-10)', 'mood_score'])
    df_transformado['atividade']               = col_str(['activity', 'sub-category'])
    df_transformado['duracao_min']             = col_num(['duration (minutes)', 'duration_minutes'])
    df_transformado['calorias']                = col_num(['calories_burned', 'calories burned'])
    df_transformado['frequencia_cardiaca_media'] = col_num(['heart_rate_avg', 'heart rate avg'])
    df_transformado['qualidade_sono']          = col_str(['sleep_quality', 'sleep quality'])
    df_transformado['nivel_estresse']          = col_num(['stress level (1-10)', 'stress_level'])
    
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