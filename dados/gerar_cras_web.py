"""
Gera CSV com dados de CRAS do Amazonas coletados de agendamentocras.com.br (9 páginas)
"""
import csv, json, unicodedata, os

TRATADOS = os.path.join(os.path.dirname(__file__), "brutos")
JSON_MAPA = "C:/Users/ryzen/Downloads/AM_Municipios.json"


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").lower().strip()


def carregar_nomes_oficiais():
    with open(JSON_MAPA, encoding="utf-8") as f:
        data = json.load(f)
    geometries = data["objects"]["AM_Municipios_2023"]["geometries"]
    return {normalizar(g["properties"]["NM_MUN"]): g["properties"]["NM_MUN"] for g in geometries}


# Dados coletados das 9 páginas (nome, municipio_raw)
CRAS_RAW = [
    # Página 1
    ("CRAS 7 de Setembro",              "Urucurituba"),
    ("CRAS Crispim Lobo",               "Urucará"),
    ("CRAS Castelo Branco",             "Uarini"),
    ("CRAS Benjamin Constant",          "Tonantins"),
    ("CRAS Jerusalém",                  "Tefé"),
    ("CRAS Abial",                      "Tefé"),
    ("CRAS Monteiro de Souza",          "Tefé"),
    ("CRAS Central de Tapauá",          "Tapauá"),
    ("CRAS Comunidade São Francisco",   "Tabatinga"),
    ("CRAS Marechal Mallet",            "Tabatinga"),
    # Página 2
    ("CRAS Coronel José Esteves",       "Silves"),
    ("CRAS Centro",                     "São Sebastião do Uatumã"),
    ("CRAS Barão do Rio Branco",        "São Paulo de Olivença"),
    ("CRAS Dabaru",                     "São Gabriel da Cachoeira"),
    ("CRAS Álvaro Maia",                "São Gabriel da Cachoeira"),
    ("CRAS Rui Barbosa",                "Santo Antônio do Içá"),
    ("CRAS João Pessoa",                "Santa Isabel do Rio Negro"),
    ("CRAS Governador Ângelo Amaral",   "Rio Preto da Eva"),
    ("CRAS Maroaga",                    "Presidente Figueiredo"),
    ("CRAS Urubuí",                     "Presidente Figueiredo"),
    # Página 3
    ("CRAS Getúlio Vargas",             "Pauiní"),
    ("CRAS Itaúna II",                  "Parintins"),
    ("CRAS União",                      "Parintins"),
    ("CRAS Paulo Corrêa",               "Parintins"),
    ("CRAS Vila Novo Horizonte",        "Novo Aripuanã"),
    ("CRAS 16 de Fevereiro",            "Novo Aripuanã"),
    ("CRAS Antenor Carlos Frederico",   "Novo Airão"),
    ("CRAS Triunfo",                    "Nova Olinda do Norte"),
    ("CRAS Furtado Belém",              "Nhamundá"),
    ("CRAS Castelo Branco",             "Maraã"),
    # Página 4
    ("CRAS Auxiliadora",                "Manicoré"),
    ("CRAS 5 de Setembro",              "Manaquiri"),
    ("CRAS Novo Manacá",                "Manacapuru"),
    ("CRAS São José",                   "Manacapuru"),
    ("CRAS Terra Preta",                "Manacapuru"),
    ("CRAS 22 de Outubro",              "Lábrea"),
    ("CRAS Francisco de Paula",         "Juruá"),
    ("CRAS Coronel Salgado",            "Japurá"),
    ("CRAS Beira Rio",                  "Itamarati"),
    ("CRAS Mamoud Amed",                "Itacoatiara"),
    # Página 5
    ("CRAS Jauary",                     "Itacoatiara"),
    ("CRAS Benjamin Constant",          "Itacoatiara"),
    ("CRAS Rio Madeira",                "Iranduba"),
    ("CRAS Amazonas",                   "Ipixuna"),
    ("CRAS São Domingos Sávio",         "Humaitá"),
    ("CRAS 5 de Setembro",              "Humaitá"),
    ("CRAS Marechal Rondon",            "Fonte Boa"),
    ("CRAS Senador Fábio Lucena",       "Envira"),
    ("CRAS Santo Antônio",              "Eirunepé"),
    ("CRAS Getúlio Vargas",             "Eirunepé"),
    # Página 6
    ("CRAS Quintino Bocaiuva",          "Codajás"),
    ("CRAS Urucu",                      "Coari"),
    ("CRAS 5 de Setembro",              "Coari"),
    ("CRAS Solimões",                   "Careiro da Várzea"),
    ("CRAS Santa Luzia",                "Carauari"),
    ("CRAS Rui Barbosa",                "Carauari"),
    ("CRAS João Batista",               "Canutama"),
    ("CRAS Marechal Deodoro",           "Caapiranga"),
    ("CRAS Getúlio Vargas",             "Borba"),
    ("CRAS Platô do Piquiá",            "Boca do Acre"),
    # Página 7
    ("CRAS 7 de Setembro",              "Boca do Acre"),
    ("CRAS Castelo Branco",             "Boa Vista do Ramos"),
    ("CRAS Frei Ludovico",              "Benjamin Constant"),
    ("CRAS Boa Vista",                  "Barreirinha"),
    ("CRAS Tenreiro Aranha",            "Barcelos"),
    ("CRAS 1º de Maio",                 "Atalaia do Norte"),
    ("CRAS 31 de Março",                "Anori"),
    ("CRAS Raimundo Pereira",           "Anamã"),
    ("CRAS Beira Rio",                  "Amaturá"),
    ("CRAS João Paulo II",              "Alvarães"),
    # Página 8
    ("CRAS Donga Michiles",             "Maués"),
    ("CRAS Quintino Bocaiuva",          "Maués"),
    ("CRAS Getúlio Vargas",             "Autazes"),
    ("CRAS Amazonas",                   "Apuí"),
    ("CRAS Autazes",                    "Autazes"),
    ("CRAS Braga Mendes",               "Manaus"),
    ("CRAS Compensa II",                "Manaus"),
    ("CRAS Compensa I",                 "Manaus"),
    ("CRAS Prourbis",                   "Manaus"),
    ("CRAS Japiim",                     "Manaus"),
    # Página 9
    ("CRAS Crespo II",                  "Manaus"),
    ("CRAS Crespo I",                   "Manaus"),
    ("CRAS Cachoeirinha",               "Manaus"),
    ("CRAS Betânia",                    "Manaus"),
    ("CRAS Alvorada III",               "Manaus"),
    ("CRAS Alvorada I",                 "Manaus"),
    ("CRAS Alfredo Nascimento",         "Manaus"),
    ("CRAS Terra Nova",                 "Manaus"),
    ("CRAS Cidade Nova",                "Manaus"),
    ("CRAS Jorge Teixeira",             "Manaus"),
]


def gerar_csv():
    nomes_oficiais = carregar_nomes_oficiais()
    saida = os.path.join(TRATADOS, "cras_am_web.csv")
    sem_match = []

    with open(saida, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["tipo", "nome", "uf", "municipio", "fonte"])
        writer.writeheader()

        for nome, municipio_raw in CRAS_RAW:
            chave = normalizar(municipio_raw)
            if chave in nomes_oficiais:
                municipio = nomes_oficiais[chave]
            else:
                municipio = municipio_raw
                sem_match.append(municipio_raw)

            writer.writerow({
                "tipo": "CRAS",
                "nome": nome,
                "uf": "AM",
                "municipio": municipio,
                "fonte": "agendamentocras.com.br"
            })

    print(f"[OK] {len(CRAS_RAW)} CRAS gerados -> {saida}")
    if sem_match:
        print(f"[AVISO] Municipios sem match no JSON: {set(sem_match)}")
    else:
        print("[OK] Todos os municipios normalizados com sucesso.")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    gerar_csv()
