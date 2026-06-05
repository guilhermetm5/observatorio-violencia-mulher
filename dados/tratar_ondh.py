"""
Tratamento dos dados do Disque 100 (ONDH) — Observatório Violência Contra a Mulher
Filtra registros do Amazonas + violência contra a mulher
Normaliza colunas entre semestres e gera base consolidada para o Power BI
"""
import csv, os, glob, sys, re
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

BRUTOS  = os.path.join(os.path.dirname(__file__), "brutos")
TRATADOS = os.path.join(os.path.dirname(__file__), "tratados")

# Colunas que variam de nome entre semestres — mapeamento para nome padrão
MAPA_COLUNAS = {
    "Gênero_da_vítima":    "genero_vitima",
    "Genero_da_vítima":    "genero_vitima",
    "Sexo_da_vítima":      "genero_vitima",
    "Gênero_do_suspeito":  "genero_suspeito",
    "Genero_do_suspeito":  "genero_suspeito",
    "Sexo_do_suspeito":    "genero_suspeito",
    "Grupo_vulnerável":    "grupo_vulneravel",
    "(Nenhum nome de coluna)": None,  # ignorar
}

# Colunas 100% nulas (confirmado no perfilamento) — descartar
COLUNAS_IGNORAR = {
    "sl_vitima_naturalidade",
    "sl_vitima_naturalizado_uf",
    "sl_vitima_naturalizado_municipio",
    "sl_suspeito_naturalidade",
    "sl_suspeito_naturalizado_uf",
    "sl_suspeito_naturalizado_municipio",
    "Deficiência_relacionada_a_doença_rara",
    "Deficiência_relacionada_a_doença_rara_suspeito",
    "Grau_de_instrução_do_suspeito",
    "Faixa_de_renda_do_suspeito",
    "Vínculo_Órgão_PJ_do_suspeito",
    "(Nenhum nome de coluna)",
}

# Colunas finais desejadas no output
COLUNAS_SAIDA = [
    "arquivo_origem", "ano", "mes", "semestre",
    "canal_atendimento", "denuncia_emergencial", "denunciante",
    "cenario_violacao", "frequencia", "inicio_violacoes",
    "uf", "codigo_ibge", "municipio",
    "grupo_vulneravel", "genero_vitima", "faixa_etaria_vitima",
    "raca_cor_vitima", "relacao_vitima_suspeito",
    "violacao", "violacao_nivel1", "violacao_nivel2", "violacao_nivel3",
    "quantidade_vitimas",
]


def normalizar_col(nome):
    """Aplica o mapeamento de nomes de colunas."""
    return MAPA_COLUNAS.get(nome, nome)


def extrair_data(valor):
    """Extrai ano, mês de Data_de_cadastro (formato: 2026-03-11 13:47:53.810)."""
    try:
        dt = datetime.strptime(valor[:10], "%Y-%m-%d")
        return str(dt.year), str(dt.month).zfill(2)
    except Exception:
        return "", ""


def extrair_municipio(valor):
    """
    Extrai código IBGE e nome do município.
    Entrada: '1302603 | MANAUS'
    Saída: ('130260', 'Manaus')
    """
    match = re.match(r"^(\d+)\s*\|\s*(.+)$", valor.strip())
    if match:
        codigo = match.group(1)[:6]  # 6 dígitos
        nome   = match.group(2).strip().title()
        return codigo, nome
    return "", valor.strip().title()


def extrair_violacao(valor):
    """
    Separa a hierarquia de violação em níveis.
    Entrada: 'INTEGRIDADE>FÍSICA>MAUS TRATOS'
    Saída: ('INTEGRIDADE', 'FÍSICA', 'MAUS TRATOS')
    """
    partes = [p.strip() for p in valor.split(">")]
    while len(partes) < 3:
        partes.append("")
    return partes[0], partes[1], partes[2]


def eh_violencia_mulher(row, col_grupo, col_genero):
    """Verifica se o registro é de violência contra a mulher."""
    grupo  = row.get(col_grupo, "").upper()
    genero = row.get(col_genero, "").upper()

    if "MULHER" in grupo:
        return True
    if "FEMININO" in genero:
        return True
    return False


