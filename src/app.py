"""
Interface Streamlit para Libras Visual Builder
Integrado com:
1. Google Drive Capovilla (A-Z Imagens Individuais) + Leitura Visual Gemini Vision
2. Índice SQLite Ultrarrápido (PDF Completo)
3. Cortador Interativo de Sinal (Crop)
4. Fusão Multimodal Real via Google Gemini API + Fallback Pollinations Free
"""
import streamlit as st
import os
from pathlib import Path
from datetime import datetime
from PIL import Image

from prompt_engine import PromptEngine
from ai_generator import AIGenerator, SmartAIRouter
from models import (
    Sinal, CONFIGURACOES_MAO, PONTOS_ARTICULACAO,
    TIPOS_MOVIMENTO, ORIENTACOES, EXPRESSOES, CATEGORIAS
)
from catalog import CatalogoSinais
from pdf_extractor import PDFCapovillaExtractor, PDFConfiguracaoMaoExtractor
from pdf_manager import PDFManager
from gdrive_signals import GDriveCapovillaCatalog


st.set_page_config(
    page_title="Libras Visual Builder",
    page_icon="🤟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# INICIALIZAÇÃO DO SESSION STATE
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

if 'gdrive_catalog' not in st.session_state:
    link_pasta_az = "https://drive.google.com/drive/folders/1I7BccjSxTN_rDEPZQA7_Agd_c0RIxeoU?usp=sharing"
    st.session_state.gdrive_catalog = GDriveCapovillaCatalog(link_pasta_az)

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
    Path("output").mkdir(exist_ok=True)
    Path("assets/referencias").mkdir(parents=True, exist_ok=True)
    Path("assets/referencias/gdrive").mkdir(parents=True, exist_ok=True)
    Path("assets/personagens").mkdir(parents=True, exist_ok=True)
    Path("data/pdfs").mkdir(parents=True, exist_ok=True)


def obter_gemini_secret():
    try:
        if hasattr(st, 'secrets'):
            if 'GEMINI_API_KEY' in st.secrets:
                return st.secrets['GEMINI_API_KEY']
            if 'api_keys' in st.secrets and 'gemini' in st.secrets['api_keys']:
                return st.secrets['api_keys']['gemini']
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY", "")


def inicializar_pdfs():
    if st.session_state.pdfs_inicializados:
        return

    pdfs_disponiveis = st.session_state.pdf_manager.listar_pdfs_disponiveis()

    if len(pdfs_disponiveis) == 0:
        try:
            file_ids = {}
            if hasattr(st, 'secrets') and 'gdrive' in st.secrets:
                file_ids = {
                    "Dicionario capovilla completo.pdf": st.secrets['gdrive'].get('capovilla_file_id'),
                    "configuraçao de mao.pdf": st.secrets['gdrive'].get('config_mao_file_id')
                }

            if file_ids and all(file_ids.values()):
                if st.session_state.pdf_manager.baixar_todos_pdfs(file_ids):
                    st.session_state.pdf_capovilla = PDFCapovillaExtractor(
                        st.session_state.pdf_manager.get_pdf_path("Dicionario capovilla completo.pdf")
                    )
                    st.session_state.pdf_config_mao = PDFConfiguracaoMaoExtractor(
                        st.session_state.pdf_manager.get_pdf_path("configuraçao de mao.pdf")
                    )
        except Exception:
            pass

    st.session_state.pdfs_inicializados = True


def listar_personagens_disponiveis():
    personagens_dir = Path("assets/personagens")
    if personagens_dir.exists():
        return [f.name for f in personagens_dir.glob("*") if f.suffix.lower() in ['.png', '.jpg', '.jpeg']]
    return []


def analisar_imagem_upload(caminho_imagem: str, nome_arquivo: str, chave_gemini: str = ""):
    """
    Tenta extrair os parâmetros da imagem enviada manualmente:
    1. Via OCR (pytesseract)
    2. Via busca no PDF pelo nome do arquivo
    3. Via leitura visual direta com Gemini Vision (mesmo se a imagem só tiver o desenho sem texto!)
    """
    texto_extraido = ""
    try:
        import pytesseract
        img = Image.open(caminho_imagem)
        texto_extraido = pytesseract.image_to_string(img, lang="por")
    except Exception:
        pass

    termo_inferido = Path(nome_arquivo).stem.replace("_", " ").replace("-", " ").strip()
    if termo_inferido.lower().endswith(" d"):
        termo_inferido = termo_inferido[:-2].strip()
    if termo_inferido.lower() == "atoa":
        termo_inferido = "à toa"

    if not texto_extraido.strip() and st.session_state.pdf_capovilla is not None and len(termo_inferido) >= 2:
        try:
            resultados = st.session_state.pdf_capovilla.buscar_termo(termo_inferido, max_resultados=3)
            if resultados:
                texto_extraido = resultados[0].get('texto_completo', '')
        except Exception:
            pass

    if texto_extraido and len(texto_extraido.strip()) > 10:
        if st.session_state.pdf_capovilla is not None:
            parametros = st.session_state.pdf_capovilla.extrair_parametros_sinal(texto_extraido, termo_inferido)
            if parametros:
                return parametros, termo_inferido.upper()

    # Fallback Infalível: Leitura Visual com Gemini Vision
    if chave_gemini:
        try:
            ai_helper = AIGenerator()
            params_visuais = ai_helper.extrair_parametros_visuais_portugues(
                api_key=chave_gemini,
                img_path=caminho_imagem,
                termo=termo_inferido
            )
            if params_visuais:
                return params_visuais, termo_inferido.upper()
        except Exception:
            pass

    return None, termo_inferido.upper()


# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================
def main():
    inicializar_diretorios()
    inicializar_pdfs()

    st.title("🤟 Libras Visual Builder")
    st.markdown("**Geração de ilustrações vetoriais 2D de sinais de Libras com IA Multimodal**")
    st.divider()

    # ------------------------------------------------------------------------
    # SIDEBAR: Configurações de IA
    # ------------------------------------------------------------------------
    with st.sidebar:
        st.header("⚙️ Configurações de IA")

        gemini_default = obter_gemini_secret()
        gemini_key = st.text_input(
            "🔵 Google Gemini API Key (Principal)",
            value=gemini_default,
            type="password",
            help="Chave do Google AI Studio (começa com AIzaSy...)"
        )
        if not gemini_key:
            st.caption("🔗 [Criar API Key grátis no Google AI Studio](https://aistudio.google.com/app/apikey)")

        modo_operacao = st.radio(
            "Modo de Geração",
            ["🔄 Smart Router (Gemini 1º + Auto-Fallback)", "🎯 Provider Específico"],
            index=0
        )

        if modo_operacao.startswith("🔄"):
            with st.expander("🔑 Outras API Keys (Opcional)"):
                huggingface_key = st.text_input("HuggingFace Token", type="password", key="hf_key")
                openai_key = st.text_input("OpenAI API Key", type="password", key="openai_key")
                replicate_key = st.text_input("Replicate API Token", type="password", key="replicate_key")

            router_config = {
                "gemini_key": gemini_key,
                "huggingface_key": huggingface_key,
                "openai_key": openai_key,
                "replicate_key": replicate_key,
                "priority_order": ["gemini", "huggingface", "openai", "replicate"]
            }
            provider = "smart-router"
            api_key = gemini_key

            temp_router = SmartAIRouter(router_config)
            provider_status = temp_router.get_provider_status()

            st.subheader("📊 Status dos Providers")
            for name, status in provider_status.items():
                icon = "✅" if status['ready'] else "❌"
                st.caption(f"{icon} {status['name']}")

        else:
            provider_options = {
                "🔵 Google Gemini Multimodal (Principal)": "gemini",
                "🌸 Pollinations.ai (Flux - 100% Gratuito)": "pollinations",
                "🟠 HuggingFace FLUX.1": "huggingface",
                "🟢 OpenAI DALL-E 3": "openai"
            }
            selected = st.selectbox("Provider", list(provider_options.keys()), index=0)
            provider = provider_options[selected]

            if provider == "gemini":
                api_key = gemini_key
            elif provider == "pollinations":
                api_key = "FREE_MODE"
                st.success("✅ Sem necessidade de API key!")
            elif provider == "huggingface":
                api_key = st.text_input("HuggingFace Token", type="password")
            elif provider == "openai":
                api_key = st.text_input("OpenAI API Key", type="password")
            else:
                api_key = None

            router_config = {"gemini_key": gemini_key}

        st.divider()
        modo_otimizado = st.checkbox("🚀 RTK: Token Saver (Economiza ~40%)", value=False)

    # ========================================================================
    # LAYOUT: 3 COLUNAS
    # ========================================================================
    col1, col2, col3 = st.columns(3)

    # ------------------------------------------------------------------------
    # COLUNA 1: Item A (Referência do Sinal)
    # ------------------------------------------------------------------------
    with col1:
        st.header("📖 Item A: Referência do Sinal")

        tab_drive_az, tab_busca_pdf, tab_upload = st.tabs([
            "🗂️ Drive Capovilla (A-Z)",
            "🔍 PDF Completo",
            "📤 Upload Manual"
        ])

        # ABA 1: DRIVE CAPOVILLA (IMAGENS SEPARADAS A-Z + GEMINI VISION)
        with tab_drive_az:
            st.success("⚡ Conectado à pasta CAPOVILLA (A-Z) do Google Drive")

            col_b1, col_b2 = st.columns([2, 1])
            with col_b1:
                busca_rapida_az = st.text_input(
                    "Buscar sinal pelo nome:",
                    placeholder="Ex: à esquerda, à frente, a leste",
                    key="busca_drive_az"
                )
            with col_b2:
                letras_disp = st.session_state.gdrive_catalog.obter_letras_sincronizadas()
                if not letras_disp:
                    letras_disp = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
                letra_escolhida = st.selectbox("Letra:", letras_disp, key="sel_letra_az")

            if busca_rapida_az.strip():
                with st.spinner("Buscando imagem na pasta do Drive..."):
                    arquivos_encontrados = st.session_state.gdrive_catalog.buscar_sinal_drive(busca_rapida_az)
            else:
                with st.spinner(f"Carregando sinais da letra {letra_escolhida}..."):
                    arquivos_encontrados = st.session_state.gdrive_catalog.carregar_letra(letra_escolhida)

            if arquivos_encontrados:
                opcoes_arq = [
                    f"{a['termo'].upper()} ({'Detalhe D' if a['eh_detalhe'] else 'Sinal'} - {a['nome_arquivo']})"
                    for a in arquivos_encontrados
                ]
                idx_arq = st.selectbox(
                    f"Sinais encontrados ({len(arquivos_encontrados)}):",
                    range(len(opcoes_arq)),
                    format_func=lambda i: opcoes_arq[i],
                    key="sel_arq_drive"
                )

                arq_sel = arquivos_encontrados[idx_arq]

                if st.button("📥 Carregar Imagem Selecionada", type="primary", use_container_width=True):
                    with st.spinner(f"Baixando {arq_sel['nome_arquivo']} e analisando parâmetros do sinal..."):
                        caminho_jpg = st.session_state.gdrive_catalog.baixar_imagem_sinal(
                            arq_sel['file_id'],
                            arq_sel['nome_arquivo']
                        )
                        if caminho_jpg:
                            st.session_state.imagem_ref_path = caminho_jpg
                            st.session_state.termo_atual = arq_sel['termo'].upper()
                            st.session_state.parametros_extraidos = None

                            # 1º Tenta buscar a descrição textual no PDF (se já estiver indexado)
                            if st.session_state.pdf_capovilla is not None and st.session_state.pdf_capovilla.esta_indexado():
                                res_txt = st.session_state.pdf_capovilla.buscar_termo(arq_sel['termo'], max_resultados=2)
                                if res_txt:
                                    st.session_state.parametros_extraidos = st.session_state.pdf_capovilla.extrair_parametros_sinal(
                                        res_txt[0]['texto_completo'],
                                        arq_sel['termo']
                                    )

                            # 2º Se a imagem não tinha texto no banco, usa o Gemini Vision para ler o desenho .jpg!
                            if not st.session_state.parametros_extraidos or not st.session_state.parametros_extraidos.get('descricao_completa'):
                                chave_ativa = gemini_key or obter_gemini_secret()
                                if chave_ativa:
                                    ai_helper = AIGenerator()
                                    params_visuais = ai_helper.extrair_parametros_visuais_portugues(
                                        api_key=chave_ativa,
                                        img_path=caminho_jpg,
                                        termo=arq_sel['termo']
                                    )
                                    if params_visuais:
                                        st.session_state.parametros_extraidos = params_visuais

                            st.rerun()
            else:
                st.info("Nenhum arquivo listado nesta letra ainda. Verifique se a pasta do Drive está pública.")

        # ABA 2: PDF COMPLETO (SQLITE)
        with tab_busca_pdf:
            if st.session_state.pdf_capovilla is None:
                st.warning("⚠️ PDF completo ainda não carregado.")
            else:
                extrator = st.session_state.pdf_capovilla
                total_pags = extrator.get_total_paginas()

                if not extrator.esta_indexado():
                    st.warning(f"⚡ O dicionário ({total_pags} páginas) ainda não foi indexado em SQLite.")
                    if st.button("🚀 Criar Índice Ultrarrápido (SQLite) Agora", type="primary", use_container_width=True):
                        barra = st.progress(0, text="Varrendo páginas e separando verbetes...")
                        extrator.construir_indice(
                            progress_callback=lambda atual, tot: barra.progress(
                                atual / tot,
                                text=f"Indexando no SQLite: página {atual} de {tot}..."
                            )
                        )
                        barra.empty()
                        st.success("✅ Índice SQLite criado!")
                        st.rerun()
                else:
                    st.success(f"⚡ Índice SQLite Ativo ({total_pags} páginas)")

                tipo_busca = st.radio("Modo:", ["🔤 Buscar por Termo", "📄 Ir para Página"], horizontal=True)

                if tipo_busca == "🔤 Buscar por Termo":
                    termo_busca = st.text_input("Digite o sinal a buscar no PDF:", placeholder="Ex: à toa, casa")
                    if st.button("🔍 Buscar no PDF", use_container_width=True):
                        if termo_busca:
                            resultados = extrator.buscar_termo(termo_busca, max_resultados=15)
                            st.session_state.resultados_busca_pdf = resultados
                            st.session_state.termo_atual = termo_busca.upper()

                    if st.session_state.resultados_busca_pdf:
                        resultados = st.session_state.resultados_busca_pdf
                        opcoes = [f"Pág. {r['pagina']} — {r.get('tipo', 'Resultado')}" for r in resultados]
                        idx_sel = st.selectbox("Resultados:", range(len(opcoes)), format_func=lambda i: opcoes[i])
                        item_escolhido = resultados[idx_sel]
                        pag_sel = item_escolhido['pagina']

                        caminho_pag = f"assets/referencias/capovilla_p{pag_sel}.png"
                        if not os.path.exists(caminho_pag):
                            img_p = extrator.renderizar_pagina(pag_sel)
                            img_p.save(caminho_pag)

                        st.session_state.imagem_ref_path = caminho_pag
                        st.session_state.parametros_extraidos = extrator.extrair_parametros_sinal(
                            item_escolhido['texto_completo'],
                            st.session_state.termo_atual
                        )
                else:
                    num_pagina = st.number_input("Número da página", min_value=1, max_value=total_pags, value=127)
                    if st.button("📄 Carregar Página", use_container_width=True):
                        caminho_pag = f"assets/referencias/capovilla_p{num_pagina}.png"
                        img_p = extrator.renderizar_pagina(num_pagina)
                        img_p.save(caminho_pag)
                        st.session_state.imagem_ref_path = caminho_pag
                        txt_p = extrator.extrair_texto_pagina(num_pagina)
                        st.session_state.parametros_extraidos = extrator.extrair_parametros_sinal(txt_p)

        # ABA 3: UPLOAD MANUAL (TAMBÉM COM LEITURA VISUAL GEMINI VISION)
        with tab_upload:
            uploaded_ref = st.file_uploader("Upload da imagem de referência", type=['png', 'jpg', 'jpeg'])
            if uploaded_ref is not None:
                if st.session_state.ultimo_upload_nome != uploaded_ref.name:
                    caminho_salvo = f"assets/referencias/temp_ref_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    with open(caminho_salvo, "wb") as f:
                        f.write(uploaded_ref.getbuffer())
                    st.session_state.imagem_ref_path = caminho_salvo
                    st.session_state.ultimo_upload_nome = uploaded_ref.name

                    with st.spinner("🔎 Analisando imagem e extraindo descrição do sinal..."):
                        chave_ativa = gemini_key or obter_gemini_secret()
                        params_detectados, termo_sugerido = analisar_imagem_upload(
                            caminho_salvo, uploaded_ref.name, chave_ativa
                        )
                        if termo_sugerido:
                            st.session_state.termo_atual = termo_sugerido
                        if params_detectados:
                            st.session_state.parametros_extraidos = params_detectados
                    st.rerun()

        # EXIBIÇÃO DA IMAGEM DE REFERÊNCIA + CORTADOR INTERATIVO (CROP)
        if st.session_state.imagem_ref_path and os.path.exists(st.session_state.imagem_ref_path):
            st.image(
                st.session_state.imagem_ref_path,
                caption=f"Referência Ativa: {st.session_state.termo_atual or 'Sinal'}",
                use_container_width=True
            )

            # Botão rápido caso queira forçar a releitura visual da imagem atual (ou após recortar)
            if st.button("👁️ Extrair/Atualizar Descrição Visual desta Imagem (IA)", use_container_width=True):
                chave_ativa = gemini_key or obter_gemini_secret()
                if not chave_ativa:
                    st.warning("⚠️ Insira sua Google Gemini API Key na barra lateral para usar a leitura visual.")
                else:
                    with st.spinner("Lendo os detalhes anatômicos do desenho com Gemini Vision..."):
                        ai_helper = AIGenerator()
                        params_visuais = ai_helper.extrair_parametros_visuais_portugues(
                            api_key=chave_ativa,
                            img_path=st.session_state.imagem_ref_path,
                            termo=st.session_state.termo_atual
                        )
                        if params_visuais:
                            st.session_state.parametros_extraidos = params_visuais
                            st.rerun()

            with st.expander("✂️ Recortar / Isolar apenas o Desenho do Sinal", expanded=False):
                st.caption("Use as barras para focar somente no boneco executando o sinal:")
                img_orig = Image.open(st.session_state.imagem_ref_path)
                larg_total, alt_total = img_orig.size

                c_y1, c_y2 = st.columns(2)
                with c_y1:
                    topo_pct = st.slider("Topo (%)", 0, 90, 0, key="crop_top")
                with c_y2:
                    base_pct = st.slider("Base (%)", 10, 100, 100, key="crop_bottom")

                c_x1, c_x2 = st.columns(2)
                with c_x1:
                    esq_pct = st.slider("Esquerda (%)", 0, 90, 0, key="crop_left")
                with c_x2:
                    dir_pct = st.slider("Direita (%)", 10, 100, 100, key="crop_right")

                if base_pct > topo_pct and dir_pct > esq_pct:
                    caixa = (
                        int(larg_total * esq_pct / 100),
                        int(alt_total * topo_pct / 100),
                        int(larg_total * dir_pct / 100),
                        int(alt_total * base_pct / 100)
                    )
                    img_recortada = img_orig.crop(caixa)
                    st.image(img_recortada, caption="Prévia do Recorte", use_container_width=True)

                    if st.button("✅ Aplicar Este Recorte", use_container_width=True):
                        caminho_crop = "assets/referencias/recorte_focado_atual.png"
                        img_recortada.save(caminho_crop)
                        st.session_state.imagem_ref_path = caminho_crop
                        st.success("🎯 Recorte aplicado com sucesso!")
                        st.rerun()

        st.divider()
        st.subheader("🔧 Parâmetros do Sinal (Opcional)")

        params = st.session_state.parametros_extraidos or {}
        obs_default = params.get('descricao_completa', '')
        orientacao_default = params.get('orientacao', 'Palma para cima')
        ponto_default = params.get('ponto_articulacao', 'Espaço neutro')

        if obs_default:
            st.info("📝 Descrição e parâmetros autopreenchidos a partir da análise do sinal!")

        termo = st.text_input("Nome do Sinal", value=st.session_state.termo_atual, placeholder="Ex: À ESQUERDA")
        st.session_state.termo_atual = termo

        with st.expander("⚙️ Ajustar Parâmetros Manuais (Opcional)", expanded=False):
            categoria = st.selectbox("Categoria", CATEGORIAS)
            configuracoes = st.multiselect("Configuração de Mão", CONFIGURACOES_MAO)
            ponto_articulacao = st.selectbox(
                "Ponto de Articulação",
                PONTOS_ARTICULACAO,
                index=PONTOS_ARTICULACAO.index(ponto_default) if ponto_default in PONTOS_ARTICULACAO else 0
            )
            movimentos = st.multiselect("Movimento", TIPOS_MOVIMENTO)
            orientacao = st.selectbox(
                "Orientação",
                ORIENTACOES,
                index=ORIENTACOES.index(orientacao_default) if orientacao_default in ORIENTACOES else 0
            )
            expressoes = st.multiselect("Expressão Facial", EXPRESSOES, default=["Neutra"])

        observacoes = st.text_area("Descrição / Observações do Sinal", value=obs_default, height=120)

    # ------------------------------------------------------------------------
    # COLUNA 2: Item B (Personagem Base)
    # ------------------------------------------------------------------------
    with col2:
        st.header("👤 Item B: Personagem Base")
        opcao_personagem = st.radio("Escolha o personagem", ["Usar personagem salvo", "Fazer upload"])
        imagem_personagem_path = None

        if opcao_personagem == "Usar personagem salvo":
            personagens = listar_personagens_disponiveis()
            if personagens:
                personagem_selecionado = st.selectbox("Selecione o personagem", personagens)
                imagem_personagem_path = f"assets/personagens/{personagem_selecionado}"
                st.image(imagem_personagem_path, use_container_width=True)
            else:
                st.info("ℹ️ Nenhum personagem salvo ainda. Escolha 'Fazer upload'.")
        else:
            uploaded_char = st.file_uploader("Upload do personagem", type=['png', 'jpg', 'jpeg'])
            if uploaded_char:
                nome_personagem = st.text_input("Nome do personagem (para salvar)", value="Jefferson")
                imagem_personagem_path = f"assets/personagens/{nome_personagem or 'temp_char'}.png"
                with open(imagem_personagem_path, "wb") as f:
                    f.write(uploaded_char.getbuffer())
                st.success(f"✅ Personagem carregado: {nome_personagem}")
                st.image(imagem_personagem_path, use_container_width=True)

    # ------------------------------------------------------------------------
    # COLUNA 3: Item C (Geração Multimodal + Fallback)
    # ------------------------------------------------------------------------
    with col3:
        st.header("✨ Item C: Resultado Gerado")

        tem_referencia = bool(st.session_state.imagem_ref_path and os.path.exists(st.session_state.imagem_ref_path))
        tem_personagem = bool(imagem_personagem_path and os.path.exists(imagem_personagem_path))
        tem_termo_ou_desc = bool(termo.strip() or observacoes.strip())

        faltando = []
        if not tem_referencia:
            faltando.append("Imagem de Referência (Coluna 1)")
        if not tem_personagem:
            faltando.append("Personagem Base (Coluna 2)")
        if not tem_termo_ou_desc:
            faltando.append("Nome do Sinal (Coluna 1)")

        pode_gerar = (len(faltando) == 0)

        if not pode_gerar:
            st.warning(f"⚠️ **Falta preencher:** {', '.join(faltando)}")
        else:
            st.success("✅ Tudo pronto para gerar a ilustração!")

        def construir_prompt_atual():
            nome_sinal_final = termo.strip() or "SINAL_LIBRAS"
            if modo_otimizado:
                return st.session_state.prompt_engine.gerar_prompt_otimizado(
                    termo=nome_sinal_final, configuracao_mao=configuracoes,
                    ponto_articulacao=ponto_articulacao, movimento=movimentos,
                    orientacao=orientacao, expressao=expressoes, observacoes=observacoes
                )
            return st.session_state.prompt_engine.gerar_prompt_completo(
                termo=nome_sinal_final, configuracao_mao=configuracoes,
                ponto_articulacao=ponto_articulacao, movimento=movimentos,
                orientacao=orientacao, expressao=expressoes, observacoes=observacoes
            )

        if st.button("🚀 Gerar Ilustração 2D", disabled=not pode_gerar, type="primary", use_container_width=True):
            st.session_state.mostrar_fallback_free = False
            st.session_state.erro_geracao_msg = ""

            with st.spinner("🎨 Analisando imagens e gerando ilustração vetorial 2D..."):
                prompt = construir_prompt_atual()
                st.session_state.ultimo_prompt = prompt
                nome_base = (termo.strip() or "sinal").lower().replace(' ', '_')
                nome_arquivo = f"{nome_base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

                if provider == "pollinations":
                    cfg = {"gemini_key": gemini_key, "priority_order": ["pollinations"]}
                elif provider == "smart-router":
                    cfg = router_config
                else:
                    cfg = {"gemini_key": api_key, "priority_order": [provider]}

                ai_gen = AIGenerator(provider="smart-router", config=cfg)
                sucesso, msg, caminho_saida = ai_gen.gerar_imagem(
                    prompt=prompt,
                    imagem_referencia_a=st.session_state.imagem_ref_path,
                    imagem_personagem_b=imagem_personagem_path,
                    output_dir="output",
                    nome_arquivo=nome_arquivo
                )

                if sucesso:
                    st.success(f"✅ {msg}")
                    st.session_state.imagem_gerada = caminho_saida
                else:
                    st.session_state.erro_geracao_msg = msg
                    st.session_state.mostrar_fallback_free = True

        if st.session_state.mostrar_fallback_free:
            st.error(f"⚠️ **Aviso do Provedor Principal:** {st.session_state.erro_geracao_msg}")
            st.info("💡 **Deseja gerar agora no modo 100% Gratuito (usando Leitura Visual do Gemini + Pollinations 2D)?**")

            if st.button("🌸 Sim, gerar com Pollinations.ai (Estilo 2D)", type="primary", use_container_width=True):
                with st.spinner("🌸 Lendo a pose do sinal e gerando o personagem em 2D..."):
                    prompt = st.session_state.ultimo_prompt or construir_prompt_atual()
                    nome_arquivo = f"free_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    ai_gen = AIGenerator(
                        provider="smart-router",
                        config={"gemini_key": gemini_key, "priority_order": ["pollinations"]}
                    )
                    sucesso, msg, caminho_saida = ai_gen.gerar_imagem(
                        prompt=prompt,
                        imagem_referencia_a=st.session_state.imagem_ref_path,
                        imagem_personagem_b=imagem_personagem_path,
                        output_dir="output",
                        nome_arquivo=nome_arquivo
                    )
                    if sucesso:
                        st.session_state.mostrar_fallback_free = False
                        st.success(f"✅ {msg}")
                        st.session_state.imagem_gerada = caminho_saida
                    else:
                        st.error(f"❌ Falha no Pollinations: {msg}")

        if st.session_state.imagem_gerada and os.path.exists(st.session_state.imagem_gerada):
            st.image(st.session_state.imagem_gerada, caption="Ilustração Gerada", use_container_width=True)
            with open(st.session_state.imagem_gerada, "rb") as file:
                st.download_button(
                    label="💾 Baixar Ilustração",
                    data=file,
                    file_name=os.path.basename(st.session_state.imagem_gerada),
                    mime="image/png",
                    use_container_width=True
                )


if __name__ == "__main__":
    main()