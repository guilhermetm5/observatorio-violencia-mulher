"""
Tratamento dos dados brutos do Observatório Violência Contra a Mulher - AM
Fontes: SINANNET (DATASUS) + SUAS (CADSUAS/MDS)
Autor: Projeto Observatório
Data: 2026-05
"""

import csv
import os
import re

BRUTOS = os.path.join(os.path.dirname(__file__), "brutos")
TRATADOS = os.path.join(os.path.dirname(__file__), "tratados")
os.makedirs(TRATADOS, exist_ok=True)


# ──────────────────────────────────────────────
# 1. SINAN — Violência Interpessoal/Autoprovocada (Amazonas, Sexo Feminino)
# ──────────────────────────────────────────────
def tratar_sinan():
    arquivo_entrada = os.path.join(BRUTOS, "sinannet_cnv_violeam222130191_189_25_82.csv")
    arquivo_saida = os.path.join(TRATADOS, "sinan_violencia_feminina_am.csv")

    dados = []

    with open(arquivo_entrada, encoding="latin-1") as f:
        linhas = f.readlines()

    # Ignora as primeiras 6 linhas de metadados e o rodapé (linhas que começam com espaço ou são vazias após os dados)
    inicio_dados = 7  # linha do cabeçalho real começa em índice 6, dados em 7
    for linha in linhas[inicio_dados:]:
        linha = linha.strip()
        if not linha or linha.startswith('"Total"') or linha.startswith(" ") or linha.startswith("*"):
            continue

        partes = linha.split(";")
        if len(partes) < 2:
            continue

        municipio_raw = partes[0].strip().strip('"')
        casos_raw = partes[1].strip().strip('"')

        # Separa código IBGE do nome do município
        match = re.match(r"^(\d{6})\s+(.+)$", municipio_raw)
        if match:
            codigo_ibge = match.group(1)
            municipio = match.group(2).strip().title()  # Ex: "ALVARAES" → "Alvaraes"
        else:
            codigo_ibge = ""
            municipio = municipio_raw.title()

        # Converte casos para inteiro (trata "-" como 0)
        try:
            casos = int(casos_raw.replace("-", "0"))
        except ValueError:
            continue

        dados.append({
            "codigo_ibge": codigo_ibge,
            "municipio": municipio,
            "uf": "AM",
            "ano": 2025,
            "casos_violencia_feminina": casos
        })

    with open(arquivo_saida, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["codigo_ibge", "municipio", "uf", "ano", "casos_violencia_feminina"])
        writer.writeheader()
        writer.writerows(dados)

    print(f"[OK] SINAN tratado: {len(dados)} municipios -> {arquivo_saida}")
    return dados


# ──────────────────────────────────────────────
# 2. SUAS — CREAS do Amazonas
# ──────────────────────────────────────────────
def tratar_suas_creas():
    arquivo_entrada = os.path.join(BRUTOS, "suas_creas_amazonas.csv")
    arquivo_saida = os.path.join(TRATADOS, "suas_creas_am.csv")

    dados = []

    with open(arquivo_entrada, encoding="latin-1") as f:
        reader = csv.reader(f)
        next(reader)  # pula cabeçalho desalinhado

        for row in reader:
            if len(row) < 5:
                continue
            # Estrutura real: [vazio, nome, identificador, uf, municipio]
            nome = row[1].strip().title() if row[1].strip() else "CREAS"
            identificador = row[2].strip()
            uf = row[3].strip()
            municipio = row[4].strip().title()

            if not municipio or municipio.lower() == "município":
                continue

            dados.append({
                "tipo": "CREAS",
                "nome": nome,
                "identificador": identificador,
                "uf": uf,
                "municipio": municipio
            })

    with open(arquivo_saida, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["tipo", "nome", "identificador", "uf", "municipio"])
        writer.writeheader()
        writer.writerows(dados)

    print(f"[OK] SUAS CREAS tratado: {len(dados)} unidades -> {arquivo_saida}")
    return dados


# ──────────────────────────────────────────────
# 3. SUAS — CRAS de Manaus
# ──────────────────────────────────────────────
def tratar_suas_cras():
    arquivo_entrada = os.path.join(BRUTOS, "suas_cras_manaus.csv")
    arquivo_saida = os.path.join(TRATADOS, "suas_cras_manaus.csv")

    dados = []

    with open(arquivo_entrada, encoding="latin-1") as f:
        reader = csv.reader(f)
        next(reader)  # pula cabeçalho

        for row in reader:
            if len(row) < 5:
                continue
            nome = row[1].strip().title() if row[1].strip() else "CRAS"
            identificador = row[2].strip()
            uf = row[3].strip()
            municipio = row[4].strip().title()

            if not municipio or municipio.lower() == "município":
                continue

            dados.append({
                "tipo": "CRAS",
                "nome": nome,
                "identificador": identificador,
                "uf": uf,
                "municipio": municipio
            })

    with open(arquivo_saida, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["tipo", "nome", "identificador", "uf", "municipio"])
        writer.writeheader()
        writer.writerows(dados)

    print(f"[OK] SUAS CRAS tratado: {len(dados)} unidades -> {arquivo_saida}")
    return dados


# ──────────────────────────────────────────────
# 4. Consolida rede SUAS (CREAS + CRAS juntos)
# ──────────────────────────────────────────────
def consolidar_rede_suas(creas, cras):
    arquivo_saida = os.path.join(TRATADOS, "rede_suas_am_consolidada.csv")
    todos = creas + cras

    with open(arquivo_saida, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["tipo", "nome", "identificador", "uf", "municipio"])
        writer.writeheader()
        writer.writerows(todos)

    print(f"[OK] Rede SUAS consolidada: {len(todos)} unidades totais -> {arquivo_saida}")


# ──────────────────────────────────────────────
# Execução
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    print("\nIniciando tratamento dos dados...\n")
    sinan = tratar_sinan()
    creas = tratar_suas_creas()
    cras = tratar_suas_cras()
    consolidar_rede_suas(creas, cras)
    print("\nTodos os arquivos tratados salvos em /dados/tratados/")
    print("Prontos para importar no Power BI.\n")
