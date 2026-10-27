# Correção final: requirements.txt simplificado
# Execute no PowerShell

cd C:\Users\Jeffe\libras-visual-builder

git add requirements.txt

git commit -m "Fix: Simplificado requirements.txt - apenas essenciais

- PyMuPDF==1.24.0 (versão mais recente estável)
- Removido replicate (pode instalar depois se necessário)
- Removido stability-sdk (causava conflitos)
- Apenas dependências essenciais para funcionar"

git push origin main

Write-Host "✅ Requirements.txt simplificado enviado!" -ForegroundColor Green
Write-Host "📦 Apenas pacotes essenciais:" -ForegroundColor Cyan
Write-Host "   - streamlit, Pillow, pandas, requests" -ForegroundColor Gray
Write-Host "   - PyMuPDF (PDFs), gdown (Google Drive)" -ForegroundColor Gray
Write-Host "   - google-generativeai, openai" -ForegroundColor Gray
