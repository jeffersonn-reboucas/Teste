"""
Sistema de catalogação de sinais de Libras
"""
import json
import os
from typing import List, Optional, Dict
from pathlib import Path
from models import Sinal


class CatalogoSinais:
    """Gerencia o catálogo de sinais"""

    def __init__(self, caminho_arquivo: str = "data/catalog.json"):
        self.caminho_arquivo = caminho_arquivo
        self.sinais: Dict[str, Sinal] = {}
        self._carregar()

    def _carregar(self):
        """Carrega o catálogo do arquivo JSON"""
        if os.path.exists(self.caminho_arquivo):
            try:
                with open(self.caminho_arquivo, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    self.sinais = {
                        termo: Sinal.from_dict(sinal_data)
                        for termo, sinal_data in dados.items()
                    }
            except Exception as e:
                print(f"Erro ao carregar catálogo: {e}")
                self.sinais = {}
        else:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.caminho_arquivo), exist_ok=True)
            self.sinais = {}

    def salvar(self):
        """Salva o catálogo no arquivo JSON"""
        try:
            dados = {termo: sinal.to_dict() for termo, sinal in self.sinais.items()}
            with open(self.caminho_arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Erro ao salvar catálogo: {e}")
            return False

    def adicionar_sinal(self, sinal: Sinal) -> bool:
        """Adiciona um novo sinal ao catálogo"""
        if sinal.termo in self.sinais:
            return False
        self.sinais[sinal.termo] = sinal
        self.salvar()
        return True

    def atualizar_sinal(self, termo: str, sinal: Sinal) -> bool:
        """Atualiza um sinal existente"""
        if termo not in self.sinais:
            return False
        sinal.atualizar_modificacao()
        self.sinais[termo] = sinal
        self.salvar()
        return True

    def remover_sinal(self, termo: str) -> bool:
        """Remove um sinal do catálogo"""
        if termo in self.sinais:
            del self.sinais[termo]
            self.salvar()
            return True
        return False

    def buscar_sinal(self, termo: str) -> Optional[Sinal]:
        """Busca um sinal específico"""
        return self.sinais.get(termo)

    def listar_todos(self) -> List[Sinal]:
        """Lista todos os sinais"""
        return list(self.sinais.values())

    def filtrar_por_categoria(self, categoria: str) -> List[Sinal]:
        """Filtra sinais por categoria"""
        return [s for s in self.sinais.values() if s.categoria == categoria]

    def filtrar_por_tag(self, tag: str) -> List[Sinal]:
        """Filtra sinais por tag"""
        return [s for s in self.sinais.values() if tag in s.tags]

    def buscar_por_parametro(self, **parametros) -> List[Sinal]:
        """
        Busca sinais por parâmetros específicos
        Exemplo: buscar_por_parametro(ponto_articulacao="rosto")
        """
        resultados = []
        for sinal in self.sinais.values():
            match = True
            for chave, valor in parametros.items():
                sinal_valor = getattr(sinal, chave, None)
                if isinstance(sinal_valor, list):
                    if valor not in sinal_valor:
                        match = False
                        break
                elif sinal_valor != valor:
                    match = False
                    break
            if match:
                resultados.append(sinal)
        return resultados

    def exportar_para_csv(self, caminho_saida: str):
        """Exporta o catálogo para CSV"""
        import csv

        if not self.sinais:
            return False

        try:
            with open(caminho_saida, 'w', newline='', encoding='utf-8') as f:
                # Pegar os campos do primeiro sinal
                campos = list(list(self.sinais.values())[0].to_dict().keys())
                writer = csv.DictWriter(f, fieldnames=campos)

                writer.writeheader()
                for sinal in self.sinais.values():
                    writer.writerow(sinal.to_dict())
            return True
        except Exception as e:
            print(f"Erro ao exportar: {e}")
            return False

    def estatisticas(self) -> Dict:
        """Retorna estatísticas do catálogo"""
        categorias = {}
        total_tags = set()

        for sinal in self.sinais.values():
            categorias[sinal.categoria] = categorias.get(sinal.categoria, 0) + 1
            total_tags.update(sinal.tags)

        return {
            "total_sinais": len(self.sinais),
            "categorias": categorias,
            "total_categorias": len(categorias),
            "total_tags_unicas": len(total_tags)
        }
