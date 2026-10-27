"""
Módulo de extração e busca em PDFs do Dicionário Capovilla e Configurações de Mão
Usa PyMuPDF (fitz) com lazy loading para eficiência de memória
"""
import fitz  # PyMuPDF
import re
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from PIL import Image
import io


class PDFCapovillaExtractor:
    """Extrator para o Dicionário Capovilla completo"""

    def __init__(self, caminho_pdf: str = None):
        # Se não especificado, usar caminho relativo ao projeto
        if caminho_pdf is None:
            caminho_pdf = "data/pdfs/Dicionario capovilla completo.pdf"

        self.caminho_pdf = caminho_pdf
        self.doc = None
        self._verificar_arquivo()

    def _verificar_arquivo(self):
        """Verifica se o arquivo PDF existe"""
        if not Path(self.caminho_pdf).exists():
            raise FileNotFoundError(f"PDF não encontrado: {self.caminho_pdf}")

    def abrir(self):
        """Abre o documento PDF (lazy - só quando necessário)"""
        if self.doc is None:
            self.doc = fitz.open(self.caminho_pdf)
        return self.doc

    def fechar(self):
        """Fecha o documento PDF"""
        if self.doc:
            self.doc.close()
            self.doc = None

    def get_total_paginas(self) -> int:
        """Retorna o número total de páginas"""
        self.abrir()
        return len(self.doc)

    def renderizar_pagina(self, num_pagina: int, dpi: int = 150) -> Image.Image:
        """
        Renderiza uma página específica como imagem PIL

        Args:
            num_pagina: Número da página (1-indexed)
            dpi: Resolução da imagem (default 150)

        Returns:
            Imagem PIL da página
        """
        self.abrir()

        # Ajustar para 0-indexed
        pagina = self.doc[num_pagina - 1]

        # Renderizar com zoom baseado no DPI
        zoom = dpi / 72  # 72 DPI é o padrão
        mat = fitz.Matrix(zoom, zoom)
        pix = pagina.get_pixmap(matrix=mat)

        # Converter para PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        return img

    def extrair_texto_pagina(self, num_pagina: int) -> str:
        """
        Extrai o texto de uma página específica

        Args:
            num_pagina: Número da página (1-indexed)

        Returns:
            Texto da página
        """
        self.abrir()
        pagina = self.doc[num_pagina - 1]
        return pagina.get_text()

    def buscar_termo(self, termo: str, max_resultados: int = 20) -> List[Dict]:
        """
        Busca um termo no dicionário

        Args:
            termo: Palavra/sinal a buscar
            max_resultados: Máximo de resultados a retornar

        Returns:
            Lista de dicionários com {pagina, texto_contexto}
        """
        self.abrir()
        resultados = []
        termo_upper = termo.upper()

        # Buscar nas páginas (lazy - uma por vez)
        for num_pagina in range(1, len(self.doc) + 1):
            if len(resultados) >= max_resultados:
                break

            texto = self.extrair_texto_pagina(num_pagina)

            # Verificar se o termo aparece no início de linha (verbete)
            # Padrão: termo em maiúsculas ou negrito no início
            if termo_upper in texto.upper():
                # Extrair contexto (primeiras linhas)
                linhas = texto.split('\n')
                contexto = '\n'.join(linhas[:10])  # Primeiras 10 linhas

                resultados.append({
                    'pagina': num_pagina,
                    'texto_contexto': contexto,
                    'texto_completo': texto
                })

        return resultados

    def extrair_parametros_sinal(self, texto_pagina: str) -> Optional[Dict]:
        """
        Extrai os parâmetros do sinal do texto entre parênteses
        Exemplo: "(Mão em B horizontal, palma para frente, dedos inclinados para a direita. Movê-la ligeiramente para a direita.)"

        Args:
            texto_pagina: Texto completo da página

        Returns:
            Dicionário com parâmetros extraídos
        """
        # Regex para capturar texto entre parênteses (última ocorrência grande)
        padrao = r'\(([^()]{50,}?)\)'
        matches = re.findall(padrao, texto_pagina)

        if not matches:
            return None

        # Pegar a maior ocorrência (geralmente é a descrição do sinal)
        descricao = max(matches, key=len)

        # Extrair parâmetros
        parametros = {
            'descricao_completa': descricao,
            'configuracao_mao': self._extrair_configuracao_mao(descricao),
            'orientacao': self._extrair_orientacao(descricao),
            'ponto_articulacao': self._extrair_ponto_articulacao(descricao),
            'movimento': self._extrair_movimento(descricao)
        }

        return parametros

    def _extrair_configuracao_mao(self, descricao: str) -> List[str]:
        """Extrai configuração de mão da descrição"""
        configs = []

        # Padrões: "Mão em X", "Mãos em X", etc.
        padrao = r'[Mm]ão(?:s)?\s+em\s+([A-Z])\b'
        matches = re.findall(padrao, descricao)

        for letra in matches:
            configs.append(f"Mão em {letra}")

        # Padrões adicionais
        if "mão aberta" in descricao.lower():
            configs.append("Mão aberta")
        if "mão fechada" in descricao.lower():
            configs.append("Mão fechada")

        return list(set(configs)) if configs else ["Não identificada"]

    def _extrair_orientacao(self, descricao: str) -> str:
        """Extrai orientação da mão"""
        descricao_lower = descricao.lower()

        if "palma para cima" in descricao_lower:
            return "Palma para cima"
        elif "palma para baixo" in descricao_lower:
            return "Palma para baixo"
        elif "palma para frente" in descricao_lower or "palma para a frente" in descricao_lower:
            return "Palma para frente"
        elif "palma para trás" in descricao_lower or "palma para tras" in descricao_lower:
            return "Palma para trás"
        elif "palma para dentro" in descricao_lower:
            return "Palma para dentro"
        elif "palma para fora" in descricao_lower:
            return "Palma para fora"

        # Dedos
        if "dedos para cima" in descricao_lower:
            return "Dedos para cima"
        elif "dedos para baixo" in descricao_lower:
            return "Dedos para baixo"

        return "Não identificada"

    def _extrair_ponto_articulacao(self, descricao: str) -> str:
        """Extrai ponto de articulação"""
        descricao_lower = descricao.lower()

        pontos = {
            "testa": "Testa",
            "cabeça": "Cabeça",
            "rosto": "Cabeça",
            "olho": "Olhos",
            "nariz": "Nariz",
            "boca": "Boca",
            "orelha": "Orelha",
            "queixo": "Boca",
            "pescoço": "Pescoço",
            "ombro": "Ombro",
            "peito": "Peito",
            "barriga": "Barriga",
            "braço": "Braço",
            "cotovelo": "Cotovelo",
            "pulso": "Pulso",
            "frente do corpo": "À frente do corpo",
            "lado do corpo": "Ao lado do corpo",
            "espaço neutro": "Espaço neutro",
        }

        for chave, valor in pontos.items():
            if chave in descricao_lower:
                return valor

        return "Espaço neutro"

    def _extrair_movimento(self, descricao: str) -> List[str]:
        """Extrai tipo de movimento"""
        movimentos = []
        descricao_lower = descricao.lower()

        padroes_movimento = {
            "para frente": "Para frente",
            "para trás": "Para trás",
            "para tras": "Para trás",
            "para cima": "Para cima",
            "para baixo": "Para baixo",
            "para a direita": "Para direita",
            "para direita": "Para direita",
            "para a esquerda": "Para esquerda",
            "para esquerda": "Para esquerda",
            "circular": "Circular",
            "movê-la": "Para frente",
            "tocar": "Tocar",
            "esfregar": "Esfregar",
            "balançar": "Balançar",
            "tremular": "Tremular",
        }

        for padrao, movimento in padroes_movimento.items():
            if padrao in descricao_lower:
                movimentos.append(movimento)

        return list(set(movimentos)) if movimentos else ["Sem movimento"]


