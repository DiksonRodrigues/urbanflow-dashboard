import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StatusStepper } from "@/components/StatusStepper";
import { CaptchaModal } from "@/components/CaptchaModal";
import { ResultadoCard } from "@/components/ResultadoCard";
import { HistoricoTable } from "@/components/HistoricoTable";
import { useConsulta } from "@/hooks/useConsulta";
import {
  Building2,
  Play,
  Wifi,
  History,
  FileSearch,
} from "lucide-react";

export default function Dashboard() {
  const [iptusText, setIptusText] = useState("");
  const {
    consultas,
    isProcessing,
    captchaConsulta,
    iniciar,
    responderCaptcha,
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

  const consultasAtivas = consultas.filter(
    (c) => c.status !== "concluido" && c.status !== "erro"
  );
  const consultasComDados = consultas.filter((c) => c.dadosExtraidos);

  const hasBackend = consultas.length > 0;
  const erros = consultas.filter((c) => c.status === "erro").length;

  return (
    <div className="app-shell">
      <header className="border-b border-white/10 bg-background/60 backdrop-blur-xl">
        <div className="container py-8 space-y-6">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-primary/90 to-accent/80 p-[2px] shadow-lg shadow-primary/20">
                <div className="h-full w-full rounded-[14px] bg-background/80 backdrop-blur flex items-center justify-center">
                  <Building2 className="h-6 w-6 text-primary" />
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-[0.65rem] uppercase tracking-[0.35em] text-muted-foreground">
                  Urbanflow
                </p>
                <h1 className="font-display text-2xl md:text-3xl text-foreground">
                  Consulta Urbanística
                </h1>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary" className="bg-white/5 border border-white/10 text-foreground/80">
                Fluxo assistido
              </Badge>
              <Badge variant="secondary" className="bg-white/5 border border-white/10 text-foreground/80">
                Captcha guiado
              </Badge>
              <Badge variant="secondary" className="bg-white/5 border border-white/10 text-foreground/80">
                PDF validado
              </Badge>
              {hasBackend && (
                <Badge variant="secondary" className="bg-white/5 border border-white/10 text-foreground/80">
                  Backend conectado
                </Badge>
              )}
            </div>
          </div>
          <p className="text-sm md:text-base text-muted-foreground max-w-2xl animate-rise">
            Centralize consultas por IPTU com automação, revisão humana e histórico auditável. Interface pensada para equipes que precisam de precisão e velocidade.
          </p>
        </div>
      </header>

      <main className="container py-10 space-y-8">
        <Tabs defaultValue="nova" className="space-y-8">
          <TabsList className="h-auto w-fit rounded-full border border-white/10 bg-white/5 p-1.5">
            <TabsTrigger
              value="nova"
              className="gap-2 rounded-full px-4 py-2 data-[state=active]:bg-white/10 data-[state=active]:text-foreground"
            >
              <FileSearch className="h-4 w-4" />
              Nova Consulta
            </TabsTrigger>
            <TabsTrigger
              value="historico"
              className="gap-2 rounded-full px-4 py-2 data-[state=active]:bg-white/10 data-[state=active]:text-foreground"
            >
              <History className="h-4 w-4" />
              Histórico
            </TabsTrigger>
          </TabsList>

          <TabsContent value="nova">
            <div className="grid gap-8 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
              <div className="space-y-6">
                <Card className="border-white/10 bg-card/70 shadow-[0_20px_60px_-40px_rgba(0,0,0,0.7)] backdrop-blur animate-rise">
                  <CardHeader className="pb-3 space-y-2">
                    <CardTitle className="text-base text-foreground flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-primary shadow-[0_0_12px_rgba(45,212,191,0.8)]" />
                      Números de IPTU (SQL)
                    </CardTitle>
                    <p className="text-xs text-muted-foreground">
                      Cole um IPTU por linha para iniciar o fluxo automatizado.
                    </p>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Textarea
                      value={iptusText}
                      onChange={(e) => setIptusText(e.target.value)}
                      placeholder={"045.018.0042-1\n012.045.0018-9\n078.032.0091-3"}
                      rows={6}
                      className="font-mono resize-none bg-background/60 border-white/10 focus-visible:ring-primary/40"
                    />
                    <Button
                      onClick={handleIniciar}
                      disabled={!iptusText.trim() || isProcessing}
                      className="w-full h-12 text-base font-semibold bg-gradient-to-r from-primary to-accent text-slate-950 shadow-lg shadow-primary/20 hover:from-primary/90 hover:to-accent/90"
                      size="lg"
                    >
                      <Play className="h-5 w-5 mr-2" />
                      Iniciar Automação
                    </Button>
                  </CardContent>
                </Card>

                {consultasComDados.map((c) => (
                  <ResultadoCard key={c.id} consulta={c} />
                ))}
              </div>

              <div className="space-y-6 animate-rise-delay">
                <Card className="border-white/10 bg-card/70 backdrop-blur">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base text-foreground flex items-center gap-2">
                      <Wifi className="h-4 w-4 text-primary" />
                      Progresso em tempo real
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {consultasAtivas.length === 0 ? (
                      <div className="rounded-xl border border-dashed border-white/10 bg-background/40 p-6 text-center">
                        <p className="text-sm text-muted-foreground">
                          Nenhuma consulta em andamento
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-5">
                        {consultasAtivas.map((c) => (
                          <StatusStepper key={c.id} consulta={c} />
                        ))}
                      </div>
                    )}

                    {consultas.filter((c) => c.status === "concluido").length > 0 && (
                      <div className="mt-5 rounded-lg border border-white/10 bg-background/40 px-4 py-3">
                        <p className="text-xs text-muted-foreground flex items-center gap-2">
                          <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                          {consultas.filter((c) => c.status === "concluido").length} consulta(s) concluída(s)
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card className="border-white/10 bg-card/60 backdrop-blur">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm text-foreground">Status do processo</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm text-muted-foreground">
                    <div className="flex items-center justify-between">
                      <span>Captchas pendentes</span>
                      <span className="text-foreground font-medium">
                        {consultas.filter((c) => c.status === "aguardando_captcha").length}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Em revisão</span>
                      <span className="text-foreground font-medium">
                        {consultas.filter((c) => c.status === "revisao").length}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Finalizadas</span>
                      <span className="text-foreground font-medium">
                        {consultas.filter((c) => c.status === "concluido").length}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Com erro</span>
                      <span className="text-foreground font-medium">
                        {erros}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="historico">
            <Card className="border-white/10 bg-card/70 backdrop-blur">
              <CardHeader className="pb-3">
                <CardTitle className="text-base text-foreground">Histórico de consultas</CardTitle>
              </CardHeader>
              <CardContent>
                <HistoricoTable />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      <CaptchaModal
        consulta={captchaConsulta}
        onSubmit={responderCaptcha}
      />
    </div>
  );
}
