# 💳 Sistema de Gestão Financeira Pessoal (100% Nuvem)

Sistema autônomo de inteligência financeira pessoal desenvolvido para rodar **100% na nuvem** (sem depender de computador ligado 24h). O sistema captura notificações push do **Nubank** em tempo real via **MacroDroid (Android)**, armazena e autocategoriza os dados via **PostgreSQL / Supabase**, e disponibiliza um dashboard analítico interativo no **Streamlit Community Cloud**.

---

## 🏛️ Arquitetura da Solução

```mermaid
graph TD
    A[📱 Celular Android / Nubank] -->|Notificação Push Cartão/Pix| B[🤖 MacroDroid]
    B -->|HTTP POST REST API| C[(⚡ Supabase PostgreSQL)]
    C -->|Trigger PL/pgSQL| D[🏷️ Autocategorização Automática]
    E[📊 Streamlit Community Cloud] -->|Consulta & Gestão CRUD| C
    E -->|Ajuste de Metas & Lançamento Manual| C
```

---

## 💰 Parâmetros Orçamentários de Negócio

- **Renda Líquida Mensal:** R$ 3.300,00
- **Custos Fixos Totais:** R$ 1.618,00
  - Aluguel: R$ 1.200,00
  - Energia Elétrica: R$ 100,00 (estimado)
  - Água: R$ 0,00
  - Seguro do Carro: R$ 168,00
  - Parcelas de Dívidas: R$ 150,00
- **Saldo Disponível para Variáveis e Metas:** R$ 1.682,00
- **Metas Ativas:**
  1. **Reserva de Emergência:** Meta de R$ 5.000,00 com aporte mensal planejado de R$ 400,00.
  2. **Teto Semanal de Combustível:** R$ 150,00 / semana (com alertas visuais).
  3. **Teto Semanal de Alimentação:** R$ 200,00 / semana (com alertas visuais).
  4. **Quitação de Dívida:** Acompanhamento mensal de amortização.

---

## 📁 Estrutura de Arquivos do Projeto

```text
d:/Controle financeiro/
├── .streamlit/
│   ├── config.toml               # Configuração do tema escuro moderno
│   ├── secrets.toml              # Credenciais locais de conexão com Supabase
│   └── secrets.toml.example      # Modelo para configuração no Streamlit Cloud
├── app.py                        # Aplicação principal do Dashboard em Streamlit
├── requirements.txt              # Dependências Python para deploy
├── supabase_setup.sql            # Script SQL completo (tabelas, índices, triggers, RLS)
├── macrodroid_guide.md           # Guia passo a passo da automação no celular Android
└── README.md                     # Documentação geral do sistema
```

---

## 🚀 Como Fazer o Deploy no Streamlit Community Cloud (Grátis)

O Streamlit Community Cloud permite hospedar o dashboard gratuitamente direto do seu repositório no GitHub:

### Passo 1: Subir o projeto para o GitHub
1. Crie um novo repositório (público ou privado) no seu GitHub (ex: `gestao-financeira`).
2. Suba todos os arquivos desta pasta:
   ```bash
   git init
   git add .
   git commit -m "feat: initial commit sistema de gestao financeira"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/gestao-financeira.git
   git push -u origin main
   ```

### Passo 2: Publicar no Streamlit Cloud
1. Acesse [share.streamlit.io](https://share.streamlit.io/) e faça login com sua conta do GitHub.
2. Clique em **"New app"**.
3. Selecione o repositório, branch (`main`) e arquivo principal (`app.py`).
4. Clique em **"Advanced settings"** ➔ seção **Secrets**:
   Cole as variáveis de ambiente:
   ```toml
   SUPABASE_URL = "https://gwvffsdaembngybulsso.supabase.co"
   SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd3dmZmc2RhZW1ibmd5YnVsc3NvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkxNjA4OTUsImV4cCI6MjEwNDczNjg5NX0.zspVrVnKITia7lEpD1D-0OaE7-XOju0pscx9QirqUlY"
   ```
5. Clique em **Deploy**! Em instantes seu dashboard estará online 24/7 com link compartilhável e responsivo para celular e computador.

---

## 📱 Configuração da Automação no Celular (MacroDroid)

Para configurar a interceptação automática de compras do Nubank no Android:
1. Abra o arquivo [macrodroid_guide.md](macrodroid_guide.md).
2. Siga as instruções para configurar:
   - O gatilho de notificação do Nubank.
   - As regex de extração de valor e nome do estabelecimento.
   - A requisição HTTP POST para o endpoint REST do Supabase.

---

## 🏷️ Autocategorização Inteligente no Banco

O banco de dados PostgreSQL conta com um trigger nativo que roda a cada inserção:
- Estabelecimentos com termos como `Shell`, `Posto`, `Uber` são automaticamente categorizados como **Transporte / Combustível**.
- `iFood`, `Burger`, `Restaurante`, `Padaria` viram **Alimentação**.
- `Carrefour`, `Mercado`, `Atacadão` viram **Supermercado**.
- `Caixinha`, `Reserva`, `Investimento` viram **Reserva de Emergência**.
- Qualquer classificação pode ser ajustada instantaneamente direto na tabela do Dashboard!
