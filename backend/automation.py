from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
import os
import re
import xml.etree.ElementTree as ET

import httpx
from pathlib import Path
import json
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import unicodedata
from typing import Iterable, Tuple
import hashlib

from models import DadosExtraidos
from state import ConsultaState
from pdf_generator import generate_pdf
from state import store


@dataclass
class AutomationSettings:
    geosampa_wfs_url: str = "https://wfs.geosampa.prefeitura.sp.gov.br/geoserver/geoportal/wfs"
    geosampa_zone_layer: str = "geoportal:zoneamento_2016_map1"
    geosampa_zone_geom_field: str = "ge_poligono"
    geosampa_lote_layer: str = "geoportal:lote_cidadao"
    geosampa_lote_geom_field: str = "ge_poligono"
    geosampa_lote_field_setor: str = "cd_setor_fiscal"
    geosampa_lote_field_quadra: str = "cd_quadra_fiscal"
    geosampa_lote_field_lote: str = "cd_lote"
    geosampa_lote_field_digito: str = "cd_digito_sql"
    geosampa_field_zona_sigla: str = "txt_sigla"
    geosampa_field_zona_nome: str = "tx_zoneamento_perimetro"
    geosampa_field_legisla: str = ""
    geosampa_field_legisla_tipo: str = "cd_tipo_legislacao_zoneamento"
    geosampa_field_legisla_numero: str = "cd_numero_legislacao_zoneamento"
    geosampa_field_legisla_ano: str = "an_legislacao_zoneamento"
    geosampa_field_coef: str = ""
    geosampa_field_recuo: str = ""
    geosampa_field_gabarito: str = ""
    geosampa_field_taxa: str = ""
    geosampa_field_obs: str = "tx_observacao_perimetro"
    geosampa_field_area: str = "qt_area_terreno"
    geosampa_field_logradouro: str = "nm_logradouro_completo"
    geosampa_field_numero: str = "cd_numero_porta"
    geosampa_field_bairro: str = ""
    geosampa_field_subprefeitura: str = ""
    geosampa_subpref_layer: str = "geoportal:subprefeitura"
    geosampa_subpref_geom: str = "ge_poligono"
    geosampa_subpref_field_nome: str = "nm_subprefeitura"
    geosampa_distrito_layer: str = "geoportal:distrito_municipal"
    geosampa_distrito_geom: str = "ge_poligono"
    geosampa_distrito_field_nome: str = "nm_distrito_municipal"
    geosampa_macro_layer: str = "geoportal:pde_macroarea_lei_18209"
    geosampa_macro_geom: str = "ge_poligono"
    geosampa_macro_field_nome: str = "nm_macroarea"
    geosampa_logradouro_layer: str = "geoportal:segmento_logradouro"
    geosampa_logradouro_geom: str = "ge_linha"
    geosampa_logradouro_field_nome: str = "nm_logradouro"
    map_zoom_out_factor: float = 2.6
    map_zoom_out_steps: int = 3
    map_zoom_out_wheel_steps: int = 2
    map_zoom_out_wheel_delta: int = 480
    geosampa_layer_panel_selector: str = "button:has-text('Camadas'), button:has-text('Layers')"
    geosampa_layer_logradouro_text: str = "Logradouro"
    geosampa_layer_zoneamento_text: str = "Zoneamento"
    geosampa_patrimonio_layer: str = ""
    geosampa_patrimonio_geom: str = ""
    geosampa_patrimonio_label: str = ""
    geosampa_manancial_layer: str = ""
    geosampa_manancial_geom: str = ""
    geosampa_manancial_label: str = ""
    geosampa_aero_layer: str = ""
    geosampa_aero_geom: str = ""
    geosampa_aero_label: str = ""
    geosampa_melhoramento_layer: str = ""
    geosampa_melhoramento_geom: str = ""
    geosampa_melhoramento_label: str = ""
    captcha_selector: str = "img[src*='captcha'], img[alt*='Captcha'], img[alt*='captcha']"
    captcha_input_selector: str = "input[type='text'], input[type='tel'], input[name*='captcha']"
    captcha_submit_selector: str = "button[type='submit'], button:has-text('Enviar')"


_WFS_LAYER_CACHE: dict[str, list[str]] = {}
_WFS_GEOM_CACHE: dict[str, str] = {}


def parse_iptu(iptu: str) -> dict:
    digits = "".join(ch for ch in iptu if ch.isdigit())
    if len(digits) < 11:
        return {"iptu": iptu, "setor": "", "quadra": "", "lote": "", "digito": ""}
    setor = digits[:3]
    quadra = digits[3:6]
    lote = digits[6:10]
    digito = digits[10:11]
    return {
        "iptu": iptu,
        "setor": setor,
        "quadra": quadra,
        "lote": lote,
        "digito": digito,
    }


