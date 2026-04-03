from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import os
from datetime import datetime
from typing import Optional

from models import Consulta, ConsultaStatus, DadosExtraidos, HistoricoItem


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def pdf_url(consulta: "ConsultaState") -> str | None:
    if not consulta.pdf_path:
        return None
    base_url = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")
    try:
        version = int(os.path.getmtime(consulta.pdf_path))
    except Exception:
        version = int(datetime.utcnow().timestamp())
    return f"{base_url}/download/{consulta.id}?v={version}"


@dataclass
class ConsultaState:
    id: str
    iptu: str
    status: ConsultaStatus = "aguardando"
    created_at: str = field(default_factory=now_iso)
    captcha_image: Optional[str] = None
    dados_extraidos: Optional[DadosExtraidos] = None
    pdf_path: Optional[str] = None
    captcha_resposta: Optional[str] = None
    captcha_event: asyncio.Event = field(default_factory=asyncio.Event)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def to_public(self) -> Consulta:
        return Consulta(
            id=self.id,
            iptu=self.iptu,
            status=self.status,
            createdAt=self.created_at,
            captchaImage=self.captcha_image,
            dadosExtraidos=self.dados_extraidos,
            pdfUrl=pdf_url(self),
        )


class Store:
    def __init__(self) -> None:
        self.consultas: dict[str, ConsultaState] = {}
        self.historico: list[HistoricoItem] = []

    def add(self, consulta: ConsultaState) -> None:
        self.consultas[consulta.id] = consulta

    def get(self, consulta_id: str) -> Optional[ConsultaState]:
        return self.consultas.get(consulta_id)

    def add_historico(self, consulta: ConsultaState, status: str) -> None:
        zona = consulta.dados_extraidos.zonaSigla if consulta.dados_extraidos else ""
        zona_nome = consulta.dados_extraidos.zonaNome if consulta.dados_extraidos else ""
        lei = consulta.dados_extraidos.leiVigente if consulta.dados_extraidos else ""
        self.historico.append(
            HistoricoItem(
                id=consulta.id,
                data=consulta.created_at,
                iptu=consulta.iptu,
                zonaDeUso=zona,
                zonaNome=zona_nome,
                leiVigente=lei,
                status=status,
                pdfUrl=pdf_url(consulta),
            )
        )

    def update_historico(self, consulta: ConsultaState) -> None:
        for item in self.historico:
            if item.id == consulta.id:
                item.status = consulta.status
                if consulta.dados_extraidos:
                    item.zonaDeUso = consulta.dados_extraidos.zonaSigla
                    item.zonaNome = consulta.dados_extraidos.zonaNome
                    item.leiVigente = consulta.dados_extraidos.leiVigente
                item.pdfUrl = pdf_url(consulta)
                return
        self.add_historico(consulta, consulta.status)


store = Store()
