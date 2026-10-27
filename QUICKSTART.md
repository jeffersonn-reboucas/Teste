# Guia de Início Rápido

## 1️⃣ Instalação

```bash
# 1. Entre no diretório do projeto
cd libras-visual-builder

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Verifique a instalação
python setup.py
```

## 2️⃣ Configuração da API

Escolha **uma** das opções abaixo:

### Opção A: Google Gemini (Recomendado - tem tier gratuito)

1. Acesse: https://makersuite.google.com/app/apikey
2. Crie uma API key
3. Configure:
   ```bash
   # Windows (PowerShell)
   $env:GEMINI_API_KEY = "sua-key-aqui"
   
   # Linux/Mac
   export GEMINI_API_KEY="sua-key-aqui"
   ```

### Opção B: OpenAI (Melhor qualidade)

1. Acesse: https://platform.openai.com/api-keys
2. Crie uma API key
3. Configure:
   ```bash
   # Windows (PowerShell)
   $env:OPENAI_API_KEY = "sua-key-aqui"
   
   # Linux/Mac
   export OPENAI_API_KEY="sua-key-aqui"
   ```

### Opção C: Replicate (Mais customizável)

1. Acesse: https://replicate.com/account/api-tokens
2. Crie um token
3. Configure:
   ```bash
   # Windows (PowerShell)
   $env:REPLICATE_API_TOKEN = "seu-token-aqui"
   
   # Linux/Mac
   export REPLICATE_API_TOKEN="seu-token-aqui"
   ```

## 3️⃣ Primeira Execução

```bash
streamlit run src/app.py
```

A aplicação abrirá automaticamente no navegador em http://localhost:8501

## 4️⃣ Primeiro Sinal

### Passo 1: Prepare suas imagens

**Item A (Referência):** Escaneie ou fotografe uma página do dicionário de Libras (Capovilla)

**Item B (Personagem):** Crie ou use um personagem 2D:
- Fundo transparente (PNG)
- Pose neutra
- Braços ao lado do corpo
- Estilo limpo e claro

### Passo 2: Na interface

1. **Coluna 1 (Item A):**
   - Upload da imagem de referência
   - Preencha: Nome do sinal, categoria
   - Selecione os parâmetros (configuração de mão, ponto de articulação, etc.)

2. **Coluna 2 (Item B):**
   - Upload do seu personagem
   - Dê um nome para salvá-lo

3. **Coluna 3 (Item C):**
   - Clique em "🚀 Gerar Ilustração"
   - Aguarde o processamento
   - Visualize e baixe o resultado
   - Salve no catálogo

## 5️⃣ Próximos Passos

✅ Gere mais sinais usando o mesmo personagem  
✅ Organize por categorias no catálogo  
✅ Exporte o catálogo em CSV  
✅ Use as imagens em materiais pedagógicos  

## ⚠️ Problemas Comuns

**"API key não encontrada"**
- Verifique se configurou a variável de ambiente
- Ou insira diretamente na sidebar da aplicação

**"Módulo não encontrado"**
- Execute: `pip install -r requirements.txt`

**"Erro ao gerar imagem"**
- Confirme que as duas imagens foram carregadas
- Verifique se a API key é válida
- Veja os logs no terminal para mais detalhes

## 📚 Documentação Completa

Leia o `README.md` para documentação detalhada e `EXAMPLES.md` para exemplos de código.

---

**Pronto para começar! 🎉**
