"""
Gerador de prompts estruturados para IA Multimodal
Foco: instruir a IA (InstantCharacter/Gemini) a aplicar poses de Libras
RTK (Token Saver) + Style Lock + Anatomy Lock
"""
from typing import Dict, Optional, List
import re

# Sugestão: Mova este dicionário para o models.py no futuro para desacoplar.
from pdf_extractor import CONFIGURACOES_MAO_DETALHADAS


class PromptEngine:
    """Gera prompts técnicos para fusão de poses de Libras em personagens 2D"""

    def __init__(self, modo_otimizado: bool = False):
        self.modo_otimizado = modo_otimizado  # RTK: Token Saver

        # Style Lock: Trava de Estilo 2D Pedagógico
        self.style_lock = "2D flat vector illustration, clean linework, educational sign language reference, pedagogical clarity, solid colors, white background, front view, centered composition."

        # Anatomy Lock: Trava de Anatomia Precisa
        self.anatomy_lock = "CRITICAL: exact hand configuration, precise finger positions, anatomically correct, maintain character's visual identity 100%."

    def _formatar_lista(self, itens: List[str]) -> str:
        """Formata lista de itens para o prompt"""
        if not itens:
            return "Não especificado"
        return ", ".join(itens)

    def _detalhar_configuracoes(self, configuracoes: List[str]) -> str:
        """
        Adiciona descrições anatômicas detalhadas das configurações de mão
        Evita alucinações da IA sobre posição dos dedos
        """
        if not configuracoes:
            return "Não especificado"

        detalhes = []
        for config in configuracoes:
            descricao = CONFIGURACOES_MAO_DETALHADAS.get(config, "")
            if descricao:
                detalhes.append(f"{config} ({descricao})")
            else:
                detalhes.append(config)

        return "; ".join(detalhes)

    def _otimizar_tokens(self, texto: str) -> str:
        """
        RTK (Token Saver): Otimiza prompt removendo redundâncias
        """
        if not self.modo_otimizado:
            return texto

        texto = re.sub(r'\n{3,}', '\n\n', texto)
        substituicoes = {
            'por favor': '',
            'certifique-se de que': '',
            'é importante que': '',
            'deve ser': 'ser',
            'precisa ser': 'ser',
            'extremamente': '',
            'altamente': '',
            'completamente': '',
        }
        for antigo, novo in substituicoes.items():
            texto = texto.replace(antigo, novo)
        
        texto = re.sub(r' {2,}', ' ', texto)
        return texto.strip()

    # =========================================================================
    # NOVO MÉTODO: Otimizado para InstantCharacter (Image-to-Image)
    # =========================================================================
    def gerar_prompt_instant_character(
        self,
        termo: str,
        configuracao_mao: List[str],
        ponto_articulacao: str,
        movimento: List[str],
        orientacao: str,
        expressao: List[str],
        observacoes: Optional[str] = None
    ) -> str:
        """
        Gera prompt focado APENAS na ação do sinal para o InstantCharacter.
        Como ele já recebe o Personagem (Item B), não perdemos tokens descrevendo o rosto.
        """
        configs_detalhadas = self._detalhar_configuracoes(configuracao_mao)
        
        # Monta o prompt em inglês (melhor performance no InstantCharacter/Flux)
        prompt = (
            f"2D flat vector illustration of the character performing the exact pose shown in the control image. "
            f"The sign is {termo.upper()}. "
            f"Hand configuration: {configs_detalhadas}. "
            f"Point of articulation: {ponto_articulacao}. "
            f"Movement: {self._formatar_lista(movimento)}. "
            f"Orientation: {orientacao}. "
            f"Facial expression: {self._formatar_lista(expressao)}. "
            f"Keep the character's exact face and style from the subject image. "
            f"White background, clean lines, educational flashcard."
        )
        
        if observacoes:
            prompt += f" Additional visual notes: {observacoes[:150]}"

        # Aplica os locks para garantir o estilo e anatomia
        prompt += f"\nSTYLE LOCK: {self.style_lock}"
        prompt += f"\nANATOMY LOCK: {self.anatomy_lock}"

        return self._otimizar_tokens(prompt)


    # =========================================================================
    # MÉTODOS ANTIGOS: Mantidos para o Gemini Multimodal (Caso use como fallback)
    # =========================================================================
    def gerar_prompt_completo(
        self,
        termo: str,
        configuracao_mao: List[str],
        ponto_articulacao: str,
        movimento: List[str],
        orientacao: str,
        expressao: List[str],
        observacoes: Optional[str] = None
    ) -> str:
        """Versão antiga em português. Útil para o Gemini Multimodal."""
        configs_detalhadas = self._detalhar_configuracoes(configuracao_mao)

        prompt_parametros = f"""
TAREFA: Gerar ilustração do sinal "{termo.upper()}".
- Configuração de Mão: {configs_detalhadas}
- Ponto de Articulação: {ponto_articulacao}
- Movimento: {self._formatar_lista(movimento)}
- Orientação: {orientacao}
- Expressão Facial: {self._formatar_lista(expressao)}
"""
        if observacoes:
            prompt_parametros += f"- Observações: {observacoes}\n"

        instrucoes_execucao = """
INSTRUÇÕES CRÍTICAS:
1. Analise a imagem de referência do sinal (Image A).
2. Analise o personagem 2D (Image B).
3. Crie uma nova ilustração onde o personagem executa o sinal.
4. A configuração de mão deve ser IDÊNTICA à referência.
5. O estilo visual deve ser 100% fiel ao personagem original.
"""
        return (prompt_parametros + instrucoes_execucao + 
                f"\nSTYLE: {self.style_lock}\nANATOMY: {self.anatomy_lock}")

    def gerar_prompt_otimizado(self, **kwargs) -> str:
        """Versão em inglês antiga (Text-to-Image)."""
        termo = kwargs.get('termo', '')
        configuracao_mao = kwargs.get('configuracao_mao', [])
        ponto_articulacao = kwargs.get('ponto_articulacao', '')
        
        return self.gerar_prompt_instant_character(
            termo=termo,
            configuracao_mao=configuracao_mao,
            ponto_articulacao=ponto_articulacao,
            movimento=kwargs.get('movimento', []),
            orientacao=kwargs.get('orientacao', ''),
            expressao=kwargs.get('expressao', []),
            observacoes=kwargs.get('observacoes', None)
        )