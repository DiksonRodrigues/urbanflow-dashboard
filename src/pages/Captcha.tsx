import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { obterCaptcha, enviarCaptcha, getStatus } from "@/services/api";

const CaptchaPage = () => {
  const { id } = useParams();
  const [image, setImage] = useState<string | null>(null);
  const [resposta, setResposta] = useState("");
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      if (!id) return;
      try {
        const st = await getStatus(id);
        if (!active) return;
        setStatus(st.status);
        if (st.captchaImage) {
          setImage(st.captchaImage);
        } else {
          const img = await obterCaptcha(id);
          if (active) setImage(img);
        }
      } catch {
        if (active) setStatus("erro");
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => {
      active = false;
    };
  }, [id]);

  const handleSubmit = async () => {
    if (!id || !resposta.trim()) return;
    setLoading(true);
    try {
      const st = await enviarCaptcha(id, resposta.trim());
      setStatus(st.status);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <main className="container py-12">
        <Card className="max-w-lg mx-auto border-white/10 bg-card/80 backdrop-blur">
          <CardHeader>
            <CardTitle className="text-base">Resolver Captcha</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading && <p className="text-sm text-muted-foreground">Carregando...</p>}
            {!loading && status !== "aguardando_captcha" && (
              <p className="text-sm text-muted-foreground">
                Status atual: <span className="text-foreground">{status}</span>
              </p>
            )}
            {image && (
              <div className="w-full rounded-md border border-white/10 bg-background/60 p-4 flex items-center justify-center min-h-[120px]">
                <img src={image} alt="Captcha" className="max-h-28 object-contain" />
              </div>
            )}
            <Input
              value={resposta}
              onChange={(e) => setResposta(e.target.value)}
              placeholder="Digite o captcha..."
              className="text-center text-lg font-mono tracking-widest bg-background/60 border-white/10 focus-visible:ring-primary/40"
            />
            <Button onClick={handleSubmit} className="w-full bg-gradient-to-r from-primary to-accent text-slate-950" disabled={!resposta.trim()}>
              Enviar Captcha
            </Button>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default CaptchaPage;