def load_zone_map() -> dict:
    path = Path(__file__).resolve().parent / "data" / "zoneamento_siglas.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {str(k).strip().upper(): v for k, v in data.items()}
    except Exception:
        return {}


def load_param_map() -> dict:
    path = Path(__file__).resolve().parent / "data" / "zoneamento_parametros.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def normalize_key(value: str | None) -> str:
    if not value:
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return " ".join(text.split())


def load_distrito_subpref_map() -> dict:
    path = Path(__file__).resolve().parent / "data" / "distritos_subprefeituras.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    mapping: dict[str, dict[str, str]] = {}
    for item in data:
        distrito = normalize_key(item.get("distrito"))
        if not distrito:
            continue
        mapping[distrito] = {
            "distrito": item.get("distrito", ""),
            "subprefeitura": item.get("subprefeitura", ""),
            "regiao": item.get("regiao", ""),
        }
    return mapping


def fill(value: str, fallback: str) -> str:
    return value if value else fallback


async def wfs_get_json(client: httpx.AsyncClient, base_url: str, params: dict, tries: int = 3) -> dict:
    last_exc: Exception | None = None
    for attempt in range(tries):
        try:
            resp = await client.get(base_url, params=params)
            resp.raise_for_status()
            return resp.json()
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError) as exc:
            last_exc = exc
            await asyncio.sleep(1.5 * (attempt + 1))
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"GeoSampa retornou erro HTTP {exc.response.status_code}") from exc
    raise RuntimeError("Timeout ao consultar GeoSampa") from last_exc


def normalize_value(value: str | None) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text in {"-", "—", "–", "NA", "N/A", "na", "n/a"}:
        return ""
    return text


async def fetch_wfs_layers(client: httpx.AsyncClient, base_url: str) -> list[str]:
    cached = _WFS_LAYER_CACHE.get(base_url)
    if cached is not None:
        return cached
    resp = await client.get(
        base_url,
        params={
            "service": "WFS",
            "request": "GetCapabilities",
        },
    )
    resp.raise_for_status()
    text = resp.text
    names = re.findall(r"<Name>([^<]+)</Name>", text)
    layers = sorted({n for n in names if ":" in n})
    _WFS_LAYER_CACHE[base_url] = layers
    return layers


async def fetch_geom_field(client: httpx.AsyncClient, base_url: str, layer: str) -> str:
    cached = _WFS_GEOM_CACHE.get(layer)
    if cached is not None:
        return cached
    resp = await client.get(
        base_url,
        params={
            "service": "WFS",
            "version": "2.0.0",
            "request": "DescribeFeatureType",
            "typeName": layer,
        },
    )
    resp.raise_for_status()
    text = resp.text
    geom_name = ""
    try:
        root = ET.fromstring(text)
        for elem in root.iter():
            tag = elem.tag.lower()
            if not tag.endswith("element"):
                continue
            name = elem.attrib.get("name", "")
            field_type = elem.attrib.get("type", "")
            if "gml" in field_type.lower() and name:
                geom_name = name
                break
    except ET.ParseError:
        geom_name = ""

    if not geom_name:
        for candidate in ("ge_poligono", "the_geom", "geom", "geometria", "shape"):
            if candidate in text:
                geom_name = candidate
                break

    _WFS_GEOM_CACHE[layer] = geom_name
    return geom_name


def pick_layer(layers: list[str], keywords: list[str]) -> str:
    if not layers:
        return ""
    layers_lower = [(layer, layer.lower()) for layer in layers]
    for keyword in keywords:
        for layer, layer_lower in layers_lower:
            if keyword in layer_lower:
                return layer
    return ""


async def resolve_restriction(
    client: httpx.AsyncClient,
    base_url: str,
    wkt: str,
    category_name: str,
    keywords: list[str],
    explicit_layer: str,
    explicit_geom: str,
    explicit_label: str,
) -> str:
    try:
        layer = explicit_layer
        if not layer:
            layers = await fetch_wfs_layers(client, base_url)
            layer = pick_layer(layers, keywords)

        if not layer:
            return "Nao identificado (camada indisponivel)"

        geom_field = explicit_geom or await fetch_geom_field(client, base_url, layer)
        if not geom_field:
            return "Nao identificado (geometria indisponivel)"

        cql = f"INTERSECTS({geom_field}, SRID=31983;{wkt})"
        payload = await wfs_get_json(
            client,
            base_url,
            {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeName": layer,
                "outputFormat": "application/json",
                "cql_filter": cql,
                "count": 1,
            },
        )
        feats = payload.get("features") or []
        if not feats:
            return "Sem restricoes identificadas nesta data"

        label = ""
        if explicit_label:
            props = feats[0].get("properties") or {}
            label = str(props.get(explicit_label, "")) if explicit_label else ""

        if label:
            return f"Restricao identificada: {label}"
        return f"Restricao identificada ({category_name})"
    except Exception:
        return "Nao identificado (erro ao consultar GeoSampa)"


