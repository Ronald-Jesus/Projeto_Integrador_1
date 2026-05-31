import os
import sqlite3
import pandas as pd
import logging
import time

# ── 1. Configuração de Logs e Caminhos ────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if 'scripts' in SCRIPT_DIR:
    BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
else:
    BASE_DIR = SCRIPT_DIR

CSV_DIR = os.path.join(BASE_DIR, 'data', 'processed', 'csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data', 'processed')
os.makedirs(OUTPUT_DIR, exist_ok=True)

DB_PATH = os.path.join(OUTPUT_DIR, 'saude_mental.db')
EXCEL_PATH = os.path.join(OUTPUT_DIR, 'banco_saude_mental.xlsx')

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('Consolidador')

# ── EXECUÇÃO ──────────────────────────────────────────────────────────────────
def main():
    inicio = time.time()
    logger.info("=" * 70)
    logger.info(" 🗄️  INICIANDO A CONSOLIDAÇÃO DO BANCO DE DADOS (SQLite + Excel) ")
    logger.info("=" * 70)

    if not os.path.exists(CSV_DIR):
        logger.error(f"Pasta não encontrada: {CSV_DIR}")
        logger.error("Rode o 'run_all_etl.py' primeiro para gerar os CSVs.")
        return

    # Pega todos os arquivos .csv que os seus 7 ETLs geraram
    csv_files = [f for f in os.listdir(CSV_DIR) if f.endswith('.csv')]
    
    if not csv_files:
        logger.warning("⚠️ Nenhum arquivo CSV encontrado na pasta para consolidar!")
        return

    logger.info(f"🔎 Encontrados {len(csv_files)} arquivos CSV. Processando...\n")

    # Prepara as conexões para o Banco e para o Excel
    conn = sqlite3.connect(DB_PATH)
    excel_writer = pd.ExcelWriter(EXCEL_PATH, engine='openpyxl')

    tabelas_sucesso = 0
    total_linhas_banco = 0

    for arquivo in csv_files:
        caminho_csv = os.path.join(CSV_DIR, arquivo)
        nome_tabela = arquivo.replace('.csv', '') # Tira o .csv para virar nome de tabela
        
        try:
            df = pd.read_csv(caminho_csv, sep=';', encoding='utf-8-sig', low_memory=False)

            if len(df.columns) <= 1:
                df = pd.read_csv(caminho_csv, sep=',', encoding='utf-8-sig', low_memory=False)

            qtd_linhas = len(df)
            total_linhas_banco += qtd_linhas

            # 1. Salva no SQLite
            df.to_sql(nome_tabela, conn, if_exists='replace', index=False)
            
            # 2. Salva no Excel (Nomes de abas no Excel têm limite de 31 caracteres)
            nome_aba = nome_tabela[:31]
            df.to_excel(excel_writer, sheet_name=nome_aba, index=False)
            
            logger.info(f"  ✅ Tabela criada: '{nome_tabela}' -> {qtd_linhas} registros")
            tabelas_sucesso += 1
            
        except Exception as e:
            logger.error(f" Erro ao processar o arquivo {arquivo}: {e}")

    # Fecha os arquivos e salva
    excel_writer.close()
    conn.close()

    tempo_total = round(time.time() - inicio, 2)
    
    logger.info("\n" + "=" * 70)
    logger.info(f" 🎉 SUCESSO! {tabelas_sucesso} tabelas consolidadas em {tempo_total}s.")
    logger.info(f" 📊 Total de registros no banco: {total_linhas_banco} linhas.")
    logger.info("-" * 70)
    logger.info(f" 🛢️  Banco SQLite salvo em: data/processed/saude_mental.db")
    logger.info(f" 📗 Planilha Excel salva em: data/processed/banco_saude_mental.xlsx")
    logger.info("=" * 70)

if __name__ == '__main__':
    main()