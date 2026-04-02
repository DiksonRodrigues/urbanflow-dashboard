import type { Consulta, DadosExtraidos, HistoricoItem } from "@/types/consulta";

const BASE_URL = "http://localhost:8000";

// Simulated delay
const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

// Mock data for when backend is unavailable
const mockDados: DadosExtraidos = {
  zonaDeUso: "ZM-2",
  coeficiente: "2.0",
  recuo: "5m",
  gabarito: "15m",
  taxaOcupacao: "0.5",
  observacoes: "Zona Mista de média densidade",
};

let mockIdCounter = 1;

export async function iniciarConsulta(iptus: string[]): Promise<Consulta[]> {
  try {
    const res = await fetch(`${BASE_URL}/consultar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ iptus }),
    });
    if (!res.ok) throw new Error("Backend error");
    return res.json();
  } catch {
    // Simulação mock
    await delay(500);
    return iptus.map((iptu) => ({
      id: `mock-${mockIdCounter++}`,
      iptu,
      status: "acessando_prefeitura" as const,
      createdAt: new Date().toISOString(),
    }));
  }
}

export async function getStatus(id: string): Promise<Consulta> {
  try {
    const res = await fetch(`${BASE_URL}/status/${id}`);
    if (!res.ok) throw new Error("Backend error");
    return res.json();
  } catch {
    await delay(800);
    // Simulate progression
    return {
      id,
      iptu: "000.000.0000-0",
      status: "aguardando_captcha",
      captchaImage: "/placeholder.svg",
      createdAt: new Date().toISOString(),
    };
  }
}

export async function enviarCaptcha(id: string, resposta: string): Promise<Consulta> {
  try {
    const res = await fetch(`${BASE_URL}/captcha/${id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resposta }),
    });
    if (!res.ok) throw new Error("Backend error");
    return res.json();
  } catch {
    await delay(1000);
    return {
      id,
      iptu: "000.000.0000-0",
      status: "revisao",
      dadosExtraidos: { ...mockDados },
      createdAt: new Date().toISOString(),
    };
  }
}

export async function confirmarDados(id: string, dados: DadosExtraidos): Promise<Consulta> {
  try {
    const res = await fetch(`${BASE_URL}/confirmar/${id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    if (!res.ok) throw new Error("Backend error");
    return res.json();
  } catch {
    await delay(1500);
    return {
      id,
      iptu: "000.000.0000-0",
      status: "concluido",
      dadosExtraidos: dados,
      pdfUrl: "#",
      createdAt: new Date().toISOString(),
    };
  }
}

export async function getHistorico(): Promise<HistoricoItem[]> {
  try {
    const res = await fetch(`${BASE_URL}/historico`);
    if (!res.ok) throw new Error("Backend error");
    return res.json();
  } catch {
    await delay(300);
    return [
      { id: "h1", data: "2026-04-01", iptu: "045.018.0042-1", zonaDeUso: "ZM-2", status: "concluido", pdfUrl: "#" },
      { id: "h2", data: "2026-03-28", iptu: "012.045.0018-9", zonaDeUso: "ZER-1", status: "concluido", pdfUrl: "#" },
      { id: "h3", data: "2026-03-25", iptu: "078.032.0091-3", zonaDeUso: "ZC", status: "erro" },
    ];
  }
}