class PDFConfiguracaoMaoExtractor:
    """Extrator para o PDF de Configurações de Mão"""

    def __init__(self, caminho_pdf: str = None):
        # Se não especificado, usar caminho relativo ao projeto
        if caminho_pdf is None:
            caminho_pdf = "data/pdfs/configuraçao de mao.pdf"

        self.caminho_pdf = caminho_pdf
        self.doc = None
        self._verificar_arquivo()

    def _verificar_arquivo(self):
        """Verifica se o arquivo PDF existe"""
        if not Path(self.caminho_pdf).exists():
            raise FileNotFoundError(f"PDF não encontrado: {self.caminho_pdf}")

    def abrir(self):
        """Abre o documento PDF"""
        if self.doc is None:
            self.doc = fitz.open(self.caminho_pdf)
        return self.doc

    def fechar(self):
        """Fecha o documento PDF"""
        if self.doc:
            self.doc.close()
            self.doc = None

    def extrair_configuracao(self, letra: str) -> Optional[Dict]:
        """
        Extrai a descrição detalhada de uma configuração de mão

        Args:
            letra: Letra da configuração (A-Z)

        Returns:
            Dicionário com descrição e imagem
        """
        self.abrir()

        # Buscar a letra no documento
        for num_pagina in range(len(self.doc)):
            pagina = self.doc[num_pagina]
            texto = pagina.get_text()

            # Procurar por padrões como "Mão em A", "Configuração A", etc.
            if f"mão em {letra.upper()}" in texto.lower() or f"configuração {letra.upper()}" in texto.lower():
                return {
                    'letra': letra.upper(),
                    'pagina': num_pagina + 1,
                    'descricao': texto[:500],  # Primeiros 500 caracteres
                    'texto_completo': texto
                }

        return None

    def renderizar_pagina_configuracao(self, letra: str, dpi: int = 150) -> Optional[Image.Image]:
        """Renderiza a página da configuração específica"""
        info = self.extrair_configuracao(letra)
        if info:
            pagina = self.doc[info['pagina'] - 1]
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = pagina.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            return Image.open(io.BytesIO(img_data))
        return None


