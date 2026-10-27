"""
Gerador de prompts estruturados para IA Multimodal
Foco: instruir a IA a fundir parâmetros de sinais de Libras com personagens 2D
RTK (Token Saver) + Style Lock + Anatomy Lock
"""
from typing import Dict, Optional, List
import re
from pdf_extractor import CONFIGURACOES_MAO_DETALHADAS


class PromptEngine:
    """Gera prompts técnicos para fusão de poses de Libras em personagens 2D"""

    def __init__(self, modo_otimizado: bool = False):
        self.prompt_base = self._carregar_prompt_base()
        self.modo_otimizado = modo_otimizado  # RTK: Token Saver

        # Style Lock: Trava de Estilo 2D Pedagógico
        self.style_lock = "2D flat illustration, clean linework, educational sign language reference, pedagogical clarity, solid colors, white background, front view, centered composition, technical drawing style"

        # Anatomy Lock: Trava de Anatomia Precisa
        self.anatomy_lock = "CRITICAL: exact hand configuration, precise finger positions, anatomically correct, maintain character's visual identity 100%, pedagogical accuracy"

    def _carregar_prompt_base(self) -> str:
        """Template base do prompt para instrução da IA"""
        return """Você é um especialista em ilustração técnica de Língua Brasileira de Sinais (Libras).

TAREFA: Gerar uma ilustração 2D que combine:
- A POSE e CONFIGURAÇÃO DE MÃO da imagem de referência do sinal de Libras
- O ESTILO VISUAL e ANATOMIA do personagem fornecido

REGRAS CRÍTICAS:
1. Mantenha 100% da identidade visual do personagem (traços faciais, proporções, estilo de desenho)
2. Replique EXATAMENTE a configuração das mãos mostrada na referência de Libras
3. Posicione o sinal no mesmo ponto de articulação da referência
4. Preserve o movimento/direção indicado na referência
5. Adapte a expressão facial conforme indicado nos parâmetros do sinal
6. Use fundo transparente ou neutro (branco)
7. Mantenha a clareza pedagógica - a imagem será usada em material educacional

ESTILO: Ilustração técnica 2D, limpa, com contornos definidos, adequada para materiais didáticos."""

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
        """
        Gera o prompt completo para a IA com base nos parâmetros do sinal

        Args:
            termo: Nome do sinal (ex: "CASA", "ESTUDAR")
            configuracao_mao: Lista de configurações de mão (ex: ["Mão em C"])
            ponto_articulacao: Localização do sinal (ex: "rosto", "peito")
            movimento: Lista de movimentos (ex: ["circular", "para frente"])
            orientacao: Orientação da palma/dedos
            expressao: Expressões faciais necessárias
            observacoes: Observações adicionais

        Returns:
            Prompt completo estruturado
        """
        # Adicionar descrições anatômicas detalhadas
        configs_detalhadas = self._detalhar_configuracoes(configuracao_mao)

        prompt_parametros = f"""

PARÂMETROS DO SINAL "{termo.upper()}":

📍 Configuração de Mão:
{self._formatar_lista(configuracao_mao)}

⚠️ DETALHES ANATÔMICOS DA(S) MÃO(S) (CRÍTICO - não alucine a anatomia):
{configs_detalhadas}

📍 Ponto de Articulação:
- {ponto_articulacao}

📍 Movimento:
{self._formatar_lista(movimento)}

📍 Orientação:
- {orientacao}

📍 Expressão Facial:
{self._formatar_lista(expressao)}
"""

        if observacoes:
            prompt_parametros += f"""
📍 Observações Adicionais:
- {observacoes}
"""

        instrucoes_execucao = """

INSTRUÇÕES DE EXECUÇÃO:
1. Analise a imagem de referência do sinal de Libras (Item A)
2. Analise o personagem 2D fornecido (Item B)
3. Crie uma nova ilustração onde o personagem executa o sinal
4. A configuração de mão deve ser IDÊNTICA à referência
5. O ponto de articulação deve estar EXATAMENTE onde a referência indica
6. O estilo visual deve ser 100% fiel ao personagem original
7. Mantenha proporções anatômicas coerentes e pedagógicas

FORMATO DE SAÍDA:
- Ilustração 2D em alta resolução
- Fundo transparente ou branco
- Foco central no sinal sendo executado
- Clareza visual para uso educacional"""

        return self.prompt_base + prompt_parametros + instrucoes_execucao

    def _formatar_lista(self, itens: List[str]) -> str:
        """Formata lista de itens para o prompt"""
        if not itens:
            return "- Não especificado"
        return "\n".join([f"- {item}" for item in itens])

    def _detalhar_configuracoes(self, configuracoes: List[str]) -> str:
        """
        Adiciona descrições anatômicas detalhadas das configurações de mão
        Evita alucinações da IA sobre posição dos dedos
        """
        if not configuracoes:
            return "- Não especificado"

        detalhes = []
        for config in configuracoes:
            # Buscar no dicionário de configurações detalhadas
            descricao = CONFIGURACOES_MAO_DETALHADAS.get(config, "")
            if descricao:
                detalhes.append(f"• {config}: {descricao}")
            else:
                detalhes.append(f"• {config}")

        return "\n".join(detalhes)

    def _otimizar_tokens(self, texto: str) -> str:
        """
        RTK (Token Saver): Otimiza prompt removendo redundâncias
        Economiza até 40% de tokens mantendo qualidade
        """
        if not self.modo_otimizado:
            return texto

        # Remover emojis (economiza tokens)
        texto = re.sub(r'[📍📖👤✨⚠️🔧💡]', '', texto)

        # Remover linhas vazias excessivas
        texto = re.sub(r'\n{3,}', '\n\n', texto)

        # Remover palavras redundantes comuns
        substituicoes = {
            'por favor': '',
            'certifique-se de que': '',
            'é importante que': '',
            'deve ser': 'ser',
            'precisa ser': 'ser',
            'muito importante': 'crítico',
            'extremamente': '',
            'altamente': '',
            'completamente': '',
            'totalmente': '100%',
        }

        for antigo, novo in substituicoes.items():
            texto = texto.replace(antigo, novo)

        # Comprimir espaços múltiplos
        texto = re.sub(r' {2,}', ' ', texto)

        return texto.strip()

    def aplicar_style_lock(self, prompt: str) -> str:
        """
        Aplica Style Lock: garante estilo 2D pedagógico consistente
        """
        if self.style_lock not in prompt:
            prompt += f"\n\nSTYLE LOCK: {self.style_lock}"
        return prompt

    def aplicar_anatomy_lock(self, prompt: str) -> str:
        """
        Aplica Anatomy Lock: garante anatomia precisa do sinal
        """
        if self.anatomy_lock not in prompt:
            prompt += f"\n\nANATOMY LOCK: {self.anatomy_lock}"
        return prompt

    def gerar_prompt_otimizado(
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
        Versão otimizada do prompt (RTK: Token Saver ativado)
        Economiza ~40% de tokens mantendo qualidade
        """
        # Prompt base ultra compacto
        prompt_base = f"""Expert Libras 2D illustrator. Task: fuse sign pose (Image A) + character style (Image B).

SIGN: {termo.upper()}
Hand: {', '.join(configuracao_mao)}
Anatomy: {self._detalhar_configuracoes(configuracao_mao)[:200]}...
Point: {ponto_articulacao}
Move: {', '.join(movimento)}
Orient: {orientacao}
Face: {', '.join(expressao)}"""

        if observacoes:
            prompt_base += f"\nNotes: {observacoes[:100]}"

        # Aplicar locks
        prompt_base = self.aplicar_style_lock(prompt_base)
        prompt_base = self.aplicar_anatomy_lock(prompt_base)

        return self._otimizar_tokens(prompt_base)

    def gerar_prompt_para_analise_visual(
        self,
        termo: str
    ) -> str:
        """
        Prompt especializado para análise visual (Gemini/GPT-4 Vision)
        Usado na estratégia Fusion do SmartRouter
        """
        return f"""Analyze these 2 images for LIBRAS sign "{termo.upper()}":

IMAGE 1 (Sign Reference): Extract EXACT hand configuration, finger positions, articulation point, movement direction.

IMAGE 2 (Character): Extract EXACT art style (line weight, colors, proportions, shading technique).

OUTPUT: Single detailed paragraph (500 words) describing how to draw Image 2's character performing Image 1's sign EXACTLY, maintaining 100% visual identity.

Use specific terms: "index and middle fingers fully extended forming 90° V", "solid black 3px outline", "flat fill #FF5733", etc.

{self.style_lock}
{self.anatomy_lock}"""

    def gerar_prompt_refinamento(
        self,
        problema: str,
        ajuste_solicitado: str
    ) -> str:
        """
        Gera prompt para refinamento/correção de uma imagem já gerada

        Args:
            problema: Descrição do problema na imagem atual
            ajuste_solicitado: O que precisa ser ajustado

        Returns:
            Prompt de refinamento
        """
        return f"""REFINAMENTO DE ILUSTRAÇÃO DE LIBRAS:

PROBLEMA IDENTIFICADO:
{problema}

AJUSTE NECESSÁRIO:
{ajuste_solicitado}

INSTRUÇÕES:
1. Mantenha todos os elementos corretos da versão atual
2. Corrija APENAS o problema identificado
3. Preserve a identidade visual do personagem
4. Preserve a configuração de mão se ela estiver correta
5. Mantenha o estilo e qualidade da ilustração

REGRA CRÍTICA: Não altere elementos que já estão corretos. Foque apenas no ajuste solicitado."""

    def gerar_prompt_variacao(
        self,
        contexto: str,
        variacao_desejada: str
    ) -> str:
        """
        Gera prompt para criar variações de um sinal
        (ex: ângulo diferente, versão simplificada)

        Args:
            contexto: Contexto da variação (ex: "vista lateral")
            variacao_desejada: Descrição da variação

        Returns:
            Prompt de variação
        """
        return f"""VARIAÇÃO DE ILUSTRAÇÃO DE LIBRAS:

CONTEXTO:
{contexto}

VARIAÇÃO DESEJADA:
{variacao_desejada}

INSTRUÇÕES:
1. Mantenha os parâmetros fundamentais do sinal (configuração de mão, ponto de articulação)
2. Adapte conforme o contexto solicitado
3. Preserve a identidade visual do personagem
4. Mantenha a clareza pedagógica
5. Garanta que a variação seja tecnicamente correta para Libras

IMPORTANTE: A variação deve continuar representando o mesmo sinal de forma precisa."""

    def extrair_parametros_imagem(self, descricao_visual: str) -> Dict[str, str]:
        """
        Helper para estruturar parâmetros a partir de uma descrição visual
        (útil quando o usuário descreve a imagem em vez de selecionar parâmetros)

        Args:
            descricao_visual: Descrição textual do que se vê na imagem de referência

        Returns:
            Dicionário estruturado com os parâmetros identificados
        """
        # Este método pode ser expandido com NLP/LLM para extrair parâmetros
        # Por ora, retorna um template
        return {
            "prompt_adicional": f"""
ANÁLISE DA IMAGEM DE REFERÊNCIA:
{descricao_visual}

Com base nesta descrição, replique os elementos visuais do sinal mantendo o estilo do personagem fornecido."""
        }
