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
        """
        Gera ilustração via Google AI Studio usando Imagen 3 oficial.
        """
        instrucao_completa = (
            "2D vector didactic illustration for Brazilian Sign Language (Libras), "
            "clean white background, flat color, clear handshape and arm articulation. "
            f"Details: {prompt[:800]}"
        )

        # 1. Tentativa com Imagen 3 oficial da Google
        url_imagen = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={api_key}"
        payload_imagen = {
            "instances": [{"prompt": instrucao_completa}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "1:1",
                "outputOptions": {"mimeType": "image/png"}
            }
        }

        try:
            resp = requests.post(url_imagen, json=payload_imagen, timeout=60)
            if resp.status_code == 200:
                dados = resp.json()
                preds = dados.get("predictions", [])
                if preds and "bytesBase64Encoded" in preds[0]:
                    img_bytes = base64.b64decode(preds[0]["bytesBase64Encoded"])
                    with open(caminho_saida, "wb") as f:
                        f.write(img_bytes)
                    return True, "Gerado via Google Imagen 3 (Google AI Studio)"
            
            # Se a conta não tiver cota de imagem habilitada no Imagen 3
            msg_erro = resp.json().get("error", {}).get("message", f"HTTP {resp.status_code}")
            return False, f"Imagen 3: {msg_erro}"
        except Exception as e:
            return False, f"Erro na conexão Gemini: {str(e)}"

    def _gerar_com_pollinations(self, prompt: str, caminho_saida: str) -> tuple:
        """
        Geração via Pollinations.ai com tratamento de query e múltiplos endpoints.
        """
        # Sanitização: remove caracteres não-ASCII e pontuações complexas
        prompt_limpo = re.sub(r'[^a-zA-Z0-9\s,]', ' ', prompt)
        resumo = " ".join(prompt_limpo.split())[:200]
        
        texto_final = f"vector flat illustration Libras sign language pose didactic character, {resumo}"
        prompt_encoded = urllib.parse.quote_plus(texto_final)

        pollinations_key = self.config.get("pollinations_key") or os.getenv("POLLINATIONS_API_KEY")
        if not pollinations_key:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "POLLINATIONS_API_KEY" in st.secrets:
                    pollinations_key = st.secrets["POLLINATIONS_API_KEY"]
            except Exception:
                pass

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        if pollinations_key:
            headers["Authorization"] = f"Bearer {pollinations_key}"

        tentativas = [
            f"https://image.pollinations.ai/prompt/{prompt_encoded}?model=flux&width=512&height=512&nologo=true&seed=42",
            f"https://image.pollinations.ai/prompt/{prompt_encoded}?model=turbo&width=512&height=512&nologo=true",
            f"https://pollinations.ai/p/{prompt_encoded}?width=512&height=512"
        ]

        for url in tentativas:
            try:
                r = requests.get(url, headers=headers, timeout=40)
                if r.status_code == 200 and len(r.content) > 1500:
                    with open(caminho_saida, "wb") as f:
                        f.write(r.content)
                    return True, "Gerado com sucesso via Pollinations.ai"
            except Exception:
                continue

        return False, "Servidores do Pollinations temporariamente sobrecarregados."

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