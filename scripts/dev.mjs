import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";

const isWin = process.platform === "win32";
const repoRoot = process.cwd();
const backendDir = join(repoRoot, "backend");

const pythonCandidates = [
  process.env.PYTHON,
  "C:\\Users\\amoza\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
  "python",
].filter(Boolean);

const python = pythonCandidates.find((p) => existsSync(p)) || "python";

const run = (cmd, args, cwd) =>
  spawn(cmd, args, { cwd, stdio: "inherit", shell: false });

const backend = run(
  python,
  ["-m", "uvicorn", "main:app", "--reload", "--port", "8000"],
  backendDir
);

const npmCmd = isWin ? "npm.cmd" : "npm";
const frontend = run(npmCmd, ["run", "dev"], repoRoot);

const shutdown = (signal) => {
  if (backend && !backend.killed) backend.kill(signal);
  if (frontend && !frontend.killed) frontend.kill(signal);
};

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));
