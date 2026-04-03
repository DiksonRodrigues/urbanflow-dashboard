import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Consulta } from "@/types/consulta";

interface Props {
  consulta: Consulta;
}

export function ResultadoCard({ consulta }: Props) {
  const d = consulta.dadosExtraidos;
  if (!d) return null;

  const Field = ({ label, value }: { label: string; value: string }) => (
    <div className="space-y-1">
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="text-sm text-foreground">{value || "—"}</p>
    </div>
  );

  return (
    <Card className="border-white/10 bg-card/70 backdrop-blur">
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2 text-foreground">
          Resultado — IPTU: <span className="font-mono">{consulta.iptu}</span>
          <Badge variant="secondary" className="bg-white/5 border border-white/10 text-foreground/80">
            {consulta.status === "concluido" ? "Concluído" : "Em processamento"}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="SQL (Setor/Quadra/Lote)" value={d.sql} />
          <Field label="Endereço Completo" value={d.enderecoCompleto} />
          <Field label="Bairro" value={d.bairro} />
          <Field label="Subprefeitura" value={d.subprefeitura} />
          <Field label="Área do Terreno (m²)" value={d.areaTerreno} />
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Sigla da Zona" value={d.zonaSigla && d.zonaNome ? `${d.zonaSigla} (${d.zonaNome})` : d.zonaSigla} />
          <Field label="Nome da Zona" value={d.zonaNome} />
          <Field label="Lei Vigente" value={d.leiVigente} />
          <Field label="Macroárea" value={d.macroarea} />
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Field label="C.A. Mínimo" value={d.caMin} />
          <Field label="C.A. Básico" value={d.caBasico} />
          <Field label="C.A. Máximo" value={d.caMax} />
          <Field label="Taxa de Ocupação" value={d.taxaOcupacao} />
          <Field label="Gabarito de Altura" value={d.gabaritoAltura} />
          <Field label="Recuos" value={d.recuos} />
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Patrimônio Histórico" value={d.restricaoPatrimonio} />
          <Field label="Área de Manancial" value={d.restricaoManancial} />
          <Field label="Proteção Aeroportuária" value={d.restricaoAeroportuaria} />
          <Field label="Melhoramento Público" value={d.restricaoMelhoramento} />
        </div>

        {d.mapaUrl && (
          <div className="space-y-2">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Croqui do Lote</p>
            <div className="rounded-xl border border-white/10 bg-background/40 p-3">
              <img src={d.mapaUrl} alt="Croqui" className="w-full rounded-lg" />
            </div>
          </div>
        )}

        {consulta.pdfUrl && (
          <a
            href={consulta.pdfUrl}
            className="inline-flex text-sm text-primary underline underline-offset-4"
          >
            Baixar PDF
          </a>
        )}
      </CardContent>
    </Card>
  );
}
