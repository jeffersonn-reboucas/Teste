"""
Gerador Multimodal Real de Ilustrações de Libras
Fusão de Item A (Referência Recortada) + Item B (Ficha de Personagem 2D) via Google Gemini API
"""
import os
import io
import re
import base64
import urllib.parse
import requests
from pathlib import Path
from PIL import Image


class SmartAIRouter:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def get_provider_status(self) -> dict:
        gemini_key = self.config.get("gemini_key") or os.getenv("GEMINI_API_KEY")
        hf_key = self.config.get("huggingface_key") or os.getenv("HUGGINGFACE_TOKEN")
        openai_key = self.config.get("openai_key") or os.getenv("OPENAI_API_KEY")
        replicate_key = self.config.get("replicate_key") or os.getenv("REPLICATE_API_TOKEN")

        return {
            "gemini": {
                "name": "1️⃣ Google Gemini Multimodal (AI Studio)",
                "ready": bool(gemini_key),
                "requires_key": True
            },
            "pollinations": {
                "name": "2️⃣ Pollinations.ai (Flux - Free)",
                "ready": True,
                "requires_key": False
            },
            "huggingface": {
                "name": "3️⃣ HuggingFace (FLUX.1-schnell)",
                "ready": bool(hf_key),
                "requires_key": True
            },
            "openai": {
                "name": "4️⃣ OpenAI (DALL-E 3)",
                "ready": bool(openai_key),
                "requires_key": True
            },
            "replicate": {
                "name": "5️⃣ Replicate (Flux)",
                "ready": bool(replicate_key),
                "requires_key": True
            }
        }