async def fetch_first_field(
    client: httpx.AsyncClient,
    base_url: str,
    layer: str,
    geom_field: str,
    wkt: str,
    field: str,
) -> str:
    if not layer or not field:
        return ""
    cql = f"INTERSECTS({geom_field}, SRID=31983;{wkt})"
    payload = await wfs_get_json(
        client,
        base_url,
        {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": layer,
            "outputFormat": "application/json",
            "cql_filter": cql,
            "count": 1,
        },
    )
    feats = payload.get("features") or []
    if not feats:
        return ""
    props = feats[0].get("properties") or {}
    return str(props.get(field, "")) if field else ""


async def geocode_address(client: httpx.AsyncClient, endereco: str) -> tuple[str, str]:
    if not endereco:
        return "", ""
    try:
        resp = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": f"{endereco}, Sao Paulo, Brasil",
                "format": "json",
                "addressdetails": 1,
                "limit": 1,
            },
            headers={
                "User-Agent": "UrbanFlow/1.0 (geosampa local tool)",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return "", ""
        address = data[0].get("address") or {}
        bairro = address.get("suburb") or address.get("neighbourhood") or address.get("quarter") or ""
        subprefeitura = address.get("city_district") or address.get("district") or ""
        return str(bairro), str(subprefeitura)
    except Exception:
        return "", ""


def polygon_to_wkt(geometry: dict) -> str:
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates") or []

    def ring_to_text(ring):
        return ", ".join(f"{pt[0]} {pt[1]}" for pt in ring)

    if geom_type == "Polygon":
        rings = []
        for ring in coords:
            rings.append(f"({ring_to_text(ring)})")
        return f"POLYGON({', '.join(rings)})"
    if geom_type == "MultiPolygon":
        polys = []
        for poly in coords:
            rings = []
            for ring in poly:
                rings.append(f"({ring_to_text(ring)})")
            polys.append(f"({', '.join(rings)})")
        return f"MULTIPOLYGON({', '.join(polys)})"
    raise ValueError(f"Geometria nao suportada: {geom_type}")


def geometry_bbox(geometry: dict) -> tuple[float, float, float, float]:
    coords = geometry.get("coordinates") or []

    def all_points():
        geom_type = geometry.get("type")
        if geom_type == "Polygon":
            for ring in coords:
                for pt in ring:
                    yield pt
        elif geom_type == "MultiPolygon":
            for poly in coords:
                for ring in poly:
                    for pt in ring:
                        yield pt
        else:
            return

    xs, ys = [], []
    for x, y in all_points():
        xs.append(x)
        ys.append(y)
    if not xs or not ys:
        raise ValueError("BBox vazio")
    return min(xs), min(ys), max(xs), max(ys)


def expand_bbox(bbox: tuple[float, float, float, float], factor: float) -> tuple[float, float, float, float]:
    if factor <= 1.0:
        return bbox
    minx, miny, maxx, maxy = bbox
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0
    half_w = (maxx - minx) / 2.0 * factor
    half_h = (maxy - miny) / 2.0 * factor
    return (cx - half_w, cy - half_h, cx + half_w, cy + half_h)


def _zone_color(sigla: str) -> tuple[int, int, int, int]:
    if sigla == "ZM":
        return (245, 158, 11, 120)  # orange for Zona Mista
    palette = [
        "#10B981", "#22D3EE", "#F59E0B", "#EF4444", "#8B5CF6",
        "#14B8A6", "#A3E635", "#F472B6", "#60A5FA", "#F97316",
    ]
    if not sigla:
        return (255, 255, 255, 0)
    h = hashlib.md5(sigla.encode("utf-8")).hexdigest()
    idx = int(h[:8], 16) % len(palette)
    hex_color = palette[idx].lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, 90)


def polygon_rings(geometry: dict) -> Iterable[list[tuple[float, float]]]:
    coords = geometry.get("coordinates") or []
    geom_type = geometry.get("type")
    if geom_type == "Polygon":
        if coords:
            ring = [(pt[0], pt[1]) for pt in coords[0]]
            if len(ring) > 2 and ring[0] == ring[-1]:
                ring = ring[:-1]
            yield ring
    elif geom_type == "MultiPolygon":
        for poly in coords:
            if poly:
                ring = [(pt[0], pt[1]) for pt in poly[0]]
                if len(ring) > 2 and ring[0] == ring[-1]:
                    ring = ring[:-1]
                yield ring


def line_strings(geometry: dict) -> Iterable[list[tuple[float, float]]]:
    coords = geometry.get("coordinates") or []
    geom_type = geometry.get("type")
    if geom_type == "LineString":
        yield [(pt[0], pt[1]) for pt in coords]
    elif geom_type == "MultiLineString":
        for line in coords:
            yield [(pt[0], pt[1]) for pt in line]


