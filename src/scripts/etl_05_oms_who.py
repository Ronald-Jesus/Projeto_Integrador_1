
import pandas as pd
import os
import logging
import time
import requests

# ── Configuração de Pastas ───────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CSV_DIR = os.path.join(BASE_DIR, 'data', 'processed', 'csv')
os.makedirs(CSV_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger('ETL_05_OMS_WHO')

URL_API = "https://ghoapi.azureedge.net/api/MH_12"

def extrair():
    logger.info("[EXTRAÇÃO] Chamando API Global da OMS (WHO)...")
    try:
        response = requests.get(URL_API)
        response.raise_for_status()
        dados_json = response.json()
        df_bruto = pd.DataFrame(dados_json['value'])
        logger.info(f"  Dados mundiais recebidos: {len(df_bruto)} registros.")
        return df_bruto
    except Exception as e:
        logger.error(f"[ERRO] Falha ao conectar na OMS: {e}")
        return pd.DataFrame()
    
    # ── TRANSFORMAÇÃO ─────────────────────────────────────────────────────────────
def transformar(df):
    if df.empty:
        return df
        
    logger.info("[TRANSFORMAÇÃO] Investigando e filtrando dados da OMS...")
    
    logger.info(f"Colunas recebidas: {list(df.columns)}")
    if 'SpatialValueCode' in df.columns:
        exemplo_paises = df['SpatialValueCode'].unique()[:10]
        logger.info(f"Exemplos de códigos de países na API: {exemplo_paises}")
    
    df_transformado = pd.DataFrame()
    df_transformado['id_fonte'] = 5
    df_transformado['pais_codigo'] = df.get('SpatialValueCode')
    df_transformado['ano'] = df.get('TimeDimensionValue')
    df_transformado['genero'] = df.get('Dim1', 'Both sexes')
    df_transformado['taxa_prevalencia'] = pd.to_numeric(df.get('NumericValue', 0), errors='coerce').round(2)
    
    paises_comparacao = ['BRA', 'USA', 'ARG', 'PRT', 'CHN', 'FRA', 'CAN', 'JPN']
    df_filtrado = df_transformado[df_transformado['pais_codigo'].isin(paises_comparacao)].copy()
    
    if df_filtrado.empty:
        logger.warning("[AVISO] O filtro não encontrou 'BRA'. Guardando base completa para análise.")
        df_final = df_transformado
    else:
        mapeamento_sexo = {'BTSX': 'Ambos', 'MLE': 'Masculino', 'FMLE': 'Feminino'}
        df_filtrado['genero'] = df_filtrado['genero'].replace(mapeamento_sexo)
        df_final = df_filtrado

    logger.info(f"  Registros prontos para carga: {len(df_final)}")
    return df_final

# ── CARGA ─────────────────────────────────────────────────────────────────────
def carregar(df):
    if df.empty:
        logger.error("[CARGA] Nenhum dado disponível.")
        return
        
    caminho = os.path.join(CSV_DIR, 'prevalencia_oms.csv')
    df.to_csv(caminho, index=False, sep=';', encoding='utf-8-sig')
    logger.info(f"[CARGA] Ficheiro gerado com sucesso em: {caminho}")

def main():
    inicio = time.time()
    df_bruto = extrair()
    df_processado = transformar(df_bruto)
    carregar(df_processado)
    logger.info(f"ETL 05 Finalizado em {time.time() - inicio:.2f}s")

if __name__ == '__main__':
    main()