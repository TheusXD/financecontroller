# Guia Completo de Automação: Nubank + MacroDroid + Supabase REST API

Este guia detalha o passo a passo exato para interceptar as notificações do Nubank no Android através do aplicativo **MacroDroid** e enviá-las em tempo real diretamente para o banco de dados Supabase, sem depender de nenhum computador ligado.

---

## 1. Dados de Conexão com o Supabase

Guarde estes dados para preencher na ação de requisição HTTP do MacroDroid:

- **Endpoint URL:**
  ```text
  https://gwvffsdaembngybulsso.supabase.co/rest/v1/transacoes
  ```
- **Método HTTP:** `POST`
- **Headers Obrigatórios:**
  - `Content-Type`: `application/json`
  - `apikey`: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd3dmZmc2RhZW1ibmd5YnVsc3NvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkxNjA4OTUsImV4cCI6MjEwNDczNjg5NX0.zspVrVnKITia7lEpD1D-0OaE7-XOju0pscx9QirqUlY`
  - `Authorization`: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd3dmZmc2RhZW1ibmd5YnVsc3NvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkxNjA4OTUsImV4cCI6MjEwNDczNjg5NX0.zspVrVnKITia7lEpD1D-0OaE7-XOju0pscx9QirqUlY`
  - `Prefer`: `return=minimal`

---

## 2. Estrutura de Variáveis Locais no MacroDroid

Dentro da macro que você criará no MacroDroid, crie as seguintes **Variáveis Locais**:

| Nome da Variável | Tipo | Descrição |
|---|---|---|
| `notif_texto` | String | Recebe o texto completo da notificação (`[not_text]`) |
| `valor_bruto` | String | Extrai o valor com vírgula (ex: `45,90`) |
| `valor_formatado` | String / Decimal | Converte a vírgula para ponto (ex: `45.90`) para SQL |
| `estabelecimento` | String | Nome limpo da loja / destinatário |

---

## 3. Passo a Passo da Criação da Macro

### Passo 1: Gatilho (Trigger)
1. Clique em **Adicionar Gatilho** (`+` verde).
2. Vá em **Eventos do Dispositivo** ➔ **Notificação** ➔ **Notificação Recebida**.
3. Selecione **Selecionar Aplicativo(s)** e marque o **Nubank**.
4. Em **Conteúdo do Texto**, selecione **Qualquer**.
5. Clique em **OK**.

---

### Passo 2: Ações (Actions)

Adicione as ações em sequência:

#### Ação 2.1: Capturar o texto da notificação
1. **Adicionar Ação** (`+` azul) ➔ **MacroDroid Específico** ➔ **Definir Variável**.
2. Escolha a variável `notif_texto`.
3. Defina o valor como `[not_text]` (código mágico de texto da notificação).

---

#### Ação 2.2: Extrair o Valor e Estabelecimento via Regex
O Nubank utiliza dois padrões principais de notificação:

##### Padrão A - Compras no Cartão (Crédito / Débito):
> Exemplo: *"Compra de R$ 45,90 no Supermercado Carrefour aprovada"* ou *"Você realizou uma compra de R$ 23,50 em Padaria Central"*

- **Expressão Regular (Regex) para o Valor:**
  ```regex
  R\$\s*(\d+[.,]\d{2})
  ```
  - No MacroDroid: **Manipulação de Texto** ➔ **Extração de Texto** (ou **Regex**).
  - Texto de origem: `{lv=notif_texto}`
  - Regex: `R\$\s*(\d+[.,]\d{2})`
  - Salvar no grupo 1 na variável `valor_bruto`.

- **Expressão Regular (Regex) para o Estabelecimento:**
  ```regex
  (?:em|no|na|para)\s+([A-Za-z0-9\s\.\-_*]+?)(?:\s+aprovad[ao]|\.|$|\s+via)
  ```
  - Texto de origem: `{lv=notif_texto}`
  - Salvar o grupo 1 na variável `estabelecimento`.

##### Padrão B - Pix Enviado / Transferências:
> Exemplo: *"Você transferiu R$ 150,00 para João da Silva."* ou *"Transferência de R$ 150,00 enviada para Fulano"*

- Se a notificação contiver a palavra "transferiu" ou "Transferência", a regex de estabelecimento pode capturar o nome após `para`:
  ```regex
  para\s+([A-Za-z0-9\s\.\-_*]+?)(?:\.|$|\s+via)
  ```

---

#### Ação 2.3: Formatar o Valor para Ponto Decimal (Padrão PostgreSQL)
O banco Supabase espera números no formato `45.90` (ponto em vez de vírgula).
1. **Adicionar Ação** ➔ **Manipulação de Texto** ➔ **Substituição de Texto**.
2. Texto de origem: `{lv=valor_bruto}`
3. Texto a localizar: `,`
4. Substituir por: `.`
5. Salvar o resultado na variável `valor_formatado`.

---

#### Ação 2.4: Requisição HTTP POST para o Supabase
1. **Adicionar Ação** ➔ **Conectividade** ➔ **Requisição HTTP (HTTP Request)**.
2. Configure exatamente assim:
   - **Método de Requisição:** `POST`
   - **URL:**
     ```text
     https://gwvffsdaembngybulsso.supabase.co/rest/v1/transacoes
     ```
   - **Headers (Cabeçalhos HTTP):** Adicione 4 cabeçalhos:
     ```text
     Content-Type: application/json
     apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd3dmZmc2RhZW1ibmd5YnVsc3NvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkxNjA4OTUsImV4cCI6MjEwNDczNjg5NX0.zspVrVnKITia7lEpD1D-0OaE7-XOju0pscx9QirqUlY
     Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd3dmZmc2RhZW1ibmd5YnVsc3NvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkxNjA4OTUsImV4cCI6MjEwNDczNjg5NX0.zspVrVnKITia7lEpD1D-0OaE7-XOju0pscx9QirqUlY
     Prefer: return=minimal
     ```
   - **Tipo de Conteúdo do Corpo:** `application/json`
   - **Corpo da Requisição (Body):**
     ```json
     {
       "estabelecimento": "{lv=estabelecimento}",
       "valor": {lv=valor_formatado},
       "tipo": "Nubank Push"
     }
     ```
3. Salve a ação.

---

## 4. Por que a Autocategorização Funciona Sem Configuração Adicional?

Você não precisa tentar categorizar no MacroDroid!
O banco PostgreSQL no Supabase já possui um **Trigger inteligente em PL/pgSQL** ativado:
- Se o estabelecimento contiver palavras como `"Posto"`, `"Shell"`, `"Ipiranga"`, `"Uber"`, ele salva automaticamente como **Transporte / Combustível**.
- Se contiver `"iFood"`, `"Burger"`, `"Restaurante"`, `"Padaria"`, salva como **Alimentação**.
- Se contiver `"Carrefour"`, `"Mercado"`, `"Atacadão"`, salva como **Supermercado**.
- Se for uma loja desconhecida, classifica como **Outros** e você pode ajustar com 1 clique no Dashboard do Streamlit.

---

## 5. Como Testar Manualmente no Celular

Para testar se tudo está funcionando antes de fazer uma compra real:
1. No MacroDroid, crie uma ação temporária de teste definindo a variável `notif_texto` como:
   `"Compra de R$ 38,50 no Posto Shell aprovada"`
2. Execute as ações da macro manualmente (botão "Testar Ações" no menu da macro).
3. Abra o Dashboard no Streamlit e observe a nova linha inserida com o valor R$ 38,50 categorizada automaticamente em **Transporte / Combustível**!
