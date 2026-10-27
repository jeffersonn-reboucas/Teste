"""
Interface Streamlit para Libras Visual Builder
Fluxo: Item A (Referência) + Item B (Personagem) → Item C (Resultado)
"""
import streamlit as st
import os
import re
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

# ============================================================================
# INICIALIZAÇÃO DO SESSION STATE (PERSISTÊNCIA ENTRE RERUNS)
# ============================================================================
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

if 'pdfs_inicializados' not in st.session_state:
    st.session_state.pdfs_inicializados = False

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

# Estados persistentes para Referência (Item A), Busca e Fallback
if 'parametros_extraidos' not in st.session_state:
    st.session_state.parametros_extraidos = None

if 'imagem_ref_path' not in st.session_state:
    st.session_state.imagem_ref_path = None

if 'termo_atual' not in st.session_state:
    st.session_state.termo_atual = ""

if 'resultados_busca_pdf' not in st.session_state:
    st.session_state.resultados_busca_pdf = []

if 'ultimo_upload_nome' not in st.session_state:
    st.session_state.ultimo_upload_nome = None

if 'mostrar_fallback_free' not in st.session_state:
    st.session_state.mostrar_fallback_free = False

if 'erro_geracao_msg' not in st.session_state:
    st.session_state.erro_geracao_msg = ""


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def inicializar_diretorios():
    """Cria os diretórios necessários"""
    Path("output").mkdir(exist_ok=True)
    Path("assets/referencias").mkdir(parents=True, exist_ok=True)
    Path("assets/personagens").mkdir(parents=True, exist_ok=True)
    Path("data/pdfs").mkdir(parents=True, exist_ok=True)


def inicializar_pdfs():
    """Inicializa e baixa PDFs do Google Drive se necessário"""
    if 'pdfs_inicializados' not in st.session_state:
        st.session_state.pdfs_inicializados = False

    if st.session_state.pdfs_inicializados:
        return

    pdfs_disponiveis = st.session_state.pdf_manager.listar_pdfs_disponiveis()

    if len(pdfs_disponiveis) == 0:
        st.warning("⚠️ PDFs não encontrados localmente")
        st.info("🌐 Tentando baixar do Google Drive...")

        try:
            file_ids = {}
            if hasattr(st, 'secrets') and 'gdrive' in st.secrets:
                file_ids = {
                    "Dicionario capovilla completo.pdf": st.secrets['gdrive'].get('capovilla_file_id'),
                    "configuraçao de mao.pdf": st.secrets['gdrive'].get('config_mao_file_id')
                }

            if file_ids and all(file_ids.values()):
                if st.session_state.pdf_manager.baixar_todos_pdfs(file_ids):
                    st.success("✅ PDFs baixados com sucesso!")
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


def analisar_imagem_upload(caminho_imagem: str, nome_arquivo: str):
    """
    Tenta extrair texto/parâmetros da imagem enviada manualmente (via OCR/PyMuPDF ou busca inteligente no PDF pelo nome).
    """
    texto_extraido = ""

    # 1. Tentar OCR via PyMuPDF ou pytesseract se disponível no ambiente
    try:
        import pytesseract
        img = Image.open(caminho_imagem)
        texto_extraido = pytesseract.image_to_string(img, lang="por")
    except Exception:
        pass

    # 2. Se não houver OCR de sistema instalado, tenta cruzar o nome do arquivo com o dicionário PDF carregado
    termo_inferido = Path(nome_arquivo).stem.replace("_", " ").replace("-", " ").strip()
    if termo_inferido.lower() == "atoa":
        termo_inferido = "à toa"

    if not texto_extraido.strip() and st.session_state.pdf_capovilla is not None and len(termo_inferido) >= 2:
        try:
            resultados = st.session_state.pdf_capovilla.buscar_termo(termo_inferido, max_resultados=3)
            if resultados:
                texto_extraido = resultados[0].get('texto_completo', '')
        except Exception:
            pass

    # 3. Extrair parâmetros se encontrou texto
    if texto_extraido and len(texto_extraido.strip()) > 10:
        if st.session_state.pdf_capovilla is not None:
            parametros = st.session_state.pdf_capovilla.extrair_parametros_sinal(texto_extraido)
            if parametros:
                return parametros, termo_inferido.upper()
        return {
            'configuracao_mao': [],
            'orientacao': 'Palma para cima',
            'ponto_articulacao': 'Espaço neutro',
            'movimento': [],
            'descricao_completa': texto_extraido.strip()
        }, termo_inferido.upper()

    return None, termo_inferido.upper()


# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

def main():
    inicializar_diretorios()
    inicializar_pdfs()

    # Cabeçalho
    st.title("🤟 Libras Visual Builder")
    st.markdown("**Geração de ilustrações de sinais de Libras com IA Multimodal**")
    st.divider()

    # Sidebar: Configurações
    with st.sidebar:
        st.header("⚙️ Configurações de IA")

        modo_operacao = st.radio(
            "Modo de Geração",
            ["🔄 Smart Router (Auto-Fallback)", "🎯 Provider Específico"],
            help="Smart Router tenta múltiplos provedores automaticamente se um falhar"
        )

        if modo_operacao == "🔄 Smart Router (Auto-Fallback)":
            st.success("✨ Modo inteligente ativado: nunca para por falta de crédito!")

            with st.expander("🔑 Configurar API Keys (Opcional)"):
                st.info("Configure quantas quiser. Se nenhuma for configurada, você poderá usar o Pollinations.ai gratuitamente.")

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
            api_key = None

            from ai_generator import SmartAIRouter
            try:
                temp_router = SmartAIRouter(router_config)
                provider_status = temp_router.get_provider_status()

                st.divider()
                st.subheader("📊 Status dos Providers")

                for name, status in provider_status.items():
                    icon = "✅" if status['ready'] else "❌"
                    col_s1, col_s2 = st.columns([3, 1])
                    with col_s1:
                        st.text(f"{icon} {status['name']}")
                    with col_s2:
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
                "🌸 Pollinations.ai (Flux - 100% Gratuito)": "pollinations",
                "🔵 Google Gemini (Gratuito - Análise)": "gemini",
                "🟢 OpenAI DALL-E 3": "openai",
                "🟣 Replicate Flux": "replicate-flux",
                "🟠 HuggingFace FLUX.1": "huggingface"
            }

            selected = st.selectbox("Provider", list(provider_options.keys()))
            provider = provider_options[selected]

            if provider == "openai":
                api_key = st.text_input("OpenAI API Key", type="password")
            elif provider == "gemini":
                api_key = st.text_input("Gemini API Key", type="password")
            elif provider == "replicate-flux":
                api_key = st.text_input("Replicate Token", type="password")
            elif provider == "huggingface":
                api_key = st.text_input("HuggingFace Token", type="password")
            elif provider == "pollinations":
                api_key = "FREE_MODE"
                st.success("✅ Sem necessidade de API key!")
            else:
                api_key = None

            router_config = None

        st.divider()
        st.subheader("🚀 Otimizações")

        modo_otimizado = st.checkbox(
            "RTK: Token Saver (Economiza ~40%)",
            value=False,
            help="Otimiza o prompt removendo redundâncias mantendo qualidade"
        )

        if modo_otimizado:
            st.caption("✅ Prompt será otimizado para economizar tokens")

        st.divider()
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

        tab_upload, tab_busca_pdf = st.tabs(["📤 Upload Manual", "🔍 Buscar no Dicionário (PDF)"])

        # Tab 1: Upload Manual com Análise Automática
        with tab_upload:
            uploaded_ref = st.file_uploader(
                "Upload da imagem de referência",
                type=['png', 'jpg', 'jpeg'],
                key="upload_ref"
            )

            if uploaded_ref is not None:
                # Se é um novo arquivo enviado, salva e analisa automaticamente
                if st.session_state.ultimo_upload_nome != uploaded_ref.name:
                    caminho_salvo = f"assets/referencias/temp_ref_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    with open(caminho_salvo, "wb") as f:
                        f.write(uploaded_ref.getbuffer())

                    st.session_state.imagem_ref_path = caminho_salvo
                    st.session_state.ultimo_upload_nome = uploaded_ref.name

                    with st.spinner("🔎 Analisando imagem para extrair parâmetros do sinal..."):
                        params_detectados, termo_sugerido = analisar_imagem_upload(caminho_salvo, uploaded_ref.name)
                        if termo_sugerido and not st.session_state.termo_atual:
                            st.session_state.termo_atual = termo_sugerido

                        if params_detectados:
                            st.session_state.parametros_extraidos = params_detectados
                            st.success("✅ Descrição e parâmetros extraídos automaticamente da imagem!")
                        else:
                            st.info("ℹ️ Nenhuma descrição textual detectada na imagem. Por favor, preencha o Nome do Sinal (e observações se desejar) abaixo.")

                if st.session_state.imagem_ref_path and os.path.exists(st.session_state.imagem_ref_path):
                    st.image(st.session_state.imagem_ref_path, caption="Referência do Sinal", use_container_width=True)

        # Tab 2: Busca no PDF do Capovilla com Persistência
        with tab_busca_pdf:
            if st.session_state.pdf_capovilla is None:
                st.error("❌ PDF do Capovilla não encontrado!")
            else:
                st.success(f"✅ PDF carregado ({st.session_state.pdf_capovilla.get_total_paginas()} páginas)")

                tipo_busca = st.radio(
                    "Tipo de busca",
                    ["🔤 Buscar por Termo", "📄 Ir para Página"],
                    horizontal=True,
                    key="tipo_busca"
                )

                if tipo_busca == "🔤 Buscar por Termo":
                    termo_busca = st.text_input(
                        "Digite o termo a buscar",
                        placeholder="Ex: CASA, À TOA, ESCOLA",
                        key="termo_busca_pdf"
                    )

                    if st.button("🔍 Buscar", key="btn_buscar_termo"):
                        if termo_busca:
                            with st.spinner("Buscando no dicionário..."):
                                resultados = st.session_state.pdf_capovilla.buscar_termo(termo_busca, max_resultados=10)
                                st.session_state.resultados_busca_pdf = resultados
                                st.session_state.termo_atual = termo_busca.upper()
                                if not resultados:
                                    st.warning("⚠️ Nenhum resultado encontrado para este termo.")

                    # Exibir resultados persistidos no session_state
                    if st.session_state.resultados_busca_pdf:
                        resultados = st.session_state.resultados_busca_pdf
                        st.success(f"✅ Encontrados {len(resultados)} resultado(s)")

                        opcoes_resultados = [f"Página {r['pagina']}" for r in resultados]
                        resultado_selecionado = st.selectbox(
                            "Selecione o resultado",
                            range(len(opcoes_resultados)),
                            format_func=lambda i: opcoes_resultados[i],
                            key="resultado_sel"
                        )

                        pagina_selecionada = resultados[resultado_selecionado]['pagina']

                        # Renderizar e persistir página selecionada
                        caminho_pag = f"assets/referencias/capovilla_p{pagina_selecionada}.png"
                        if not os.path.exists(caminho_pag):
                            with st.spinner("Renderizando página..."):
                                img_pagina = st.session_state.pdf_capovilla.renderizar_pagina(pagina_selecionada)
                                img_pagina.save(caminho_pag)

                        st.session_state.imagem_ref_path = caminho_pag
                        st.image(caminho_pag, caption=f"Página {pagina_selecionada}", use_container_width=True)

                        # Extrair parâmetros automaticamente da página selecionada
                        texto_pagina = resultados[resultado_selecionado]['texto_completo']
                        parametros = st.session_state.pdf_capovilla.extrair_parametros_sinal(texto_pagina)
                        if parametros:
                            st.session_state.parametros_extraidos = parametros
                        else:
                            st.session_state.parametros_extraidos = {
                                'configuracao_mao': [],
                                'orientacao': 'Palma para cima',
                                'ponto_articulacao': 'Espaço neutro',
                                'movimento': [],
                                'descricao_completa': texto_pagina[:800] if texto_pagina else ""
                            }

                else:  # Ir para página
                    num_pagina = st.number_input(
                        "Número da página",
                        min_value=1,
                        max_value=st.session_state.pdf_capovilla.get_total_paginas(),
                        value=127,
                        key="num_pagina_pdf"
                    )

                    if st.button("📄 Carregar Página", key="btn_carregar_pagina"):
                        with st.spinner("Renderizando página..."):
                            img_pagina = st.session_state.pdf_capovilla.renderizar_pagina(num_pagina)
                            caminho_pag = f"assets/referencias/capovilla_p{num_pagina}.png"
                            img_pagina.save(caminho_pag)
                            st.session_state.imagem_ref_path = caminho_pag

                            texto_pagina = st.session_state.pdf_capovilla.extrair_texto_pagina(num_pagina)
                            parametros = st.session_state.pdf_capovilla.extrair_parametros_sinal(texto_pagina)
                            if parametros:
                                st.session_state.parametros_extraidos = parametros
                            else:
                                st.session_state.parametros_extraidos = {
                                    'configuracao_mao': [],
                                    'orientacao': 'Palma para cima',
                                    'ponto_articulacao': 'Espaço neutro',
                                    'movimento': [],
                                    'descricao_completa': texto_pagina[:800] if texto_pagina else ""
                                }

                    if st.session_state.imagem_ref_path and f"capovilla_p{num_pagina}.png" in st.session_state.imagem_ref_path:
                        st.image(st.session_state.imagem_ref_path, caption=f"Página {num_pagina}", use_container_width=True)

            # Mostrar descrição extraída se disponível
            if st.session_state.parametros_extraidos and st.session_state.parametros_extraidos.get('descricao_completa'):
                st.success("✅ Descrição do sinal extraída automaticamente! (Preenchimento manual dispensado)")
                with st.expander("📋 Ver Descrição Extraída"):
                    st.write(st.session_state.parametros_extraidos['descricao_completa'])

        st.divider()

        # --------------------------------------------------------------------
        # PARÂMETROS DO SINAL (OPCIONAIS / AUTOPREENCHIDOS)
        # --------------------------------------------------------------------
        st.subheader("🔧 Parâmetros do Sinal (Opcional)")

        if st.session_state.parametros_extraidos:
            st.info("📝 Parâmetros autopreenchidos a partir da descrição do sinal.")
            params = st.session_state.parametros_extraidos
            configuracoes_default = [c for c in params.get('configuracao_mao', []) if c in CONFIGURACOES_MAO]
            orientacao_default = params.get('orientacao', 'Palma para cima')
            ponto_default = params.get('ponto_articulacao', 'Espaço neutro')
            movimentos_default = [m for m in params.get('movimento', []) if m in TIPOS_MOVIMENTO]
            obs_default = params.get('descricao_completa', '')
        else:
            st.caption("Preencha apenas se desejar detalhar manualmente o sinal.")
            configuracoes_default = []
            orientacao_default = "Palma para cima"
            ponto_default = "Espaço neutro"
            movimentos_default = []
            obs_default = ""

        termo = st.text_input(
            "Nome do Sinal",
            value=st.session_state.termo_atual,
            placeholder="Ex: À TOA, CASA, ESTUDAR",
            key="termo_input"
        )
        st.session_state.termo_atual = termo

        with st.expander("⚙️ Ajustar Parâmetros Detalhados (Opcional)", expanded=not bool(st.session_state.parametros_extraidos)):
            categoria = st.selectbox("Categoria", CATEGORIAS, key="categoria")
            configuracoes = st.multiselect("Configuração de Mão", CONFIGURACOES_MAO, default=configuracoes_default)
            ponto_articulacao = st.selectbox(
                "Ponto de Articulação",
                PONTOS_ARTICULACAO,
                index=PONTOS_ARTICULACAO.index(ponto_default) if ponto_default in PONTOS_ARTICULACAO else 0
            )
            movimentos = st.multiselect("Movimento", TIPOS_MOVIMENTO, default=movimentos_default)
            orientacao = st.selectbox(
                "Orientação",
                ORIENTACOES,
                index=ORIENTACOES.index(orientacao_default) if orientacao_default in ORIENTACOES else 0
            )
            expressoes = st.multiselect("Expressão Facial", EXPRESSOES, default=["Neutra"])

        observacoes = st.text_area(
            "Descrição / Observações do Sinal",
            value=obs_default,
            height=120,
            placeholder="A descrição extraída do dicionário ou da imagem aparecerá aqui automaticamente..."
        )

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
                st.image(imagem_personagem_path, caption="Personagem Selecionado", use_container_width=True)
            else:
                st.info("ℹ️ Nenhum personagem salvo ainda. Escolha 'Fazer upload' acima.")

        else:  # Upload
            uploaded_char = st.file_uploader(
                "Upload do personagem",
                type=['png', 'jpg', 'jpeg'],
                key="upload_char"
            )

            if uploaded_char:
                nome_personagem = st.text_input(
                    "Nome do personagem (para salvar)",
                    placeholder="Ex: Jefferson",
                    key="nome_personagem"
                )

                if nome_personagem:
                    imagem_personagem_path = f"assets/personagens/{nome_personagem}.png"
                    with open(imagem_personagem_path, "wb") as f:
                        f.write(uploaded_char.getbuffer())

                    st.success(f"✅ Personagem salvo: {nome_personagem}")
                    st.image(imagem_personagem_path, caption="Personagem", use_container_width=True)
                else:
                    imagem_personagem_path = "assets/personagens/temp_char.png"
                    with open(imagem_personagem_path, "wb") as f:
                        f.write(uploaded_char.getbuffer())
                    st.image(imagem_personagem_path, caption="Personagem (temporário)", use_container_width=True)

        st.divider()

        with st.expander("ℹ️ Dicas de Personagem"):
            st.markdown("""
            **Características ideais:**
            - Fundo transparente ou neutro
            - Pose neutra (braços visíveis)
            - Proporções anatômicas claras
            - Estilo 2D consistente
            """)

    # ------------------------------------------------------------------------
    # COLUNA 3: Item C (Geração e Resultado)
    # ------------------------------------------------------------------------
    with col3:
        st.header("✨ Item C: Resultado Gerado")
        st.markdown("*Personagem executando o sinal*")

        # Verificar requisitos essenciais (sem travar por api_key ou parâmetros opcionais)
        tem_referencia = bool(st.session_state.imagem_ref_path and os.path.exists(st.session_state.imagem_ref_path))
        tem_personagem = bool(imagem_personagem_path and os.path.exists(imagem_personagem_path))
        tem_termo_ou_desc = bool(termo.strip() or observacoes.strip() or st.session_state.parametros_extraidos)

        itens_faltando = []
        if not tem_referencia:
            itens_faltando.append("Imagem de Referência (Coluna 1)")
        if not tem_personagem:
            itens_faltando.append("Personagem Base (Coluna 2)")
        if not tem_termo_ou_desc:
            itens_faltando.append("Nome do Sinal ou Descrição (Coluna 1)")

        pode_gerar = (len(itens_faltando) == 0)

        if not pode_gerar:
            st.warning(f"⚠️ **Para liberar a geração, falta:** {', '.join(itens_faltando)}")
        else:
            st.success("✅ Tudo pronto para gerar a ilustração!")

        # Função interna para construir o prompt
        def construir_prompt_atual():
            nome_sinal_final = termo.strip() if termo.strip() else "SINAL_LIBRAS"
            st.session_state.prompt_engine.modo_otimizado = modo_otimizado
            if modo_otimizado:
                return st.session_state.prompt_engine.gerar_prompt_otimizado(
                    termo=nome_sinal_final,
                    configuracao_mao=configuracoes,
                    ponto_articulacao=ponto_articulacao,
                    movimento=movimentos,
                    orientacao=orientacao,
                    expressao=expressoes,
                    observacoes=observacoes
                )
            else:
                return st.session_state.prompt_engine.gerar_prompt_completo(
                    termo=nome_sinal_final,
                    configuracao_mao=configuracoes,
                    ponto_articulacao=ponto_articulacao,
                    movimento=movimentos,
                    orientacao=orientacao,
                    expressao=expressoes,
                    observacoes=observacoes
                )

        # Botão principal de geração
        if st.button("🚀 Gerar Ilustração", disabled=not pode_gerar, type="primary", use_container_width=True):
            st.session_state.mostrar_fallback_free = False
            st.session_state.erro_geracao_msg = ""

            with st.spinner("🎨 Processando ilustração com IA..."):
                try:
                    prompt = construir_prompt_atual()
                    st.session_state.ultimo_prompt = prompt
                    nome_base = (termo.strip() or "sinal").lower().replace(' ', '_')
                    nome_arquivo = f"{nome_base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

                    # Verificar se o usuário tentou um provider pago sem chave configurada
                    if provider != "pollinations" and provider != "smart-router" and not api_key:
                        st.session_state.erro_geracao_msg = f"Nenhuma API Key foi informada para o provedor '{provider}'."
                        st.session_state.mostrar_fallback_free = True
                    elif provider == "smart-router":
                        tem_alguma_chave = any([
                            router_config.get("openai_key"),
                            router_config.get("gemini_key"),
                            router_config.get("replicate_key"),
                            router_config.get("huggingface_key"),
                            router_config.get("custom_proxy_key")
                        ])
                        if not tem_alguma_chave:
                            st.session_state.erro_geracao_msg = "Nenhuma API Key paga/externa foi configurada nas Configurações de IA."
                            st.session_state.mostrar_fallback_free = True
                        else:
                            # Tenta apenas nos provedores com chave antes de perguntar sobre o Free
                            config_sem_free = dict(router_config)
                            config_sem_free["priority_order"] = ["custom_proxy", "gemini", "huggingface", "openai", "replicate"]
                            ai_gen = AIGenerator(provider="smart-router", config=config_sem_free)
                            sucesso, mensagem, caminho_saida = ai_gen.gerar_imagem(
                                prompt=prompt,
                                imagem_referencia_a=st.session_state.imagem_ref_path,
                                imagem_personagem_b=imagem_personagem_path,
                                output_dir="output",
                                nome_arquivo=nome_arquivo
                            )
                            if sucesso:
                                st.success(f"✅ {mensagem}")
                                st.session_state.imagem_gerada = caminho_saida
                            else:
                                st.session_state.erro_geracao_msg = mensagem
                                st.session_state.mostrar_fallback_free = True
                    else:
                        # Execução direta (Pollinations ou Provider Específico com chave)
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
                            imagem_referencia_a=st.session_state.imagem_ref_path,
                            imagem_personagem_b=imagem_personagem_path,
                            output_dir="output",
                            nome_arquivo=nome_arquivo
                        )

                        if sucesso:
                            st.success(f"✅ {mensagem}")
                            st.session_state.imagem_gerada = caminho_saida
                        else:
                            st.session_state.erro_geracao_msg = mensagem
                            if provider != "pollinations":
                                st.session_state.mostrar_fallback_free = True
                            else:
                                st.error(f"❌ {mensagem}")

                except Exception as e:
                    st.session_state.erro_geracao_msg = str(e)
                    st.session_state.mostrar_fallback_free = True

        # --------------------------------------------------------------------
        # PERGUNTA INTERATIVA DE FALLBACK PARA POLLINATIONS.AI (FREE)
        # --------------------------------------------------------------------
        if st.session_state.mostrar_fallback_free:
            st.error(f"⚠️ **Aviso das Configurações de IA:** {st.session_state.erro_geracao_msg}")
            st.info("💡 **Deseja gerar esta ilustração agora no modo 100% Gratuito usando ✅ Pollinations.ai (Flux)?**")

            if st.button("🌸 Sim, gerar no modo Free (Pollinations.ai)", type="primary", use_container_width=True):
                with st.spinner("🌸 Gerando gratuitamente com Pollinations.ai (Flux)..."):
                    try:
                        prompt = st.session_state.ultimo_prompt or construir_prompt_atual()
                        nome_base = (termo.strip() or "sinal").lower().replace(' ', '_')
                        nome_arquivo = f"{nome_base}_free_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

                        free_config = {"priority_order": ["pollinations"]}
                        ai_gen = AIGenerator(provider="smart-router", config=free_config)
                        sucesso, mensagem, caminho_saida = ai_gen.gerar_imagem(
                            prompt=prompt,
                            imagem_referencia_a=st.session_state.imagem_ref_path,
                            imagem_personagem_b=imagem_personagem_path,
                            output_dir="output",
                            nome_arquivo=nome_arquivo
                        )

                        if sucesso:
                            st.session_state.mostrar_fallback_free = False
                            st.success(f"✅ Gerado com sucesso no modo Free! ({mensagem})")
                            st.session_state.imagem_gerada = caminho_saida
                        else:
                            st.error(f"❌ Erro no Pollinations.ai: {mensagem}")
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar no modo Free: {str(e)}")

        # Exibir imagem gerada
        if st.session_state.imagem_gerada:
            if os.path.exists(st.session_state.imagem_gerada):
                st.image(
                    st.session_state.imagem_gerada,
                    caption="Ilustração Gerada",
                    use_container_width=True
                )

                st.divider()
                col3a, col3b = st.columns(2)

                with col3a:
                    with open(st.session_state.imagem_gerada, "rb") as file:
                        st.download_button(
                            label="💾 Download",
                            data=file,
                            file_name=os.path.basename(st.session_state.imagem_gerada),
                            mime="image/png"
                        )

                with col3b:
                    if st.button("📚 Salvar no Catálogo"):
                        novo_sinal = Sinal(
                            termo=termo or "Sinal",
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
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_cat = st.selectbox("Filtrar por categoria", ["Todas"] + CATEGORIAS, key="filtro_cat")
        with col_f2:
            busca_termo = st.text_input("Buscar termo", placeholder="Digite o nome do sinal...", key="busca_termo")

        sinais_filtrados = sinais
        if filtro_cat != "Todas":
            sinais_filtrados = [s for s in sinais_filtrados if s.categoria == filtro_cat]
        if busca_termo:
            sinais_filtrados = [s for s in sinais_filtrados if busca_termo.lower() in s.termo.lower()]

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