"""
Gerador Multimodal de Ilustrações de Libras
Prioridade #1: Google Gemini API (Google AI Studio)
Fallback Gratuito: Pollinations.ai (Flux)
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
                "name": "1️⃣ Google Gemini API (Google AI Studio)",
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
            img.save(buffer, format="JPEG", quality=85)
            b64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return b64_data, "image/jpeg"

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
                ok, msg = self._gerar_com_pollinations(prompt, caminho_saida)
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

    def _gerar_com_gemini(self, api_key: str, prompt: str, img_ref: str, img_char: str, caminho_saida: str) -> tuple:
        partes = []

        if img_ref and os.path.exists(img_ref):
            b64_ref, mime_ref = self._encode_image_b64(img_ref)
            partes.append({"inlineData": {"mimeType": mime_ref, "data": b64_ref}})

        if img_char and os.path.exists(img_char):
            b64_char, mime_char = self._encode_image_b64(img_char)
            partes.append({"inlineData": {"mimeType": mime_char, "data": b64_char}})

        instrucao_multimodal = (
            "Generate a high-quality 2D pedagogical illustration for Brazilian Sign Language (Libras). "
            "Use the SECOND attached image as the exact character model (keep the same face, hair, clothes, and 2D vector style). "
            "Use the FIRST attached image (dictionary technical drawing) and the following description to position the character's hands, "
            "fingers, and facial expression accurately executing the sign. Clean white background, didactic flashcards style.\n\n"
            f"Sign Details:\n{prompt}"
        )
        partes.append({"text": instrucao_multimodal})

        modelos_gemini_img = [
            "gemini-2.5-flash-image-preview",
            "gemini-2.0-flash-preview-image-generation",
            "gemini-2.0-flash-exp-image-generation",
            "gemini-2.0-flash-exp"
        ]

        ultimo_erro = ""

        for modelo in modelos_gemini_img:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": partes}],
                "generationConfig": {
                    "responseModalities": ["TEXT", "IMAGE"]
                }
            }
            try:
                resp = requests.post(url, json=payload, timeout=60)
                if resp.status_code == 200:
                    dados = resp.json()
                    candidatos = dados.get("candidates", [])
                    for cand in candidatos:
                        for part in cand.get("content", {}).get("parts", []):
                            if "inlineData" in part and "data" in part["inlineData"]:
                                img_bytes = base64.b64decode(part["inlineData"]["data"])
                                with open(caminho_saida, "wb") as f:
                                    f.write(img_bytes)
                                return True, f"Gerado via Google Gemini ({modelo})"
                else:
                    msg_api = resp.json().get("error", {}).get("message", f"HTTP {resp.status_code}")
                    ultimo_erro = f"{modelo}: {msg_api}"
            except Exception as e:
                ultimo_erro = str(e)

        url_imagen = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={api_key}"
        try:
            resp_img = requests.post(
                url_imagen,
                json={
                    "instances": [{"prompt": instrucao_multimodal[:900]}],
                    "parameters": {"sampleCount": 1}
                },
                timeout=60
            )
            if resp_img.status_code == 200:
                preds = resp_img.json().get("predictions", [])
                if preds and "bytesBase64Encoded" in preds[0]:
                    img_bytes = base64.b64decode(preds[0]["bytesBase64Encoded"])
                    with open(caminho_saida, "wb") as f:
                        f.write(img_bytes)
                    return True, "Gerado via Google Gemini (Imagen 3)"
        except Exception:
            pass

        return False, ultimo_erro or "A chave Gemini informada não retornou imagem."

    def _gerar_com_pollinations(self, prompt: str, caminho_saida: str) -> tuple:
        prompt_sanitizado = re.sub(r'[^a-zA-Z0-9\s,.-]', '', prompt)
        resumo = " ".join(prompt_sanitizado.split())[:300]
        texto_final = f"2D vector flat illustration Brazilian sign language Libras character: {resumo}"
        prompt_encoded = urllib.parse.quote(texto_final)

        pollinations_key = self.config.get("pollinations_key") or os.getenv("POLLINATIONS_API_KEY")
        if not pollinations_key:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "POLLINATIONS_API_KEY" in st.secrets:
                    pollinations_key = st.secrets["POLLINATIONS_API_KEY"]
            except Exception:
                pass

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        if pollinations_key:
            headers["Authorization"] = f"Bearer {pollinations_key}"

        urls = [
            f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=768&height=768&model=flux&nologo=true&seed=42",
            f"https://image.pollinations.ai/prompt/{prompt_encoded}?model=turbo&nologo=true"
        ]

        for url in urls:
            try:
                r = requests.get(url, headers=headers, timeout=50)
                if r.status_code == 200 and len(r.content) > 2000:
                    with open(caminho_saida, "wb") as f:
                        f.write(r.content)
                    return True, "Gerado com sucesso via Pollinations.ai"
            except Exception:
                continue

        return False, "Pollinations indisponível de momento."

    def _gerar_com_huggingface(self, token: str, prompt: str, caminho_saida: str) -> tuple:
        url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            resp = requests.post(url, headers=headers, json={"inputs": prompt[:800]}, timeout=60)
            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(caminho_saida, "wb") as f:
                    f.write(resp.content)
                return True, "Gerado via HuggingFace (FLUX.1-schnell)"
            return False, f"HTTP {resp.status_code}: {resp.text[:120]}"
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