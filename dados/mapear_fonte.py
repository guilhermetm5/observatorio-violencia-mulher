"""
Mapeamento de fonte de dados — Observatório Violência Contra a Mulher
Uso: python mapear_fonte.py <arquivo.csv>
Gera um relatório completo da estrutura e qualidade do arquivo.
"""
import csv, sys, os, unicodedata
from collections import Counter
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")


def detectar_encoding(caminho):
    """Tenta identificar o encoding do arquivo."""
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            with open(caminho, encoding=enc) as f:
                f.read(1024)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


def detectar_separador(caminho, encoding):
    """Detecta o separador do CSV."""
    with open(caminho, encoding=encoding) as f:
        primeira = f.readline()
    for sep in [";", ",", "\t", "|"]:
        if sep in primeira:
            return sep
    return ","


def perfil_coluna(valores):
    """Gera estatísticas de uma coluna."""
    total      = len(valores)
    vazios     = sum(1 for v in valores if not v or v.strip() == "")
    unicos     = len(set(v.strip() for v in valores if v.strip()))
    mais_freq  = Counter(v.strip() for v in valores if v.strip()).most_common(5)
    return {
        "total":     total,
        "vazios":    vazios,
        "pct_vazio": round(vazios / total * 100, 1) if total else 0,
        "unicos":    unicos,
        "mais_freq": mais_freq
    }


def mapear_fonte(caminho):
    if not os.path.exists(caminho):
        print(f"Arquivo nao encontrado: {caminho}")
        sys.exit(1)

    encoding  = detectar_encoding(caminho)
    separador = detectar_separador(caminho, encoding)

    print("=" * 70)
    print("  MAPEAMENTO DE FONTE DE DADOS")
    print(f"  Arquivo : {os.path.basename(caminho)}")
    print(f"  Data    : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 70)

    # Lê o arquivo
    with open(caminho, encoding=encoding, newline="") as f:
        reader  = csv.DictReader(f, delimiter=separador)
        colunas = reader.fieldnames or []
        linhas  = list(reader)

    total_linhas = len(linhas)

    print(f"\n[INFO] Encoding detectado : {encoding}")
    print(f"[INFO] Separador detectado: '{separador}'")
    print(f"[INFO] Total de linhas    : {total_linhas:,}")
    print(f"[INFO] Total de colunas   : {len(colunas)}")

    # ── COLUNAS ──────────────────────────────────────────────────────────
    print("\n" + "-" * 70)
    print("  COLUNAS E PERFIL")
    print("-" * 70)

    dados_por_coluna = {}
    for col in colunas:
        vals = [row.get(col, "") for row in linhas]
        dados_por_coluna[col] = perfil_coluna(vals)

    for col in colunas:
        p = dados_por_coluna[col]
        print(f"\n  [{col}]")
        print(f"    Valores unicos : {p['unicos']:,}")
        print(f"    Vazios         : {p['vazios']:,} ({p['pct_vazio']}%)")
        print(f"    Top 5 valores  :")
        for val, cnt in p["mais_freq"]:
            print(f"      '{val}' → {cnt:,}x")

    # ── FILTRO AMAZONAS ───────────────────────────────────────────────────
    print("\n" + "-" * 70)
    print("  FILTRO: REGISTROS DO AMAZONAS (AM)")
    print("-" * 70)

    # Procura coluna de UF
    col_uf = None
    for candidato in ["uf", "UF", "sg_uf", "SG_UF", "estado", "Estado", "UF_vítima", "uf_vitima"]:
        if candidato in colunas:
            col_uf = candidato
            break

    if col_uf:
        am_linhas = [r for r in linhas if r.get(col_uf, "").strip().upper() in ["AM", "AMAZONAS"]]
        print(f"  Coluna UF encontrada : '{col_uf}'")
        print(f"  Registros do AM      : {len(am_linhas):,} de {total_linhas:,} ({round(len(am_linhas)/total_linhas*100,1)}%)")

        # Perfila municípios do AM
        col_mun = None
        for candidato in ["municipio", "Municipio", "município", "nm_municipio", "NM_MUNICIPIO", "municipio_vitima"]:
            if candidato in colunas:
                col_mun = candidato
                break
        if col_mun and am_linhas:
            top_mun = Counter(r.get(col_mun, "").strip() for r in am_linhas if r.get(col_mun, "").strip()).most_common(10)
            print(f"\n  Top 10 municipios no AM (coluna '{col_mun}'):")
            for mun, cnt in top_mun:
                print(f"    {mun:30} {cnt:,}")
    else:
        print("  Coluna de UF nao identificada automaticamente.")
        print(f"  Colunas disponiveis: {colunas}")

    # ── MAPEAMENTO DE PERGUNTAS ──────────────────────────────────────────
    print("\n" + "-" * 70)
    print("  MAPEAMENTO: QUAIS PERGUNTAS DO DASHBOARD ESSA FONTE RESPONDE?")
    print("-" * 70)

    perguntas = [
        ("Casos por ano/mes/dia?",              ["ano", "mes", "data", "dt_", "year", "month"]),
        ("Tipo de violencia?",                  ["tipo", "natureza", "violencia", "modalidade", "descricao"]),
        ("Municipio com mais casos?",           ["municipio", "cidade", "nm_mun"]),
        ("Perfil da vitima (sexo, idade)?",     ["sexo", "idade", "faixa", "raca", "cor"]),
        ("Canal de atendimento?",               ["canal", "servico", "origem", "disque", "ligue"]),
    ]

    colunas_norm = [unicodedata.normalize("NFD", c.lower())
                    .replace(" ", "_")
                    .encode("ascii", "ignore").decode() for c in colunas]

    for pergunta, palavras in perguntas:
        colunas_match = [
            colunas[i] for i, cn in enumerate(colunas_norm)
            if any(p in cn for p in palavras)
        ]
        status = "✅" if colunas_match else "❌"
        print(f"\n  {status} {pergunta}")
        if colunas_match:
            print(f"     Colunas relevantes: {colunas_match}")

    # ── COMPATIBILIDADE ──────────────────────────────────────────────────
    print("\n" + "-" * 70)
    print("  COMPATIBILIDADE COM DADOS JA EXISTENTES")
    print("-" * 70)
    print("  Chave de junção com SINAN/SUAS: municipio + UF")

    col_join = [c for c in colunas if any(p in c.lower() for p in ["municipio", "mun", "cidade"])]
    if col_join:
        print(f"  Coluna de municipio encontrada: {col_join}")
        print("  -> Podera ser cruzada com sinan_violencia_feminina_am.csv")
        print("  -> Podera ser cruzada com rede_suas_am_consolidada.csv")
    else:
        print("  Atencao: coluna de municipio nao encontrada — verificar manualmente")

    print("\n" + "=" * 70)
    print("  FIM DO MAPEAMENTO")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Tenta arquivo padrão
        padrao = os.path.join(os.path.dirname(__file__), "brutos", "ondh_amostra.csv")
        caminho = padrao
    else:
        caminho = sys.argv[1]

    mapear_fonte(caminho)
