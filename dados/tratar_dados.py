"""
Tratamento dos dados brutos do Observatório Violência Contra a Mulher - AM
Fontes: SINANNET (DATASUS) + SUAS (CADSUAS/MDS)
Autor: Projeto Observatório
Data: 2026-05
"""

import csv
import json
import os
import re

BRUTOS = os.path.join(os.path.dirname(__file__), "brutos")
TRATADOS = os.path.join(os.path.dirname(__file__), "tratados")
JSON_MAPA = "C:/Users/ryzen/Downloads/AM_Municipios.json"
os.makedirs(TRATADOS, exist_ok=True)


def carregar_nomes_oficiais():
    """Carrega os nomes oficiais dos municípios do JSON do IBGE (com acentos corretos).
    Retorna dois dicionários:
      - por código IBGE (6 dígitos)
      - por nome normalizado (sem acento, minúsculo) para cruzar com dados do SUAS
    """
    import unicodedata
    with open(JSON_MAPA, encoding="utf-8") as f:
        data = json.load(f)
    geometries = data["objects"]["AM_Municipios_2023"]["geometries"]

    por_codigo = {}
    por_nome_normalizado = {}

    for g in geometries:
        cd = g["properties"]["CD_MUN"][:6]
        nm = g["properties"]["NM_MUN"]
        # Normaliza: remove acentos, minúsculo, sem espaços extras
        nm_norm = unicodedata.normalize("NFD", nm)
        nm_norm = "".join(c for c in nm_norm if unicodedata.category(c) != "Mn").lower().strip()
        por_codigo[cd] = nm
        por_nome_normalizado[nm_norm] = nm

    return por_codigo, por_nome_normalizado


def normalizar(texto):
    """Remove acentos e converte para minúsculo para comparação."""
    import unicodedata
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").lower().strip()


# ──────────────────────────────────────────────
# 1. SINAN — Violência Interpessoal/Autoprovocada (Amazonas, Sexo Feminino)
# ──────────────────────────────────────────────
def tratar_sinan():
    arquivo_entrada = os.path.join(BRUTOS, "sinannet_cnv_violeam222130191_189_25_82.csv")
    arquivo_saida = os.path.join(TRATADOS, "sinan_violencia_feminina_am.csv")

    nomes_oficiais, _ = carregar_nomes_oficiais()
    dados = []

    with open(arquivo_entrada, encoding="latin-1") as f:
        linhas = f.readlines()

    inicio_dados = 7
    for linha in linhas[inicio_dados:]:
        linha = linha.strip()
        if not linha or linha.startswith('"Total"') or linha.startswith(" ") or linha.startswith("*"):
            continue

        partes = linha.split(";")
        if len(partes) < 2:
            continue

        municipio_raw = partes[0].strip().strip('"')
        casos_raw = partes[1].strip().strip('"')

        # Separa código IBGE do nome bruto
        match = re.match(r"^(\d{6})\s+(.+)$", municipio_raw)
        if match:
            codigo_ibge = match.group(1)
            # Usa nome oficial do JSON (com acentos corretos); fallback para nome bruto
            municipio = nomes_oficiais.get(codigo_ibge, match.group(2).strip().title())
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

    _, nomes_por_norm = carregar_nomes_oficiais()
    dados = []
    sem_match = []

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
            municipio_raw = row[4].strip().title()

            if not municipio_raw or municipio_raw.lower() == "município":
                continue

            # Corrige nome pelo JSON oficial
            municipio_norm = normalizar(municipio_raw)
            if municipio_norm in nomes_por_norm:
                municipio = nomes_por_norm[municipio_norm]
            else:
                municipio = municipio_raw
                sem_match.append(municipio_raw)

            dados.append({
                "tipo": "CREAS",
                "nome": nome,
                "identificador": identificador,
                "uf": uf,
                "municipio": municipio
            })

    if sem_match:
        print(f"  [AVISO] CREAS sem match no JSON ({len(sem_match)}): {set(sem_match)}")

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

    _, nomes_por_norm = carregar_nomes_oficiais()
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
            municipio_raw = row[4].strip().title()

            if not municipio_raw or municipio_raw.lower() == "município":
                continue

            municipio_norm = normalizar(municipio_raw)
            municipio = nomes_por_norm.get(municipio_norm, municipio_raw)

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
