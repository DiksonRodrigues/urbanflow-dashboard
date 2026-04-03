from __future__ import annotations

import re
import json
from pathlib import Path

import pdfplumber
import requests

PDF_URL = "https://legislacao.prefeitura.sp.gov.br/leis/decreto-57377-de-11-de-outubro-de-2016/anexo/5fa40b7114119228d2161425/Quadros%201%20a%207%20do%20Decreto%20n%C2%BA%2057.377_2016.pdf"

OUT_DIR = Path(__file__).resolve().parents[1] / "data"
PDF_PATH = OUT_DIR / "quadros_57_377_2016.pdf"
OUT_JSON = OUT_DIR / "zoneamento_parametros.json"


def download_pdf() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if PDF_PATH.exists():
        return
    resp = requests.get(PDF_URL, timeout=30)
    resp.raise_for_status()
    PDF_PATH.write_bytes(resp.content)


def clean_tokens(tokens: list[str]) -> list[str]:
    cleaned = []
    for tok in tokens:
        if re.fullmatch(r"\([a-z]\)", tok):  # remove (a)(b)
            continue
        cleaned.append(tok)
    return cleaned


def parse_quadro2(lines: list[str]) -> dict:
    params = {}
    for line in lines:
        line = line.strip()
        if not line or not line.startswith("Z"):
            continue
        # split tokens
        tokens = clean_tokens(line.split())
        zone = tokens[0]
        values = tokens[1:]
        # Expect at least 8 numeric/NA values
        if len(values) < 8:
            continue

        # Map columns by order in Quadro 2
        # caMin, caBasico, caMax<=500, caMax>500, to<=500, to>500, gabarito, recuo_frente, recuo_lat_ate10, recuo_lat_acima10, cota_parte
        def safe(i):
            return values[i] if i < len(values) else "NA"

        params[zone] = {
            "caMin": safe(0),
            "caBasico": safe(1),
            "caMaxAte500": safe(2),
            "caMaxAcima500": safe(3),
            "toAte500": safe(4),
            "toAcima500": safe(5),
            "gabaritoAltura": safe(6),
            "recuoFrente": safe(7),
            "recuoLatAte10": safe(8),
            "recuoLatAcima10": safe(9),
            "cotaParteTerreno": safe(10),
        }
    return params


def main() -> None:
    download_pdf()
    with pdfplumber.open(PDF_PATH) as pdf:
        # Quadro 2 está na página 2 (index 1)
        text = pdf.pages[1].extract_text() or ""
    lines = text.splitlines()
    data = parse_quadro2(lines)
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Gerado: {OUT_JSON} ({len(data)} zonas)")


if __name__ == "__main__":
    main()