def tratar_arquivo(caminho):
    """Processa um arquivo do Disque 100 e retorna registros do AM filtrados."""
    nome_arquivo = os.path.basename(caminho)
    # Extrai semestre do nome (ex: "disque100-primeiro-semestre-2023.csv")
    sem_match = re.search(r"(primeiro|segundo)-semestre-(\d{4})", nome_arquivo)
    semestre_txt = sem_match.group(1) if sem_match else ""
    ano_arquivo  = sem_match.group(2) if sem_match else ""
    semestre_num = "1" if semestre_txt == "primeiro" else "2"

    registros = []
    total     = 0
    am_total  = 0

    with open(caminho, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        colunas_orig = reader.fieldnames or []

        # Identifica nomes normalizados das colunas variáveis
        col_grupo  = next((c for c in colunas_orig if normalizar_col(c) == "grupo_vulneravel"), None)
        col_genero = next((c for c in colunas_orig if normalizar_col(c) == "genero_vitima"), None)

        for row in reader:
            total += 1

            # Filtro 1: apenas Amazonas
            if row.get("UF", "").strip().upper() != "AM":
                continue
            am_total += 1

            # Filtro 2: violência contra a mulher
            if not eh_violencia_mulher(row, col_grupo or "", col_genero or ""):
                continue

            ano, mes = extrair_data(row.get("Data_de_cadastro", ""))
            codigo_ibge, municipio = extrair_municipio(row.get("Município", ""))
            violacao_raw = row.get("violacao", "")
            n1, n2, n3 = extrair_violacao(violacao_raw)

            registros.append({
                "arquivo_origem":        nome_arquivo,
                "ano":                   ano or ano_arquivo,
                "mes":                   mes,
                "semestre":              semestre_num,
                "canal_atendimento":     row.get("Canal_de_atendimento", "").strip(),
                "denuncia_emergencial":  row.get("Denúncia_emergencial", "").strip(),
                "denunciante":           row.get("Denunciante", "").strip(),
                "cenario_violacao":      row.get("Cenário_da_violação", "").strip(),
                "frequencia":            row.get("Frequência", "").strip(),
                "inicio_violacoes":      row.get("Início_das_violações", "").strip(),
                "uf":                    "AM",
                "codigo_ibge":           codigo_ibge,
                "municipio":             municipio,
                "grupo_vulneravel":      row.get(col_grupo, "").strip() if col_grupo else "",
                "genero_vitima":         row.get(col_genero, "").strip() if col_genero else "",
                "faixa_etaria_vitima":   row.get("Faixa_etária_da_vítima", "").strip(),
                "raca_cor_vitima":       row.get("Raça_Cor_da_vítima", "").strip(),
                "relacao_vitima_suspeito": row.get("Relação_vítima_suspeito", "").strip(),
                "violacao":              violacao_raw.strip(),
                "violacao_nivel1":       n1,
                "violacao_nivel2":       n2,
                "violacao_nivel3":       n3,
                "quantidade_vitimas":    row.get("sl_quantidade_vitimas", "").strip(),
            })

    return registros, total, am_total


def tratar_ondh():
    arquivos = sorted(glob.glob(os.path.join(BRUTOS, "disque100*.csv")))
    if not arquivos:
        print("[ERRO] Nenhum arquivo disque100*.csv encontrado em brutos/")
        return

    todos  = []
    resumo = []

    for arq in arquivos:
        nome = os.path.basename(arq)
        print(f"  Processando {nome}...", end=" ", flush=True)
        regs, total, am = tratar_arquivo(arq)
        todos.extend(regs)
        resumo.append((nome, total, am, len(regs)))
        print(f"{len(regs):,} registros (AM mulher) de {total:,} total")

    # Salva consolidado
    saida = os.path.join(TRATADOS, "ondh_violencia_mulher_am.csv")
    with open(saida, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS_SAIDA)
        writer.writeheader()
        writer.writerows(todos)

    print(f"\n[OK] {len(todos):,} registros consolidados -> {saida}")

    # Resumo por arquivo
    print("\n  Resumo por semestre:")
    print(f"  {'Arquivo':<45} {'Total':>10} {'AM':>8} {'Mulher':>8}")
    print("  " + "-" * 75)
    for nome, total, am, mulher in resumo:
        print(f"  {nome:<45} {total:>10,} {am:>8,} {mulher:>8,}")


if __name__ == "__main__":
    print("\nIniciando tratamento ONDH/Disque 100...\n")
    tratar_ondh()
    print("\nConcluido. Arquivo pronto para o Power BI.\n")
