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
    
    # Coluna de texto (nome varia por versão do dataset)
    texto_col = next((c for c in df.columns if 'answer' in c and 'f1' not in c and 't1' not in c), None)
    df_transformado['texto_entrada'] = df[texto_col] if texto_col else 'Sem Texto'

    # Colunas de emoção: padrão "answer.f1.<emocao>.raw"
    emocao_cols = [c for c in df.columns if 'answer.f1.' in c and c.endswith('.raw')]

    if emocao_cols:
        logger.info(f"  Colunas de emoção encontradas: {emocao_cols}")
        # Para cada linha, pega todas as emoções marcadas como True e escolhe a primeira
        def descobrir_emocao(linha):
            ativas = [c for c in emocao_cols if linha[c] == True]
            if not ativas:
                return 'Não Informado'
            # Extrai o nome da emoção do padrão "answer.f1.<emocao>.raw"
            return ativas[0].split('.')[2].strip().capitalize()
        df_transformado['emocao_rotulada'] = df[emocao_cols].apply(
            lambda row: next(
                (col.split('.')[2].capitalize() for col in emocao_cols if row[col] == True),
                'Não Informado'
            ), axis=1
        )
    else:
        logger.warning("  Nenhuma coluna de emoção encontrada — usando 'Não Informado'")
        df_transformado['emocao_rotulada'] = 'Não Informado'
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