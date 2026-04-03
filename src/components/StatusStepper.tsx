import { Check, Circle, Loader2, AlertTriangle } from "lucide-react";
import type { Consulta } from "@/types/consulta";
import { CONSULTA_STEPS } from "@/types/consulta";
import { cn } from "@/lib/utils";

const statusOrder = ["acessando_prefeitura", "aguardando_captcha", "extraindo_dados", "gerando_pdf", "concluido"];

function getStepIndex(status: string) {
  if (status === "revisao") return 2; // between extraindo and gerando
  if (status === "concluido") return 4;
  return statusOrder.indexOf(status);
}

interface Props {
  consulta: Consulta;
}

export function StatusStepper({ consulta }: Props) {
  const currentIndex = getStepIndex(consulta.status);

  return (
    <div className="space-y-2 rounded-xl border border-white/10 bg-background/40 p-4">
      <p className="text-xs font-mono text-muted-foreground mb-2 truncate">
        IPTU: {consulta.iptu}
      </p>
      <div className="space-y-0">
        {CONSULTA_STEPS.map((step, i) => {
          const isActive = statusOrder.indexOf(step.key) === currentIndex;
          const isDone = currentIndex > statusOrder.indexOf(step.key);
          const isWaiting = step.key === "aguardando_captcha" && isActive;
          const isError = consulta.status === "erro";

          return (
            <div key={step.key} className="flex items-center gap-3 py-1.5">
              <div
                className={cn(
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 transition-all",
                  isDone && "border-primary bg-primary text-primary-foreground",
                  isActive && !isDone && "border-primary text-primary",
                  isWaiting && "animate-pulse-glow border-primary text-primary",
                  !isActive && !isDone && "border-muted-foreground/30 text-muted-foreground/40",
                  isError && isActive && "border-destructive text-destructive"
                )}
              >
                {isDone ? (
                  <Check className="h-3.5 w-3.5" />
                ) : isActive ? (
                  isWaiting ? (
                    <AlertTriangle className="h-3.5 w-3.5" />
                  ) : (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  )
                ) : (
                  <Circle className="h-2.5 w-2.5" />
                )}
              </div>
              <span
                className={cn(
                  "text-sm transition-colors",
                  isDone && "text-foreground",
                  isActive && "text-primary font-medium",
                  !isActive && !isDone && "text-muted-foreground"
                )}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