def point_segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    # Distance from point P to segment AB in projected CRS (meters)
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    c1 = vx * wx + vy * wy
    if c1 <= 0:
        dx, dy = px - ax, py - ay
        return (dx * dx + dy * dy) ** 0.5
    c2 = vx * vx + vy * vy
    if c2 <= c1:
        dx, dy = px - bx, py - by
        return (dx * dx + dy * dy) ** 0.5
    t = c1 / c2
    projx, projy = ax + t * vx, ay + t * vy
    dx, dy = px - projx, py - projy
    return (dx * dx + dy * dy) ** 0.5


def polyline_distance_to_point(lines: list[list[tuple[float, float]]], px: float, py: float) -> float:
    best = float("inf")
    for line in lines:
        for i in range(len(line) - 1):
            ax, ay = line[i]
            bx, by = line[i + 1]
            d = point_segment_distance(px, py, ax, ay, bx, by)
            if d < best:
                best = d
    return best


def edge_midpoints(ring: list[tuple[float, float]]) -> list[tuple[tuple[float, float], tuple[float, float], tuple[float, float]]]:
    edges = []
    for i in range(len(ring) - 1):
        ax, ay = ring[i]
        bx, by = ring[i + 1]
        mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
        edges.append(((ax, ay), (bx, by), (mx, my)))
    return edges


def edge_length(a: tuple[float, float], b: tuple[float, float]) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    return (dx * dx + dy * dy) ** 0.5


async def fetch_features_bbox(
    client: httpx.AsyncClient,
    base_url: str,
    layer: str,
    geom_field: str,
    bbox: tuple[float, float, float, float],
    count: int | None = None,
) -> list[dict]:
    minx, miny, maxx, maxy = bbox
    cql = f"BBOX({geom_field},{minx},{miny},{maxx},{maxy},'EPSG:31983')"
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeName": layer,
        "outputFormat": "application/json",
        "cql_filter": cql,
    }
    if count:
        params["count"] = count
    payload = await wfs_get_json(client, base_url, params, tries=2)
    return payload.get("features") or []


