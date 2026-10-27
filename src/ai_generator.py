"""
Gerador Multimodal Real de Ilustrações de Libras
Fusão de Item A (Referência) + Item B (Ficha de Personagem 2D)
Provedores: Gemini (Multimodal), Replicate (InstantCharacter), HuggingFace, OpenAI.
"""
import os
import io
import re
import base64
import urllib.parse
import requests
import time
from pathlib import Path
from PIL import Image


class SmartAIRouter:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def get_provider_status(self) -> dict:
        gemini_key = self.config.get("gemini_key") or os.getenv("GEMINI_API_KEY")
        replicate_key = self.config.get("replicate_key") or os.getenv("REPLICATE_API_TOKEN")
        hf_key = self.config.get("huggingface_key") or os.getenv("HUGGINGFACE_TOKEN")
        openai_key = self.config.get("openai_key") or os.getenv("OPENAI_API_KEY")

        return {
            "gemini": {
                "name": "1️⃣ Google Gemini Multimodal",
                "ready": bool(gemini_key),
                "requires_key": True
            },
            "replicate": {
                "name": "2️⃣ Replicate (InstantCharacter)",
                "ready": bool(replicate_key),
                "requires_key": True
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

        # Nova ordem: Gemini -> Replicate -> HuggingFace -> OpenAI
        ordem = self.config.get(
            "priority_order",
            ["gemini", "replicate", "huggingface", "openai"]
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

            elif prov == "replicate":
                key = self.config.get("replicate_key") or os.getenv("REPLICATE_API_TOKEN")
                if not key:
                    continue
                ok, msg = self._gerar_com_replicate(
                    key, prompt, imagem_referencia_a, imagem_personagem_b, caminho_saida
                )
                if ok:
                    return True, msg, caminho_saida
                erros_acumulados.append(f"Replicate: {msg}")

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
        modelos_conta = self.listar_modelos_gemini_disponiveis(api_key)

        candidatos_img = [
            m for m in modelos_conta
            if ("image" in m.lower() or "exp" in m.lower()) and "embedding" not in m.lower()
        ]
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

        self.config["ultima_descricao_vision"] = descricao_visual
        return False, " | ".join(erros[:2]) if erros else "Modelo de imagem não habilitado nesta chave."

    def _gerar_com_replicate(self, api_key: str, prompt: str, img_ref: str, img_char: str, caminho_saida: str) -> tuple:
        """
        Gera imagem usando a API do Replicate (Modelo InstantCharacter).
        Usa a biblioteca requests em vez do SDK do Replicate para manter o código leve.
        """
        if not img_ref or not img_char:
            return False, "As duas imagens (Referência e Personagem) são obrigatórias para o InstantCharacter."

        try:
            b64_ref, mime_ref = self._encode_image_b64(img_ref)
            b64_char, mime_char = self._encode_image_b64(img_char)
            
            # O Replicate aceita imagens no formato Data URI
            ref_data_uri = f"data:{mime_ref};base64,{b64_ref}"
            char_data_uri = f"data:{mime_char};base64,{b64_char}"

            # Endpoint da API do Replicate para o InstantCharacter
            url = "https://api.replicate.com/v1/models/bytedance/instant-character/predictions"
            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "input": {
                    "prompt": prompt,
                    "subject_image": char_data_uri,   # Item B (Seu personagem)
                    "control_image": ref_data_uri,    # Item A (O sinal)
                    "width": 1024,
                    "height": 1024
                }
            }

            # 1. Cria a predição
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code not in (200, 201):
                return False, f"Erro API Replicate (HTTP {resp.status_code}): {resp.text[:100]}"

            prediction = resp.json()
            get_url = prediction.get("urls", {}).get("get")
            
            if not get_url:
                return False, "Não foi possível obter URL de polling no Replicate."

            # 2. Polling (Aguardar a geração da imagem)
            # O Replicate demora cerca de 10 a 30 segundos para gerar
            for _ in range(30): # Tentar por 60 segundos (30 * 2s)
                time.sleep(2)
                poll_resp = requests.get(get_url, headers=headers, timeout=15)
                if poll_resp.status_code == 200:
                    poll_data = poll_resp.json()
                    status = poll_data.get("status")
                    
                    if status == "succeeded":
                        output = poll_data.get("output")
                        if isinstance(output, list) and len(output) > 0:
                            img_url = output[0]
                        elif isinstance(output, str):
                            img_url = output
                        else:
                            return False, "Formato de saída do Replicate desconhecido."
                        
                        # 3. Baixa a imagem final
                        img_resp = requests.get(img_url, timeout=30)
                        if img_resp.status_code == 200:
                            with open(caminho_saida, "wb") as f:
                                f.write(img_resp.content)
                            return True, "Gerado via InstantCharacter (Replicate)"
                        return False, "Falha ao baixar imagem gerada do Replicate."
                        
                    elif status == "failed":
                        erro_msg = poll_data.get("error", "Motivo desconhecido")
                        return False, f"Replicate falhou: {erro_msg}"
            
            return False, "Timeout: O Replicate demorou muito para responder."
            
        except Exception as e:
            return False, f"Erro de conexão Replicate: {str(e)[:100]}"

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