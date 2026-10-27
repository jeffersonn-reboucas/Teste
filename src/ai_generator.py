"""
Smart AI Router - Roteador Inteligente de IA com Auto-Fallback
Inspirado no 9Router: Unificação de múltiplos provedores + Fallback automático
Nunca para por falta de crédito ou limite de API!
"""
import os
import base64
import requests
from typing import Optional, Dict, Tuple, List, Any
from pathlib import Path
from datetime import datetime
import json
import time
from abc import ABC, abstractmethod
import streamlit as st


# ==============================================================================
# UTILITÁRIOS
# ==============================================================================

def log_provider_status(provider_name: str, status: str, message: str = ""):
    """Registra status do provider no log"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {provider_name}: {status} - {message}")


# ==============================================================================
# CLASSE BASE ABSTRATA
# ==============================================================================

class BaseAIProvider(ABC):
    """Classe base para todos os provedores de IA"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model_name = ""
        self.requires_api_key = True
        self.supports_vision = False
        self.supports_generation = False

    @abstractmethod
    def analisar_imagens(
        self,
        prompt: str,
        imagem_a: str,
        imagem_b: str
    ) -> Tuple[bool, str]:
        """Analisa imagens e retorna descrição detalhada"""
        pass

    @abstractmethod
    def gerar_imagem(
        self,
        prompt: str,
        output_path: str,
        imagem_init: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """Gera imagem a partir do prompt"""
        pass

    def _carregar_imagem_base64(self, caminho: str) -> str:
        """Carrega imagem e converte para base64"""
        with open(caminho, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def _baixar_e_salvar_imagem(self, url: str, output_path: str, timeout: int = 60) -> bool:
        """Baixa imagem de URL e salva localmente"""
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            log_provider_status(self.model_name, "ERROR", f"Falha no download: {e}")
            return False


# ==============================================================================
# POLLINATIONS.AI - 100% GRATUITO SEM API KEY (FALLBACK UNIVERSAL)
# ==============================================================================

class PollinationsAIProvider(BaseAIProvider):
    """Pollinations.ai - API gratuita sem necessidade de chave"""

    def __init__(self):
        super().__init__(api_key=None)
        self.model_name = "Pollinations.ai (Flux)"
        self.requires_api_key = False
        self.supports_generation = True
        self.supports_vision = False
        self.base_url = "https://image.pollinations.ai/prompt"

    def analisar_imagens(self, prompt: str, imagem_a: str, imagem_b: str) -> Tuple[bool, str]:
        """Pollinations não suporta análise de imagens"""
        return False, "Pollinations.ai não suporta análise multimodal"

    def gerar_imagem(
        self,
        prompt: str,
        output_path: str,
        imagem_init: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        try:
            # Otimizar prompt para Pollinations
            prompt_otimizado = f"{prompt}, 2D flat illustration, clean linework, educational sign language reference, pedagogical style, white background, centered composition"

            # URL de geração (Pollinations aceita prompt direto na URL)
            # Formato: https://image.pollinations.ai/prompt/{prompt}?width=1024&height=1024&model=flux&seed={seed}
            import urllib.parse
            encoded_prompt = urllib.parse.quote(prompt_otimizado[:1000])  # Limite de caracteres

            url = f"{self.base_url}/{encoded_prompt}"
            params = {
                "width": 1024,
                "height": 1024,
                "model": "flux",  # Flux ou turbo
                "seed": int(time.time())  # Seed aleatório
            }

            # Construir URL completa
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{url}?{query_string}"

            log_provider_status(self.model_name, "GENERATING", "Gerando imagem...")

            # Baixar imagem diretamente
            if self._baixar_e_salvar_imagem(full_url, output_path, timeout=120):
                log_provider_status(self.model_name, "SUCCESS", "Imagem gerada")
                return True, f"Gerado com {self.model_name} (GRATUITO)", output_path
            else:
                return False, "Erro ao baixar imagem do Pollinations", None

        except Exception as e:
            log_provider_status(self.model_name, "ERROR", str(e))
            return False, f"Erro no Pollinations.ai: {str(e)}", None


# ==============================================================================
# HUGGING FACE - API GRATUITA COM TOKEN
# ==============================================================================

class HuggingFaceProvider(BaseAIProvider):
    """Hugging Face Inference API - Gratuito com token"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.model_name = "HuggingFace (FLUX.1-schnell)"
        self.requires_api_key = True  # Mas o token é gratuito
        self.supports_generation = True
        self.supports_vision = False
        self.api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"

    def analisar_imagens(self, prompt: str, imagem_a: str, imagem_b: str) -> Tuple[bool, str]:
        """HuggingFace não suporta análise (só geração)"""
        return False, "HuggingFace FLUX não suporta análise multimodal"

    def gerar_imagem(
        self,
        prompt: str,
        output_path: str,
        imagem_init: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        try:
            if not self.api_key:
                return False, "HuggingFace token não configurado", None

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Prompt otimizado
            prompt_otimizado = f"{prompt}, high quality 2D illustration, clean lines, educational material, sign language reference, flat color style"

            payload = {
                "inputs": prompt_otimizado[:900],  # Limite do modelo
                "parameters": {
                    "num_inference_steps": 4,  # FLUX.1-schnell é rápido (4 steps)
                    "guidance_scale": 0.0  # Schnell não usa guidance
                }
            }

            log_provider_status(self.model_name, "GENERATING", "Gerando...")

            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)

            if response.status_code == 200:
                # Salvar imagem
                with open(output_path, 'wb') as f:
                    f.write(response.content)

                log_provider_status(self.model_name, "SUCCESS", "Imagem gerada")
                return True, f"Gerado com {self.model_name} (GRATUITO)", output_path
            else:
                error_msg = response.text
                log_provider_status(self.model_name, "ERROR", f"Status {response.status_code}: {error_msg}")
                return False, f"Erro HuggingFace: {error_msg}", None

        except Exception as e:
            log_provider_status(self.model_name, "ERROR", str(e))
            return False, f"Erro no HuggingFace: {str(e)}", None


# ==============================================================================
# GOOGLE GEMINI - VISÃO + GERAÇÃO
# ==============================================================================

class GoogleGeminiProvider(BaseAIProvider):
    """Google Gemini - Visão multimodal + Imagen"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.model_name = "Google Gemini Flash"
        self.requires_api_key = True
        self.supports_vision = True
        self.supports_generation = False  # Imagen ainda em preview

        try:
            import google.generativeai as genai
            if self.api_key:
                genai.configure(api_key=self.api_key)
            self.client = genai
        except ImportError:
            raise ImportError("Instale: pip install google-generativeai")

    def analisar_imagens(
        self,
        prompt: str,
        imagem_a: str,
        imagem_b: str
    ) -> Tuple[bool, str]:
        try:
            from PIL import Image

            model = self.client.GenerativeModel('gemini-1.5-flash')

            img_a = Image.open(imagem_a)
            img_b = Image.open(imagem_b)

            # Prompt de análise visual
            analise_prompt = f"""{prompt}

TAREFA CRÍTICA - ANÁLISE VISUAL PARA FUSÃO:

Analise as duas imagens e extraia:

IMAGEM 1 (Referência Libras):
- Configuração EXATA de cada dedo (quais estão estendidos, dobrados, formando qual letra)
- Posição das mãos (altura em relação ao corpo, distância do rosto/peito)
- Orientação da palma e dos dedos
- Movimento indicado (setas, linhas de movimento)
- Ponto de articulação (tocando onde? próximo a quê?)

IMAGEM 2 (Personagem):
- Estilo artístico EXATO: (traço grosso/fino, linha preta, colorido/P&B, sombreamento)
- Proporções anatômicas (tamanho cabeça/corpo, braços)
- Características faciais (formato olhos, nariz, boca, cabelo)
- Paleta de cores (RGB principais, saturação)
- Técnica: (vetorial, cartoon, flat, gradiente, textura)

DESCRIÇÃO FINAL: Crie UM parágrafo ULTRA DETALHADO (500 palavras) descrevendo como desenhar o personagem da Imagem 2 executando EXATAMENTE o sinal da Imagem 1, mantendo 100% do estilo visual.

Use linguagem específica para IA: "dedos indicador e médio totalmente estendidos formando V de 90 graus", "traço de contorno preto sólido 3px", "preenchimento chapado cor #FF5733", etc."""

            log_provider_status(self.model_name, "ANALYZING", "Analisando imagens...")

            response = model.generate_content([analise_prompt, img_a, img_b])
            descricao = response.text

            log_provider_status(self.model_name, "SUCCESS", "Análise completa")
            return True, descricao

        except Exception as e:
            log_provider_status(self.model_name, "ERROR", str(e))
            return False, f"Erro na análise Gemini: {str(e)}"

    def gerar_imagem(
        self,
        prompt: str,
        output_path: str,
        imagem_init: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        # Gemini Imagen ainda em preview - não implementado
        return False, "Gemini Imagen ainda não disponível publicamente", None


# ==============================================================================
# OPENAI - VISÃO + DALL-E 3
# ==============================================================================

class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT-4o Vision + DALL-E 3"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.model_name = "OpenAI GPT-4o + DALL-E 3"
        self.requires_api_key = True
        self.supports_vision = True
        self.supports_generation = True

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("Instale: pip install openai")

    def analisar_imagens(
        self,
        prompt: str,
        imagem_a: str,
        imagem_b: str
    ) -> Tuple[bool, str]:
        try:
            img_a_b64 = self._carregar_imagem_base64(imagem_a)
            img_b_b64 = self._carregar_imagem_base64(imagem_b)

            log_provider_status(self.model_name, "ANALYZING", "GPT-4o analisando...")

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_a_b64}"}},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b_b64}"}}
                    ]
                }],
                max_tokens=2000
            )

            descricao = response.choices[0].message.content
            log_provider_status(self.model_name, "SUCCESS", "Análise GPT-4o completa")
            return True, descricao

        except Exception as e:
            log_provider_status(self.model_name, "ERROR", str(e))
            return False, f"Erro na análise OpenAI: {str(e)}"

    def gerar_imagem(
        self,
        prompt: str,
        output_path: str,
        imagem_init: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        try:
            log_provider_status(self.model_name, "GENERATING", "DALL-E 3 gerando...")

            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt[:4000],
                size="1024x1024",
                quality="standard",
                n=1
            )

            img_url = response.data[0].url

            if self._baixar_e_salvar_imagem(img_url, output_path):
                log_provider_status(self.model_name, "SUCCESS", "DALL-E 3 gerado")
                return True, f"Gerado com DALL-E 3", output_path
            else:
                return False, "Erro ao baixar DALL-E 3", None

        except Exception as e:
            log_provider_status(self.model_name, "ERROR", str(e))
            return False, f"Erro no DALL-E 3: {str(e)}", None


