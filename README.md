# Urbanflow Dashboard

Dashboard front-end para acompanhar consultas urbanísticas por IPTU, com fluxo de automação, captcha, revisão de dados e geração de PDF. O app funciona em modo simulado quando o backend não está disponível, permitindo testar a experiência completa no navegador.

**Stack**
- Vite + React + TypeScript
- Tailwind CSS + shadcn/ui (Radix)
- React Router + React Query

**Funcionalidades**
- Nova consulta: colar múltiplos IPTUs e iniciar automação
- Captcha: modal com alerta e envio da resposta
- Revisão: edição dos dados extraídos antes de gerar o PDF
- Histórico: tabela com filtros e download de PDF

**Backend**
- O front-end tenta acessar `http://localhost:8000`.
- Se não houver backend, o app usa dados simulados para o fluxo completo.

**Como rodar**
1. Instalar dependências:
```bash
npm.cmd install
```
2. Iniciar o ambiente de desenvolvimento:
```bash
npm.cmd run dev
```
3. Acessar o endereço exibido no terminal (normalmente `http://localhost:5173`).

**Scripts úteis**
- `npm.cmd run dev`: inicia o servidor de desenvolvimento
- `npm.cmd run build`: build de produção
- `npm.cmd run preview`: pré-visualização do build
- `npm.cmd run lint`: ESLint
- `npm.cmd run test`: testes (Vitest)
