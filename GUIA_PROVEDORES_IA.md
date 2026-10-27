# 🤖 Guia Completo de Provedores de IA

## 📊 Comparativo de Provedores

| Provider | Qualidade | Velocidade | Custo | Melhor Para |
|----------|-----------|------------|-------|-------------|
| **OpenAI DALL-E 3** | ⭐⭐⭐⭐⭐ | ⚡⚡ | 💰💰💰 | Alta fidelidade, consistência |
| **Google Imagen** | ⭐⭐⭐⭐ | ⚡⚡⚡ | 💰💰 | Análise multimodal |
| **Replicate SDXL** | ⭐⭐⭐⭐ | ⚡⚡⚡ | 💰 | Custo-benefício, flexível |
| **SDXL Lightning** | ⭐⭐⭐ | ⚡⚡⚡⚡⚡ | 💰 | Rapidez, protótipos |
| **SDXL Cartoon** | ⭐⭐⭐⭐ | ⚡⚡⚡ | 💰 | Estilo ilustração 2D |
| **Stability AI** | ⭐⭐⭐⭐ | ⚡⚡⚡ | 💰💰 | API oficial, confiável |

---

## 🎯 Escolha o Provider Certo

### Para Materiais Pedagógicos Profissionais
**Recomendado: OpenAI DALL-E 3**
- ✅ Melhor qualidade geral
- ✅ Consistência visual alta
- ✅ Entende instruções complexas
- ❌ Mais caro (~$0.04/imagem HD)

### Para Prototipagem Rápida
**Recomendado: Replicate SDXL Lightning**
- ✅ Geração em 2-5 segundos
- ✅ Muito barato (~$0.0032/imagem)
- ✅ Iteração rápida
- ❌ Qualidade um pouco inferior

### Para Estilo Cartoon/Ilustração
**Recomendado: Replicate SDXL Cartoon**
- ✅ Otimizado para ilustrações 2D
- ✅ Estilo pedagógico
- ✅ Barato
- ✅ Bom para Libras

### Para Melhor Custo-Benefício
**Recomendado: Replicate SDXL (padrão)**
- ✅ Qualidade excelente
- ✅ Preço acessível (~$0.0095/imagem)
- ✅ Controle fino
- ✅ Diversos modelos customizados

---

## 🔑 Como Obter API Keys

### 1. OpenAI DALL-E 3

**Passo a Passo:**
1. Acesse: https://platform.openai.com/signup
2. Crie uma conta ou faça login
3. Vá para: https://platform.openai.com/api-keys
4. Clique em **"Create new secret key"**
5. Copie a key (começa com `sk-...`)
6. Configure no app: `OPENAI_API_KEY`

**Preços:**
- DALL-E 3 Standard (1024x1024): $0.040/imagem
- DALL-E 3 HD (1024x1024): $0.080/imagem
- Crédito inicial: $5 grátis (novos usuários)

**Limites:**
- 50 imagens/minuto

---

### 2. Google Gemini (Imagen)

**Passo a Passo:**
1. Acesse: https://makersuite.google.com/app/apikey
2. Faça login com conta Google
3. Clique em **"Get API key"** ou **"Create API key"**
4. Copie a key
5. Configure no app: `GEMINI_API_KEY`

**Preços:**
- Gemini 1.5 Flash: Gratuito (até 1500 req/dia)
- Imagen (quando disponível): A definir

**Nota:** Imagen 3 ainda está em preview limitado. Por ora, o sistema usa Gemini para análise multimodal.

---

### 3. Replicate

**Passo a Passo:**
1. Acesse: https://replicate.com/signin
2. Crie conta (pode usar GitHub)
3. Vá para: https://replicate.com/account/api-tokens
4. Clique em **"Create token"**
5. Copie o token (começa com `r8_...`)
6. Configure no app: `REPLICATE_API_TOKEN`

**Preços (por imagem):**
- SDXL Standard: ~$0.0095
- SDXL Lightning (4-step): ~$0.0032
- SDXL Cartoon: ~$0.0095

**Crédito inicial:**
- $5 grátis para novos usuários

**Limites:**
- Pay-as-you-go, sem limite fixo

---

### 4. Stability AI

**Passo a Passo:**
1. Acesse: https://platform.stability.ai/
2. Crie uma conta
3. Vá para: https://platform.stability.ai/account/keys
4. Clique em **"Create API Key"**
5. Copie a key (começa com `sk-...`)
6. Configure no app: `STABILITY_API_KEY`

**Preços:**
- Stable Diffusion XL: $0.008/imagem (1024x1024)
- Stable Diffusion 3: $0.035/imagem

**Crédito inicial:**
- 25 créditos grátis (~3125 imagens SDXL)

---

## 💰 Comparativo de Custos

### Para 100 Imagens:

| Provider | Modelo | Custo | Tempo Total |
|----------|--------|-------|-------------|
| OpenAI | DALL-E 3 HD | $8.00 | ~15 min |
| OpenAI | DALL-E 3 Standard | $4.00 | ~15 min |
| Replicate | SDXL Standard | $0.95 | ~15 min |
| Replicate | SDXL Lightning | $0.32 | ~5 min |
| Replicate | SDXL Cartoon | $0.95 | ~15 min |
| Stability AI | SDXL | $0.80 | ~15 min |

---

## 🔄 Estratégia de Uso: Alternância Inteligente

### Fluxo Recomendado:

```
1. Prototipagem Inicial
   └─> Replicate SDXL Lightning (rápido e barato)
   
2. Refinamento
   └─> Replicate SDXL Cartoon (estilo pedagógico)
   
3. Versão Final
   └─> OpenAI DALL-E 3 HD (máxima qualidade)
```

### Quando Alternar:

✅ **Use DALL-E 3 quando:**
- Material será impresso profissionalmente
- Precisa de máxima consistência
- Cliente paga pelo projeto

✅ **Use Replicate SDXL quando:**
- Criar múltiplas variações
- Testar conceitos
- Volume alto (100+ imagens)
- Orçamento limitado

✅ **Use SDXL Lightning quando:**
- Iteração rápida
- Validação de conceito
- Demonstrações ao vivo

---

## 🛠️ Configuração de API Keys no App

### Opção 1: Via Interface (Temporário)
1. Abra o app
2. Na barra lateral, selecione o provider
3. Cole a API key no campo
4. Use durante a sessão

### Opção 2: Variáveis de Ambiente (Permanente)

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:GEMINI_API_KEY = "..."
$env:REPLICATE_API_TOKEN = "r8_..."
$env:STABILITY_API_KEY = "sk-..."
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="..."
export REPLICATE_API_TOKEN="r8_..."
export STABILITY_API_KEY="sk-..."
```

### Opção 3: Streamlit Cloud (Deploy)
1. Vá em **App Settings** → **Secrets**
2. Adicione:

```toml
[api_keys]
openai_api_key = "sk-..."
gemini_api_key = "..."
replicate_api_token = "r8_..."
stability_api_key = "sk-..."
```

---

## 🎨 Qualidade do Prompt: O Segredo

### ✅ Todos os Provedores Recebem o MESMO Prompt

O `PromptEngine` gera um prompt estruturado e detalhado que é enviado **identicamente** para todos os provedores. Isso garante:

1. ✅ **Consistência**: Mesmo resultado visual entre providers
2. ✅ **Anatomia Correta**: Descrições detalhadas de configuração de mão
3. ✅ **Identidade Visual**: 100% do estilo do personagem
4. ✅ **Reprodutibilidade**: Mesmos parâmetros = mesma pose

### Exemplo de Prompt Gerado:

```
Você é um especialista em ilustração técnica de Língua Brasileira de Sinais (Libras).

TAREFA: Gerar uma ilustração 2D que combine:
- A POSE e CONFIGURAÇÃO DE MÃO da imagem de referência do sinal de Libras
- O ESTILO VISUAL e ANATOMIA do personagem fornecido

PARÂMETROS DO SINAL "OBRIGADO":

📍 Configuração de Mão:
- Mão aberta

⚠️ DETALHES ANATÔMICOS DA(S) MÃO(S) (CRÍTICO):
• Mão aberta: Todos os dedos estendidos e separados, palma visível.

📍 Ponto de Articulação:
- Boca

📍 Movimento:
- Para frente

📍 Orientação:
- Palma para cima

[...]
```

Este prompt é otimizado para cada provider, mas mantém a essência idêntica.

---

## 🔍 Troubleshooting

### Erro: "API key inválida"
**Solução:**
1. Verifique se copiou a key completa
2. Confirme que não há espaços extras
3. Teste a key diretamente na plataforma do provider

### Erro: "Quota exceeded"
**Solução:**
1. Verifique seu saldo na plataforma
2. Adicione créditos ou
3. **Alterne para outro provider** (botão "🔄 Alternar Provider")

### Erro: "Rate limit"
**Solução:**
1. Aguarde 1 minuto
2. Reduza a frequência de geração
3. Use provider com limite maior (Replicate)

### Qualidade baixa
**Solução:**
1. Use DALL-E 3 HD
2. Verifique qualidade das imagens de entrada (Item A e B)
3. Ajuste manualmente os parâmetros do sinal

---

## 🚀 Dicas Pro

1. **Teste com Lightning primeiro** - Valide o conceito rápido
2. **Use Cartoon para volume** - Melhor custo-benefício para Libras
3. **DALL-E 3 para versão final** - Máxima qualidade
4. **Mantenha múltiplas keys** - Alterne quando acabar crédito
5. **Monitore custos** - Configure alertas nas plataformas

---

## 📞 Suporte dos Provedores

- **OpenAI**: https://help.openai.com/
- **Google**: https://ai.google.dev/support
- **Replicate**: https://replicate.com/docs/support
- **Stability AI**: https://platform.stability.ai/docs

---

**Última atualização**: 2026-10-27  
**Versão do sistema**: 2.0 com suporte multi-provider