# ==============================================================================
# REPLICATE - FLUX / SDXL
# ==============================================================================

class ReplicateProvider(BaseAIProvider):
    """Replicate com Flux ou SDXL"""

    def __init__(self, api_key: Optional[str] = None, model: str = "flux"):
        super().__init__(api_key)
        self.model_type = model
        self.model_name = f"Replicate ({model.upper()})"
        self.requires_api_key = True
        self.supports_generation = True
        self.supports_vision = False

        self.models = {
            "flux": "black-forest-labs/flux-schnell",
            "sdxl": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
        }

        try:
            import replicate
            self.client = replicate.Client(api_token=self.api_key)
        except ImportError:
            raise ImportError("Instale: pip install replicate")

    def analisar_imagens(self, prompt: str, imagem_a: str, imagem_b: str) -> Tuple[bool, str]:
        return False, "Replicate não suporta análise multimodal"

    def gerar_imagem(
        self,
        prompt: str,
        output_path: str,
        imagem_init: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        try:
            log_provider_status(self.model_name, "GENERATING", "Gerando...")

            model_id = self.models[self.model_type]

            input_params = {
                "prompt": prompt,
                "guidance_scale": 7.5,
                "num_inference_steps": 4 if self.model_type == "flux" else 30
            }

            if imagem_init and os.path.exists(imagem_init):
                with open(imagem_init, "rb") as f:
                    input_params["image"] = f.read()
                input_params["strength"] = 0.7

            output = self.client.run(model_id, input=input_params)

            if isinstance(output, list):
                img_url = output[0]
            else:
                img_url = output

            if self._baixar_e_salvar_imagem(img_url, output_path):
                log_provider_status(self.model_name, "SUCCESS", "Imagem gerada")
                return True, f"Gerado com {self.model_name}", output_path
            else:
                return False, "Erro ao baixar Replicate", None

        except Exception as e:
            log_provider_status(self.model_name, "ERROR", str(e))
            return False, f"Erro no Replicate: {str(e)}", None


# ==============================================================================
# CUSTOM OPENAI-COMPATIBLE PROXY (9ROUTER / OPENROUTER)
# ==============================================================================

class CustomProxyProvider(BaseAIProvider):
    """Provider customizado compatível com OpenAI (9Router, OpenRouter, etc)"""

    def __init__(self, api_key: Optional[str] = None, base_url: str = "", model_name: str = ""):
        super().__init__(api_key)
        self.model_name = model_name or "Custom Proxy"
        self.base_url = base_url
        self.requires_api_key = True
        self.supports_vision = True
        self.supports_generation = True

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError("Instale: pip install openai")

    def analisar_imagens(
        self,
        prompt: str,
        imagem_a: str,
        imagem_b: str
    ) -> Tuple[bool, str]:
        try:
            img_a_b64 = self._carregar_imagem_base64(imagem_a)
            img_b_b64 = self._carregar_imagem_base64(imagem_b)

            log_provider_status(self.model_name, "ANALYZING", "Analisando via proxy...")

            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",  # Modelo genérico
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_a_b64}"}},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b_b64}"}}
                    ]
                }],
                max_tokens=2000
            )

            descricao = response.choices[0].message.content
            log_provider_status(self.model_name, "SUCCESS", "Análise completa")
            return True, descricao

        except Exception as e:
            log_provider_status(self.model_name, "ERROR", str(e))
            return False, f"Erro no proxy: {str(e)}"

    def gerar_imagem(
        self,
        prompt: str,
        output_path: str,
        imagem_init: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        try:
            log_provider_status(self.model_name, "GENERATING", "Gerando via proxy...")

            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt[:4000],
                size="1024x1024",
                n=1
            )

            img_url = response.data[0].url

            if self._baixar_e_salvar_imagem(img_url, output_path):
                log_provider_status(self.model_name, "SUCCESS", "Imagem gerada")
                return True, f"Gerado com {self.model_name}", output_path
            else:
                return False, "Erro ao baixar do proxy", None

        except Exception as e:
            log_provider_status(self.model_name, "ERROR", str(e))
            return False, f"Erro no proxy: {str(e)}", None


