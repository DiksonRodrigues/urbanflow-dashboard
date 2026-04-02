import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StatusStepper } from "@/components/StatusStepper";
import { CaptchaModal } from "@/components/CaptchaModal";
import { EditorRevisao } from "@/components/EditorRevisao";
import { HistoricoTable } from "@/components/HistoricoTable";
import { useConsulta } from "@/hooks/useConsulta";
import {
  Building2,
  Play,
  Wifi,
  WifiOff,
  History,
  FileSearch,
} from "lucide-react";

export default function Dashboard() {
  const [iptusText, setIptusText] = useState("");
  const [backendOnline] = useState(false);
  const {
    consultas,
    isProcessing,
    captchaConsulta,
    iniciar,
    responderCaptcha,
    confirmar,
  } = useConsulta();

  const handleIniciar = () => {
    const iptus = iptusText
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);
    if (iptus.length === 0) return;
    iniciar(iptus);
    setIptusText("");
  };

  const consultasRevisao = consultas.filter((c) => c.status === "revisao");
  const consultasAtivas = consultas.filter(
    (c) => c.status !== "concluido" && c.status !== "erro"
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur sticky top-0 z-40">
        <div className="container flex h-14 items-center justify-between">
          <div className="flex items-center gap-3">
            <Building2 className="h-6 w-6 text-primary" />
            <h1 className="text-lg font-bold tracking-tight">
              Consulta Urbanística
            </h1>
          </div>
          <Badge
            variant={backendOnline ? "default" : "secondary"}
            className="gap-1.5"
          >
            {backendOnline ? (
              <Wifi className="h-3 w-3" />
            ) : (
              <WifiOff className="h-3 w-3" />
            )}
            {backendOnline ? "Backend Online" : "Modo Simulado"}
          </Badge>
        </div>
      </header>

      <main className="container py-6">
        <Tabs defaultValue="nova" className="space-y-6">
          <TabsList>
            <TabsTrigger value="nova" className="gap-1.5">
              <FileSearch className="h-4 w-4" />
              Nova Consulta
            </TabsTrigger>
            <TabsTrigger value="historico" className="gap-1.5">
              <History className="h-4 w-4" />
              Histórico
            </TabsTrigger>
          </TabsList>

          <TabsContent value="nova">
            <div className="grid gap-6 lg:grid-cols-3">
              {/* Input Area */}
              <div className="lg:col-span-2 space-y-6">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">
                      Números de IPTU (SQL)
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Textarea
                      value={iptusText}
                      onChange={(e) => setIptusText(e.target.value)}
                      placeholder={"045.018.0042-1\n012.045.0018-9\n078.032.0091-3"}
                      rows={5}
                      className="font-mono resize-none"
                    />
                    <Button
                      onClick={handleIniciar}
                      disabled={!iptusText.trim() || isProcessing}
                      className="w-full h-12 text-base font-semibold"
                      size="lg"
                    >
                      <Play className="h-5 w-5 mr-2" />
                      Iniciar Automação
                    </Button>
                  </CardContent>
                </Card>

                {/* Revisão editors */}
                {consultasRevisao.map((c) => (
                  <EditorRevisao
                    key={c.id}
                    consulta={c}
                    onConfirmar={confirmar}
                  />
                ))}
              </div>

              {/* Status Sidebar */}
              <div>
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">
                      Progresso
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {consultasAtivas.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-6">
                        Nenhuma consulta em andamento
                      </p>
                    ) : (
                      <div className="space-y-5">
                        {consultasAtivas.map((c) => (
                          <StatusStepper key={c.id} consulta={c} />
                        ))}
                      </div>
                    )}

                    {/* Show completed count */}
                    {consultas.filter((c) => c.status === "concluido").length > 0 && (
                      <div className="mt-4 pt-4 border-t">
                        <p className="text-xs text-muted-foreground">
                          ✓{" "}
                          {consultas.filter((c) => c.status === "concluido").length}{" "}
                          consulta(s) concluída(s)
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="historico">
            <HistoricoTable />
          </TabsContent>
        </Tabs>
      </main>

      {/* Captcha Modal */}
      <CaptchaModal
        consulta={captchaConsulta}
        onSubmit={responderCaptcha}
      />
    </div>
  );
}
