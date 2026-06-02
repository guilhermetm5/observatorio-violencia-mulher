"""
Calcula o centroide de cada município do Amazonas a partir do TopoJSON do IBGE.
Gera municipios_centroides.csv com latitude e longitude de cada município.
"""
import json, csv, os, unicodedata

JSON_MAPA = "C:/Users/ryzen/Downloads/AM_Municipios.json"
TRATADOS  = os.path.join(os.path.dirname(__file__), "tratados")


def decodificar_arco(arco, scale, translate):
    """Converte um arco TopoJSON (delta-encoded) em lista de [lon, lat]."""
    pontos = []
    x, y = 0, 0
    for dx, dy in arco:
        x += dx
        y += dy
        lon = x * scale[0] + translate[0]
        lat = y * scale[1] + translate[1]
        pontos.append((lon, lat))
    return pontos


def centroide_de_pontos(pontos):
    """Centroide simples: média de todas as coordenadas."""
    if not pontos:
        return None, None
    lons = [p[0] for p in pontos]
    lats = [p[1] for p in pontos]
    return sum(lats) / len(lats), sum(lons) / len(lons)  # retorna lat, lon


def coletar_pontos_geometria(geometria, arcos, scale, translate):
    """Coleta todos os pontos de uma geometria (Polygon ou MultiPolygon)."""
    pontos = []

    def processar_rings(rings):
        for ring in rings:
            for idx in ring:
                arco = arcos[~idx] if idx < 0 else arcos[idx]
                coords = decodificar_arco(arco, scale, translate)
                if idx < 0:
                    coords = coords[::-1]  # arco invertido
                pontos.extend(coords)

    tipo = geometria.get("type")
    if tipo == "Polygon":
        processar_rings(geometria["arcs"])
    elif tipo == "MultiPolygon":
        for poligono in geometria["arcs"]:
            processar_rings(poligono)

    return pontos


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").lower().strip()


def gerar_centroides():
    with open(JSON_MAPA, encoding="utf-8") as f:
        data = json.load(f)

    scale     = data["transform"]["scale"]
    translate = data["transform"]["translate"]
    arcos     = data["arcs"]
    geometrias = data["objects"]["AM_Municipios_2023"]["geometries"]

    resultados = []
    for geo in geometrias:
        props   = geo["properties"]
        cd_mun  = props["CD_MUN"][:6]
        nm_mun  = props["NM_MUN"]

        pontos = coletar_pontos_geometria(geo, arcos, scale, translate)
        lat, lon = centroide_de_pontos(pontos)

        if lat and lon:
            resultados.append({
                "codigo_ibge": cd_mun,
                "municipio":   nm_mun,
                "uf":          "AM",
                "latitude":    round(lat, 6),
                "longitude":   round(lon, 6)
            })

    saida = os.path.join(TRATADOS, "municipios_centroides.csv")
    with open(saida, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["codigo_ibge", "municipio", "uf", "latitude", "longitude"])
        writer.writeheader()
        writer.writerows(resultados)

    print(f"[OK] {len(resultados)} centroides gerados -> {saida}")
    # Mostra alguns exemplos
    for r in resultados[:5]:
        print(f"  {r['municipio']:30} lat={r['latitude']}  lon={r['longitude']}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    gerar_centroides()
