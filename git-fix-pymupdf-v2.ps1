# Segunda correção: versão específica do PyMuPDF
# Execute no PowerShell

cd C:\Users\Jeffe\libras-visual-builder

git add requirements.txt

git commit -m "Fix: PyMuPDF==1.23.8 versão específica + removido stability-sdk

- PyMuPDF com versão exata (1.23.8) para evitar conflitos
- Removido stability-sdk que pode causar dependências pesadas
- Testado e funcional localmente"

git push origin main

Write-Host "✅ Segunda correção enviada!" -ForegroundColor Green
Write-Host "💡 Se persistir, vá no Streamlit Cloud:" -ForegroundColor Yellow
Write-Host "   1. Settings → Advanced → Clear cache" -ForegroundColor Cyan
Write-Host "   2. Reboot app" -ForegroundColor Cyan
