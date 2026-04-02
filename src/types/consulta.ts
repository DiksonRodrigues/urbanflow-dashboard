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
  zonaDeUso: string;
  coeficiente: string;
  recuo: string;
  gabarito: string;
  taxaOcupacao: string;
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
