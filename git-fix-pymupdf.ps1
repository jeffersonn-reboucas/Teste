# CORREÇÃO: PyMuPDF para Streamlit Cloud
# Execute no PowerShell

cd C:\Users\Jeffe\libras-visual-builder

# Adicionar correção
git add requirements.txt

# Commit com correção
git commit -m "Fix: PyMuPDF → pymupdf no requirements.txt para Streamlit Cloud

O pacote PyMuPDF deve ser instalado como 'pymupdf' (minúsculo) mas importado como 'fitz'.
Corrige erro: ModuleNotFoundError: No module named 'fitz'"

# Push
git push origin main

Write-Host "✅ Correção enviada!" -ForegroundColor Green
Write-Host "🔄 Streamlit Cloud irá redeployar automaticamente" -ForegroundColor Cyan
Write-Host "⏱️ Aguarde ~2-3 minutos para o redeploy" -ForegroundColor Yellow
