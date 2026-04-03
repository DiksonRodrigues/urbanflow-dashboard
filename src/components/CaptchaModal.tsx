import { useEffect, useRef, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ShieldAlert } from "lucide-react";
import type { Consulta } from "@/types/consulta";

interface Props {
  consulta: Consulta | undefined;
  onSubmit: (id: string, resposta: string) => void;
}

export function CaptchaModal({ consulta, onSubmit }: Props) {
  const [resposta, setResposta] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const isOpen = !!consulta;

  useEffect(() => {
    if (isOpen) {
      setResposta("");
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const handleSubmit = () => {
    if (consulta && resposta.trim()) {
      onSubmit(consulta.id, resposta.trim());
      setResposta("");
    }
  };

  return (
    <Dialog open={isOpen}>
      <DialogContent
        className="sm:max-w-md border-white/10 bg-card/80 backdrop-blur"
        onInteractOutside={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-primary animate-pulse-glow" />
            Captcha Requerido
          </DialogTitle>
          <DialogDescription>
            IPTU: <span className="font-mono">{consulta?.iptu}</span> — Digite o
            texto exibido na imagem abaixo.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col items-center gap-4 py-2">
          <div className="w-full rounded-md border border-white/10 bg-background/60 p-4 flex items-center justify-center min-h-[100px]">
            <img
              src={consulta?.captchaImage || "/placeholder.svg"}
              alt="Captcha"
              className="max-h-24 object-contain"
            />
          </div>

          <Input
            ref={inputRef}
            value={resposta}
            onChange={(e) => setResposta(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            placeholder="Digite o captcha..."
            className="text-center text-lg font-mono tracking-widest bg-background/60 border-white/10 focus-visible:ring-primary/40"
          />

          <Button onClick={handleSubmit} className="w-full bg-gradient-to-r from-primary to-accent text-slate-950" disabled={!resposta.trim()}>
            Enviar Captcha
          </Button>

          {consulta?.id && (
            <a
              href={`/captcha/${consulta.id}`}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-muted-foreground underline underline-offset-4"
            >
              Abrir captcha em nova janela
            </a>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
