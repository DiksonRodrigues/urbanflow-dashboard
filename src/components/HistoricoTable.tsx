import { useState, useEffect } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Download, Search } from "lucide-react";
import type { HistoricoItem } from "@/types/consulta";
import { getHistorico, regenPdf } from "@/services/api";

export function HistoricoTable() {
  const [items, setItems] = useState<HistoricoItem[]>([]);
  const [filtro, setFiltro] = useState("");
  const [loadingId, setLoadingId] = useState<string | null>(null);

  useEffect(() => {
    getHistorico().then(setItems);
  }, []);

  const filtered = items.filter((i) =>
    i.iptu.toLowerCase().includes(filtro.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          value={filtro}
          onChange={(e) => setFiltro(e.target.value)}
          placeholder="Buscar por IPTU..."
          className="pl-9 bg-background/60 border-white/10 focus-visible:ring-primary/40"
        />
      </div>

      <div className="rounded-xl border border-white/10 bg-background/40">
        <Table>
          <TableHeader>
            <TableRow className="border-white/10">
              <TableHead className="text-muted-foreground">Data</TableHead>
              <TableHead className="text-muted-foreground">IPTU</TableHead>
              <TableHead className="text-muted-foreground">Zona de Uso</TableHead>
              <TableHead className="text-muted-foreground">Status</TableHead>
              <TableHead className="text-right text-muted-foreground">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                  Nenhum registro encontrado
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((item) => (
                <TableRow key={item.id} className="border-white/10">
                  <TableCell className="font-mono text-xs">
                    {new Date(item.data).toLocaleDateString("pt-BR")}
                  </TableCell>
                  <TableCell className="font-mono">{item.iptu}</TableCell>
                  <TableCell>{item.zonaDeUso || "—"}</TableCell>
                  <TableCell>
                    <Badge
                      variant={item.status === "concluido" ? "default" : "destructive"}
                      className={item.status === "concluido" ? "bg-primary/20 text-primary border border-primary/30" : ""}
                    >
                      {item.status === "concluido" ? "Concluído" : "Erro"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    {item.pdfUrl && (
                      <Button variant="ghost" size="sm" asChild>
                        <a href={item.pdfUrl} download>
                          <Download className="h-4 w-4 mr-1" />
                          PDF
                        </a>
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="ml-2"
                      onClick={async () => {
                        try {
                          setLoadingId(item.id);
                          await regenPdf(item.id);
                          const updated = await getHistorico();
                          setItems(updated);
                        } catch (err) {
                          window.alert("Falha ao re-gerar o PDF. Verifique se o backend esta rodando em http://localhost:8000");
                        } finally {
                          setLoadingId(null);
                        }
                      }}
                      disabled={loadingId === item.id}
                    >
                      {loadingId === item.id ? "Gerando..." : "Re-gerar PDF"}
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
