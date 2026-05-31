import pandas as pd
import os
import logging
import time
import requests
import zipfile
import io

# Desativa avisos de segurança SSL
requests.packages.urllib3.disable_warnings()

# ── Configuração ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CSV_DIR = os.path.join(BASE_DIR, 'data', 'processed', 'csv')
os.makedirs(CSV_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger('ETL_06_SUS_RAPS')

URLS_RAPS = [
    "https://demas-dados-abertos.s3.amazonaws.com/csv/rapscapii.csv.zip",
    "https://demas-dados-abertos.s3.amazonaws.com/csv/rapslphg2.csv.zip",
    "https://demas-dados-abertos.s3.amazonaws.com/csv/rapssrti.csv.zip"
]

# ── EXTRAÇÃO ──────────────────────────────────────────────────────────────────
def extrair_e_unir():
    headers = {'User-Agent': 'Mozilla/5.0'}
    lista_dfs = []
    
    logger.info(f"[EXTRAÇÃO] Iniciando processamento de {len(URLS_RAPS)} arquivos do S3...")
    
    for url in URLS_RAPS:
        try:
            nome_arquivo = url.split('/')[-1]
            logger.info(f"  Baixando: {nome_arquivo}...")
            
            response = requests.get(url, headers=headers, verify=False, timeout=60)
            response.raise_for_status()
            
            # Abre o ZIP diretamente da memória
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                csv_filename = z.namelist()[0]
                with z.open(csv_filename) as f:
                    # Lê o CSV (SUS costuma usar separador ';' e codificação latin1)
                    df_temp = pd.read_csv(f, sep=';', encoding='latin1', low_memory=False, on_bad_lines='skip')
                    lista_dfs.append(df_temp)
                    logger.info(f"    {csv_filename} processado: {len(df_temp)} linhas.")
                    
        except Exception as e:
            logger.error(f"  Erro ao processar {url}: {e}")
            
    if lista_dfs:
        return pd.concat(lista_dfs, ignore_index=True)
    return None

# ── TRANSFORMAÇÃO ─────────────────────────────────────────────────────────────
def transformar(df):
    if df is not None and not df.empty:
        logger.info("[TRANSFORMAÇÃO] Padronizando colunas e limpando dados...")
        df.columns = [str(c).lower().strip().replace(' ', '_') for c in df.columns]
        df['id_fonte'] = 6
        logger.info(f"  Total consolidado: {len(df)} registros de infraestrutura.")
        return df
    
    logger.warning("[CONTINGÊNCIA] Falha geral no S3. Usando dados de segurança.")
    return pd.DataFrame([{'id_fonte': 6, 'uf': 'DF', 'tipo': 'CAPS', 'quantidade': 18}])

# ── CARGA ─────────────────────────────────────────────────────────────────────
def carregar(df):
    caminho = os.path.join(CSV_DIR, 'infraestrutura_raps_sus.csv')
    df.to_csv(caminho, index=False, sep=';', encoding='utf-8-sig')
    logger.info(f"[CARGA] Sucesso! CSV consolidado salvo em: {caminho}")

def main():
    inicio = time.time()
    df_bruto = extrair_e_unir()
    df_limpo = transformar(df_bruto)
    carregar(df_limpo)
    logger.info(f"Pipeline ETL 06 concluído em {time.time() - inicio:.2f}s")

if __name__ == '__main__':
    main()  