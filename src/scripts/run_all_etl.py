import sys
import os
import time
import logging
from datetime import datetime

# ── 1. Ajuste de Caminhos (Blindagem contra erros de importação) ──────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
LOG_DIR = os.path.join(BASE_DIR, 'output', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f'etl_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('Orquestrador')

# ── Módulos ETL ───────────────────────────────────────────────────────────────
try:
    import etl_01_kaggle_fitlife as etl_01
    import etl_02_kaggle_journal as etl_02
    import etl_03_ibge_pof as etl_03
    import etl_04_datasus as etl_04
    import etl_05_oms_who as etl_05
    import etl_06_sus_raps as etl_06
    import etl_07_owid_depressao as etl_07
except ImportError as e:
    logger.error(f"Erro Crítico de Importação: {e}")
    logger.error("Verifique se o run_all_etl.py está na mesma pasta que os arquivos etl_*.py")
    sys.exit(1)

# ── 3. Dicionário de Fontes ───────────────────────────────────────────────────
FONTES = {
    1: {'nome': 'Kaggle – FitLife',           'modulo': etl_01},
    2: {'nome': 'Kaggle – Journal',           'modulo': etl_02},
    3: {'nome': 'IBGE – POF 2017-2018',       'modulo': etl_03},
    4: {'nome': 'DATASUS – Internações SUS',  'modulo': etl_04},
    5: {'nome': 'OMS – WHO Global Data',      'modulo': etl_05},
    6: {'nome': 'SUS – Infraestrutura RAPS',  'modulo': etl_06},
    7: {'nome': 'OWID – Depressão Global',    'modulo': etl_07},
}

def executar_pipeline():
    inicio_total = time.time()
    resultados = {}
    
    logger.info("=" * 70)
    logger.info("  INICIANDO PIPELINE DE DADOS (7 FONTES)")
    logger.info("=" * 70)

    for idx in sorted(FONTES.keys()):
        fonte = FONTES[idx]
        logger.info(f"\n[{idx}/7] Iniciando: {fonte['nome']}...")
        
        t0 = time.time()
        try:
            # Chama a função main() de cada arquivo
            df = fonte['modulo'].main()
            duracao = time.time() - t0
            
            # Validação para evitar erros se o script não retornar um DataFrame
            qtd_registros = len(df) if df is not None and hasattr(df, '__len__') else 0
            
            resultados[idx] = {
                'status': '✅ OK',
                'registros': qtd_registros,
                'tempo': round(duracao, 2)
            }
        except Exception as e:
            duracao = time.time() - t0
            logger.error(f"❌ ERRO na execução da fonte {idx}: {e}")
            resultados[idx] = {
                'status': '❌ ERRO',
                'registros': 0,
                'tempo': round(duracao, 2)
            }

    # ── 4. Relatório Final de Execução ──────────────────────────────────────────
    logger.info("\n" + "=" * 25 + " RELATÓRIO FINAL " + "=" * 28)
    logger.info(f"  {'Fonte':<30} | {'Status':<8} | {'Registros':>10} | {'Tempo'}")
    logger.info("-" * 75)
    
    total_linhas = 0
    for idx, r in resultados.items():
        total_linhas += r['registros']
        logger.info(f"  {FONTES[idx]['nome']:<30} | {r['status']:<8} | {r['registros']:>10} | {r['tempo']}s")
    
    tempo_total = round(time.time() - inicio_total, 2)
    logger.info("-" * 75)
    logger.info(f"  TOTAL PROCESSADO: {total_linhas} linhas em {tempo_total}s.")
    logger.info("=" * 75)

if __name__ == '__main__':
    executar_pipeline()