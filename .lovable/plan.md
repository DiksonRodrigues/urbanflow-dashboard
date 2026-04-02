
# Dashboard de Gestão de Consultas Urbanísticas

## Visão Geral
Sistema interno (SPA) para processar números de IPTU e gerar relatórios de zoneamento, com comunicação simulada com backend Python local.

## Design
- **Dark mode padrão** com accent verde esmeralda (`emerald-500/600`)
- Layout responsivo com sidebar de status + área principal
- Componentes Lucide React + Tailwind CSS

## Páginas e Componentes

### 1. Layout Principal (`Dashboard.tsx`)
- Header com logo/título "Consulta Urbanística" e indicador de conexão com backend
- Navegação por tabs: **Nova Consulta** | **Histórico**

### 2. Nova Consulta - Área de Input
- Textarea para múltiplos IPTUs (um por linha)
- Botão grande "Iniciar Automação" em verde esmeralda
- Validação básica do formato de IPTU

### 3. Stepper de Status
- Barra lateral/central com 4 etapas visuais:
  1. Acessando Prefeitura
  2. Aguardando Captcha (com ícone pulsante)
  3. Extraindo Dados
  4. Gerando PDF
- Indicador visual (ícone animado) para etapa ativa
- Lista de IPTUs em processamento com status individual

### 4. Modal de Captcha (Human-in-the-loop)
- Modal que aparece automaticamente quando status = "Aguardando Captcha"
- Exibe imagem do captcha (placeholder simulado)
- Input com auto-focus para digitar resposta
- Submit com Enter → envia para backend e fecha modal
- **Notificação sonora (beep)** + badge visual pulsante ao ativar

### 5. Editor de Revisão
- Campos editáveis com dados extraídos: Zona de Uso, Coeficiente, Recuo, Gabarito, etc.
- Botão "Confirmar e Gerar PDF" em verde esmeralda
- Aparece após extração bem-sucedida de cada IPTU

### 6. Tabela de Histórico (Cache)
- Colunas: Data, IPTU, Zona de Uso, Status (badge colorido), Ações
- Botão "Download PDF" por linha
- Filtro/busca por IPTU
- Ordenação por data

### 7. Serviços e Estado
- Hook `useConsulta` gerenciando estado global das consultas
- Funções fetch simuladas apontando para `http://localhost:8000`:
  - `POST /consultar` — inicia consulta
  - `GET /status/{id}` — polling de status
  - `POST /captcha/{id}` — envia resposta do captcha
  - `POST /confirmar/{id}` — confirma dados editados e gera PDF
  - `GET /historico` — lista histórico
- Simulação com dados mock para funcionar sem backend
- ID de consulta vinculado a cada processo de captcha

### 8. Tema e CSS
- Variáveis CSS customizadas para dark mode com emerald accent
- Animações sutis no stepper e no badge de captcha
