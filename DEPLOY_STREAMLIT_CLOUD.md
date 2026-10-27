# 🚀 Deploy no Streamlit Community Cloud

## Pré-requisitos

1. ✅ Conta no GitHub
2. ✅ Conta no [Streamlit Community Cloud](https://streamlit.io/cloud)
3. ✅ PDFs no Google Drive com compartilhamento público

---

## 📋 Passo a Passo

### 1. Preparar Google Drive

#### a) Fazer Upload dos PDFs
1. Acesse: https://drive.google.com/drive/folders/1GyE1k4Qb5Of2mAhIIYMaD3TOaJnLSB1-
2. Faça upload dos arquivos:
   - `Dicionario capovilla completo.pdf` (212 MB)
   - `configuraçao de mao.pdf` (33 MB)

#### b) Configurar Compartilhamento Público
Para **cada arquivo**:
1. Clique com botão direito → **Compartilhar**
2. Clique em **Alterar** (ao lado de "Restrito")
3. Selecione: **Qualquer pessoa com o link**
4. Escolha: **Leitor**
5. Clique em **Concluído**

#### c) Obter File IDs
Para **cada arquivo**:
1. Abra o arquivo no Google Drive
2. Copie a URL (formato: `https://drive.google.com/file/d/FILE_ID_AQUI/view`)
3. Extraia o **FILE_ID** (parte entre `/d/` e `/view`)

Exemplo:
```
URL: https://drive.google.com/file/d/1ABC123xyz789DEF/view
FILE_ID: 1ABC123xyz789DEF
```

Anote os IDs:
- **Dicionário Capovilla**: `_________________`
- **Configurações de Mão**: `_________________`

---

### 2. Preparar Repositório GitHub

#### a) Criar Repositório
1. Acesse: https://github.com/new
2. Nome: `libras-visual-builder`
3. Deixe como **Público**
4. **NÃO** adicione README, .gitignore ou licença (já temos)
5. Clique em **Create repository**

#### b) Fazer Push do Código
No terminal/PowerShell:

```powershell
cd C:\Users\Jeffe\libras-visual-builder

# Inicializar git (se ainda não foi)
git init

# Adicionar todos os arquivos
git add .

# Fazer commit
git commit -m "Initial commit - Libras Visual Builder com integração PDF"

# Adicionar remote (substitua SEU_USUARIO pelo seu username do GitHub)
git remote add origin https://github.com/SEU_USUARIO/libras-visual-builder.git

# Fazer push
git branch -M main
git push -u origin main
```

---

### 3. Deploy no Streamlit Cloud

#### a) Acessar Streamlit Cloud
1. Vá para: https://share.streamlit.io/
2. Faça login com GitHub

#### b) Criar Nova Aplicação
1. Clique em **"New app"**
2. Preencha:
   - **Repository**: `SEU_USUARIO/libras-visual-builder`
   - **Branch**: `main`
   - **Main file path**: `src/app.py`
3. Clique em **"Advanced settings"**

#### c) Configurar Secrets
Na seção **Secrets**, cole o seguinte (substituindo os FILE_IDs):

```toml
[gdrive]
capovilla_file_id = "COLE_O_FILE_ID_DO_DICIONARIO_AQUI"
config_mao_file_id = "COLE_O_FILE_ID_DAS_CONFIGURACOES_AQUI"
```

#### d) Deploy
1. Clique em **"Deploy!"**
2. Aguarde 2-5 minutos (primeira vez é mais demorado)
3. O app estará disponível em: `https://SEU_APP.streamlit.app`

---

### 4. Atualizar pdf_manager.py com File IDs

Depois de obter os File IDs do Google Drive, atualize o arquivo:

```python
# Em src/pdf_manager.py, linha ~15
GOOGLE_DRIVE_FILES = {
    "Dicionario capovilla completo.pdf": {
        "file_id": "COLE_O_FILE_ID_AQUI",  # ← Adicionar
        "filename": "Dicionario capovilla completo.pdf",
        "size_mb": 212
    },
    "configuraçao de mao.pdf": {
        "file_id": "COLE_O_FILE_ID_AQUI",  # ← Adicionar
        "filename": "configuraçao de mao.pdf",
        "size_mb": 33
    }
}
```

Depois faça commit e push:
```powershell
git add src/pdf_manager.py
git commit -m "Adicionar File IDs do Google Drive"
git push
```

O Streamlit Cloud redeployará automaticamente.

---

## 🔧 Configuração Opcional: API Keys

Se quiser configurar API keys no Streamlit Cloud:

1. Vá para **App settings** → **Secrets**
2. Adicione:

```toml
[api_keys]
gemini_api_key = "sua_key_aqui"
openai_api_key = "sua_key_aqui"
replicate_api_token = "seu_token_aqui"
```

3. No código, ler assim:
```python
import streamlit as st
api_key = st.secrets.get("api_keys", {}).get("gemini_api_key", "")
```

---

## 📊 Primeira Execução no Cloud

**IMPORTANTE**: Na primeira vez que alguém acessar o app:

1. ⏳ O sistema baixará os PDFs do Google Drive (~245 MB)
2. ⏳ Isso pode levar **5-10 minutos**
3. ✅ Após o download, os PDFs ficam em cache
4. ✅ Próximos acessos serão instantâneos

**Mostrar progresso ao usuário:**
- O Streamlit exibirá mensagens de status do download
- Barra de progresso do gdown será visível

---

## 🐛 Troubleshooting

### Erro: "PDF não encontrado"
**Causa**: Download do Google Drive falhou

**Solução**:
1. Verifique se os File IDs estão corretos em `pdf_manager.py`
2. Confirme que os arquivos estão com compartilhamento **público**
3. Teste os links diretamente: `https://drive.google.com/uc?id=FILE_ID`

### Erro: "Permission denied" no Google Drive
**Solução**:
1. Vá no Google Drive → Arquivo → Compartilhar
2. Mude para "Qualquer pessoa com o link"
3. Aguarde 5 minutos para propagar
4. Tente novamente

### App muito lento na primeira vez
**Normal**: Download de 245 MB leva tempo. Próximas execuções serão rápidas.

### Erro de memória no Streamlit Cloud
**Causa**: Streamlit Cloud tem limite de 1 GB RAM (plano gratuito)

**Solução temporária**:
- O app usa lazy loading, então só carrega páginas sob demanda
- Se persistir, considere hospedar os PDFs em outro lugar ou usar Streamlit Cloud pago

---

## 🔄 Atualizar o App

Para fazer updates no código:

```powershell
# Fazer alterações no código
git add .
git commit -m "Descrição das mudanças"
git push
```

O Streamlit Cloud redeployará automaticamente em ~1-2 minutos.

---

## 🌐 Acessar do Chromebook

Depois do deploy, você terá uma URL tipo:
```
https://libras-visual-builder.streamlit.app
```

Salve essa URL nos favoritos do Chromebook e acesse de qualquer lugar! 🎉

---

## 📱 Compartilhar com Outros

A URL é pública! Qualquer pessoa pode acessar:
- Professores de Libras
- Estudantes
- Pesquisadores

Sem necessidade de instalação ou configuração. ✨

---

**Pronto para deploy! 🚀**
