import sqlite3
import pandas as pd
import os
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))
raw_path = os.path.join(BASE, 'data', 'raw', 'data.csv')
csv_path = os.path.join(BASE, 'data', 'processed', 'csv', 'diarios_emocoes.csv')

print("=" * 50)
print("  SAPA - Corrigindo emocoes dos Diarios")
print("=" * 50)

# Ler o CSV raw do Journal
print("\n[1/3] Lendo data.csv...")
df = pd.read_csv(raw_path)
df.columns = [str(c).lower().strip() for c in df.columns]

emocao_cols = [c for c in df.columns if 'answer.f1.' in c and c.endswith('.raw')]
texto_col = next((c for c in df.columns if 'answer' in c and 'f1' not in c and 't1' not in c), None)
print(f"  Colunas de emocao encontradas: {len(emocao_cols)}")

# Montar CSV corrigido
out = pd.DataFrame()
out['id_entrada'] = range(1, len(df) + 1)
out['id_fonte'] = 2
out['data_entrada'] = pd.Timestamp.now().strftime('%Y-%m-%d')
out['texto_entrada'] = df[texto_col] if texto_col else 'Sem Texto'
out['emocao_rotulada'] = df[emocao_cols].apply(
    lambda row: next(
        (col.split('.')[2].capitalize() for col in emocao_cols if row[col] == True),
        'Nao Informado'
    ), axis=1
)
out['comprimento_texto'] = out['texto_entrada'].astype(str).str.len()

out.to_csv(csv_path, index=False, encoding='utf-8-sig')
print(f"  CSV salvo: {len(out)} registros")
print(out['emocao_rotulada'].value_counts().head(6).to_string())

# Atualizar banco de dados
print("\n[2/3] Atualizando banco de dados...")
dbs = [
    os.path.join(BASE, 'saude_mental.db'),
    os.path.join(BASE, 'data', 'processed', 'saude_mental.db'),
]
for db in dbs:
    if os.path.exists(db):
        try:
            conn = sqlite3.connect(db, timeout=10)
            out.to_sql('diarios_emocoes', conn, if_exists='replace', index=False)
            conn.commit()
            conn.close()
            print(f"  OK: {os.path.basename(db)}")
        except Exception as e:
            print(f"  ERRO em {os.path.basename(db)}: {e}")

# Sincronizar raiz <- processed
src = os.path.join(BASE, 'data', 'processed', 'saude_mental.db')
dst = os.path.join(BASE, 'saude_mental.db')
if os.path.exists(src) and src != dst:
    shutil.copy2(src, dst)
    print("  Banco sincronizado para raiz.")

print("\n[3/3] Concluido!")
print("\nReabra o dashboard:")
print("  python -m streamlit run dashboard.py")
print("=" * 50)
input("\nPressione Enter para sair...")
