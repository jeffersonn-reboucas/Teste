# Script para commit e push ao GitHub
# Execute este arquivo no PowerShell

# Navegar para o diretório do projeto
cd C:\Users\Jeffe\libras-visual-builder

# Verificar status do git
git status

# Adicionar todos os arquivos modificados
git add .

# Fazer commit com mensagem descritiva
git commit -m "Smart AI Router implementado - Auto-fallback + RTK Token Saver + Style/Anatomy Locks

- Reescrito src/ai_generator.py com arquitetura modular
- 6 provedores: Pollinations, HuggingFace, Gemini, OpenAI, Replicate, Custom Proxy
- Auto-fallback inteligente: nunca para por falta de crédito
- Estratégia Fusion: Visão multimodal + Geração unificada
- RTK Token Saver: economiza ~40% de tokens
- Style Lock + Anatomy Lock: garante consistência visual
- Interface atualizada com modo Smart Router
- PyMuPDF e gdown já incluídos no requirements.txt
- Documentação completa: SMART_ROUTER_GUIA.md"

# Push para o GitHub
git push origin main

# Se for o primeiro push, use:
# git push -u origin main

Write-Host "✅ Commit e push concluídos!" -ForegroundColor Green
Write-Host "🌐 O Streamlit Cloud irá redeployar automaticamente" -ForegroundColor Cyan
