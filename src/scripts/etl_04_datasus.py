import pandas as pd
import os
import logging
import time
from datetime import datetime
from pysus import sih

# ── Configuração ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CSV_DIR = os.path.join(BASE_DIR, 'data', 'processed', 'csv')
os.makedirs(CSV_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger('ETL_04_DATASUS_REAL')

NOME_CSV_FINAL = 'internacoes_saude_mental.csv'

# ── EXTRAÇÃO (CONEXÃO REAL COM DATASUS VIA PYSUS 2.0) ─────────────────────────
def extrair():
    logger.info("[EXTRAÇÃO] Conectando aos servidores do DATASUS (SIH)...")
    
    estado_alvo = 'DF' 
    ano_atual = datetime.now().year - 1
    mes_alvo = 6 
    
    logger.info(f"[EXTRAÇÃO] Baixando Internações Hospitalares - UF: {estado_alvo} | Ano: {ano_atual} | Mês: {mes_alvo}")
    
    try:
        df_bruto = sih(state=estado_alvo, year=ano_atual, month=mes_alvo)
        logger.info(f"[EXTRAÇÃO] Download concluído! Registros brutos obtidos: {len(df_bruto)}")
        return df_bruto
    except Exception as e:
        logger.error(f"[ERRO] Falha ao baixar dados do DATASUS: {e}")
        return pd.DataFrame()
    
# ── TRANSFORMAÇÃO FINAL (COM O NOME DE COLUNA CORRETO) ──────────────────────────
def transformar(df):
    if df.empty:
        logger.warning("[AVISO] DataFrame vazio. Pulando transformação.")
        return df
        
    logger.info("[TRANSFORMAÇÃO] Filtrando internações de Saúde Mental (SP_CIDPRI)...")
    
    df.columns = [str(c).upper().strip() for c in df.columns]
    
    df_transformado = pd.DataFrame()
    df_transformado['id_internacao'] = range(1, len(df) + 1)
    df_transformado['id_fonte'] = 4
    df_transformado['ano_atendimento'] = df.get('SP_AA', 0)
    df_transformado['mes_atendimento'] = df.get('SP_MM', 0)
    df_transformado['uf'] = df.get('SP_UF', 'DF')
    df_transformado['regiao'] = 'Centro-Oeste' 
    df_transformado['cid_diagnostico'] = df.get('SP_CIDPRI', 'NAO_INFORMADO')
    
    # Criando a flag de Saúde Mental (CIDs que começam com F)
    df_transformado['eh_saude_mental'] = df_transformado['cid_diagnostico'].astype(str).str.startswith('F').map({True: 'Sim', False: 'Não'})    
    df_transformado['carater_atendimento'] = df.get('SP_DTINTER', 'Não Informado') # Data de internação ou caráter
    df_transformado['valor_total'] = pd.to_numeric(df.get('SP_VALATO', 0), errors='coerce').fillna(0).round(2)
    
    # FILTRO REAL: Agora sim, manter apenas os casos de Saúde Mental
    df_final = df_transformado[df_transformado['eh_saude_mental'] == 'Sim'].copy()
    df_final = df_final.drop(columns=['eh_saude_mental'])
    
    logger.info(f"  Sucesso! Dos {len(df)} registros, {len(df_final)} são de Saúde Mental.")
    return df_final

# ── CARGA ─────────────────────────────────────────────────────────────────────
def carregar(df):
    if df.empty:
        logger.warning("[AVISO] Nenhum dado para salvar.")
        return
        
    caminho = os.path.join(CSV_DIR, 'internacoes_saude_mental.csv')
    df.to_csv(caminho, index=False, sep=';', encoding='utf-8-sig')
    logger.info(f"[CARGA] CSV Real do DATASUS salvo em: {caminho}")

def main():
    inicio = time.time()
    df_bruto = extrair()
    df_processado = transformar(df_bruto)
    carregar(df_processado)
    logger.info(f"ETL 04 Finalizado em {time.time() - inicio:.2f}s")

if __name__ == '__main__':
    main()