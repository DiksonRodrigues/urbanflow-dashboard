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
import { getHistorico } from "@/services/api";

export function HistoricoTable() {
  const [items, setItems] = useState<HistoricoItem[]>([]);
  const [filtro, setFiltro] = useState("");

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
          className="pl-9"
        />
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Data</TableHead>
              <TableHead>IPTU</TableHead>
              <TableHead>Zona de Uso</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Ações</TableHead>
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
                <TableRow key={item.id}>
                  <TableCell className="font-mono text-xs">
                    {new Date(item.data).toLocaleDateString("pt-BR")}
                  </TableCell>
                  <TableCell className="font-mono">{item.iptu}</TableCell>
                  <TableCell>{item.zonaDeUso || "—"}</TableCell>
                  <TableCell>
                    <Badge
                      variant={item.status === "concluido" ? "default" : "destructive"}
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