class AIGenerator:
    def __init__(self, provider: str = "smart-router", config: dict = None):
        self.provider = provider
        self.config = config or {}

    def _encode_image_b64(self, image_path: str) -> tuple:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            img.thumbnail((1024, 1024))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=90)
            b64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return b64_data, "image/jpeg"

    def listar_modelos_gemini_disponiveis(self, api_key: str) -> list:
        """Consulta a API do Google AI Studio para descobrir os nomes exatos dos modelos ativos na conta"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                modelos = resp.json().get("models", [])
                return [m.get("name", "").replace("models/", "") for m in modelos]
        except Exception:
            pass
        return []
def extrair_parametros_visuais_portugues(self, api_key: str, img_path: str, termo: str = "") -> dict:
        """
        Olha para a imagem .jpg do sinal (com ou sem texto escrito nela) usando o Gemini Vision
        e devolve a descrição técnica em Português + parâmetros estruturados.
        """
        if not api_key or not img_path or not os.path.exists(img_path):
            return None

        b64_img, mime_img = self._encode_image_b64(img_path)
        prompt_extracao = (
            f"Analise esta ilustração do dicionário de Libras para o sinal '{termo}'. "
            "Se houver texto na imagem, transcreva a descrição da execução do sinal. "
            "Se houver APENAS o desenho (sem texto), descreva tecnicamente em Português como o sinal é executado "
            "observando o desenho (configuração das mãos, orientação da palma, ponto de articulação no corpo/espaço, "
            "movimento indicado pelas setas e expressão facial).\n"
            "Responda APENAS em formato texto direto e conciso (máximo 3 frases), no estilo do dicionário Capovilla."
        )

        partes = [
            {"inlineData": {"mimeType": mime_img, "data": b64_img}},
            {"text": prompt_extracao}
        ]

        for mod in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={api_key}"
            try:
                r = requests.post(url, json={"contents": [{"parts": partes}]}, timeout=25)
                if r.status_code == 200:
                    desc_pt = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if desc_pt:
                        desc_lower = desc_pt.lower()
                        orientacao = "Palma para cima"
                        if "palma para baixo" in desc_lower:
                            orientacao = "Palma para baixo"
                        elif "palma para frente" in desc_lower or "palma para a frente" in desc_lower:
                            orientacao = "Palma para frente"
                        elif "palma para trás" in desc_lower or "palma para o corpo" in desc_lower:
                            orientacao = "Palma para trás"
                        elif "palma para dentro" in desc_lower or "palma para a esquerda" in desc_lower:
                            orientacao = "Palma para dentro"

                        ponto = "Espaço neutro"
                        for p_cand, nome_p in [
                            ("queixo", "Queixo"), ("testa", "Testa"), ("boca", "Boca"),
                            ("peito", "Peito"), ("ombro", "Ombro"), ("cabeça", "Cabeça"), ("rosto", "Rosto")
                        ]:
                            if p_cand in desc_lower:
                                ponto = nome_p
                                break

                        return {
                            "configuracao_mao": [],
                            "orientacao": orientacao,
                            "ponto_articulacao": ponto,
                            "movimento": [],
                            "descricao_completa": desc_pt
                        }
            except Exception:
                continue
        return None
    def gerar_imagem(
        self,
        prompt: str,
        imagem_referencia_a: str = None,
        imagem_personagem_b: str = None,
        output_dir: str = "output",
        nome_arquivo: str = "sinal_gerado.png"
    ) -> tuple:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        caminho_saida = str(Path(output_dir) / nome_arquivo)

        ordem = self.config.get(
            "priority_order",
            ["gemini", "huggingface", "openai", "replicate", "pollinations"]
        )

        erros_acumulados = []

        for prov in ordem:
            if prov == "gemini":
                key = self.config.get("gemini_key") or os.getenv("GEMINI_API_KEY")
                if not key:
                    continue
                ok, msg = self._gerar_com_gemini(
                    key, prompt, imagem_referencia_a, imagem_personagem_b, caminho_saida
                )
                if ok:
                    return True, msg, caminho_saida
                erros_acumulados.append(f"Gemini: {msg}")

            elif prov == "pollinations":
                ok, msg = self._gerar_com_pollinations(
                    prompt, imagem_referencia_a, imagem_personagem_b, caminho_saida
                )
                if ok:
                    return True, msg, caminho_saida
                erros_acumulados.append(f"Pollinations: {msg}")

            elif prov == "huggingface":
                key = self.config.get("huggingface_key") or os.getenv("HUGGINGFACE_TOKEN")
                if not key:
                    continue
                ok, msg = self._gerar_com_huggingface(key, prompt, caminho_saida)
                if ok:
                    return True, msg, caminho_saida
                erros_acumulados.append(f"HuggingFace: {msg}")

            elif prov == "openai":
                key = self.config.get("openai_key") or os.getenv("OPENAI_API_KEY")
                if not key:
                    continue
                ok, msg = self._gerar_com_openai(key, prompt, caminho_saida)
                if ok:
                    return True, msg, caminho_saida
                erros_acumulados.append(f"OpenAI: {msg}")

        resumo_erros = " | ".join(erros_acumulados) if erros_acumulados else "Nenhum provedor configurado respondeu."
        return False, resumo_erros, None

    def _analisar_sinal_com_gemini_vision(self, api_key: str, img_ref: str, img_char: str, prompt_usuario: str) -> str:
        """
        Usa o Gemini Vision (100% gratuito) para ler o recorte do Capovilla + Ficha do Personagem
        e produzir uma descrição anatômica cirúrgica em inglês para qualquer gerador de imagem.
        """
        partes = []
        if img_ref and os.path.exists(img_ref):
            b64_ref, mime_ref = self._encode_image_b64(img_ref)
            partes.append({"inlineData": {"mimeType": mime_ref, "data": b64_ref}})

        instrucao = (
            "Analyze this Brazilian Sign Language (Libras) dictionary illustration. "
            "Describe in concise English (max 90 words) ONLY the exact physical pose: "
            "which hand is active (left/right/both), exact handshape and finger positions, palm orientation, "
            "where the hand touches or hovers near the body/face, facial expression, and movement arrow direction. "
            f"Additional context: {prompt_usuario[:400]}"
        )
        partes.append({"text": instrucao})

        for mod_vision in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod_vision}:generateContent?key={api_key}"
            try:
                r = requests.post(url, json={"contents": [{"parts": partes}]}, timeout=25)
                if r.status_code == 200:
                    texto = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    return texto.strip()
            except Exception:
                continue
        return ""

    def _gerar_com_gemini(self, api_key: str, prompt: str, img_ref: str, img_char: str, caminho_saida: str) -> tuple:
        """
        1. Descobre automaticamente os modelos de geração de imagem ativos na chave do usuário.
        2. Envia a Ficha de Personagem (Item B) + Recorte do Sinal (Item A) juntos.
        """
        modelos_conta = self.listar_modelos_gemini_disponiveis(api_key)

        # Filtrar modelos capazes de gerar imagem nativamente (Nano Banana / Flash Image / Imagen)
        candidatos_img = [
            m for m in modelos_conta
            if ("image" in m.lower() or "exp" in m.lower()) and "embedding" not in m.lower()
        ]
        # Garantir modelos conhecidos no topo da tentativa
        for padrao in [
            "gemini-2.0-flash-preview-image-generation",
            "gemini-2.0-flash-exp-image-generation",
            "gemini-2.5-flash-image-preview",
            "gemini-2.0-flash"
        ]:
            if padrao in modelos_conta and padrao not in candidatos_img:
                candidatos_img.insert(0, padrao)

        if not candidatos_img:
            candidatos_img = ["gemini-2.0-flash-preview-image-generation", "gemini-2.0-flash"]

        partes = []
        if img_char and os.path.exists(img_char):
            b64_char, mime_char = self._encode_image_b64(img_char)
            partes.append({"text": "CHARACTER SHEET (Keep this exact 2D male teacher character: curly dark hair, round glasses, short goatee, black v-neck t-shirt, flat cel-shaded vector style):"})
            partes.append({"inlineData": {"mimeType": mime_char, "data": b64_char}})

        if img_ref and os.path.exists(img_ref):
            b64_ref, mime_ref = self._encode_image_b64(img_ref)
            partes.append({"text": "SIGN POSE REFERENCE (Copy the exact handshape, fingers, arm position, and movement arrows from this Libras diagram):"})
            partes.append({"inlineData": {"mimeType": mime_ref, "data": b64_ref}})

        instrucao_fusao = (
            "Generate a single clean 2D vector educational flashcard illustration on a solid white background. "
            "Draw ONLY the waist-up view of the male teacher character from CHARACTER SHEET performing the exact "
            "Brazilian Sign Language (Libras) gesture shown in SIGN POSE REFERENCE. "
            "High anatomical precision on all 5 fingers, clean black outlines, flat cel shading, didactic movement arrows. "
            "Do NOT draw multiple panels, grids, text labels, or decorative frames.\n\n"
            f"Sign details: {prompt[:700]}"
        )
        partes.append({"text": instrucao_fusao})

        erros = []
        for modelo in candidatos_img[:4]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": partes}],
                "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
            }
            try:
                resp = requests.post(url, json=payload, timeout=65)
                if resp.status_code == 200:
                    for cand in resp.json().get("candidates", []):
                        for part in cand.get("content", {}).get("parts", []):
                            if "inlineData" in part and "data" in part["inlineData"]:
                                img_bytes = base64.b64decode(part["inlineData"]["data"])
                                with open(caminho_saida, "wb") as f:
                                    f.write(img_bytes)
                                return True, f"Fusão Multimodal Gerada ({modelo})"
                else:
                    msg = resp.json().get("error", {}).get("message", f"HTTP {resp.status_code}")
                    erros.append(f"{modelo}: {msg[:90]}")
            except Exception as e:
                erros.append(f"{modelo}: {str(e)[:80]}")

        # Tentativa via Imagen 3 enriquecido pelo Gemini Vision (lê a imagem do sinal antes!)
        modelos_imagen = [m for m in modelos_conta if "imagen" in m.lower()]
        if not modelos_imagen:
            modelos_imagen = ["imagen-3.0-generate-002"]

        descricao_visual = self._analisar_sinal_com_gemini_vision(api_key, img_ref, img_char, prompt)
        prompt_imagen = (
            "Clean 2D didactic vector illustration, flat cel shading, solid white background, educational flashcard style. "
            "Waist-up portrait of a slim Brazilian male teacher with curly dark hair, round glasses, short goatee, wearing a plain black v-neck t-shirt. "
            f"He is performing a Brazilian Sign Language gesture: {descricao_visual or prompt[:500]}. "
            "Anatomical precision on all 5 fingers, sharp black outlines, no text, no frames, no 3D, no anime."
        )

        for mod_img in modelos_imagen[:2]:
            url_img = f"https://generativelanguage.googleapis.com/v1beta/models/{mod_img}:predict?key={api_key}"
            try:
                r_img = requests.post(
                    url_img,
                    json={"instances": [{"prompt": prompt_imagen[:950]}], "parameters": {"sampleCount": 1}},
                    timeout=60
                )
                if r_img.status_code == 200:
                    preds = r_img.json().get("predictions", [])
                    if preds and "bytesBase64Encoded" in preds[0]:
                        with open(caminho_saida, "wb") as f:
                            f.write(base64.b64decode(preds[0]["bytesBase64Encoded"]))
                        return True, f"Gerado via Gemini Vision + {mod_img}"
            except Exception:
                pass

        # Guardar descrição visual para ajudar o fallback Pollinations caso necessário
        self.config["ultima_descricao_vision"] = descricao_visual
        return False, " | ".join(erros[:2]) if erros else "Modelo de imagem não habilitado nesta chave."

    def _gerar_com_pollinations(self, prompt: str, img_ref: str, img_char: str, caminho_saida: str) -> tuple:
        """
        Usa a análise visual do Gemini Vision (que leu o recorte do Capovilla) + Estilo Ficha 2D
        para que até o modo Free desenhe o personagem correto!
        """
        gemini_key = self.config.get("gemini_key") or os.getenv("GEMINI_API_KEY")
        descricao_vision = self.config.get("ultima_descricao_vision", "")

        if not descricao_vision and gemini_key and img_ref:
            descricao_vision = self._analisar_sinal_com_gemini_vision(gemini_key, img_ref, img_char, prompt)

        base_pose = descricao_vision if descricao_vision else re.sub(r'[^a-zA-Z0-9\s,]', ' ', prompt)[:220]
        base_pose_limpa = " ".join(re.sub(r'[^a-zA-Z0-9\s,.-]', ' ', base_pose).split())[:320]

        estilo_personagem_fixo = (
            "clean 2D vector didactic flashcard illustration, flat cel shading, sharp black outlines, "
            "solid white background, waist-up front view of a slim Brazilian male teacher with short curly dark hair, "
            "round glasses, short goatee beard, wearing a plain black v-neck t-shirt, clear 5 fingers hand gesture: "
        )

        texto_final = f"{estilo_personagem_fixo} {base_pose_limpa}, no frame, no circle, no text"
        prompt_encoded = urllib.parse.quote(texto_final)

        pollinations_key = self.config.get("pollinations_key") or os.getenv("POLLINATIONS_API_KEY")
        if not pollinations_key:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "POLLINATIONS_API_KEY" in st.secrets:
                    pollinations_key = st.secrets["POLLINATIONS_API_KEY"]
            except Exception:
                pass

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        if pollinations_key:
            headers["Authorization"] = f"Bearer {pollinations_key}"

        tentativas = [
            f"https://image.pollinations.ai/prompt/{prompt_encoded}?model=flux&width=768&height=768&nologo=true&seed=42",
            f"https://image.pollinations.ai/prompt/{prompt_encoded}?model=turbo&width=768&height=768&nologo=true"
        ]

        for url in tentativas:
            try:
                r = requests.get(url, headers=headers, timeout=55)
                if r.status_code == 200 and len(r.content) > 1500:
                    with open(caminho_saida, "wb") as f:
                        f.write(r.content)
                    extra = " + Leitura Visual Gemini" if descricao_vision else ""
                    return True, f"Gerado via Pollinations.ai (Estilo Vetorial 2D{extra})"
            except Exception:
                continue

        return False, "Servidores do Pollinations temporariamente ocupados."

    def _gerar_com_huggingface(self, token: str, prompt: str, caminho_saida: str) -> tuple:
        url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            resp = requests.post(url, headers=headers, json={"inputs": prompt[:800]}, timeout=60)
            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(caminho_saida, "wb") as f:
                    f.write(resp.content)
                return True, "Gerado via HuggingFace (FLUX.1-schnell)"
            return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, str(e)

    def _gerar_com_openai(self, api_key: str, prompt: str, caminho_saida: str) -> tuple:
        url = "https://api.openai.com/v1/images/generations"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": "dall-e-3", "prompt": prompt[:3500], "n": 1, "size": "1024x1024"}
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                img_url = resp.json()["data"][0]["url"]
                img_data = requests.get(img_url, timeout=30).content
                with open(caminho_saida, "wb") as f:
                    f.write(img_data)
                return True, "Gerado via OpenAI (DALL-E 3)"
            return False, resp.json().get("error", {}).get("message", f"HTTP {resp.status_code}")
        except Exception as e:
            return False, str(e)