async def render_map_from_wfs(
    settings: AutomationSettings,
    bbox: tuple[float, float, float, float],
    lote_geom: dict,
    output_path: Path,
) -> tuple[str, tuple[float, float, float, float], list[str], list[str]]:
    from PIL import Image, ImageDraw, ImageFont

    expanded = expand_bbox(bbox, settings.map_zoom_out_factor)
    minx, miny, maxx, maxy = expanded

    width, height = 900, 600
    img = Image.new("RGBA", (width, height), (11, 18, 16, 255))
    draw = ImageDraw.Draw(img)

    def to_px(x: float, y: float) -> tuple[int, int]:
        px = int((x - minx) / (maxx - minx) * width)
        py = int((maxy - y) / (maxy - miny) * height)
        return px, py

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=60.0, connect=20.0)) as client:
        zone_features = await fetch_features_bbox(
            client,
            settings.geosampa_wfs_url,
            settings.geosampa_zone_layer,
            settings.geosampa_zone_geom_field,
            expanded,
        )
        lote_features = await fetch_features_bbox(
            client,
            settings.geosampa_wfs_url,
            settings.geosampa_lote_layer,
            settings.geosampa_lote_geom_field,
            expanded,
            count=200,
        )
        lograd_features = await fetch_features_bbox(
            client,
            settings.geosampa_wfs_url,
            settings.geosampa_logradouro_layer,
            settings.geosampa_logradouro_geom,
            expanded,
        )
    lograd_lines = []
    for feat in lograd_features:
        geom = feat.get("geometry") or {}
        for line in line_strings(geom):
            if len(line) >= 2:
                lograd_lines.append(line)

    # Draw zones with semi-transparent fill + subtle hatch
    hatch = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    hatch_draw = ImageDraw.Draw(hatch)
    spacing = 16
    for x in range(-height, width, spacing):
        hatch_draw.line((x, 0, x + height, height), fill=(255, 255, 255, 25), width=1)

    legend_entries: list[str] = []
    zone_map = load_zone_map()
    seen = set()

    for feat in zone_features:
        geom = feat.get("geometry") or {}
        props = feat.get("properties") or {}
        sigla = str(props.get(settings.geosampa_field_zona_sigla, "")).strip().upper()
        if sigla and sigla not in seen:
            seen.add(sigla)
            nome = zone_map.get(sigla, "")
            if nome:
                legend_entries.append(f"{sigla} = {nome}")
            else:
                legend_entries.append(sigla)
        color = _zone_color(sigla)
        for ring in polygon_rings(geom):
            pts = [to_px(x, y) for x, y in ring]
            if len(pts) < 3:
                continue
            draw.polygon(pts, fill=color, outline=(255, 255, 255, 70))
            mask = Image.new("L", (width, height), 0)
            ImageDraw.Draw(mask).polygon(pts, fill=255)
            img.paste(hatch, (0, 0), mask)

    # Draw street lines
    for feat in lograd_features:
        geom = feat.get("geometry") or {}
        for line in line_strings(geom):
            pts = [to_px(x, y) for x, y in line]
            if len(pts) < 2:
                continue
            draw.line(pts, fill=(200, 200, 200, 200), width=1)

    # Draw neighboring lots for context
    for feat in lote_features:
        geom = feat.get("geometry") or {}
        if geom == lote_geom:
            continue
        for ring in polygon_rings(geom):
            pts = [to_px(x, y) for x, y in ring]
            if len(pts) >= 3:
                draw.polygon(pts, outline=(120, 120, 120, 140))

    # Draw lot outline and compute dimensions
    dimensoes = []
    lot_edges = []
    for ring in polygon_rings(lote_geom):
        pts = [to_px(x, y) for x, y in ring]
        if len(pts) >= 3:
            draw.polygon(pts, outline=(16, 185, 129, 220), fill=(16, 185, 129, 40))
        # collect edges from ring in map coordinates
        for a, b, m in edge_midpoints(ring):
            if edge_length(a, b) > 1.0:
                lot_edges.append((a, b, m))

    # classify edges by distance to logradouro (front = closest)
    edge_infos = []
    for a, b, m in lot_edges:
        length = edge_length(a, b)
        dist = polyline_distance_to_point(lograd_lines, m[0], m[1]) if lograd_lines else float("inf")
        edge_infos.append({"a": a, "b": b, "m": m, "length": length, "dist": dist})
    edge_infos.sort(key=lambda e: e["dist"])
    front_edges = edge_infos[:1] if edge_infos else []
    remaining = edge_infos[1:] if len(edge_infos) > 1 else []
    back_edges = []
    if remaining:
        back_edges = [max(remaining, key=lambda e: e["dist"])]
        remaining = [e for e in remaining if e is not back_edges[0]]
    # pick two longest for laterals
    side_edges = sorted(remaining, key=lambda e: e["length"], reverse=True)[:2]

    def label_edge(edge, label):
        mx, my = edge["m"]
        px, py = to_px(mx, my)
        text = f"{label}: {edge['length']:.1f} m"
        # small background for legibility
        tw = 70
        th = 12
        draw.rectangle((px - tw // 2, py - th // 2, px + tw // 2, py + th // 2), fill=(0, 0, 0, 130))
        draw.text((px - tw // 2 + 3, py - th // 2 + 1), text, fill=(255, 255, 255, 230))

    for e in front_edges:
        label_edge(e, "Frente")
        dimensoes.append(f"Frente: {e['length']:.1f} m")
    for e in back_edges:
        label_edge(e, "Fundos")
        dimensoes.append(f"Fundos: {e['length']:.1f} m")
    for idx, e in enumerate(side_edges[:2], 1):
        label_edge(e, f"Lateral {idx}")
        dimensoes.append(f"Lateral {idx}: {e['length']:.1f} m")

    # Street labels
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except Exception:
        font = ImageFont.load_default()

    for feat in lograd_features:
        geom = feat.get("geometry") or {}
        props = feat.get("properties") or {}
        name = str(props.get(settings.geosampa_logradouro_field_nome, "")).strip()
        if not name:
            continue
        center = line_centroid(geom)
        if not center:
            continue
        px, py = to_px(center[0], center[1])
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            draw.text((px + ox, py + oy), name, font=font, fill=(0, 0, 0, 200))
        draw.text((px, py), name, font=font, fill=(255, 255, 255, 230))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return str(output_path), expanded, legend_entries, dimensoes


def iter_lines(geometry: dict) -> Iterable[Tuple[float, float]]:
    coords = geometry.get("coordinates") or []
    geom_type = geometry.get("type")
    if geom_type == "LineString":
        for pt in coords:
            yield pt
    elif geom_type == "MultiLineString":
        for line in coords:
            for pt in line:
                yield pt


def line_centroid(geometry: dict) -> tuple[float, float] | None:
    pts = list(iter_lines(geometry))
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


async def overlay_logradouros(
    settings: AutomationSettings,
    image_path: Path,
    bbox: tuple[float, float, float, float],
) -> None:
    if not image_path.exists():
        return
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return

    minx, miny, maxx, maxy = bbox
    bbox_filter = f"BBOX({settings.geosampa_logradouro_geom},{minx},{miny},{maxx},{maxy},'EPSG:31983')"

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=60.0, connect=20.0)) as client:
        payload = await wfs_get_json(
            client,
            settings.geosampa_wfs_url,
            {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeName": settings.geosampa_logradouro_layer,
                "outputFormat": "application/json",
                "cql_filter": bbox_filter,
            },
            tries=2,
        )

    features = payload.get("features") or []
    if not features:
        return

    img = Image.open(image_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except Exception:
        font = ImageFont.load_default()

    width, height = img.size
    def to_px(x: float, y: float) -> tuple[int, int]:
        px = int((x - minx) / (maxx - minx) * width)
        py = int((maxy - y) / (maxy - miny) * height)
        return px, py

    for feat in features:
        geom = feat.get("geometry") or {}
        props = feat.get("properties") or {}
        name = str(props.get(settings.geosampa_logradouro_field_nome, "")).strip()
        if not name:
            continue
        center = line_centroid(geom)
        if not center:
            continue
        px, py = to_px(center[0], center[1])
        # Outline for legibility
        for ox, oy in ((-1,0),(1,0),(0,-1),(0,1)):
            draw.text((px+ox, py+oy), name, font=font, fill=(0,0,0,200))
        draw.text((px, py), name, font=font, fill=(255,255,255,230))

    img.save(image_path)


async def fetch_geosampa(iptu: str, settings: AutomationSettings) -> tuple[DadosExtraidos, tuple[float, float, float, float] | None, dict | None]:
    parsed = parse_iptu(iptu)

    if not (parsed["setor"] and parsed["quadra"] and parsed["lote"]):
        return DadosExtraidos(observacoes="IPTU invalido. Use formato 000.000.0000-0."), None, None

    lote_cql = (
        f"{settings.geosampa_lote_field_setor}='{parsed['setor']}' AND "
        f"{settings.geosampa_lote_field_quadra}='{parsed['quadra']}' AND "
        f"{settings.geosampa_lote_field_lote}='{parsed['lote']}'"
    )
    if settings.geosampa_lote_field_digito and parsed["digito"]:
        lote_cql += f" AND {settings.geosampa_lote_field_digito}='{parsed['digito']}'"

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=60.0, connect=20.0)) as client:
        lote_payload = await wfs_get_json(
            client,
            settings.geosampa_wfs_url,
            {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeName": settings.geosampa_lote_layer,
                "outputFormat": "application/json",
                "cql_filter": lote_cql,
                "count": 1,
            },
        )

    lote_features = lote_payload.get("features") or []
    if not lote_features:
        return DadosExtraidos(observacoes="Lote fiscal nao encontrado para o IPTU informado."), None, None

    lote_feature = lote_features[0]
    lote_geom = lote_feature.get("geometry")
    if not lote_geom:
        return DadosExtraidos(observacoes="Geometria do lote nao encontrada."), None, None

    wkt = polygon_to_wkt(lote_geom)
    bbox = geometry_bbox(lote_geom)
    zone_cql = f"INTERSECTS({settings.geosampa_zone_geom_field}, SRID=31983;{wkt})"

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=60.0, connect=20.0)) as client:
        zone_payload = await wfs_get_json(
            client,
            settings.geosampa_wfs_url,
            {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeName": settings.geosampa_zone_layer,
                "outputFormat": "application/json",
                "cql_filter": zone_cql,
                "count": 1,
            },
        )

    features = zone_payload.get("features") or []
    if not features:
        return DadosExtraidos(observacoes="Zoneamento nao encontrado para o lote informado."), bbox, lote_geom

    props = features[0].get("properties") or {}
    lote_props = lote_feature.get("properties") or {}

    def get_field(obj: dict, name: str) -> str:
        if not name:
            return ""
        return normalize_value(obj.get(name, ""))

    legisla = ""
    if settings.geosampa_field_legisla:
        legisla = get_field(props, settings.geosampa_field_legisla)
    else:
        partes = [
            get_field(props, settings.geosampa_field_legisla_tipo),
            get_field(props, settings.geosampa_field_legisla_numero),
            get_field(props, settings.geosampa_field_legisla_ano),
        ]
        legisla = " ".join(p for p in partes if p)

    endereco = " ".join(
        p for p in [
            get_field(lote_props, settings.geosampa_field_logradouro),
            get_field(lote_props, settings.geosampa_field_numero),
        ] if p
    )

    subprefeitura = ""
    distrito = ""
    macroarea = ""
    restr_patrimonio = ""
    restr_manancial = ""
    restr_aero = ""
    restr_melhoramento = ""
    distrito_map = load_distrito_subpref_map()
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=60.0, connect=20.0)) as client:
        subprefeitura = await fetch_first_field(
            client,
            settings.geosampa_wfs_url,
            settings.geosampa_subpref_layer,
            settings.geosampa_subpref_geom,
            wkt,
            settings.geosampa_subpref_field_nome,
        )
        distrito = await fetch_first_field(
            client,
            settings.geosampa_wfs_url,
            settings.geosampa_distrito_layer,
            settings.geosampa_distrito_geom,
            wkt,
            settings.geosampa_distrito_field_nome,
        )
        macroarea = await fetch_first_field(
            client,
            settings.geosampa_wfs_url,
            settings.geosampa_macro_layer,
            settings.geosampa_macro_geom,
            wkt,
            settings.geosampa_macro_field_nome,
        )
        if not subprefeitura and distrito:
            mapped = distrito_map.get(normalize_key(distrito))
            if mapped:
                subprefeitura = mapped.get("subprefeitura", "")
        if not distrito or not subprefeitura:
            bairro_geo, subpref_geo = await geocode_address(client, endereco)
            if not distrito:
                distrito = bairro_geo
            if not subprefeitura:
                subprefeitura = subpref_geo
        restr_patrimonio = await resolve_restriction(
            client,
            settings.geosampa_wfs_url,
            wkt,
            "Patrimonio historico",
            ["tomb", "patrimon", "conpresp", "condephaat", "zepec"],
            settings.geosampa_patrimonio_layer,
            settings.geosampa_patrimonio_geom,
            settings.geosampa_patrimonio_label,
        )
        restr_manancial = await resolve_restriction(
            client,
            settings.geosampa_wfs_url,
            wkt,
            "Area de manancial",
            ["manancial", "manciais", "aprm", "represa", "bacia"],
            settings.geosampa_manancial_layer,
            settings.geosampa_manancial_geom,
            settings.geosampa_manancial_label,
        )
        restr_aero = await resolve_restriction(
            client,
            settings.geosampa_wfs_url,
            wkt,
            "Protecao aeroportuaria",
            ["aero", "aerop", "comaer", "proteca", "zona_de_protecao"],
            settings.geosampa_aero_layer,
            settings.geosampa_aero_geom,
            settings.geosampa_aero_label,
        )
        restr_melhoramento = await resolve_restriction(
            client,
            settings.geosampa_wfs_url,
            wkt,
            "Melhoramento publico",
            ["melhoramento", "alargamento", "alinhamento", "viario", "sistema_viario"],
            settings.geosampa_melhoramento_layer,
            settings.geosampa_melhoramento_geom,
            settings.geosampa_melhoramento_label,
        )

    zona_sigla = get_field(props, settings.geosampa_field_zona_sigla)
    zone_map = load_zone_map()
    zona_sigla = zona_sigla.strip().upper() if zona_sigla else ""
    zona_nome = get_field(props, settings.geosampa_field_zona_nome) or zone_map.get(zona_sigla, "")
    if not zona_sigla and zona_nome:
        zona_sigla = zona_nome.strip().upper()
        zona_nome = zone_map.get(zona_sigla, zona_nome)
    if zona_sigla and not zona_nome:
        zona_nome = zone_map.get(zona_sigla, zona_nome)
    if zona_sigla and zona_nome and zona_nome.strip().upper() == zona_sigla:
        zona_nome = zone_map.get(zona_sigla, zona_nome)

    parametros = load_param_map().get(zona_sigla, {})

    # Escolha do CA maximo por area do lote (quando disponivel)
    area_raw = get_field(lote_props, settings.geosampa_field_area)
    try:
        area_val = float(str(area_raw).replace(",", "."))
    except Exception:
        area_val = None
    ca_max = parametros.get("caMax")
    if area_val is not None:
        if area_val <= 500 and parametros.get("caMaxAte500"):
            ca_max = parametros.get("caMaxAte500")
        if area_val > 500 and parametros.get("caMaxAcima500"):
            ca_max = parametros.get("caMaxAcima500")

    to_max = parametros.get("toMax")
    if area_val is not None:
        if area_val <= 500 and parametros.get("toAte500"):
            to_max = parametros.get("toAte500")
        if area_val > 500 and parametros.get("toAcima500"):
            to_max = parametros.get("toAcima500")

    recuo_frente = parametros.get("recuoFrente")
    recuo_ate10 = parametros.get("recuoLatAte10")
    recuo_acima10 = parametros.get("recuoLatAcima10")
    recuos_texto = ""
    if recuo_frente or recuo_ate10 or recuo_acima10:
        recuos_texto = f"Frente {recuo_frente or 'NA'}; Laterais/Fundos <=10m {recuo_ate10 or 'NA'}; >10m {recuo_acima10 or 'NA'}"

    return DadosExtraidos(
        sql=f"{parsed['setor']}.{parsed['quadra']}.{parsed['lote']}-{parsed['digito']}",
        enderecoCompleto=fill(endereco, "Endereco nao identificado"),
        bairro=fill(get_field(lote_props, settings.geosampa_field_bairro) or normalize_value(distrito), "Bairro nao identificado"),
        subprefeitura=fill(get_field(lote_props, settings.geosampa_field_subprefeitura) or normalize_value(subprefeitura), "Subprefeitura nao identificada"),
        areaTerreno=fill(normalize_value(get_field(lote_props, settings.geosampa_field_area)), "Nao identificado"),
        zonaSigla=fill(normalize_value(zona_sigla), "Nao identificado"),
        zonaNome=fill(normalize_value(zona_nome), "Nao identificado"),
        leiVigente=fill(normalize_value(legisla), "Nao identificado"),
        macroarea=fill(normalize_value(macroarea), "Nao identificado"),
        caMin=fill(normalize_value(parametros.get("caMin") or get_field(props, settings.geosampa_field_coef)), "Nao identificado"),
        caBasico=fill(normalize_value(parametros.get("caBasico")), "Nao identificado"),
        caMax=fill(normalize_value(ca_max), "Nao identificado"),
        taxaOcupacao=fill(normalize_value(to_max or get_field(props, settings.geosampa_field_taxa)), "Nao identificado"),
        gabaritoAltura=fill(normalize_value(parametros.get("gabaritoAltura") or get_field(props, settings.geosampa_field_gabarito)), "Nao identificado"),
        recuos=fill(normalize_value(recuos_texto or get_field(props, settings.geosampa_field_recuo)), "Nao identificado"),
        restricaoPatrimonio=fill(restr_patrimonio, "Sem restricoes identificadas nesta data"),
        restricaoManancial=fill(restr_manancial, "Sem restricoes identificadas nesta data"),
        restricaoAeroportuaria=fill(restr_aero, "Sem restricoes identificadas nesta data"),
        restricaoMelhoramento=fill(restr_melhoramento, "Sem restricoes identificadas nesta data"),
        observacoes=fill(normalize_value(get_field(props, settings.geosampa_field_obs)), "Sem observacoes"),
    ), bbox, lote_geom


