import urllib.request
import os
import sys
import subprocess

PROJ = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(PROJ, "src", "scripts")
BASE_URL = "https://raw.githubusercontent.com/Ronald-Jesus/Projeto_Integrador_1/main/src/scripts"

SCRIPTS = [
    "etl_01_kaggle_fitlife.py",
    "etl_02_kaggle_journal.py",
    "etl_03_ibge_pof.py",
    "etl_04_datasus.py",
    "etl_05_oms_who.py",
    "etl_06_sus_raps.py",
    "etl_07_owid_depressao.py",
    "gerar_banco_dados.py",
    "run_all_etl.py",
]

def main():
    print("=" * 55)
    print("  SAPA - Pipeline de Dados Reais")
    print("=" * 55)

    # Criar pastas
    for pasta in [
        SCRIPTS_DIR,
        os.path.join(PROJ, "data", "raw"),
        os.path.join(PROJ, "data", "processed", "csv"),
        os.path.join(PROJ, "output", "logs"),
    ]:
        os.makedirs(pasta, exist_ok=True)
    print("[1/4] Pastas criadas.")

    # Instalar dependencias
    print("[2/4] Instalando dependencias...")
    pacotes = ["kaggle", "pandas", "requests", "openpyxl", "pysus", "numpy"]
    for p in pacotes:
        r = subprocess.run([sys.executable, "-m", "pip", "install", p, "-q"], capture_output=True)
        status = "OK" if r.returncode == 0 else "FALHOU (continuando)"
        print(f"      {p}: {status}")
    print("      Dependencias prontas.")

    # Baixar scripts
    print("[3/4] Baixando scripts do GitHub...")
    for script in SCRIPTS:
        url = f"{BASE_URL}/{script}"
        dest = os.path.join(SCRIPTS_DIR, script)
        try:
            urllib.request.urlretrieve(url, dest)
            print(f"      OK: {script}")
        except Exception as e:
            print(f"      ERRO: {script} -> {e}")

    # Rodar pipeline
    print("\n[4/4] Rodando o pipeline...")
    os.environ["KAGGLE_API_TOKEN"] = "KGAT_8afdffa9194200cbcdf33dd2875c9a02"

    os.chdir(SCRIPTS_DIR)

    print("\n--- Executando ETLs ---")
    # Tenta o runner robusto primeiro (pula ETLs com dependencias faltando)
    runner = "run_etls_robusto.py" if os.path.exists("run_etls_robusto.py") else "run_all_etl.py"
    ret = subprocess.run([sys.executable, runner], env=os.environ)

    print("\n--- Gerando banco de dados ---")
    ret2 = subprocess.run([sys.executable, "gerar_banco_dados.py"], env=os.environ)

    # Copiar banco para raiz do projeto
    for candidato in [
        os.path.join(PROJ, "data", "processed", "saude_mental.db"),
        os.path.join(PROJ, "data", "saude_mental.db"),
        os.path.join(SCRIPTS_DIR, "..", "..", "data", "processed", "saude_mental.db"),
    ]:
        candidato = os.path.normpath(candidato)
        if os.path.exists(candidato):
            import shutil
            dest_db = os.path.join(PROJ, "saude_mental.db")
            shutil.copy2(candidato, dest_db)
            print(f"\nBanco copiado para: {dest_db}")
            break

    print("\n" + "=" * 55)
    print("  CONCLUIDO!")
    print("  Rode agora:")
    print("  python -m streamlit run dashboard.py")
    print("=" * 55)
    input("\nPressione Enter para sair...")

if __name__ == "__main__":
    main()
