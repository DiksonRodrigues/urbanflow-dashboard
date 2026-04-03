from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field

ConsultaStatus = Literal[
    "aguardando",
    "acessando_prefeitura",
    "aguardando_captcha",
    "extraindo_dados",
    "revisao",
    "gerando_pdf",
    "concluido",
    "erro",
]


class DadosExtraidos(BaseModel):
    sql: str = ""
    enderecoCompleto: str = ""
    bairro: str = ""
    subprefeitura: str = ""
    areaTerreno: str = ""

    zonaSigla: str = ""
    zonaNome: str = ""
    leiVigente: str = ""
    macroarea: str = ""

    caMin: str = ""
    caBasico: str = ""
    caMax: str = ""
    taxaOcupacao: str = ""
    gabaritoAltura: str = ""
    recuos: str = ""

    restricaoPatrimonio: str = ""
    restricaoManancial: str = ""
    restricaoAeroportuaria: str = ""
    restricaoMelhoramento: str = ""

    mapaUrl: str = ""
    legendaZoneamento: list[str] = Field(default_factory=list)
    dimensoesLote: list[str] = Field(default_factory=list)
    arruamento: str = ""
    observacoes: str = ""


class Consulta(BaseModel):
    id: str
    iptu: str
    status: ConsultaStatus
    createdAt: str
    captchaImage: Optional[str] = None
    dadosExtraidos: Optional[DadosExtraidos] = None
    pdfUrl: Optional[str] = None


class HistoricoItem(BaseModel):
    id: str
    data: str
    iptu: str
    zonaDeUso: str
    zonaNome: Optional[str] = None
    leiVigente: Optional[str] = None
    status: Literal["concluido", "erro"]
    pdfUrl: Optional[str] = None


class ConsultarRequest(BaseModel):
    iptus: list[str] = Field(default_factory=list)


class CaptchaResposta(BaseModel):
    resposta: str


class ResolverCaptchaRequest(BaseModel):
    id: str
    resposta: str


class ConfirmarRequest(BaseModel):
    sql: str
    enderecoCompleto: str
    bairro: str
    subprefeitura: str
    areaTerreno: str
    zonaSigla: str
    zonaNome: str
    leiVigente: str
    macroarea: str
    caMin: str
    caBasico: str
    caMax: str
    taxaOcupacao: str
    gabaritoAltura: str
    recuos: str
    restricaoPatrimonio: str
    restricaoManancial: str
    restricaoAeroportuaria: str
    restricaoMelhoramento: str
    mapaUrl: str
    legendaZoneamento: list[str] = Field(default_factory=list)
    dimensoesLote: list[str] = Field(default_factory=list)
    arruamento: str = ""
    observacoes: str
