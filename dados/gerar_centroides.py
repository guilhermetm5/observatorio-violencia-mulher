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


def centroide_poligono(anel):
    """
    Centroide geométrico ponderado pela área (fórmula de Shoelace).
    Muito mais preciso que a média de vértices para polígonos irregulares
    como os municípios do Amazonas (fronteiras cheias de curvas de rios).
    Recebe lista de (lon, lat). Retorna (lat, lon).
    """
    n = len(anel)
    if n < 3:
        return None, None

    area = 0.0
    cx = 0.0
    cy = 0.0

    for i in range(n):
        x0, y0 = anel[i]
        x1, y1 = anel[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx   += (x0 + x1) * cross
        cy   += (y0 + y1) * cross

    area *= 0.5
    if abs(area) < 1e-12:
        # Fallback para média simples se área for degenerada
        lons = [p[0] for p in anel]
        lats = [p[1] for p in anel]
        return sum(lats) / len(lats), sum(lons) / len(lons)

    cx /= (6.0 * area)
    cy /= (6.0 * area)
    return cy, cx  # retorna lat, lon


def coletar_aneis_geometria(geometria, arcos, scale, translate):
    """Coleta os anéis exteriores de uma geometria (Polygon ou MultiPolygon).
    Retorna lista de anéis, cada um sendo lista de (lon, lat)."""
    aneis = []

    def reconstruir_anel(ring_indices):
        anel = []
        for idx in ring_indices:
            arco = arcos[~idx] if idx < 0 else arcos[idx]
            pts  = decodificar_arco(arco, scale, translate)
            if idx < 0:
                pts = pts[::-1]
            anel.extend(pts)
        return anel

    tipo = geometria.get("type")
    if tipo == "Polygon":
        # Apenas o anel exterior (índice 0)
        aneis.append(reconstruir_anel(geometria["arcs"][0]))
    elif tipo == "MultiPolygon":
        for poligono in geometria["arcs"]:
            aneis.append(reconstruir_anel(poligono[0]))

    return aneis


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

        aneis = coletar_aneis_geometria(geo, arcos, scale, translate)

        # Para MultiPolygon: usa o anel com maior área como representante
        melhor_lat, melhor_lon, maior_area = None, None, 0.0
        for anel in aneis:
            lat, lon = centroide_poligono(anel)
            # Calcula área aproximada para escolher o maior polígono
            area = abs(sum(
                anel[i][0] * anel[(i+1) % len(anel)][1] -
                anel[(i+1) % len(anel)][0] * anel[i][1]
                for i in range(len(anel))
            ) * 0.5)
            if lat is not None and area > maior_area:
                melhor_lat, melhor_lon, maior_area = lat, lon, area

        lat, lon = melhor_lat, melhor_lon

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
