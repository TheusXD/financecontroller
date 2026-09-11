-- ==============================================================================
-- SISTEMA DE GESTÃO FINANCEIRA PESSOAL - ESTRUTURA SUPABASE (POSTGRESQL)
-- Projeto: gestao-financeira (Região: sa-east-1)
-- ==============================================================================

-- 1. TABELA PRINCIPAL DE TRANSAÇÕES
CREATE TABLE IF NOT EXISTS public.transacoes (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    data_transacao TIMESTAMPTZ DEFAULT NOW(),
    estabelecimento TEXT NOT NULL,
    valor NUMERIC(10, 2) NOT NULL,
    categoria TEXT DEFAULT 'Outros',
    tipo TEXT DEFAULT 'Nubank Push'
);

-- Índices para otimização de consultas analíticas do dashboard
CREATE INDEX IF NOT EXISTS idx_transacoes_data ON public.transacoes(data_transacao DESC);
CREATE INDEX IF NOT EXISTS idx_transacoes_categoria ON public.transacoes(categoria);
CREATE INDEX IF NOT EXISTS idx_transacoes_tipo ON public.transacoes(tipo);

-- 2. FUNÇÃO E TRIGGER DE AUTOCATEGORIZAÇÃO AUTOMÁTICA
-- Quando o MacroDroid ou o Dashboard insere uma transação sem categoria definida (ou como 'Outros'),
-- esta função identifica palavras-chave no nome do estabelecimento e atribui a categoria correta.
CREATE OR REPLACE FUNCTION public.autocategorizar_transacao()
RETURNS TRIGGER AS $$
DECLARE
    nome_norm TEXT;
BEGIN
    IF NEW.categoria IS NULL OR TRIM(NEW.categoria) = '' OR NEW.categoria = 'Outros' THEN
        nome_norm := lower(coalesce(NEW.estabelecimento, ''));
        
        -- Regras de classificação inteligente
        IF nome_norm ~* '(posto|shell|ipiranga|petrobras|gasolina|combustivel|combustível|auto posto|uber|99app|99pop|99 tecnologia|estacionamento|pedagio|pedágio|sem parar|veloe)' THEN
            NEW.categoria := 'Transporte / Combustível';
            
        ELSIF nome_norm ~* '(ifood|ze delivery|zé delivery|restaurante|burger|burguer|pizza|pizzaria|lanche|lanches|mcdonald|subway|habib|outback|bar |padaria|panificadora|cafe|café|cacau show|sorvete|acai|açaí|churrascaria|pastel)' THEN
            NEW.categoria := 'Alimentação';
            
        ELSIF nome_norm ~* '(mercado|supermercado|hipermercado|atacadao|atacadão|assai|assaí|carrefour|pao de acucar|pão de açúcar|dia |big |sams|extra|hortifruti|sacolao|sacolão|quitanda)' THEN
            NEW.categoria := 'Supermercado';
            
        ELSIF nome_norm ~* '(farmacia|farmácia|drogaria|drogasil|droga raia|raia|pacheco|pague menos|panvel|hospital|clinica|clínica|medico|médico|laboratorio|laboratório|consulta|exame|odonto)' THEN
            NEW.categoria := 'Saúde';
            
        ELSIF nome_norm ~* '(caixinha|reserva|investimento|nuinvest|aporte|tesouro|cdb|renda fixa)' THEN
            NEW.categoria := 'Reserva de Emergência';
            
        ELSIF nome_norm ~* '(parcela|divida|dívida|emprestimo|empréstimo|renegociacao|renegociação)' THEN
            NEW.categoria := 'Dívidas';
            
        ELSIF nome_norm ~* '(netflix|spotify|amazon prime|disney|hbo|max|steam|playstation|xbox|cinema|cinemark|cinepolis|ingresso)' THEN
            NEW.categoria := 'Lazer & Streaming';
            
        ELSIF nome_norm ~* '(amazon|mercado livre|shopee|shein|magalu|magazine luiza|zara|renner|riachuelo|c&a|lojas americanas)' THEN
            NEW.categoria := 'Compras & Vestuário';
            
        ELSIF nome_norm ~* '(enel|cpfl|light|cemig|sabesp|copasa|sanepar|vivo|claro|tim|oi|internet|condominio|condomínio|aluguel)' THEN
            NEW.categoria := 'Moradia & Contas';
            
        ELSE
            NEW.categoria := 'Outros';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_autocategorizar_transacao ON public.transacoes;
