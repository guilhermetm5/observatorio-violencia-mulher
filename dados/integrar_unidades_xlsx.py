"""
Integra a planilha 'Unidades de enfretamento a violencia a mulher.xlsx'
com a rede SUAS existente, gerando a base completa da rede de atendimento.

Prioridade das coordenadas:
  1. GPS exato da planilha (quando disponível)
  2. Coordenadas Nominatim/OSM dos centroides municipais (fallback)
"""
import csv, os, sys, unicodedata, openpyxl
sys.stdout.reconfigure(encoding="utf-8")

TRATADOS = os.path.join(os.path.dirname(__file__), "tratados")

XLSX      = os.path.join(TRATADOS, "Unidades de enfretamento a violencia a mulher.xlsx")
REDE_SUAS = os.path.join(TRATADOS, "rede_suas_am_consolidada.csv")
CENTROIDES = os.path.join(TRATADOS, "municipios_centroides.csv")
SAIDA     = os.path.join(TRATADOS, "rede_atendimento_am_completa.csv")

COLUNAS_SAIDA = [
    "tipo", "nome", "municipio", "uf",
    "endereco", "horario",
    "latitude", "longitude",
    "regiao", "fonte"
]

# Mapeamento de tipos para nomes padronizados e legíveis
TIPOS_PADRAO = {
    "CRAS":          "CRAS",
    "CREAS":         "CREAS",
    "DEP":           "Delegacia Especializada",
    "DECCM":         "Delegacia Especializada",
    "PROMOTORIA":    "Promotoria de Justiça",
    "SAMIC":         "SAMIC",
    "SAPEM":         "SAPEM",
    "CREAM":         "Centro de Referência (CREAM)",
    "NUDEM":         "NUDEM",
    "PROGRAMA PMAM": "Programa PMAM",
    "Programa PMAM": "Programa PMAM",
}


def normalizar(texto):
    if not texto:
        return ""
    texto = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").lower().strip()


def carregar_centroides():
    centroides = {}
    with open(CENTROIDES, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            centroides[normalizar(row["municipio"])] = (row["latitude"], row["longitude"])
    return centroides


def ler_xlsx():
    """Lê a planilha ignorando linhas completamente vazias."""
    wb  = openpyxl.load_workbook(XLSX)
    ws  = wb.active
    headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]

    unidades = []
    for r in range(2, ws.max_row + 1):
        row = {headers[c]: ws.cell(r, c + 1).value for c in range(len(headers))}
        # Ignora linhas completamente vazias
        if not any(v for v in row.values()):
            continue
        unidades.append(row)

    return unidades


def ler_rede_suas(centroides):
    """Lê a rede SUAS existente (CREAS + CRAS)."""
    unidades = []
    with open(REDE_SUAS, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            # Tenta usar coordenadas existentes; se vazias, usa centroide
            lat = row.get("latitude", "").strip()
            lon = row.get("longitude", "").strip()
            if not lat or not lon:
                lat, lon = centroides.get(normalizar(row["municipio"]), ("", ""))

            unidades.append({
                "tipo":      row["tipo"],
                "nome":      row["nome"],
                "municipio": row["municipio"],
                "uf":        "AM",
                "endereco":  "",
                "horario":   "",
                "latitude":  lat,
                "longitude": lon,
                "regiao":    "Capital" if normalizar(row["municipio"]) == "manaus" else "Interior",
                "fonte":     "CADSUAS/MDS + agendamentocras.com.br"
            })
    return unidades


def integrar():
    centroides = carregar_centroides()

    # 1. Lê planilha xlsx
    xlsx_units = ler_xlsx()
    print(f"[INFO] Planilha xlsx: {len(xlsx_units)} unidades reais")

    # 2. Lê rede SUAS existente
    suas_units = ler_rede_suas(centroides)
    print(f"[INFO] Rede SUAS existente: {len(suas_units)} unidades")

    # 3. Processa unidades da planilha
    xlsx_processadas = []
    tipos_novos = set()
    for u in xlsx_units:
        tipo_raw = str(u.get("Tipo") or "").strip()
        tipo     = TIPOS_PADRAO.get(tipo_raw, tipo_raw)
        municipio = str(u.get("Município") or "").strip().title()

        lat = str(u.get("Latitude") or "").strip()
        lon = str(u.get("Longitude") or "").strip()
        # Fallback para centroide se não tiver GPS
        if not lat or not lon:
            lat, lon = centroides.get(normalizar(municipio), ("", ""))

        if tipo not in ("CRAS", "CREAS"):
            tipos_novos.add(tipo)

        xlsx_processadas.append({
            "tipo":      tipo,
            "nome":      str(u.get("Unidade") or "").strip().title(),
            "municipio": municipio,
            "uf":        "AM",
            "endereco":  str(u.get("Endereço") or "").strip(),
            "horario":   str(u.get("Horário") or "").strip(),
            "latitude":  lat,
            "longitude": lon,
            "regiao":    str(u.get("Região") or "Interior").strip(),
            "fonte":     "Planilha unidades enfrentamento AM"
        })

    # 4. Remove CRAS/CREAS duplicados da rede SUAS
    #    (a planilha tem GPS exato; para os que ela cobre, descartamos o centroide)
    xlsx_chaves = {
        (normalizar(u["tipo"]), normalizar(u["municipio"]))
        for u in xlsx_processadas
        if u["tipo"] in ("CRAS", "CREAS")
    }

    suas_filtradas = [
        u for u in suas_units
        if (normalizar(u["tipo"]), normalizar(u["municipio"])) not in xlsx_chaves
        or u["tipo"] not in ("CRAS", "CREAS")
    ]

    # 5. Consolida tudo
    todas = xlsx_processadas + suas_filtradas

    # 6. Salva
    with open(SAIDA, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS_SAIDA)
        writer.writeheader()
        writer.writerows(todas)

    # 7. Resumo
    from collections import Counter
    tipos_count = Counter(u["tipo"] for u in todas)
    municipios  = len({u["municipio"] for u in todas})
    com_gps     = sum(1 for u in todas if u["latitude"] and u["longitude"])

    print(f"\n[OK] Rede completa: {len(todas)} unidades / {municipios} municípios -> {SAIDA}")
    print(f"     Com GPS exato ou OSM: {com_gps} ({round(com_gps/len(todas)*100)}%)")
    print(f"\n  Tipos novos adicionados: {sorted(tipos_novos)}")
    print(f"\n  Unidades por tipo:")
    for tipo, qtd in sorted(tipos_count.items(), key=lambda x: -x[1]):
        print(f"    {tipo:<35} {qtd:>4}")


if __name__ == "__main__":
    print("\nIntegrando planilha xlsx com rede SUAS...\n")
    integrar()
    print("\nConcluido.\n")