# ==============================================================================
# SMART ROUTER - ROTEADOR INTELIGENTE COM AUTO-FALLBACK
# ==============================================================================

class SmartAIRouter:
    """
    Roteador Inteligente de IA com Auto-Fallback
    Nunca para por falta de crédito!
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa o router com configuração

        config = {
            "openai_key": "sk-...",
            "gemini_key": "...",
            "replicate_key": "r8_...",
            "huggingface_key": "hf_...",
            "custom_proxy_url": "https://...",
            "custom_proxy_key": "...",
            "priority_order": ["openai", "gemini", "replicate", "huggingface", "pollinations"]
        }
        """
        self.config = config or {}
        self.providers = {}
        self.fallback_order = self.config.get("priority_order", [
            "gemini",  # Gratuito para começar
            "huggingface",  # Gratuito com token
            "openai",  # Alta qualidade
            "replicate",  # Custo-benefício
            "pollinations"  # Fallback universal gratuito
        ])

        self._inicializar_providers()

    def _inicializar_providers(self):
        """Inicializa todos os provedores disponíveis"""
        # Google Gemini
        if self.config.get("gemini_key"):
            try:
                self.providers["gemini"] = GoogleGeminiProvider(self.config["gemini_key"])
            except Exception as e:
                log_provider_status("Gemini", "INIT_ERROR", str(e))

        # OpenAI
        if self.config.get("openai_key"):
            try:
                self.providers["openai"] = OpenAIProvider(self.config["openai_key"])
            except Exception as e:
                log_provider_status("OpenAI", "INIT_ERROR", str(e))

        # Replicate
        if self.config.get("replicate_key"):
            try:
                self.providers["replicate"] = ReplicateProvider(
                    self.config["replicate_key"],
                    self.config.get("replicate_model", "flux")
                )
            except Exception as e:
                log_provider_status("Replicate", "INIT_ERROR", str(e))

        # HuggingFace
        if self.config.get("huggingface_key"):
            try:
                self.providers["huggingface"] = HuggingFaceProvider(self.config["huggingface_key"])
            except Exception as e:
                log_provider_status("HuggingFace", "INIT_ERROR", str(e))

        # Custom Proxy
        if self.config.get("custom_proxy_url") and self.config.get("custom_proxy_key"):
            try:
                self.providers["custom"] = CustomProxyProvider(
                    self.config["custom_proxy_key"],
                    self.config["custom_proxy_url"],
                    self.config.get("custom_proxy_model", "9Router")
                )
            except Exception as e:
                log_provider_status("CustomProxy", "INIT_ERROR", str(e))

        # Pollinations (sempre disponível - sem API key)
        try:
            self.providers["pollinations"] = PollinationsAIProvider()
        except Exception as e:
            log_provider_status("Pollinations", "INIT_ERROR", str(e))

    def fusion_generate(
        self,
        prompt: str,
        imagem_referencia_a: str,
        imagem_personagem_b: str,
        output_path: str
    ) -> Tuple[bool, str, Optional[str], str]:
        """
        Estratégia Fusion: Análise multimodal + Geração com auto-fallback

        Returns:
            (sucesso, mensagem, caminho_arquivo, provider_usado)
        """
        log_provider_status("SmartRouter", "START", "Iniciando Fusion Generate")

        # ETAPA 1: ANÁLISE MULTIMODAL (Visão)
        descricao_fusao = None
        vision_provider = None

        # Tentar análise com providers que suportam visão
        for provider_name in self.fallback_order:
            if provider_name not in self.providers:
                continue

            provider = self.providers[provider_name]

            if provider.supports_vision:
                log_provider_status("SmartRouter", "VISION_TRY", f"Tentando análise com {provider.model_name}")
                sucesso, resultado = provider.analisar_imagens(prompt, imagem_referencia_a, imagem_personagem_b)

                if sucesso:
                    descricao_fusao = resultado
                    vision_provider = provider.model_name
                    log_provider_status("SmartRouter", "VISION_SUCCESS", f"Análise completa com {vision_provider}")
                    break

        # Se não conseguiu análise, usar prompt original
        if not descricao_fusao:
            log_provider_status("SmartRouter", "VISION_FALLBACK", "Usando prompt original sem análise")
            descricao_fusao = prompt

        # ETAPA 2: GERAÇÃO DE IMAGEM COM AUTO-FALLBACK
        for provider_name in self.fallback_order:
            if provider_name not in self.providers:
                continue

            provider = self.providers[provider_name]

            if not provider.supports_generation:
                continue

            log_provider_status("SmartRouter", "GEN_TRY", f"Tentando geração com {provider.model_name}")

            try:
                sucesso, mensagem, caminho = provider.gerar_imagem(
                    descricao_fusao,
                    output_path,
                    imagem_personagem_b
                )

                if sucesso:
                    provider_info = f"Visão: {vision_provider or 'N/A'} | Geração: {provider.model_name}"
                    log_provider_status("SmartRouter", "SUCCESS", provider_info)
                    return True, mensagem, caminho, provider_info
                else:
                    log_provider_status("SmartRouter", "GEN_FAIL", f"{provider.model_name}: {mensagem}")
                    # Continuar para próximo provider
                    continue

            except Exception as e:
                log_provider_status("SmartRouter", "GEN_ERROR", f"{provider.model_name}: {str(e)}")
                # Continuar para próximo provider
                continue

        # Se chegou aqui, todos falharam
        return False, "Todos os provedores falharam (incluindo Pollinations)", None, "Nenhum"

    def get_available_providers(self) -> List[str]:
        """Retorna lista de providers disponíveis"""
        return list(self.providers.keys())

    def get_provider_status(self) -> Dict[str, Dict]:
        """Retorna status de cada provider"""
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                "name": provider.model_name,
                "vision": provider.supports_vision,
                "generation": provider.supports_generation,
                "requires_key": provider.requires_api_key,
                "ready": True
            }
        return status


# ==============================================================================
# CLASSE LEGACY (Compatibilidade com código antigo)
# ==============================================================================

class AIGenerator:
    """Wrapper para manter compatibilidade com código antigo"""

    def __init__(self, provider: str = "smart-router", api_key: Optional[str] = None, config: Dict = None):
        if provider == "smart-router":
            self.router = SmartAIRouter(config or {})
            self.provider_name = "Smart Router"
        else:
            # Modo single-provider (legado)
            self.router = None
            self.provider_name = provider

    def gerar_imagem(
        self,
        prompt: str,
        imagem_referencia_a: str,
        imagem_personagem_b: str,
        output_dir: str = "output",
        nome_arquivo: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """Interface compatível com código legado"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        if not nome_arquivo:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"sinal_{timestamp}.png"

        output_path = os.path.join(output_dir, nome_arquivo)

        if self.router:
            sucesso, msg, caminho, provider_usado = self.router.fusion_generate(
                prompt,
                imagem_referencia_a,
                imagem_personagem_b,
                output_path
            )
            return sucesso, f"{msg} [{provider_usado}]", caminho
        else:
            return False, "Modo single-provider não implementado nesta versão", None