# Dicionário de Configurações de Mão Detalhadas (para o prompt engine)
CONFIGURACOES_MAO_DETALHADAS = {
    "Mão em A": "Mão fechada com o polegar ao lado do indicador, formando um punho com o polegar para fora.",
    "Mão em B": "Mão aberta com dedos juntos e estendidos, polegar cruzado sobre a palma.",
    "Mão em C": "Mão em formato de 'C', com todos os dedos curvados e separados do polegar.",
    "Mão em D": "Indicador estendido apontando para cima, demais dedos fechados tocando o polegar.",
    "Mão em E": "Mão fechada com dedos dobrados sobre a palma e polegar sobre os dedos.",
    "Mão em F": "Polegar e indicador formando um círculo (como 'OK'), demais dedos estendidos.",
    "Mão em G": "Indicador e polegar estendidos horizontalmente, demais dedos fechados.",
    "Mão em H": "Indicador e médio estendidos juntos horizontalmente, demais dedos fechados.",
    "Mão em I": "Mínimo (dedinho) estendido, demais dedos fechados com polegar cruzado.",
    "Mão em L": "Indicador e polegar formando 'L', demais dedos fechados.",
    "Mão em M": "Três dedos (indicador, médio e anelar) sobre o polegar, mínimo fechado.",
    "Mão em N": "Indicador e médio sobre o polegar, demais dedos fechados.",
    "Mão em O": "Dedos curvados formando círculo, pontas dos dedos tocando o polegar.",
    "Mão em P": "Indicador e médio estendidos para baixo, polegar entre eles, demais dedos fechados.",
    "Mão em Q": "Polegar e indicador apontando para baixo, demais dedos fechados.",
    "Mão em R": "Indicador e médio cruzados, demais dedos fechados.",
    "Mão em S": "Mão fechada em punho com polegar sobre os dedos.",
    "Mão em T": "Polegar entre indicador e médio, demais dedos fechados.",
    "Mão em U": "Indicador e médio estendidos juntos para cima, demais dedos fechados.",
    "Mão em V": "Indicador e médio estendidos separados (formato 'V'), demais dedos fechados.",
    "Mão em W": "Indicador, médio e anelar estendidos separados, polegar e mínimo fechados.",
    "Mão em X": "Indicador dobrado em gancho, demais dedos fechados.",
    "Mão em Y": "Polegar e mínimo estendidos, demais dedos fechados.",
    "Mão aberta": "Todos os dedos estendidos e separados, palma visível.",
    "Mão fechada": "Todos os dedos dobrados formando um punho fechado."
}
