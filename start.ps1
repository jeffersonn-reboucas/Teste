# Script de Instalação e Inicialização
# Execute este script no PowerShell para instalar dependências e iniciar o Streamlit

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LIBRAS VISUAL BUILDER - SETUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navegar para o diretório do projeto
Set-Location "C:\Users\Jeffe\libras-visual-builder"
Write-Host "[1/4] Navegando para o diretório do projeto..." -ForegroundColor Yellow
Write-Host "      Diretório: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# Instalar dependências
Write-Host "[2/4] Instalando dependências..." -ForegroundColor Yellow
Write-Host "      Isso pode levar alguns minutos..." -ForegroundColor Gray
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "      ✓ Dependências instaladas com sucesso!" -ForegroundColor Green
} else {
    Write-Host "      ✗ Erro ao instalar dependências" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Verificar PDFs
Write-Host "[3/4] Verificando PDFs..." -ForegroundColor Yellow

$pdf_capovilla = "C:\Users\Jeffe\Downloads\Dicionario capovilla completo.pdf"
$pdf_config = "C:\Users\Jeffe\Downloads\configuraçao de mao.pdf"

if (Test-Path $pdf_capovilla) {
    $size_mb = [math]::Round((Get-Item $pdf_capovilla).Length / 1MB, 2)
    Write-Host "      ✓ Dicionário Capovilla encontrado ($size_mb MB)" -ForegroundColor Green
} else {
    Write-Host "      ⚠ Dicionário Capovilla NÃO encontrado" -ForegroundColor Yellow
    Write-Host "        Esperado em: $pdf_capovilla" -ForegroundColor Gray
    Write-Host "        (Você ainda pode usar upload manual)" -ForegroundColor Gray
}

if (Test-Path $pdf_config) {
    $size_mb = [math]::Round((Get-Item $pdf_config).Length / 1MB, 2)
    Write-Host "      ✓ PDF de Configurações encontrado ($size_mb MB)" -ForegroundColor Green
} else {
    Write-Host "      ⚠ PDF de Configurações NÃO encontrado" -ForegroundColor Yellow
    Write-Host "        Esperado em: $pdf_config" -ForegroundColor Gray
}
Write-Host ""

# Iniciar Streamlit
Write-Host "[4/4] Iniciando servidor Streamlit..." -ForegroundColor Yellow
Write-Host "      A aplicação abrirá no navegador em instantes..." -ForegroundColor Gray
Write-Host "      URL: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "      Pressione Ctrl+C para parar o servidor" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

streamlit run src/app.py
