from __future__ import annotations

import asyncio
import os
import re
import uuid
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from automation import AutomationSettings, run_automation
from models import (
    CaptchaResposta,
    ConfirmarRequest,
    ConsultarRequest,
    Consulta,
    ResolverCaptchaRequest,
)
from pdf_generator import generate_pdf
from state import ConsultaState, store


app = FastAPI(title="UrbanFlow Local API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def settings() -> AutomationSettings:
    return AutomationSettings(
        geosampa_wfs_url=os.getenv("GEOSAMPA_WFS_URL") or AutomationSettings.geosampa_wfs_url,
        geosampa_zone_layer=os.getenv("GEOSAMPA_ZONE_LAYER") or AutomationSettings.geosampa_zone_layer,
        geosampa_zone_geom_field=os.getenv("GEOSAMPA_ZONE_GEOM_FIELD") or AutomationSettings.geosampa_zone_geom_field,
        geosampa_lote_layer=os.getenv("GEOSAMPA_LOTE_LAYER") or AutomationSettings.geosampa_lote_layer,
        geosampa_lote_geom_field=os.getenv("GEOSAMPA_LOTE_GEOM_FIELD") or AutomationSettings.geosampa_lote_geom_field,
        geosampa_lote_field_setor=os.getenv("GEOSAMPA_LOTE_FIELD_SETOR") or AutomationSettings.geosampa_lote_field_setor,
        geosampa_lote_field_quadra=os.getenv("GEOSAMPA_LOTE_FIELD_QUADRA") or AutomationSettings.geosampa_lote_field_quadra,
        geosampa_lote_field_lote=os.getenv("GEOSAMPA_LOTE_FIELD_LOTE") or AutomationSettings.geosampa_lote_field_lote,
        geosampa_lote_field_digito=os.getenv("GEOSAMPA_LOTE_FIELD_DIGITO") or AutomationSettings.geosampa_lote_field_digito,
        geosampa_field_zona_sigla=os.getenv("GEOSAMPA_FIELD_ZONA_SIGLA") or AutomationSettings.geosampa_field_zona_sigla,
        geosampa_field_zona_nome=os.getenv("GEOSAMPA_FIELD_ZONA_NOME") or AutomationSettings.geosampa_field_zona_nome,
        geosampa_field_legisla=os.getenv("GEOSAMPA_FIELD_LEGISLA") or AutomationSettings.geosampa_field_legisla,
        geosampa_field_legisla_tipo=os.getenv("GEOSAMPA_FIELD_LEGISLA_TIPO") or AutomationSettings.geosampa_field_legisla_tipo,
        geosampa_field_legisla_numero=os.getenv("GEOSAMPA_FIELD_LEGISLA_NUMERO") or AutomationSettings.geosampa_field_legisla_numero,
        geosampa_field_legisla_ano=os.getenv("GEOSAMPA_FIELD_LEGISLA_ANO") or AutomationSettings.geosampa_field_legisla_ano,
        geosampa_field_coef=os.getenv("GEOSAMPA_FIELD_COEF") or AutomationSettings.geosampa_field_coef,
        geosampa_field_recuo=os.getenv("GEOSAMPA_FIELD_RECUO") or AutomationSettings.geosampa_field_recuo,
        geosampa_field_gabarito=os.getenv("GEOSAMPA_FIELD_GABARITO") or AutomationSettings.geosampa_field_gabarito,
        geosampa_field_taxa=os.getenv("GEOSAMPA_FIELD_TAXA") or AutomationSettings.geosampa_field_taxa,
        geosampa_field_obs=os.getenv("GEOSAMPA_FIELD_OBS") or AutomationSettings.geosampa_field_obs,
        geosampa_field_area=os.getenv("GEOSAMPA_FIELD_AREA") or AutomationSettings.geosampa_field_area,
        geosampa_field_logradouro=os.getenv("GEOSAMPA_FIELD_LOGRADOURO") or AutomationSettings.geosampa_field_logradouro,
        geosampa_field_numero=os.getenv("GEOSAMPA_FIELD_NUMERO") or AutomationSettings.geosampa_field_numero,
        geosampa_field_bairro=os.getenv("GEOSAMPA_FIELD_BAIRRO") or AutomationSettings.geosampa_field_bairro,
        geosampa_field_subprefeitura=os.getenv("GEOSAMPA_FIELD_SUBPREFEITURA") or AutomationSettings.geosampa_field_subprefeitura,
        geosampa_subpref_layer=os.getenv("GEOSAMPA_SUBPREF_LAYER") or AutomationSettings.geosampa_subpref_layer,
        geosampa_subpref_geom=os.getenv("GEOSAMPA_SUBPREF_GEOM") or AutomationSettings.geosampa_subpref_geom,
        geosampa_subpref_field_nome=os.getenv("GEOSAMPA_SUBPREF_FIELD_NOME") or AutomationSettings.geosampa_subpref_field_nome,
        geosampa_distrito_layer=os.getenv("GEOSAMPA_DISTRITO_LAYER") or AutomationSettings.geosampa_distrito_layer,
        geosampa_distrito_geom=os.getenv("GEOSAMPA_DISTRITO_GEOM") or AutomationSettings.geosampa_distrito_geom,
        geosampa_distrito_field_nome=os.getenv("GEOSAMPA_DISTRITO_FIELD_NOME") or AutomationSettings.geosampa_distrito_field_nome,
        geosampa_macro_layer=os.getenv("GEOSAMPA_MACRO_LAYER") or AutomationSettings.geosampa_macro_layer,
        geosampa_macro_geom=os.getenv("GEOSAMPA_MACRO_GEOM") or AutomationSettings.geosampa_macro_geom,
        geosampa_macro_field_nome=os.getenv("GEOSAMPA_MACRO_FIELD_NOME") or AutomationSettings.geosampa_macro_field_nome,
        geosampa_logradouro_layer=os.getenv("GEOSAMPA_LOGRADOURO_LAYER") or AutomationSettings.geosampa_logradouro_layer,
        geosampa_logradouro_geom=os.getenv("GEOSAMPA_LOGRADOURO_GEOM") or AutomationSettings.geosampa_logradouro_geom,
        geosampa_logradouro_field_nome=os.getenv("GEOSAMPA_LOGRADOURO_FIELD_NOME") or AutomationSettings.geosampa_logradouro_field_nome,
        map_zoom_out_factor=float(os.getenv("MAP_ZOOM_OUT_FACTOR") or AutomationSettings.map_zoom_out_factor),
        map_zoom_out_steps=int(os.getenv("MAP_ZOOM_OUT_STEPS") or AutomationSettings.map_zoom_out_steps),
        map_zoom_out_wheel_steps=int(os.getenv("MAP_ZOOM_OUT_WHEEL_STEPS") or AutomationSettings.map_zoom_out_wheel_steps),
        map_zoom_out_wheel_delta=int(os.getenv("MAP_ZOOM_OUT_WHEEL_DELTA") or AutomationSettings.map_zoom_out_wheel_delta),
        geosampa_layer_panel_selector=os.getenv("GEOSAMPA_LAYER_PANEL_SELECTOR") or AutomationSettings.geosampa_layer_panel_selector,
        geosampa_layer_logradouro_text=os.getenv("GEOSAMPA_LAYER_LOGRADOURO_TEXT") or AutomationSettings.geosampa_layer_logradouro_text,
        geosampa_layer_zoneamento_text=os.getenv("GEOSAMPA_LAYER_ZONEAMENTO_TEXT") or AutomationSettings.geosampa_layer_zoneamento_text,
        geosampa_patrimonio_layer=os.getenv("GEOSAMPA_PATRIMONIO_LAYER") or AutomationSettings.geosampa_patrimonio_layer,
        geosampa_patrimonio_geom=os.getenv("GEOSAMPA_PATRIMONIO_GEOM") or AutomationSettings.geosampa_patrimonio_geom,
        geosampa_patrimonio_label=os.getenv("GEOSAMPA_PATRIMONIO_LABEL") or AutomationSettings.geosampa_patrimonio_label,
        geosampa_manancial_layer=os.getenv("GEOSAMPA_MANANCIAL_LAYER") or AutomationSettings.geosampa_manancial_layer,
        geosampa_manancial_geom=os.getenv("GEOSAMPA_MANANCIAL_GEOM") or AutomationSettings.geosampa_manancial_geom,
        geosampa_manancial_label=os.getenv("GEOSAMPA_MANANCIAL_LABEL") or AutomationSettings.geosampa_manancial_label,
        geosampa_aero_layer=os.getenv("GEOSAMPA_AERO_LAYER") or AutomationSettings.geosampa_aero_layer,
        geosampa_aero_geom=os.getenv("GEOSAMPA_AERO_GEOM") or AutomationSettings.geosampa_aero_geom,
        geosampa_aero_label=os.getenv("GEOSAMPA_AERO_LABEL") or AutomationSettings.geosampa_aero_label,
        geosampa_melhoramento_layer=os.getenv("GEOSAMPA_MELHORAMENTO_LAYER") or AutomationSettings.geosampa_melhoramento_layer,
        geosampa_melhoramento_geom=os.getenv("GEOSAMPA_MELHORAMENTO_GEOM") or AutomationSettings.geosampa_melhoramento_geom,
        geosampa_melhoramento_label=os.getenv("GEOSAMPA_MELHORAMENTO_LABEL") or AutomationSettings.geosampa_melhoramento_label,
        captcha_selector=os.getenv("CAPTCHA_SELECTOR") or AutomationSettings.captcha_selector,
        captcha_input_selector=os.getenv("CAPTCHA_INPUT_SELECTOR") or AutomationSettings.captcha_input_selector,
        captcha_submit_selector=os.getenv("CAPTCHA_SUBMIT_SELECTOR") or AutomationSettings.captcha_submit_selector,
    )


async def fetch_wfs_capabilities(base_url: str) -> str:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(f"{base_url}?service=WFS&request=GetCapabilities")
        resp.raise_for_status()
        return resp.text


async def fetch_describe_feature(base_url: str, layer: str) -> str:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(
            f"{base_url}?service=WFS&request=DescribeFeatureType&typeName={layer}"
        )
        resp.raise_for_status()
        return resp.text


@app.get("/geosampa/layers")
async def geosampa_layers():
    cfg = settings()
    xml = await fetch_wfs_capabilities(cfg.geosampa_wfs_url)
    names = re.findall(r"<Name>([^<]*zoneamento[^<]*)</Name>", xml, flags=re.IGNORECASE)
    return {"layers": sorted(set(names))}


@app.get("/geosampa/describe/{layer}")
async def geosampa_describe(layer: str):
    cfg = settings()
    xml = await fetch_describe_feature(cfg.geosampa_wfs_url, layer)
    fields = re.findall(r'name=\"([^\"]+)\"', xml)
    return {"layer": layer, "fields": fields}


@app.post("/consultar")
async def consultar(payload: ConsultarRequest) -> list[Consulta]:
    if not payload.iptus:
        raise HTTPException(status_code=400, detail="Lista de IPTUs vazia.")

    consultas: list[Consulta] = []
    for iptu in payload.iptus:
        consulta_id = str(uuid.uuid4())
        consulta = ConsultaState(id=consulta_id, iptu=iptu)
        store.add(consulta)
        consultas.append(consulta.to_public())
        asyncio.create_task(run_automation(consulta, settings()))

    return consultas


@app.get("/status/{consulta_id}")
async def status(consulta_id: str) -> Consulta:
    consulta = store.get(consulta_id)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")
    return consulta.to_public()


@app.get("/captcha/{consulta_id}")
async def obter_captcha(consulta_id: str) -> dict:
    consulta = store.get(consulta_id)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")
    if not consulta.captcha_image:
        raise HTTPException(status_code=404, detail="Captcha não disponível.")
    return {"image": consulta.captcha_image}


@app.post("/captcha/{consulta_id}")
async def enviar_captcha(consulta_id: str, payload: CaptchaResposta) -> Consulta:
    consulta = store.get(consulta_id)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")
    consulta.captcha_resposta = payload.resposta
    consulta.captcha_event.set()
    return consulta.to_public()


@app.post("/resolver-captcha")
async def resolver_captcha(payload: ResolverCaptchaRequest) -> Consulta:
    consulta = store.get(payload.id)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")
    consulta.captcha_resposta = payload.resposta
    consulta.captcha_event.set()
    return consulta.to_public()


@app.post("/confirmar/{consulta_id}")
async def confirmar(consulta_id: str, payload: ConfirmarRequest) -> Consulta:
    consulta = store.get(consulta_id)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")

    consulta.status = "gerando_pdf"
    consulta.dados_extraidos = payload

    pdf_path = Path(__file__).resolve().parent.parent / "output" / "pdf" / f"{consulta_id}.pdf"
    generate_pdf(pdf_path, consulta.iptu, payload)
    consulta.pdf_path = str(pdf_path)
    consulta.status = "concluido"
    store.add_historico(consulta, "concluido")
    return consulta.to_public()


@app.get("/download/{consulta_id}")
async def download(consulta_id: str):
    consulta = store.get(consulta_id)
    if not consulta or not consulta.pdf_path:
        raise HTTPException(status_code=404, detail="PDF não encontrado.")
    return FileResponse(
        consulta.pdf_path,
        media_type="application/pdf",
        filename=f"urbanflow-{consulta_id}.pdf",
        headers={"Cache-Control": "no-store"},
    )


@app.post("/regen/{consulta_id}")
async def regen_pdf(consulta_id: str) -> Consulta:
    consulta = store.get(consulta_id)
    if not consulta or not consulta.dados_extraidos:
        raise HTTPException(status_code=404, detail="Consulta não encontrada ou sem dados.")

    pdf_path = Path(__file__).resolve().parent.parent / "output" / "pdf" / f"{consulta_id}.pdf"
    generate_pdf(pdf_path, consulta.iptu, consulta.dados_extraidos)
    consulta.pdf_path = str(pdf_path)
    store.update_historico(consulta)
    return consulta.to_public()


@app.get("/map/{consulta_id}")
async def map_image(consulta_id: str):
    consulta = store.get(consulta_id)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")
    map_path = Path(__file__).resolve().parent.parent / "output" / "maps" / f"{consulta_id}.png"
    if not map_path.exists():
        raise HTTPException(status_code=404, detail="Mapa não encontrado.")
    return FileResponse(map_path, media_type="image/png", filename=f"mapa-{consulta_id}.png")


@app.get("/historico")
async def historico():
    return store.historico
