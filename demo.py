"""
Script de teste/demonstração do sistema
Use para testar os módulos sem a interface Streamlit
"""
import os
import sys
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from prompt_engine import PromptEngine
from models import CONFIGURACOES_MAO, PONTOS_ARTICULACAO, TIPOS_MOVIMENTO, ORIENTACOES, EXPRESSOES


def demo_prompt_engine():
    """Demonstra o gerador de prompts"""
    print("=" * 70)
    print("🎯 DEMO: Gerador de Prompts")
    print("=" * 70)

    engine = PromptEngine()

    # Exemplo 1: Sinal "OBRIGADO"
    prompt = engine.gerar_prompt_completo(
        termo="OBRIGADO",
        configuracao_mao=["Mão aberta"],
        ponto_articulacao="Boca",
        movimento=["Para frente"],
        orientacao="Palma para cima",
        expressao=["Sorriso"],
        observacoes="Sinal comum de gratidão, mão começa próxima aos lábios"
    )

    print("\n📝 Prompt gerado para o sinal 'OBRIGADO':\n")
    print(prompt)
    print("\n" + "=" * 70)


def demo_catalog():
    """Demonstra o sistema de catalogação"""
    print("\n\n" + "=" * 70)
    print("📚 DEMO: Sistema de Catalogação")
    print("=" * 70)

    from catalog import CatalogoSinais
    from models import Sinal

    # Criar catálogo de demonstração
    catalogo = CatalogoSinais("data/catalog_demo.json")

    # Criar alguns sinais de exemplo
    sinais_exemplo = [
        Sinal(
            termo="OLÁ",
            categoria="Cumprimentos",
            configuracao_mao=["Mão aberta"],
            ponto_articulacao="Cabeça",
            movimento=["Balançar"],
            orientacao="Palma para frente",
            expressao=["Sorriso"],
            tags=["cumprimento", "saudação"],
            observacoes="Mão ao lado da cabeça, movimento lateral"
        ),
        Sinal(
            termo="CASA",
            categoria="Lugares",
            configuracao_mao=["Mão em C"],
            ponto_articulacao="Espaço neutro",
            movimento=["Para cima", "Para baixo"],
            orientacao="Palma para dentro",
            expressao=["Neutra"],
            tags=["lugar", "moradia"],
            observacoes="Formato de telhado"
        ),
        Sinal(
            termo="ESTUDAR",
            categoria="Educação",
            configuracao_mao=["Mão aberta"],
            ponto_articulacao="Testa",
            movimento=["Circular"],
            orientacao="Palma para baixo",
            expressao=["Concentração"],
            tags=["educação", "aprendizado"],
            observacoes="Movimento circular na altura da testa"
        )
    ]

    # Adicionar ao catálogo
    print("\n➕ Adicionando sinais ao catálogo...")
    for sinal in sinais_exemplo:
        catalogo.adicionar_sinal(sinal)
        print(f"  ✓ {sinal.termo} ({sinal.categoria})")

    # Estatísticas
    stats = catalogo.estatisticas()
    print(f"\n📊 Estatísticas:")
    print(f"  Total de sinais: {stats['total_sinais']}")
    print(f"  Categorias: {stats['categorias']}")

    # Buscar por categoria
    print(f"\n🔍 Buscando sinais da categoria 'Educação':")
    sinais_educacao = catalogo.filtrar_por_categoria("Educação")
    for sinal in sinais_educacao:
        print(f"  • {sinal.termo}: {', '.join(sinal.configuracao_mao)}")

    # Buscar por parâmetro
    print(f"\n🔍 Buscando sinais com ponto de articulação 'Cabeça':")
    sinais_cabeca = catalogo.buscar_por_parametro(ponto_articulacao="Cabeça")
    for sinal in sinais_cabeca:
        print(f"  • {sinal.termo}: {', '.join(sinal.movimento)}")

    print("\n" + "=" * 70)


def demo_ai_generator():
    """Demonstra o gerador de IA (apenas configuração, sem gerar)"""
    print("\n\n" + "=" * 70)
    print("🤖 DEMO: Verificação de Providers de IA")
    print("=" * 70)

    from ai_generator import AIGenerator

    # Verificar quais providers estão disponíveis
    print("\n🔍 Verificando providers configurados:\n")

    providers = {
        'gemini': 'GEMINI_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'replicate': 'REPLICATE_API_TOKEN'
    }

    for provider, env_var in providers.items():
        if os.getenv(env_var):
            print(f"  ✓ {provider.upper()}: Configurado")
            try:
                # Tentar inicializar
                gen = AIGenerator(provider=provider)
                print(f"    Modelo: {gen.model_name}")
            except Exception as e:
                print(f"    ⚠️  Erro ao inicializar: {e}")
        else:
            print(f"  ✗ {provider.upper()}: Não configurado (variável {env_var})")

    print("\n💡 Para configurar uma API key:")
    print("   Windows: $env:GEMINI_API_KEY = \"sua-key\"")
    print("   Linux/Mac: export GEMINI_API_KEY=\"sua-key\"")

    print("\n" + "=" * 70)


def demo_parametros():
    """Mostra todos os parâmetros disponíveis"""
    print("\n\n" + "=" * 70)
    print("📋 DEMO: Parâmetros Disponíveis")
    print("=" * 70)

    print("\n🖐️  Configurações de Mão:")
    for i, config in enumerate(CONFIGURACOES_MAO[:10], 1):
        print(f"  {i:2}. {config}")
    print(f"  ... e mais {len(CONFIGURACOES_MAO) - 10} opções")

    print("\n📍 Pontos de Articulação:")
    for i, ponto in enumerate(PONTOS_ARTICULACAO[:10], 1):
        print(f"  {i:2}. {ponto}")
    print(f"  ... e mais {len(PONTOS_ARTICULACAO) - 10} opções")

    print("\n↔️  Tipos de Movimento:")
    for i, mov in enumerate(TIPOS_MOVIMENTO[:10], 1):
        print(f"  {i:2}. {mov}")
    print(f"  ... e mais {len(TIPOS_MOVIMENTO) - 10} opções")

    print("\n🧭 Orientações:")
    for i, orient in enumerate(ORIENTACOES, 1):
        print(f"  {i:2}. {orient}")

    print("\n😊 Expressões:")
    for i, expr in enumerate(EXPRESSOES, 1):
        print(f"  {i:2}. {expr}")

    print("\n" + "=" * 70)


def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "🤟 LIBRAS VISUAL BUILDER - DEMO" + " " * 22 + "║")
    print("╚" + "═" * 68 + "╝")

    try:
        # Executar demos
        demo_parametros()
        demo_prompt_engine()
        demo_catalog()
        demo_ai_generator()

        print("\n\n✅ Demonstração concluída!")
        print("\n📌 Próximos passos:")
        print("   1. Configure uma API key (Gemini, OpenAI ou Replicate)")
        print("   2. Execute: streamlit run src/app.py")
        print("   3. Comece a gerar suas ilustrações de Libras!\n")

    except Exception as e:
        print(f"\n❌ Erro durante a demonstração: {e}")
        print("   Certifique-se de ter instalado as dependências:")
        print("   pip install -r requirements.txt\n")


if __name__ == "__main__":
    main()