CREATE TRIGGER trg_autocategorizar_transacao
BEFORE INSERT OR UPDATE ON public.transacoes
FOR EACH ROW
EXECUTE FUNCTION public.autocategorizar_transacao();

-- 3. TABELA DE CONFIGURAÇÕES FINANCEIRAS (PARÂMETROS DE NEGÓCIO)
CREATE TABLE IF NOT EXISTS public.configuracoes_financeiras (
    id INT PRIMARY KEY DEFAULT 1,
    renda_liquida NUMERIC(10, 2) DEFAULT 3300.00,
    custo_aluguel NUMERIC(10, 2) DEFAULT 1200.00,
    custo_energia NUMERIC(10, 2) DEFAULT 100.00,
    custo_agua NUMERIC(10, 2) DEFAULT 0.00,
    custo_seguro_carro NUMERIC(10, 2) DEFAULT 168.00,
    custo_parcela_divida NUMERIC(10, 2) DEFAULT 150.00,
    meta_reserva_emergencia NUMERIC(10, 2) DEFAULT 5000.00,
    aporte_mensal_reserva NUMERIC(10, 2) DEFAULT 400.00,
    teto_semanal_combustivel NUMERIC(10, 2) DEFAULT 150.00,
    teto_semanal_alimentacao NUMERIC(10, 2) DEFAULT 200.00,
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unico_registro CHECK (id = 1)
);

INSERT INTO public.configuracoes_financeiras (id)
VALUES (1)
ON CONFLICT (id) DO NOTHING;

-- 4. POLÍTICAS DE SEGURANÇA (ROW LEVEL SECURITY - RLS)
ALTER TABLE public.transacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.configuracoes_financeiras ENABLE ROW LEVEL SECURITY;

-- Políticas para a tabela transacoes
DROP POLICY IF EXISTS "Permitir insercao anonima" ON public.transacoes;
CREATE POLICY "Permitir insercao anonima" ON public.transacoes
    FOR INSERT TO anon WITH CHECK (true);

DROP POLICY IF EXISTS "Permitir leitura anonima" ON public.transacoes;
CREATE POLICY "Permitir leitura anonima" ON public.transacoes
    FOR SELECT TO anon USING (true);

DROP POLICY IF EXISTS "Permitir atualizacao anonima" ON public.transacoes;
CREATE POLICY "Permitir atualizacao anonima" ON public.transacoes
    FOR UPDATE TO anon USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Permitir exclusao anonima" ON public.transacoes;
CREATE POLICY "Permitir exclusao anonima" ON public.transacoes
    FOR DELETE TO anon USING (true);

-- Políticas para a tabela configuracoes_financeiras
DROP POLICY IF EXISTS "Permitir leitura anonima configuracoes" ON public.configuracoes_financeiras;
CREATE POLICY "Permitir leitura anonima configuracoes" ON public.configuracoes_financeiras
    FOR SELECT TO anon USING (true);

DROP POLICY IF EXISTS "Permitir atualizacao anonima configuracoes" ON public.configuracoes_financeiras;
CREATE POLICY "Permitir atualizacao anonima configuracoes" ON public.configuracoes_financeiras
    FOR UPDATE TO anon USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Permitir insercao anonima configuracoes" ON public.configuracoes_financeiras;
CREATE POLICY "Permitir insercao anonima configuracoes" ON public.configuracoes_financeiras
    FOR INSERT TO anon WITH CHECK (true);
