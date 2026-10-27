# Libras Visual Builder 🤟

Sistema inteligente para geração de ilustrações 2D de sinais de Libras usando IA Multimodal, com integração direta ao Dicionário de Libras (Capovilla).

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-Educational-green?style=for-the-badge)

## 🎯 Visão Geral

O **Libras Visual Builder** automatiza a criação de materiais pedagógicos visuais de Libras, permitindo:

- 🔍 **Busca inteligente** no Dicionário Capovilla (2847 páginas)
- 🤖 **Extração automática** de parâmetros dos sinais via Regex
- 🎨 **Geração com IA** de ilustrações personalizadas
- 📚 **Catalogação** e organização de sinais
- ☁️ **Deploy em nuvem** via Streamlit Cloud

## ✨ Funcionalidades

### 🔎 Busca no Dicionário PDF
- Busca por termo ou navegação direta por página
- Renderização de páginas como imagens
- Extração automática de parâmetros do sinal

### 🤖 Geração com IA Multimodal
- Suporte para **Google Gemini**, **OpenAI GPT-4** e **Replicate**
- Fusão de pose técnica (Item A) + personagem customizado (Item B)
- Prompts estruturados com descrições anatômicas detalhadas

### 📊 Catalogação Inteligente
- Organização por 5 parâmetros de Capovilla
- Exportação para CSV
- Filtros e busca avançada

## 🚀 Deploy no Streamlit Cloud

Este projeto está configurado para deploy automático no **Streamlit Community Cloud**.

### Pré-requisitos

1. Conta no [Streamlit Cloud](https://streamlit.io/cloud)
2. PDFs no Google Drive com compartilhamento público
3. Repositório no GitHub

### Instruções Completas

Veja o guia detalhado em: **[DEPLOY_STREAMLIT_CLOUD.md](DEPLOY_STREAMLIT_CLOUD.md)**

### Deploy Rápido

1. **Fork/Clone** este repositório
2. **Configure os PDFs** no Google Drive (compartilhamento público)
3. **Obtenha os File IDs** dos PDFs
4. **Deploy no Streamlit Cloud** e adicione os secrets:

```toml
[gdrive]
capovilla_file_id = "SEU_FILE_ID_AQUI"
config_mao_file_id = "SEU_FILE_ID_AQUI"
```

5. **Acesse** sua aplicação em: `https://seu-app.streamlit.app`

## 💻 Executar Localmente

### Instalação

```bash
git clone https://github.com/seu-usuario/libras-visual-builder.git
cd libras-visual-builder
pip install -r requirements.txt
```

### Configurar PDFs

Opção 1: Colocar PDFs localmente:
```bash
# Criar pasta
mkdir -p data/pdfs

# Copiar PDFs para a pasta
cp "caminho/para/Dicionario capovilla completo.pdf" data/pdfs/
cp "caminho/para/configuraçao de mao.pdf" data/pdfs/
```

Opção 2: Usar Google Drive (configurar file_ids em `src/pdf_manager.py`)

### Executar

```bash
streamlit run src/app.py
```

Acesse: http://localhost:8501

## 📁 Estrutura do Projeto

```
libras-visual-builder/
├── src/
│   ├── app.py                  # Interface Streamlit
│   ├── prompt_engine.py        # Gerador de prompts IA
│   ├── ai_generator.py         # Integração com APIs IA
│   ├── pdf_extractor.py        # Extração de PDFs
│   ├── pdf_manager.py          # Gerenciador Google Drive
│   ├── catalog.py              # Sistema de catalogação
│   └── models.py               # Modelos de dados
├── data/
│   ├── pdfs/                   # PDFs (não versionados)
│   └── catalog.json            # Catálogo de sinais
├── assets/
│   ├── referencias/            # Imagens de referência
│   └── personagens/            # Personagens 2D
├── output/                     # Imagens geradas
├── .streamlit/
│   ├── config.toml            # Configuração Streamlit
│   └── secrets.toml.example   # Template de secrets
├── requirements.txt
├── .gitignore
└── README.md
```

## 🛠️ Tecnologias

- **Python 3.8+**
- **Streamlit** - Interface web
- **PyMuPDF (fitz)** - Leitura de PDFs
- **Pillow** - Processamento de imagens
- **gdown** - Download do Google Drive
- **OpenAI / Gemini / Replicate** - IA Multimodal

## 📖 Documentação Adicional

- [DEPLOY_STREAMLIT_CLOUD.md](DEPLOY_STREAMLIT_CLOUD.md) - Guia completo de deploy
- [PDF_INTEGRATION.md](PDF_INTEGRATION.md) - Integração com PDFs
- [EXAMPLES.md](EXAMPLES.md) - Exemplos de código
- [QUICKSTART.md](QUICKSTART.md) - Início rápido
- [COMANDOS.md](COMANDOS.md) - Comandos úteis

## 🎓 Como Usar

### Fluxo Básico

1. **Coluna 1 (Item A)**: Busque o sinal no dicionário ou faça upload da imagem
2. **Coluna 2 (Item B)**: Selecione ou faça upload do personagem 2D
3. **Coluna 3 (Item C)**: Configure a API key e gere a ilustração
4. **Salvar**: Baixe ou adicione ao catálogo

### Extração Automática de Parâmetros

Quando você busca um sinal no PDF, o sistema automaticamente:
- ✅ Identifica a configuração de mão
- ✅ Detecta orientação (palma, dedos)
- ✅ Localiza ponto de articulação
- ✅ Extrai tipo de movimento
- ✅ Preenche os campos da interface

## 🔑 API Keys

O sistema suporta três provedores de IA:

### Google Gemini (Recomendado para começar)
- [Obter API Key](https://makersuite.google.com/app/apikey)
- Tier gratuito disponível

### OpenAI
- [Obter API Key](https://platform.openai.com/api-keys)
- Melhor qualidade de geração

### Replicate
- [Obter Token](https://replicate.com/account/api-tokens)
- Modelos customizáveis

Configure via interface ou secrets do Streamlit Cloud.

## ⚠️ Notas Importantes

### Sobre os PDFs

- **Não estão no repositório** (245 MB total)
- Baixados automaticamente do Google Drive na primeira execução
- Cache permanente após o download inicial
- Lazy loading: apenas páginas necessárias são carregadas

### Limitações do Streamlit Cloud

- **1 GB RAM** no plano gratuito
- PDFs usam lazy loading para economizar memória
- Primeira execução pode demorar 5-10 min (download dos PDFs)

## 🤝 Contribuindo

Contribuições são bem-vindas! Este projeto é educacional e voltado para facilitar a criação de materiais pedagógicos de Libras.

## 📄 Licença

Projeto educacional para criação de materiais pedagógicos de Libras.

## 🙏 Créditos

- **Dicionário de Libras**: Capovilla
- **Configurações de Mão**: Charles Lary Marques Ferraz
- Interface desenvolvida com Streamlit

## 📧 Suporte

Para dúvidas sobre:
- **Deploy**: Veja [DEPLOY_STREAMLIT_CLOUD.md](DEPLOY_STREAMLIT_CLOUD.md)
- **PDFs**: Veja [PDF_INTEGRATION.md](PDF_INTEGRATION.md)
- **Código**: Abra uma issue no GitHub

---

**Desenvolvido para educadores, estudantes e pesquisadores de Libras** 🤟

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://seu-app.streamlit.app)
