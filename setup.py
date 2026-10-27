"""
Script de inicialização e verificação do ambiente
"""
import os
import sys
from pathlib import Path


def verificar_diretorios():
    """Cria diretórios necessários"""
    diretorios = [
        "data",
        "assets/referencias",
        "assets/personagens",
        "output"
    ]

    print("📁 Verificando estrutura de diretórios...")
    for dir_path in diretorios:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {dir_path}")


def verificar_dependencias():
    """Verifica se as dependências estão instaladas"""
    print("\n📦 Verificando dependências...")

    dependencias = {
        'streamlit': 'streamlit',
        'PIL': 'Pillow',
        'pandas': 'pandas',
        'requests': 'requests'
    }

    faltando = []

    for modulo, pacote in dependencias.items():
        try:
            __import__(modulo)
            print(f"  ✓ {pacote}")
        except ImportError:
            print(f"  ✗ {pacote} (faltando)")
            faltando.append(pacote)

    if faltando:
        print(f"\n⚠️  Instale as dependências faltantes:")
        print(f"   pip install {' '.join(faltando)}")
        return False

    return True


def verificar_api_keys():
    """Verifica se há API keys configuradas"""
    print("\n🔑 Verificando API keys...")

    keys = {
        'GEMINI_API_KEY': 'Google Gemini',
        'OPENAI_API_KEY': 'OpenAI',
        'REPLICATE_API_TOKEN': 'Replicate'
    }

    encontradas = []

    for var_env, nome in keys.items():
        if os.getenv(var_env):
            print(f"  ✓ {nome}")
            encontradas.append(nome)
        else:
            print(f"  ✗ {nome} (não configurada)")

    if not encontradas:
        print("\n⚠️  Nenhuma API key encontrada!")
        print("   Configure pelo menos uma das seguintes variáveis de ambiente:")
        print("\n   Windows (PowerShell):")
        print("   $env:GEMINI_API_KEY = \"sua-key-aqui\"")
        print("\n   Linux/Mac:")
        print("   export GEMINI_API_KEY=\"sua-key-aqui\"")
        print("\n   Ou configure diretamente na interface do Streamlit.")
        return False

    return True


def verificar_providers_ia():
    """Verifica quais providers de IA estão disponíveis"""
    print("\n🤖 Verificando providers de IA disponíveis...")

    providers = []

    # Gemini
    try:
        import google.generativeai
        if os.getenv('GEMINI_API_KEY'):
            print("  ✓ Google Gemini (pronto)")
            providers.append('gemini')
        else:
            print("  ○ Google Gemini (instalado, mas sem API key)")
    except ImportError:
        print("  ✗ Google Gemini (pip install google-generativeai)")

    # OpenAI
    try:
        import openai
        if os.getenv('OPENAI_API_KEY'):
            print("  ✓ OpenAI (pronto)")
            providers.append('openai')
        else:
            print("  ○ OpenAI (instalado, mas sem API key)")
    except ImportError:
        print("  ✗ OpenAI (pip install openai)")

    # Replicate
    try:
        import replicate
        if os.getenv('REPLICATE_API_TOKEN'):
            print("  ✓ Replicate (pronto)")
            providers.append('replicate')
        else:
            print("  ○ Replicate (instalado, mas sem API key)")
    except ImportError:
        print("  ✗ Replicate (pip install replicate)")

    return providers


def criar_catalog_inicial():
    """Cria arquivo de catálogo vazio se não existir"""
    catalog_path = Path("data/catalog.json")

    if not catalog_path.exists():
        import json
        catalog_path.write_text(json.dumps({}, indent=2, ensure_ascii=False))
        print("\n📚 Catálogo inicial criado em data/catalog.json")


def main():
    print("=" * 60)
    print("🤟 LIBRAS VISUAL BUILDER - Verificação do Ambiente")
    print("=" * 60)

    # Verificações
    verificar_diretorios()
    deps_ok = verificar_dependencias()

    if deps_ok:
        api_ok = verificar_api_keys()
        providers = verificar_providers_ia()
        criar_catalog_inicial()

        print("\n" + "=" * 60)

        if providers:
            print("✅ Sistema pronto para uso!")
            print(f"\n📌 Providers disponíveis: {', '.join(providers)}")
            print("\n🚀 Para iniciar a aplicação, execute:")
            print("   streamlit run src/app.py")
        else:
            print("⚠️  Sistema parcialmente configurado")
            print("\n   Configure uma API key para começar a usar.")
            print("   Você ainda pode usar a interface para organizar referências.")
    else:
        print("\n" + "=" * 60)
        print("❌ Instale as dependências antes de continuar")
        print("   pip install -r requirements.txt")

    print("=" * 60)


if __name__ == "__main__":
    main()
