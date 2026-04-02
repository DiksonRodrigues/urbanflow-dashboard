import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileCheck } from "lucide-react";
import type { DadosExtraidos, Consulta } from "@/types/consulta";

interface Props {
  consulta: Consulta;
  onConfirmar: (id: string, dados: DadosExtraidos) => void;
}

const fieldLabels: Record<keyof DadosExtraidos, string> = {
  zonaDeUso: "Zona de Uso",
  coeficiente: "Coeficiente de Aproveitamento",
  recuo: "Recuo",
  gabarito: "Gabarito de Altura",
  taxaOcupacao: "Taxa de Ocupação",
  observacoes: "Observações",
};

export function EditorRevisao({ consulta, onConfirmar }: Props) {
  const [dados, setDados] = useState<DadosExtraidos>(
    consulta.dadosExtraidos || {
      zonaDeUso: "",
      coeficiente: "",
      recuo: "",
      gabarito: "",
      taxaOcupacao: "",
      observacoes: "",
    }
  );

  const update = (key: keyof DadosExtraidos, value: string) =>
    setDados((prev) => ({ ...prev, [key]: value }));

  return (
    <Card className="border-primary/30">
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <FileCheck className="h-4 w-4 text-primary" />
          Revisão — IPTU: <span className="font-mono">{consulta.iptu}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {(Object.keys(fieldLabels) as (keyof DadosExtraidos)[]).map((key) => (
            <div key={key} className="space-y-1.5">
              <Label htmlFor={key} className="text-xs text-muted-foreground">
                {fieldLabels[key]}
              </Label>
              <Input
                id={key}
                value={dados[key]}
                onChange={(e) => update(key, e.target.value)}
                className="font-mono text-sm"
              />
            </div>
          ))}
        </div>
        <Button
          onClick={() => onConfirmar(consulta.id, dados)}
          className="w-full mt-5"
        >
          Confirmar e Gerar PDF
        </Button>
      </CardContent>
    </Card>
  );
}
