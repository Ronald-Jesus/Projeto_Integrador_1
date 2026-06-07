"""
Runner robusto: executa cada ETL individualmente,
pulando os que falharem sem travar o pipeline.
"""
import sys
import os
import time
import logging
from datetime import datetime

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

FONTES = {
    1: {'nome': 'Kaggle – FitLife',         'modulo': 'etl_01_kaggle_fitlife'},
    2: {'nome': 'Kaggle – Journal',          'modulo': 'etl_02_kaggle_journal'},
    3: {'nome': 'IBGE – POF 2017-2018',      'modulo': 'etl_03_ibge_pof'},
    4: {'nome': 'DATASUS – Internacoes SUS', 'modulo': 'etl_04_datasus'},
    5: {'nome': 'OMS – WHO Global Data',     'modulo': 'etl_05_oms_who'},
    6: {'nome': 'SUS – Infraestrutura RAPS', 'modulo': 'etl_06_sus_raps'},
    7: {'nome': 'OWID – Depressao Global',   'modulo': 'etl_07_owid_depressao'},
}

def executar_pipeline():
    inicio_total = time.time()
    resultados = {}

    logger.info("=" * 65)
    logger.info("  INICIANDO PIPELINE DE DADOS (7 FONTES)")
    logger.info("=" * 65)

    for idx in sorted(FONTES.keys()):
        fonte = FONTES[idx]
        logger.info(f"\n[{idx}/7] Iniciando: {fonte['nome']}...")
        t0 = time.time()
        try:
            modulo = __import__(fonte['modulo'])
            df = modulo.main()
            duracao = time.time() - t0
            qtd = len(df) if df is not None and hasattr(df, '__len__') else 0
            resultados[idx] = {'status': 'OK', 'registros': qtd, 'tempo': round(duracao, 2)}
            logger.info(f"  Concluido: {qtd} registros em {round(duracao,2)}s")
        except ImportError as e:
            duracao = time.time() - t0
            logger.warning(f"  PULADO (modulo nao disponivel): {e}")
            resultados[idx] = {'status': 'PULADO', 'registros': 0, 'tempo': round(duracao, 2)}
        except Exception as e:
            duracao = time.time() - t0
            logger.error(f"  ERRO: {e}")
            resultados[idx] = {'status': 'ERRO', 'registros': 0, 'tempo': round(duracao, 2)}

    logger.info("\n" + "=" * 20 + " RELATORIO FINAL " + "=" * 28)
    logger.info(f"  {'Fonte':<30} | {'Status':<8} | {'Registros':>10} | Tempo")
    logger.info("-" * 70)
    total = 0
    for idx, r in resultados.items():
        total += r['registros']
        logger.info(f"  {FONTES[idx]['nome']:<30} | {r['status']:<8} | {r['registros']:>10} | {r['tempo']}s")
    tempo_total = round(time.time() - inicio_total, 2)
    logger.info("-" * 70)
    logger.info(f"  TOTAL: {total} registros em {tempo_total}s")
    logger.info("=" * 70)

if __name__ == '__main__':
    executar_pipeline()
