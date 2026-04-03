import { useState, useCallback, useRef, useEffect } from "react";
import type { Consulta } from "@/types/consulta";
import * as api from "@/services/api";

export function useConsulta() {
  const [consultas, setConsultas] = useState<Consulta[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [captchaConsultaId, setCaptchaConsultaId] = useState<string | null>(null);
  const pollingRef = useRef<Record<string, ReturnType<typeof setInterval>>>({});

  const playBeep = useCallback(() => {
    try {
      const ctx = new AudioContext();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = 880;
      osc.type = "sine";
      gain.gain.value = 0.3;
      osc.start();
      osc.stop(ctx.currentTime + 0.2);
    } catch {
      // audio not available
    }
  }, []);

  const updateConsulta = useCallback((id: string, updates: Partial<Consulta>) => {
    setConsultas((prev) =>
      prev.map((c) => (c.id === id ? { ...c, ...updates } : c))
    );
  }, []);

  const startPolling = useCallback(
    (id: string) => {
      if (pollingRef.current[id]) return;

      pollingRef.current[id] = setInterval(async () => {
        try {
          const status = await api.getStatus(id);
          updateConsulta(id, status);

          if (status.status === "aguardando_captcha" && status.captchaImage) {
            setCaptchaConsultaId(id);
            playBeep();
          }

          if (status.status === "concluido" || status.status === "erro") {
            clearInterval(pollingRef.current[id]);
            delete pollingRef.current[id];

            setConsultas((prev) => {
              const allDone = prev.every(
                (c) => c.id === id ? true : c.status === "concluido" || c.status === "erro"
              );
              if (allDone) setIsProcessing(false);
              return prev;
            });
          }
        } catch {
          // backend offline: stop polling to avoid spam
          clearInterval(pollingRef.current[id]);
          delete pollingRef.current[id];
        }
      }, 2000);
    },
    [updateConsulta, playBeep]
  );

  const iniciar = useCallback(
    async (iptus: string[]) => {
      setIsProcessing(true);
      const novas = await api.iniciarConsulta(iptus);
      setConsultas((prev) => [...prev, ...novas]);
      novas.forEach((c) => startPolling(c.id));
    },
    [startPolling]
  );

  const responderCaptcha = useCallback(
    async (id: string, resposta: string) => {
      setCaptchaConsultaId(null);
      updateConsulta(id, { status: "extraindo_dados" });

      const result = await api.enviarCaptcha(id, resposta);
      updateConsulta(id, result);
    },
    [updateConsulta]
  );


  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      Object.values(pollingRef.current).forEach(clearInterval);
    };
  }, []);

  const captchaConsulta = consultas.find((c) => c.id === captchaConsultaId);

  return {
    consultas,
    isProcessing,
    captchaConsulta,
    iniciar,
    responderCaptcha,
  };
}
