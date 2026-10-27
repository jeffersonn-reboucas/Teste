"""
Interface Streamlit para Libras Visual Builder
Fluxo: Item A (Referência) + Item B (Personagem) → Item C (Resultado)
"""
import streamlit as st
import os
from pathlib import Path
from datetime import datetime
from PIL import Image
import json

# Imports dos módulos do projeto
from prompt_engine import PromptEngine
from ai_generator import AIGenerator
from models import (
    Sinal, CONFIGURACOES_MAO, PONTOS_ARTICULACAO,
    TIPOS_MOVIMENTO, ORIENTACOES, EXPRESSOES, CATEGORIAS
)
from catalog import CatalogoSinais
from pdf_extractor import PDFCapovillaExtractor, PDFConfiguracaoMaoExtractor
from pdf_manager import PDFManager


# Configuração da página
st.set_page_config(
    page_title="Libras Visual Builder",
    page_icon="🤟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session state
if 'catalogo' not in st.session_state:
    st.session_state.catalogo = CatalogoSinais()

if 'prompt_engine' not in st.session_state:
    st.session_state.prompt_engine = PromptEngine()

if 'imagem_gerada' not in st.session_state:
    st.session_state.imagem_gerada = None

if 'ultimo_prompt' not in st.session_state:
    st.session_state.ultimo_prompt = None

if 'pdf_manager' not in st.session_state:
    st.session_state.pdf_manager = PDFManager()

if 'pdf_capovilla' not in st.session_state:
    try:
        caminho_pdf = st.session_state.pdf_manager.get_pdf_path("Dicionario capovilla completo.pdf")
        if Path(caminho_pdf).exists():
            st.session_state.pdf_capovilla = PDFCapovillaExtractor(caminho_pdf)
        else:
            st.session_state.pdf_capovilla = None
    except FileNotFoundError:
        st.session_state.pdf_capovilla = None

if 'pdf_config_mao' not in st.session_state:
    try:
        caminho_pdf = st.session_state.pdf_manager.get_pdf_path("configuraçao de mao.pdf")
        if Path(caminho_pdf).exists():
            st.session_state.pdf_config_mao = PDFConfiguracaoMaoExtractor(caminho_pdf)
        else:
            st.session_state.pdf_config_mao = None
    except FileNotFoundError:
        st.session_state.pdf_config_mao = None

if 'parametros_extraidos' not in st.session_state:
    st.session_state.parametros_extraidos = None

if 'pdfs_inicializados' not in st.session_state:
    st.session_state.pdfs_inicializados = False


def inicializar_diretorios():
    """Cria os diretórios necessários"""
    Path("output").mkdir(exist_ok=True)
    Path("assets/referencias").mkdir(parents=True, exist_ok=True)
    Path("assets/personagens").mkdir(parents=True, exist_ok=True)
    Path("data/pdfs").mkdir(parents=True, exist_ok=True)


def inicializar_pdfs():
    """Inicializa e baixa PDFs do Google Drive se necessário"""
    import streamlit as st
    
    if 'pdfs_inicializados' not in st.session_state:
        st.session_state.pdfs_inicializados = False

    if st.session_state.pdfs_inicializados:
        return

    # Verificar se os PDFs existem
    pdfs_disponiveis = st.session_state.pdf_manager.listar_pdfs_disponiveis()

    if len(pdfs_disponiveis) == 0:
        st.warning("⚠️ PDFs não encontrados localmente")
        st.info("🌐 Tentando baixar do Google Drive...")

        try:
            file_ids = {}

            # Tentar ler dos secrets do Streamlit Cloud
            if hasattr(st, 'secrets') and 'gdrive' in st.secrets:
                file_ids = {
                    "Dicionario capovilla completo.pdf": st.secrets['gdrive'].get('capovilla_file_id'),
                    "configuraçao de mao.pdf": st.secrets['gdrive'].get('config_mao_file_id')
                }

            # Tentar baixar
            if file_ids and all(file_ids.values()):
                if st.session_state.pdf_manager.baixar_todos_pdfs(file_ids):
                    st.success("✅ PDFs baixados com sucesso!")
                    # Reinicializar extractors
                    st.session_state.pdf_capovilla = PDFCapovillaExtractor(
                        st.session_state.pdf_manager.get_pdf_path("Dicionario capovilla completo.pdf")
                    )
                    st.session_state.pdf_config_mao = PDFConfiguracaoMaoExtractor(
                        st.session_state.pdf_manager.get_pdf_path("configuraçao de mao.pdf")
                    )
                else:
                    st.error("❌ Falha no download dos PDFs")
            else:
                st.info("""
                📌 **Para usar PDFs do Google Drive:**
                1. Configure os File IDs no painel de Secrets do Streamlit Cloud
                2. Ou coloque os PDFs manualmente na pasta `data/pdfs/`
                """)
        except Exception as e:
            st.error(f"❌ Erro ao inicializar PDFs: {str(e)}")
    else:
        st.sidebar.success(f"✅ {len(pdfs_disponiveis)} PDF(s) disponível(is)")

    st.session_state.pdfs_inicializados = True

def listar_personagens_disponiveis():
    """Lista personagens salvos na pasta assets/personagens"""
    personagens_dir = Path("assets/personagens")
    if personagens_dir.exists():
        return [f.name for f in personagens_dir.glob("*") if f.suffix.lower() in ['.png', '.jpg', '.jpeg']]
    return []


# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

def main():
    inicializar_diretorios()

    # Inicializar PDFs (baixar do Google Drive se necessário)
    inicializar_pdfs()

    # Cabeçalho
    st.title("🤟 Libras Visual Builder")
    st.markdown("**Geração de ilustrações de sinais de Libras com IA Multimodal**")
    st.divider()

    # Sidebar: Configurações
    with st.sidebar:
        st.header("⚙️ Configurações de IA")

        # Modo de operação
        modo_operacao = st.radio(
            "Modo de Geração",
            ["🔄 Smart Router (Auto-Fallback)", "🎯 Provider Específico"],
            help="Smart Router tenta múltiplos provedores automaticamente se um falhar"
        )

        if modo_operacao == "🔄 Smart Router (Auto-Fallback)":
            st.success("✨ Modo inteligente ativado: nunca para por falta de crédito!")

            # Configuração de múltiplas API keys
            with st.expander("🔑 Configurar API Keys (Opcional)"):
                st.info("Configure quantas quiser. O sistema usará as disponíveis e fará fallback para opções gratuitas.")

                openai_key = st.text_input("OpenAI API Key", type="password", key="openai_key")
                gemini_key = st.text_input("Google Gemini API Key", type="password", key="gemini_key")
                replicate_key = st.text_input("Replicate API Token", type="password", key="replicate_key")
                huggingface_key = st.text_input("HuggingFace Token", type="password", key="hf_key")

                st.divider()

                custom_proxy_enabled = st.checkbox("Usar Proxy Customizado (9Router/OpenRouter)")
                if custom_proxy_enabled:
                    custom_proxy_url = st.text_input("Base URL", placeholder="https://api.9router.com/v1")
                    custom_proxy_key = st.text_input("API Key do Proxy", type="password")
                    custom_proxy_model = st.text_input("Nome do Modelo", value="9Router")
                else:
                    custom_proxy_url = None
                    custom_proxy_key = None
                    custom_proxy_model = None

            # Ordem de prioridade
            with st.expander("⚙️ Ordem de Fallback"):
                st.markdown("**Ordem atual:**")
                fallback_order = [
                    "1️⃣ Gemini (Gratuito até 1500 req/dia)",
                    "2️⃣ HuggingFace (Gratuito com token)",
                    "3️⃣ OpenAI (Alta qualidade)",
                    "4️⃣ Replicate (Custo-benefício)",
                    "5️⃣ Pollinations.ai (100% Gratuito - Fallback Universal)"
                ]
                for item in fallback_order:
                    st.text(item)

                st.info("💡 O sistema tenta na ordem acima até conseguir gerar a imagem")

            # Configurar router
            router_config = {
                "openai_key": openai_key or os.getenv("OPENAI_API_KEY"),
                "gemini_key": gemini_key or os.getenv("GEMINI_API_KEY"),
                "replicate_key": replicate_key or os.getenv("REPLICATE_API_TOKEN"),
                "huggingface_key": huggingface_key or os.getenv("HUGGINGFACE_TOKEN"),
                "replicate_model": "flux"
            }

            if custom_proxy_enabled and custom_proxy_url and custom_proxy_key:
                router_config["custom_proxy_url"] = custom_proxy_url
                router_config["custom_proxy_key"] = custom_proxy_key
                router_config["custom_proxy_model"] = custom_proxy_model

            provider = "smart-router"
            api_key = None  # Não usado no modo router

            # Mostrar status dos providers
            from ai_generator import SmartAIRouter
            try:
                temp_router = SmartAIRouter(router_config)
                provider_status = temp_router.get_provider_status()

                st.divider()
                st.subheader("📊 Status dos Providers")

                for name, status in provider_status.items():
                    icon = "✅" if status['ready'] else "❌"
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(f"{icon} {status['name']}")
                    with col2:
                        if not status['requires_key']:
                            st.caption("FREE")
                        elif status['ready']:
                            st.caption("OK")
                        else:
                            st.caption("NO KEY")
            except Exception as e:
                st.warning(f"⚠️ Erro ao inicializar router: {e}")

        else:  # Modo Provider Específico
            st.info("Modo direto: usa apenas o provider selecionado")

            provider_options = {
                "🔵 Google Gemini (Gratuito - Análise)": "gemini",
                "🟢 OpenAI DALL-E 3": "openai",
                "🟣 Replicate Flux": "replicate-flux",
                "🟠 HuggingFace FLUX.1": "huggingface",
                "🌸 Pollinations.ai (Gratuito)": "pollinations"
            }

            selected = st.selectbox("Provider", list(provider_options.keys()))
            provider = provider_options[selected]

            # API Key específica
            if provider == "openai":
                api_key = st.text_input("OpenAI API Key", type="password")
            elif provider == "gemini":
                api_key = st.text_input("Gemini API Key", type="password")
            elif provider == "replicate-flux":
                api_key = st.text_input("Replicate Token", type="password")
            elif provider == "huggingface":
                api_key = st.text_input("HuggingFace Token", type="password")
            elif provider == "pollinations":
                api_key = None
                st.success("✅ Sem necessidade de API key!")
            else:
                api_key = None

            router_config = None

        st.divider()

        # Otimização de tokens
        st.subheader("🚀 Otimizações")

        modo_otimizado = st.checkbox(
            "RTK: Token Saver (Economiza ~40%)",
            value=False,
            help="Otimiza o prompt removendo redundâncias mantendo qualidade"
        )

        if modo_otimizado:
            st.caption("✅ Prompt será otimizado para economizar tokens")

        st.divider()

        # Estatísticas do catálogo
        st.subheader("📊 Catálogo")
        stats = st.session_state.catalogo.estatisticas()
        st.metric("Total de Sinais", stats['total_sinais'])
        st.metric("Categorias", stats['total_categorias'])

        if st.button("📥 Exportar Catálogo (CSV)"):
            caminho_csv = f"catalog_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            if st.session_state.catalogo.exportar_para_csv(caminho_csv):
                st.success(f"✅ Exportado: {caminho_csv}")

    # ========================================================================
    # LAYOUT: 3 COLUNAS
    # ========================================================================

    col1, col2, col3 = st.columns(3)

    # ------------------------------------------------------------------------
    # COLUNA 1: Item A (Referência do Sinal)
    # ------------------------------------------------------------------------
    with col1:
        st.header("📖 Item A: Referência do Sinal")
        st.markdown("*Imagem do dicionário (Capovilla) com o desenho técnico*")

        # Abas: Upload manual ou Buscar no PDF
        tab_upload, tab_busca_pdf = st.tabs(["📤 Upload Manual", "🔍 Buscar no Dicionário (PDF)"])

        imagem_ref_path = None
        termo = ""
        configuracoes = []
        ponto_articulacao = "Espaço neutro"
        movimentos = []
        orientacao = "Palma para cima"
        expressoes = ["Neutra"]
        observacoes = ""

        # Tab 1: Upload Manual
        with tab_upload:
            uploaded_ref = st.file_uploader(
                "Upload da imagem de referência",
                type=['png', 'jpg', 'jpeg'],
                key="upload_ref"
            )

            if uploaded_ref:
                # Salvar temporariamente
                imagem_ref_path = f"assets/referencias/temp_ref_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                with open(imagem_ref_path, "wb") as f:
                    f.write(uploaded_ref.getbuffer())

                # Exibir preview
                st.image(imagem_ref_path, caption="Referência do Sinal", use_container_width=True)

        # Tab 2: Busca no PDF do Capovilla
        with tab_busca_pdf:
            if st.session_state.pdf_capovilla is None:
                st.error("❌ PDF do Capovilla não encontrado!")
                st.info(f"📁 Esperado em: `C:\\Users\\Jeffe\\Downloads\\Dicionario capovilla completo.pdf`")
            else:
                st.success(f"✅ PDF carregado ({st.session_state.pdf_capovilla.get_total_paginas()} páginas)")

                # Opções de busca
                tipo_busca = st.radio(
                    "Tipo de busca",
                    ["🔤 Buscar por Termo", "📄 Ir para Página"],
                    horizontal=True,
                    key="tipo_busca"
                )

                if tipo_busca == "🔤 Buscar por Termo":
                    termo_busca = st.text_input(
                        "Digite o termo a buscar",
                        placeholder="Ex: CASA, OBRIGADO, ESCOLA",
                        key="termo_busca_pdf"
                    )

                    if st.button("🔍 Buscar", key="btn_buscar_termo"):
                        if termo_busca:
                            with st.spinner("Buscando no dicionário..."):
                                resultados = st.session_state.pdf_capovilla.buscar_termo(termo_busca, max_resultados=10)

                                if resultados:
                                    st.success(f"✅ Encontrados {len(resultados)} resultado(s)")

                                    # Selecionar resultado
                                    opcoes_resultados = [f"Página {r['pagina']}" for r in resultados]
                                    resultado_selecionado = st.selectbox(
                                        "Selecione o resultado",
                                        range(len(opcoes_resultados)),
                                        format_func=lambda i: opcoes_resultados[i],
                                        key="resultado_sel"
                                    )

                                    pagina_selecionada = resultados[resultado_selecionado]['pagina']

                                    # Renderizar página
                                    with st.spinner("Renderizando página..."):
                                        img_pagina = st.session_state.pdf_capovilla.renderizar_pagina(pagina_selecionada)

                                        # Salvar como referência
                                        imagem_ref_path = f"assets/referencias/capovilla_p{pagina_selecionada}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                                        img_pagina.save(imagem_ref_path)

                                        st.image(img_pagina, caption=f"Página {pagina_selecionada}", use_container_width=True)
                                        st.info("💡 Você pode recortar apenas a ilustração do sinal usando um editor de imagem externo")

                                    # Extrair parâmetros automaticamente
                                    texto_pagina = resultados[resultado_selecionado]['texto_completo']
                                    parametros = st.session_state.pdf_capovilla.extrair_parametros_sinal(texto_pagina)

                                    if parametros:
                                        st.success("✅ Parâmetros extraídos automaticamente!")
                                        with st.expander("📋 Ver Descrição Extraída"):
                                            st.text(parametros['descricao_completa'])

                                        st.session_state.parametros_extraidos = parametros
                                else:
                                    st.warning("⚠️ Nenhum resultado encontrado")

                else:  # Ir para página
                    num_pagina = st.number_input(
                        "Número da página",
                        min_value=1,
                        max_value=st.session_state.pdf_capovilla.get_total_paginas(),
                        value=1,
                        key="num_pagina_pdf"
                    )

                    if st.button("📄 Carregar Página", key="btn_carregar_pagina"):
                        with st.spinner("Renderizando página..."):
                            img_pagina = st.session_state.pdf_capovilla.renderizar_pagina(num_pagina)

                            # Salvar como referência
                            imagem_ref_path = f"assets/referencias/capovilla_p{num_pagina}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                            img_pagina.save(imagem_ref_path)

                            st.image(img_pagina, caption=f"Página {num_pagina}", use_container_width=True)

                            # Extrair texto e tentar extrair parâmetros
                            texto_pagina = st.session_state.pdf_capovilla.extrair_texto_pagina(num_pagina)
                            parametros = st.session_state.pdf_capovilla.extrair_parametros_sinal(texto_pagina)

                            if parametros:
                                st.success("✅ Parâmetros detectados na página!")
                                with st.expander("📋 Ver Descrição Extraída"):
                                    st.text(parametros['descricao_completa'])

                                st.session_state.parametros_extraidos = parametros

        st.divider()

        # Parâmetros do Sinal
        st.subheader("🔧 Parâmetros do Sinal")

        # Se há parâmetros extraídos do PDF, usar como valores padrão
        if st.session_state.parametros_extraidos:
            st.info("📝 Parâmetros preenchidos automaticamente do PDF")
            params = st.session_state.parametros_extraidos
            configuracoes_default = params.get('configuracao_mao', [])
            orientacao_default = params.get('orientacao', 'Palma para cima')
            ponto_default = params.get('ponto_articulacao', 'Espaço neutro')
            movimentos_default = params.get('movimento', [])
            obs_default = params.get('descricao_completa', '')
        else:
            configuracoes_default = []
            orientacao_default = "Palma para cima"
            ponto_default = "Espaço neutro"
            movimentos_default = []
            obs_default = ""

        termo = st.text_input(
            "Nome do Sinal",
            placeholder="Ex: CASA, ESTUDAR, FELIZ",
            key="termo"
        )

        categoria = st.selectbox(
            "Categoria",
            CATEGORIAS,
            key="categoria"
        )

        configuracoes = st.multiselect(
            "Configuração de Mão",
            CONFIGURACOES_MAO,
            default=configuracoes_default,
            key="config_mao"
        )

        ponto_articulacao = st.selectbox(
            "Ponto de Articulação",
            PONTOS_ARTICULACAO,
            index=PONTOS_ARTICULACAO.index(ponto_default) if ponto_default in PONTOS_ARTICULACAO else 0,
            key="ponto_art"
        )

        movimentos = st.multiselect(
            "Movimento",
            TIPOS_MOVIMENTO,
            default=movimentos_default,
            key="movimentos"
        )

        orientacao = st.selectbox(
            "Orientação",
            ORIENTACOES,
            index=ORIENTACOES.index(orientacao_default) if orientacao_default in ORIENTACOES else 0,
            key="orientacao"
        )

        expressoes = st.multiselect(
            "Expressão Facial",
            EXPRESSOES,
            default=["Neutra"],
            key="expressoes"
        )

        observacoes = st.text_area(
            "Observações",
            value=obs_default,
            placeholder="Detalhes adicionais sobre o sinal...",
            key="observacoes"
        )

        # Botão para limpar parâmetros extraídos
        if st.session_state.parametros_extraidos:
            if st.button("🔄 Limpar Parâmetros Extraídos"):
                st.session_state.parametros_extraidos = None
                st.rerun()

    # ------------------------------------------------------------------------
    # COLUNA 2: Item B (Personagem)
    # ------------------------------------------------------------------------
    with col2:
        st.header("👤 Item B: Personagem Base")
        st.markdown("*Seu modelo 2D padronizado*")

        # Opção: usar personagem existente ou fazer upload
        opcao_personagem = st.radio(
            "Escolha o personagem",
            ["Usar personagem salvo", "Fazer upload"],
            key="opcao_personagem"
        )

        imagem_personagem_path = None

        if opcao_personagem == "Usar personagem salvo":
            personagens = listar_personagens_disponiveis()

            if personagens:
                personagem_selecionado = st.selectbox(
                    "Selecione o personagem",
                    personagens,
                    key="personagem_sel"
                )
                imagem_personagem_path = f"assets/personagens/{personagem_selecionado}"

                # Exibir preview
                st.image(imagem_personagem_path, caption="Personagem Selecionado", use_container_width=True)
            else:
                st.info("ℹ️ Nenhum personagem salvo. Faça upload primeiro.")

        else:  # Upload
            uploaded_char = st.file_uploader(
                "Upload do personagem",
                type=['png', 'jpg', 'jpeg'],
                key="upload_char"
            )

            if uploaded_char:
                # Salvar
                nome_personagem = st.text_input(
                    "Nome do personagem (para salvar)",
                    placeholder="Ex: personagem_padrao",
                    key="nome_personagem"
                )

                if nome_personagem:
                    imagem_personagem_path = f"assets/personagens/{nome_personagem}.png"
                    with open(imagem_personagem_path, "wb") as f:
                        f.write(uploaded_char.getbuffer())

                    st.success(f"✅ Personagem salvo: {nome_personagem}")
                    st.image(imagem_personagem_path, caption="Personagem", use_container_width=True)
                else:
                    # Usar temporariamente
                    imagem_personagem_path = f"assets/personagens/temp_char_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    with open(imagem_personagem_path, "wb") as f:
                        f.write(uploaded_char.getbuffer())
                    st.image(imagem_personagem_path, caption="Personagem (temp)", use_container_width=True)

        st.divider()

        # Informações do personagem
        with st.expander("ℹ️ Dicas de Personagem"):
            st.markdown("""
            **Características ideais:**
            - Fundo transparente ou neutro
            - Pose neutra (braços ao lado do corpo)
            - Proporções anatômicas claras
            - Estilo 2D consistente
            - Alta resolução
            """)

    # ------------------------------------------------------------------------
    # COLUNA 3: Item C (Geração e Resultado)
    # ------------------------------------------------------------------------
    with col3:
        st.header("✨ Item C: Resultado Gerado")
        st.markdown("*Personagem executando o sinal*")

        # Validação antes de gerar
        pode_gerar = all([
            imagem_ref_path,
            imagem_personagem_path,
            termo,
            api_key
        ])

        if not pode_gerar:
            st.warning("⚠️ Complete os campos obrigatórios nas colunas 1 e 2")

        # Botão de geração
        if st.button("🚀 Gerar Ilustração", disabled=not pode_gerar, type="primary"):
            with st.spinner("🎨 Gerando ilustração com IA..."):
                try:
                    # Atualizar PromptEngine com modo de otimização
                    st.session_state.prompt_engine.modo_otimizado = modo_otimizado

                    # Gerar o prompt
                    if modo_otimizado:
                        prompt = st.session_state.prompt_engine.gerar_prompt_otimizado(
                            termo=termo,
                            configuracao_mao=configuracoes,
                            ponto_articulacao=ponto_articulacao,
                            movimento=movimentos,
                            orientacao=orientacao,
                            expressao=expressoes,
                            observacoes=observacoes
                        )
                        st.info("🚀 Prompt otimizado (RTK: Token Saver ativado)")
                    else:
                        prompt = st.session_state.prompt_engine.gerar_prompt_completo(
                            termo=termo,
                            configuracao_mao=configuracoes,
                            ponto_articulacao=ponto_articulacao,
                            movimento=movimentos,
                            orientacao=orientacao,
                            expressao=expressoes,
                            observacoes=observacoes
                        )

                    st.session_state.ultimo_prompt = prompt

                    # Gerar imagem conforme modo
                    nome_arquivo = f"{termo.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

                    if provider == "smart-router":
                        # Modo Smart Router com Auto-Fallback
                        st.info("🔄 Smart Router: Tentando múltiplos provedores...")

                        ai_gen = AIGenerator(provider="smart-router", config=router_config)

                        sucesso, mensagem, caminho_saida = ai_gen.gerar_imagem(
                            prompt=prompt,
                            imagem_referencia_a=imagem_ref_path,
                            imagem_personagem_b=imagem_personagem_path,
                            output_dir="output",
                            nome_arquivo=nome_arquivo
                        )
                    else:
                        # Modo Provider Específico (legado)
                        st.info(f"🎯 Usando provider: {provider}")

                        # Criar config para o provider específico
                        specific_config = {}
                        if provider == "openai":
                            specific_config = {"openai_key": api_key, "priority_order": ["openai"]}
                        elif provider == "gemini":
                            specific_config = {"gemini_key": api_key, "priority_order": ["gemini"]}
                        elif provider == "replicate-flux":
                            specific_config = {"replicate_key": api_key, "replicate_model": "flux", "priority_order": ["replicate"]}
                        elif provider == "huggingface":
                            specific_config = {"huggingface_key": api_key, "priority_order": ["huggingface"]}
                        elif provider == "pollinations":
                            specific_config = {"priority_order": ["pollinations"]}

                        ai_gen = AIGenerator(provider="smart-router", config=specific_config)

                        sucesso, mensagem, caminho_saida = ai_gen.gerar_imagem(
                            prompt=prompt,
                            imagem_referencia_a=imagem_ref_path,
                            imagem_personagem_b=imagem_personagem_path,
                            output_dir="output",
                            nome_arquivo=nome_arquivo
                        )

                    if sucesso:
                        st.success(f"✅ {mensagem}")
                        st.session_state.imagem_gerada = caminho_saida
                    else:
                        st.error(f"❌ {mensagem}")

                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")

        # Exibir imagem gerada
        if st.session_state.imagem_gerada:
            if os.path.exists(st.session_state.imagem_gerada):
                st.image(
                    st.session_state.imagem_gerada,
                    caption="Ilustração Gerada",
                    use_container_width=True
                )

                # Opções pós-geração
                st.divider()

                col3a, col3b = st.columns(2)

                with col3a:
                    # Download
                    with open(st.session_state.imagem_gerada, "rb") as file:
                        st.download_button(
                            label="💾 Download",
                            data=file,
                            file_name=os.path.basename(st.session_state.imagem_gerada),
                            mime="image/png"
                        )

                with col3b:
                    # Salvar no catálogo
                    if st.button("📚 Salvar no Catálogo"):
                        novo_sinal = Sinal(
                            termo=termo,
                            categoria=categoria,
                            configuracao_mao=configuracoes,
                            ponto_articulacao=ponto_articulacao,
                            movimento=movimentos,
                            orientacao=orientacao,
                            expressao=expressoes,
                            caminho_imagem=st.session_state.imagem_gerada,
                            observacoes=observacoes
                        )

                        if st.session_state.catalogo.adicionar_sinal(novo_sinal):
                            st.success("✅ Salvo no catálogo!")
                        else:
                            st.warning("⚠️ Sinal já existe no catálogo")

        # Exibir prompt usado
        if st.session_state.ultimo_prompt:
            with st.expander("🔍 Ver Prompt Usado"):
                st.code(st.session_state.ultimo_prompt, language="text")

    # ========================================================================
    # SEÇÃO INFERIOR: Visualização do Catálogo
    # ========================================================================

    st.divider()
    st.header("📚 Catálogo de Sinais")

    sinais = st.session_state.catalogo.listar_todos()

    if sinais:
        # Filtros
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            filtro_cat = st.selectbox(
                "Filtrar por categoria",
                ["Todas"] + CATEGORIAS,
                key="filtro_cat"
            )

        with col_f2:
            busca_termo = st.text_input(
                "Buscar termo",
                placeholder="Digite o nome do sinal...",
                key="busca_termo"
            )

        # Aplicar filtros
        sinais_filtrados = sinais

        if filtro_cat != "Todas":
            sinais_filtrados = [s for s in sinais_filtrados if s.categoria == filtro_cat]

        if busca_termo:
            sinais_filtrados = [s for s in sinais_filtrados if busca_termo.lower() in s.termo.lower()]

        # Exibir em grid
        if sinais_filtrados:
            cols_grid = st.columns(4)

            for idx, sinal in enumerate(sinais_filtrados):
                with cols_grid[idx % 4]:
                    if sinal.caminho_imagem and os.path.exists(sinal.caminho_imagem):
                        st.image(sinal.caminho_imagem, use_container_width=True)
                    else:
                        st.info("Sem imagem")

                    st.markdown(f"**{sinal.termo}**")
                    st.caption(f"{sinal.categoria}")

                    if st.button("🗑️", key=f"del_{sinal.termo}_{idx}"):
                        if st.session_state.catalogo.remover_sinal(sinal.termo):
                            st.rerun()
        else:
            st.info("Nenhum sinal encontrado com os filtros aplicados")
    else:
        st.info("📭 Catálogo vazio. Comece gerando seu primeiro sinal!")


if __name__ == "__main__":
    main()
