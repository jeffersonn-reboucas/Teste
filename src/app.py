"""
Interface Streamlit para Libras Visual Builder
Integrado com: Google Gemini API, Replicate (InstantCharacter), Drive Capovilla e SQLite.
"""
import streamlit as st
import os
from pathlib import Path
from datetime import datetime
from PIL import Image
import io

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
            "🔵 Google Gemini API Key",
            value=gemini_default,
            type="password",
            help="Chave do Google AI Studio para análise e geração."
        )
        if not gemini_key:
            st.caption("🔗 [Criar API Key grátis no Google AI Studio](https://aistudio.google.com/app/apikey)")

        with st.expander("🔑 Outras API Keys (Opcional)", expanded=True):
            replicate_key = st.text_input("🎭 Replicate Token (InstantCharacter)", type="password", key="replicate_key", help="Gera a imagem mantendo o personagem original")
            huggingface_key = st.text_input("🟠 HuggingFace Token", type="password", key="hf_key")
            openai_key = st.text_input("🟢 OpenAI API Key", type="password", key="openai_key")

        modo_otimizado = st.checkbox("🚀 RTK: Token Saver (Economiza ~40%)", value=True)

        # Configuração do Roteador
        router_config = {
            "gemini_key": gemini_key,
            "replicate_key": replicate_key,
            "huggingface_key": huggingface_key,
            "openai_key": openai_key,
            "priority_order": ["gemini", "replicate", "huggingface", "openai"]
        }

        temp_router = SmartAIRouter(router_config)
        provider_status = temp_router.get_provider_status()

        st.subheader("📊 Status dos Providers")
        for name, status in provider_status.items():
            icon = "✅" if status['ready'] else "❌"
            st.caption(f"{icon} {status['name']}")

    # ========================================================================
    # LAYOUT: 3 COLUNAS
    # ========================================================================
    col1, col2, col3 = st.columns(3)

    # ------------------------------------------------------------------------
    # COLUNA 1: Item A (Referência do Sinal)
    # ------------------------------------------------------------------------
    with col1:
        st.header("📖 Item A: Referência")
        tab_drive_az, tab_busca_pdf, tab_upload = st.tabs(["🗂️ Drive", "🔍 PDF", "📤 Upload"])

        with tab_drive_az:
            st.success("⚡ Conectado à pasta CAPOVILLA (A-Z)")
            col_b1, col_b2 = st.columns([2, 1])
            with col_b1:
                busca_rapida_az = st.text_input("Buscar sinal:", placeholder="Ex: bola", key="busca_drive_az")
            with col_b2:
                letras_disp = st.session_state.gdrive_catalog.obter_letras_sincronizadas()
                if not letras_disp:
                    letras_disp = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
                letra_escolhida = st.selectbox("Letra:", letras_disp, key="sel_letra_az")

            if busca_rapida_az.strip():
                with st.spinner("Buscando..."):
                    arquivos_encontrados = st.session_state.gdrive_catalog.buscar_sinal_drive(busca_rapida_az)
            else:
                with st.spinner(f"Carregando letra {letra_escolhida}..."):
                    arquivos_encontrados = st.session_state.gdrive_catalog.carregar_letra(letra_escolhida)

            if arquivos_encontrados:
                opcoes_arq = [
                    f"{a['termo'].upper()} ({'D' if a['eh_detalhe'] else 'Sinal'} - {a['nome_arquivo']})"
                    for a in arquivos_encontrados
                ]
                idx_arq = st.selectbox(f"Encontrados ({len(arquivos_encontrados)}):", range(len(opcoes_arq)), format_func=lambda i: opcoes_arq[i])
                arq_sel = arquivos_encontrados[idx_arq]

                if st.button("📥 Carregar Imagem", type="primary", use_container_width=True):
                    with st.spinner("Baixando e analisando..."):
                        caminho_jpg = st.session_state.gdrive_catalog.baixar_imagem_sinal(arq_sel['file_id'], arq_sel['nome_arquivo'])
                        if caminho_jpg:
                            st.session_state.imagem_ref_path = caminho_jpg
                            st.session_state.termo_atual = arq_sel['termo'].upper()
                            st.session_state.parametros_extraidos = None

                            # Tenta extrair do PDF
                            if st.session_state.pdf_capovilla is not None and st.session_state.pdf_capovilla.esta_indexado():
                                res_txt = st.session_state.pdf_capovilla.buscar_termo(arq_sel['termo'], max_resultados=2)
                                if res_txt:
                                    st.session_state.parametros_extraidos = st.session_state.pdf_capovilla.extrair_parametros_sinal(res_txt[0]['texto_completo'], arq_sel['termo'])

                            # Tenta Gemini Vision se não achou texto
                            if not st.session_state.parametros_extraidos:
                                chave_ativa = gemini_key or obter_gemini_secret()
                                if chave_ativa:
                                    ai_helper = AIGenerator()
                                    params_visuais = ai_helper.extrair_parametros_visuais_portugues(chave_ativa, caminho_jpg, arq_sel['termo'])
                                    if params_visuais:
                                        st.session_state.parametros_extraidos = params_visuais
                            st.rerun()
            else:
                st.info("Nenhum arquivo encontrado.")

        with tab_busca_pdf:
            if st.session_state.pdf_capovilla is None:
                st.warning("⚠️ PDF não carregado.")
            else:
                extrator = st.session_state.pdf_capovilla
                if not extrator.esta_indexado():
                    st.warning("⚡ PDF não indexado. Indexe na aba 'PDF'.")
                else:
                    termo_busca = st.text_input("Buscar no PDF:")
                    if st.button("🔍 Buscar"):
                        if termo_busca:
                            st.session_state.resultados_busca_pdf = extrator.buscar_termo(termo_busca)
                            st.session_state.termo_atual = termo_busca.upper()
                    if st.session_state.resultados_busca_pdf:
                        opcoes = [f"Pág. {r['pagina']} — {r.get('tipo', 'Resultado')}" for r in st.session_state.resultados_busca_pdf]
                        idx_sel = st.selectbox("Resultados:", range(len(opcoes)), format_func=lambda i: opcoes[i])
                        item_escolhido = st.session_state.resultados_busca_pdf[idx_sel]
                        pag_sel = item_escolhido['pagina']

                        caminho_pag = f"assets/referencias/capovilla_p{pag_sel}.png"
                        if not os.path.exists(caminho_pag):
                            extrator.renderizar_pagina(pag_sel).save(caminho_pag)

                        st.session_state.imagem_ref_path = caminho_pag
                        st.session_state.parametros_extraidos = extrator.extrair_parametros_sinal(item_escolhido['texto_completo'], st.session_state.termo_atual)

        with tab_upload:
            uploaded_ref = st.file_uploader("Upload ref", type=['png', 'jpg', 'jpeg'])
            if uploaded_ref is not None and st.session_state.ultimo_upload_nome != uploaded_ref.name:
                caminho_salvo = f"assets/referencias/temp_ref_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                Image.open(uploaded_ref).convert("RGB").save(caminho_salvo, format="PNG")
                st.session_state.imagem_ref_path = caminho_salvo
                st.session_state.ultimo_upload_nome = uploaded_ref.name

                with st.spinner("Analisando..."):
                    chave_ativa = gemini_key or obter_gemini_secret()
                    params_detectados, termo_sugerido = analisar_imagem_upload(caminho_salvo, uploaded_ref.name, chave_ativa)
                    if termo_sugerido: st.session_state.termo_atual = termo_sugerido
                    if params_detectados: st.session_state.parametros_extraidos = params_detectados
                st.rerun()

        if st.session_state.imagem_ref_path and os.path.exists(st.session_state.imagem_ref_path):
            st.image(st.session_state.imagem_ref_path, caption=f"Referência: {st.session_state.termo_atual}", use_container_width=True)

            with st.expander("✂️ Recortar Sinal", expanded=False):
                img_orig = Image.open(st.session_state.imagem_ref_path)
                larg, alt = img_orig.size
                c1, c2 = st.columns(2)
                with c1:
                    topo = st.slider("Topo (%)", 0, 90, 0)
                    esq = st.slider("Esq (%)", 0, 90, 0)
                with c2:
                    base = st.slider("Base (%)", 10, 100, 100)
                    direita = st.slider("Dir (%)", 10, 100, 100)
                
                if base > topo and direita > esq:
                    caixa = (int(larg*esq/100), int(alt*topo/100), int(larg*direita/100), int(alt*base/100))
                    st.image(img_orig.crop(caixa), caption="Prévia", use_container_width=True)
                    if st.button("✅ Aplicar Recorte"):
                        caminho_crop = "assets/referencias/recorte_focado_atual.png"
                        img_orig.crop(caixa).save(caminho_crop)
                        st.session_state.imagem_ref_path = caminho_crop
                        st.rerun()

        st.divider()
        st.subheader("🔧 Parâmetros (Opcional)")
        params = st.session_state.parametros_extraidos or {}
        
        termo = st.text_input("Nome do Sinal", value=st.session_state.termo_atual)
        st.session_state.termo_atual = termo

        with st.expander("Ajustar Parâmetros Manuais"):
            categoria = st.selectbox("Categoria", CATEGORIAS)
            configuracoes = st.multiselect("Configuração de Mão", CONFIGURACOES_MAO)
            ponto_articulacao = st.selectbox("Ponto de Articulação", PONTOS_ARTICULACAO, index=PONTOS_ARTICULACAO.index(params.get('ponto_articulacao', '')) if params.get('ponto_articulacao') in PONTOS_ARTICULACAO else 0)
            movimentos = st.multiselect("Movimento", TIPOS_MOVIMENTO)
            orientacao = st.selectbox("Orientação", ORIENTACOES, index=ORIENTACOES.index(params.get('orientacao', '')) if params.get('orientacao') in ORIENTACOES else 0)
            expressoes = st.multiselect("Expressão Facial", EXPRESSOES, default=["Neutra"])

        observacoes = st.text_area("Descrição / Obs", value=params.get('descricao_completa', ''), height=100)

    # ------------------------------------------------------------------------
    # COLUNA 2: Item B (Personagem Base)
    # ------------------------------------------------------------------------
    with col2:
        st.header("👤 Item B: Personagem")
        opcao = st.radio("Personagem", ["Usar salvo", "Upload"])
        imagem_personagem_path = None

        if opcao == "Usar salvo":
            personagens = listar_personagens_disponiveis()
            if personagens:
                p_sel = st.selectbox("Selecione", personagens)
                imagem_personagem_path = f"assets/personagens/{p_sel}"
                st.image(imagem_personagem_path, use_container_width=True)
            else:
                st.info("Nenhum salvo. Faça upload.")
        else:
            uploaded_char = st.file_uploader("Upload personagem", type=['png', 'jpg', 'jpeg'])
            if uploaded_char:
                nome_personagem = st.text_input("Nome", value="Jefferson")
                imagem_personagem_path = f"assets/personagens/{nome_personagem or 'temp_char'}.png"
                
                # BUG FIX: Converte para PNG real antes de salvar
                img_pil = Image.open(uploaded_char).convert("RGB")
                img_pil.save(imagem_personagem_path, format="PNG")
                
                st.success(f"✅ Salvo: {nome_personagem}")
                st.image(imagem_personagem_path, use_container_width=True)

    # ------------------------------------------------------------------------
    # COLUNA 3: Item C (Geração)
    # ------------------------------------------------------------------------
    with col3:
        st.header("✨ Item C: Gerado")

        tem_ref = bool(st.session_state.imagem_ref_path and os.path.exists(st.session_state.imagem_ref_path))
        tem_char = bool(imagem_personagem_path and os.path.exists(imagem_personagem_path))
        tem_termo = bool(termo.strip() or observacoes.strip())
        
        faltando = []
        if not tem_ref: faltando.append("Referência")
        if not tem_char: faltando.append("Personagem")
        if not tem_termo: faltando.append("Nome do Sinal")

        pode_gerar = (len(faltando) == 0)

        if not pode_gerar:
            st.warning(f"⚠️ **Falta:** {', '.join(faltando)}")
        else:
            st.success("✅ Tudo pronto!")

        def construir_prompt_atual():
            # AGORA USA O NOVO MÉTODO DO INSTANTCHARACTER
            return st.session_state.prompt_engine.gerar_prompt_instant_character(
                termo=termo.strip() or "SINAL",
                configuracao_mao=configuracoes,
                ponto_articulacao=ponto_articulacao,
                movimento=movimentos,
                orientacao=orientacao,
                expressao=expressoes,
                observacoes=observacoes
            )

        if st.button("🚀 Gerar Ilustração 2D", disabled=not pode_gerar, type="primary", use_container_width=True):
            st.session_state.mostrar_fallback_free = False
            st.session_state.erro_geracao_msg = ""

            with st.spinner("🎨 Gerando ilustração (tentando Gemini -> Replicate)..."):
                prompt = construir_prompt_atual()
                st.session_state.ultimo_prompt = prompt
                nome_base = (termo.strip() or "sinal").lower().replace(' ', '_')
                nome_arquivo = f"{nome_base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

                ai_gen = AIGenerator(provider="smart-router", config=router_config)
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

        # ÁREA DE FALLBACK (SE O GEMINI FALHAR)
        if st.session_state.mostrar_fallback_free:
            st.error(f"⚠️ **Aviso Principal:** {st.session_state.erro_geracao_msg}")
            st.info("💡 **Deseja forçar a geração usando o InstantCharacter via Replicate? (Mantém seu personagem)**")

            rep_key_fb = st.text_input("Replicate API Token (se não configurado na barra lateral)", type="password", key="rep_key_fb")
            chave_rep_final = rep_key_fb or replicate_key

            if st.button("🎭 Sim, gerar com InstantCharacter", type="primary", use_container_width=True):
                if not chave_rep_final:
                    st.warning("Insira seu Replicate API Token.")
                else:
                    with st.spinner("🎭 Aplicando o sinal no seu personagem (aguarde ~30s)..."):
                        prompt = st.session_state.ultimo_prompt or construir_prompt_atual()
                        nome_arquivo = f"instant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        
                        ai_gen = AIGenerator(
                            provider="smart-router",
                            config={"replicate_key": chave_rep_final, "priority_order": ["replicate"]}
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
                            st.error(f"❌ Falha no InstantCharacter: {msg}")

        # EXIBE A IMAGEM FINAL
        if st.session_state.imagem_gerada and os.path.exists(st.session_state.imagem_gerada):
            st.image(st.session_state.imagem_gerada, caption="Resultado", use_container_width=True)
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