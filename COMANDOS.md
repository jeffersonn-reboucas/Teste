# Comandos Rápidos para Windows PowerShell

## 🚀 INICIAR O SISTEMA

### Opção 1: Script Automático (Recomendado)
```powershell
cd C:\Users\Jeffe\libras-visual-builder
.\start.ps1
```

### Opção 2: Passo a Passo
```powershell
# 1. Navegar para o diretório
cd C:\Users\Jeffe\libras-visual-builder

# 2. Instalar dependências (apenas primeira vez)
pip install -r requirements.txt

# 3. Instalar PyMuPDF para PDFs (apenas primeira vez)
pip install PyMuPDF

# 4. Iniciar o Streamlit
streamlit run src/app.py
```

## 🔑 Configurar API Keys (Opcional - se não tiver nos .env)

### Google Gemini (Gratuito)
```powershell
$env:GEMINI_API_KEY = "sua-api-key-aqui"
```

### OpenAI
```powershell
$env:OPENAI_API_KEY = "sua-api-key-aqui"
```

### Replicate
```powershell
$env:REPLICATE_API_TOKEN = "seu-token-aqui"
```

## 📊 Verificar Instalação

```powershell
# Ver versão do Python
python --version

# Ver pacotes instalados
pip list | Select-String -Pattern "streamlit|PyMuPDF|Pillow"

# Testar importação
python -c "import streamlit; import fitz; print('OK')"
```

## 🧪 Executar Demo (Sem Interface)

```powershell
python demo.py
```

## 📁 Estrutura de Arquivos

```powershell
# Listar arquivos do projeto
Get-ChildItem -Recurse -Include *.py | Select-Object FullName

# Ver tamanho dos PDFs
Get-Item "C:\Users\Jeffe\Downloads\Dicionario capovilla completo.pdf" | Select-Object Name, @{Name="SizeMB";Expression={[math]::Round($_.Length / 1MB, 2)}}
Get-Item "C:\Users\Jeffe\Downloads\configuraçao de mao.pdf" | Select-Object Name, @{Name="SizeMB";Expression={[math]::Round($_.Length / 1MB, 2)}}
```

## 🔧 Troubleshooting

### Se o Streamlit não iniciar:
```powershell
# Reinstalar Streamlit
pip uninstall streamlit -y
pip install streamlit

# Limpar cache
streamlit cache clear
```

### Se PyMuPDF não instalar:
```powershell
# Tentar instalar com nome alternativo
pip install pymupdf
```

### Ver logs de erro:
```powershell
# Executar com modo verbose
streamlit run src/app.py --logger.level=debug
```

## 🛑 Parar o Servidor

Pressione `Ctrl + C` no terminal onde o Streamlit está rodando.

## 🌐 Acessar a Interface

Depois de iniciar, abra no navegador:
- **Local**: http://localhost:8501
- **Rede**: http://192.168.x.x:8501 (o IP será mostrado no terminal)

---

## ⚡ Comando Único (Tudo de Uma Vez)

```powershell
cd C:\Users\Jeffe\libras-visual-builder; if (-not (Test-Path "venv")) { python -m venv venv }; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt; streamlit run src/app.py
```

---

**Pronto! O servidor estará rodando e a interface abrirá automaticamente no navegador. 🎉**
