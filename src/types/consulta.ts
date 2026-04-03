export type ConsultaStatus =
  | "aguardando"
  | "acessando_prefeitura"
  | "aguardando_captcha"
  | "extraindo_dados"
  | "revisao"
  | "gerando_pdf"
  | "concluido"
  | "erro";

export interface ConsultaStep {
  key: ConsultaStatus;
  label: string;
}

export const CONSULTA_STEPS: ConsultaStep[] = [
  { key: "acessando_prefeitura", label: "Acessando Prefeitura" },
  { key: "aguardando_captcha", label: "Aguardando Captcha" },
  { key: "extraindo_dados", label: "Extraindo Dados" },
  { key: "gerando_pdf", label: "Gerando PDF" },
];

export interface DadosExtraidos {
  sql: string;
  enderecoCompleto: string;
  bairro: string;
  subprefeitura: string;
  areaTerreno: string;

  zonaSigla: string;
  zonaNome: string;
  leiVigente: string;
  macroarea: string;

  caMin: string;
  caBasico: string;
  caMax: string;
  taxaOcupacao: string;
  gabaritoAltura: string;
  recuos: string;

  restricaoPatrimonio: string;
  restricaoManancial: string;
  restricaoAeroportuaria: string;
  restricaoMelhoramento: string;

  mapaUrl: string;
  legendaZoneamento?: string[];
  dimensoesLote?: string[];
  arruamento?: string;
  observacoes: string;
}

export interface Consulta {
  id: string;
  iptu: string;
  status: ConsultaStatus;
  captchaImage?: string;
  dadosExtraidos?: DadosExtraidos;
  createdAt: string;
  pdfUrl?: string;
}

export interface HistoricoItem {
  id: string;
  data: string;
  iptu: string;
  zonaDeUso: string;
  status: "concluido" | "erro";
  pdfUrl?: string;
}