async def run_automation(consulta: ConsultaState, settings: AutomationSettings) -> None:
    consulta.status = "acessando_prefeitura"
    try:
        enable_browser = os.getenv("ENABLE_BROWSER_AUTOMATION", "0") == "1"
        if enable_browser:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()

                await page.goto("https://geosampa.prefeitura.sp.gov.br", wait_until="domcontentloaded", timeout=60000)

                try:
                    await page.wait_for_function(
                        "window._tscpp || window.TSPD || window.tspd", timeout=15000
                    )
                except PlaywrightTimeout:
                    pass

                # Best-effort UI actions: zoom out and toggle layers (may vary by UI state)
                try:
                    for _ in range(max(1, settings.map_zoom_out_steps)):
                        await page.keyboard.press("Control+-")
                        await page.wait_for_timeout(250)
                except Exception:
                    pass

                try:
                    for _ in range(max(1, settings.map_zoom_out_wheel_steps)):
                        await page.mouse.wheel(0, settings.map_zoom_out_wheel_delta)
                        await page.wait_for_timeout(250)
                except Exception:
                    pass

                try:
                    panel = page.locator(settings.geosampa_layer_panel_selector)
                    if await panel.count() > 0:
                        await panel.first.click()
                        await page.wait_for_timeout(500)
                    # Toggle zoneamento and logradouros if visible in layer list
                    if settings.geosampa_layer_zoneamento_text:
                        await page.get_by_text(settings.geosampa_layer_zoneamento_text, exact=False).first.click(timeout=2000)
                    if settings.geosampa_layer_logradouro_text:
                        await page.get_by_text(settings.geosampa_layer_logradouro_text, exact=False).first.click(timeout=2000)
                except Exception:
                    pass

                captcha = await page.query_selector(settings.captcha_selector)
                if captcha:
                    consulta.status = "aguardando_captcha"
                    image_bytes = await captcha.screenshot(type="png")
                    consulta.captcha_image = "data:image/png;base64," + base64.b64encode(image_bytes).decode("utf-8")

                    await consulta.captcha_event.wait()
                    consulta.status = "extraindo_dados"

                    resposta = consulta.captcha_resposta or ""
                    input_el = await page.query_selector(settings.captcha_input_selector)
                    if input_el and resposta:
                        await input_el.fill(resposta)
                        submit_el = await page.query_selector(settings.captcha_submit_selector)
                        if submit_el:
                            await submit_el.click()
                            await page.wait_for_timeout(2000)

                await browser.close()

        consulta.status = "extraindo_dados"
        dados, bbox, lote_geom = await fetch_geosampa(consulta.iptu, settings)

        if bbox and lote_geom:
            try:
                map_path = Path(__file__).resolve().parent.parent / "output" / "maps" / f"{consulta.id}.png"
                map_path_str, expanded_bbox, legend_entries, dimensoes = await render_map_from_wfs(settings, bbox, lote_geom, map_path)
                base_url = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")
                dados.mapaUrl = f"{base_url}/map/{consulta.id}"
                dados.legendaZoneamento = legend_entries
                dados.dimensoesLote = dimensoes
            except Exception:
                pass

        consulta.dados_extraidos = dados
        consulta.status = "gerando_pdf"
        pdf_path = Path(__file__).resolve().parent.parent / "output" / "pdf" / f"{consulta.id}.pdf"
        generate_pdf(pdf_path, consulta.iptu, dados)
        consulta.pdf_path = str(pdf_path)
        consulta.status = "concluido"
        store.add_historico(consulta, "concluido")
    except Exception as exc:
        consulta.status = "erro"
        consulta.dados_extraidos = DadosExtraidos(observacoes=f"Erro: {type(exc).__name__}: {exc}")
