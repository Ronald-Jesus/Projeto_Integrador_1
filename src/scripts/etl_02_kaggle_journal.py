import pandas as pd
import os
import logging
import time
import kaggle
import glob

# ── Configuração ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
CSV_DIR = os.path.join(BASE_DIR, 'data', 'processed', 'csv')

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger('ETL_02_Journal_REAL')

DATASET_KAGGLE = 'madhavmalhotra/journal-entries-with-labelled-emotions'
NOME_CSV_FINAL = 'diarios_emocoes.csv'

# ── EXTRAÇÃO ──────────────────────────────────────────────────
def extrair():
    logger.info("[EXTRAÇÃO] Conectando à API do Kaggle (Journal Entries)...")
    
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files(DATASET_KAGGLE, path=RAW_DIR, unzip=True)
    
    arquivos = glob.glob(os.path.join(RAW_DIR, '*.csv'))
    
    arquivo_recente = max(arquivos, key=os.path.getctime)
    
    logger.info(f"[EXTRAÇÃO] Lendo o arquivo: {os.path.basename(arquivo_recente)}")
    df = pd.read_csv(arquivo_recente)
    logger.info(f"  Registros reais extraídos: {len(df)}")
    return df

# ── TRANSFORMAÇÃO ─────────────────────────────────────────────────────────────
def transformar(df):
    logger.info("[TRANSFORMAÇÃO] Padronizando diários reais...")
    
    df.columns = [str(c).lower().strip() for c in df.columns]
    logger.info(f"Colunas que vieram do Kaggle: {list(df.columns)}")
    
    df_transformado = pd.DataFrame()
    
    df_transformado['id_entrada'] = range(1, len(df) + 1)
    df_transformado['id_fonte'] = 2
    df_transformado['data_entrada'] = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    df_transformado['texto_entrada'] = df.get('answer (text)', 'Sem Texto')
    
    def descobrir_emocao(linha):
        for col in df.columns:
            if col.startswith('f1.') and linha[col] == True:
                return col.split('.')[1].strip().capitalize()
        return 'Não Informado'

    df_transformado['emocao_rotulada'] = df.apply(descobrir_emocao, axis=1)
    df_transformado['comprimento_texto'] = df_transformado['texto_entrada'].str.len()
    
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
    logger.info(f"ETL 02 Finalizado em {time.time() - inicio:.2f}s")

if __name__ == '__main__':
    main()