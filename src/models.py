"""
Modelos de dados para catalogação de sinais de Libras
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime
import json


@dataclass
class Sinal:
    """Representa um sinal de Libras com seus parâmetros"""

    # Identificação
    termo: str
    categoria: str = ""

    # Parâmetros do sinal (baseados em Capovilla)
    configuracao_mao: List[str] = field(default_factory=list)  # Ex: ["mão em A", "mão em B"]
    ponto_articulacao: str = ""  # Ex: "rosto", "peito", "espaço neutro"
    movimento: List[str] = field(default_factory=list)  # Ex: ["circular", "para frente"]
    orientacao: str = ""  # Ex: "palma para baixo", "dedos para cima"
    expressao: List[str] = field(default_factory=list)  # Ex: ["sobrancelhas levantadas"]

    # Recursos visuais
    caminho_imagem: Optional[str] = None
    componentes: List[str] = field(default_factory=list)  # Componentes usados na ilustração

    # Metadados
    tags: List[str] = field(default_factory=list)
    observacoes: str = ""
    data_criacao: str = field(default_factory=lambda: datetime.now().isoformat())
    data_modificacao: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self):
        """Converte o sinal para dicionário"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        """Cria um sinal a partir de um dicionário"""
        return cls(**data)

    def atualizar_modificacao(self):
        """Atualiza a data de modificação"""
        self.data_modificacao = datetime.now().isoformat()


# Constantes para os parâmetros (baseados no sistema de Capovilla)
CONFIGURACOES_MAO = [
    "Mão em A", "Mão em B", "Mão em C", "Mão em D", "Mão em E",
    "Mão em F", "Mão em G", "Mão em H", "Mão em I", "Mão em J",
    "Mão em K", "Mão em L", "Mão em M", "Mão em N", "Mão em O",
    "Mão em P", "Mão em Q", "Mão em R", "Mão em S", "Mão em T",
    "Mão em U", "Mão em V", "Mão em W", "Mão em X", "Mão em Y",
    "Mão aberta", "Mão fechada", "Outra"
]

PONTOS_ARTICULACAO = [
    "Espaço neutro",
    "Cabeça", "Testa", "Olhos", "Nariz", "Boca", "Orelha", "Bochecha",
    "Pescoço", "Ombro", "Peito", "Barriga",
    "Braço", "Cotovelo", "Pulso", "Mão",
    "À frente do corpo", "Ao lado do corpo"
]

TIPOS_MOVIMENTO = [
    "Sem movimento",
    "Para frente", "Para trás", "Para cima", "Para baixo",
    "Para direita", "Para esquerda",
    "Circular", "Circular horário", "Circular anti-horário",
    "Tremular", "Balançar", "Tocar", "Esfregar",
    "Curvo", "Ondulado", "Ziguezague",
    "Alternado", "Simultâneo", "Repetido"
]

ORIENTACOES = [
    "Palma para cima", "Palma para baixo",
    "Palma para frente", "Palma para trás",
    "Palma para dentro", "Palma para fora",
    "Dedos para cima", "Dedos para baixo",
    "Dedos para frente", "Dedos para trás"
]

EXPRESSOES = [
    "Neutra",
    "Sobrancelhas levantadas", "Sobrancelhas franzidas",
    "Olhos arregalados", "Olhos semicerrados",
    "Bochechas infladas", "Bochechas sugadas",
    "Língua para fora", "Boca aberta", "Boca fechada",
    "Sorriso", "Tristeza", "Surpresa"
]

CATEGORIAS = [
    "Alfabeto",
    "Números",
    "Família",
    "Cores",
    "Animais",
    "Alimentos",
    "Verbos",
    "Adjetivos",
    "Lugares",
    "Tempo",
    "Educação",
    "Saúde",
    "Outros"
]
