"""
Extrator e Indexador Ultrarrápido (SQLite) para os PDFs do Capovilla e Configurações de Mão
"""
import fitz  # PyMuPDF
import sqlite3
import re
import unicodedata
from pathlib import Path
from PIL import Image
import io


def normalizar_texto(texto: str) -> str:
    """Remove acentos e converte para minúsculas para buscas precisas"""
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFKD', texto)
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return sem_acento.lower().strip()


class PDFCapovillaExtractor:
    def __init__(self, pdf_path: str, db_path: str = "data/capovilla_index.db"):
        self.pdf_path = str(pdf_path)
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.doc = fitz.open(self.pdf_path)
        self._inicializar_banco()

    def get_total_paginas(self) -> int:
        return len(self.doc)

    def _inicializar_banco(self):
        """Cria a estrutura SQLite para busca instantânea"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paginas (
                pagina INTEGER PRIMARY KEY,
                texto_completo TEXT,
                texto_normalizado TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verbetes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                termo TEXT,
                termo_normalizado TEXT,
                pagina INTEGER,
                resumo TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_termo_norm ON verbetes(termo_normalizado)")
        conn.commit()
        conn.close()

    def esta_indexado(self) -> bool:
        """Verifica se o PDF já foi varrido e salvo no SQLite"""
        if not self.db_path.exists():
            return False
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM paginas")
            count = cursor.fetchone()[0]
            conn.close()
            # Consideramos indexado se tiver pelo menos 90% das páginas salvas
            return count >= int(self.get_total_paginas() * 0.9)
        except Exception:
            return False

    def construir_indice(self, progress_callback=None):
        """
        Varre todas as páginas do PDF uma única vez, separando o que é
        VERBETE PRINCIPAL do que é apenas texto comum da página.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM paginas")
        cursor.execute("DELETE FROM verbetes")

        total = self.get_total_paginas()

        # Padrão Capovilla: "termo (sinal usado em:" ou "termo (inglês:"
        padrao_verbete = re.compile(
            r'([a-zA-Zà-úÀ-ÚçÇ\-\s]{2,35}?)\s*\((?:sinal usado em|ingl[êe]s\s*:)',
            re.IGNORECASE
        )

        lote_paginas = []
        lote_verbetes = []

        for idx in range(total):
            num_pag = idx + 1
            texto = self.doc[idx].get_text("text")
            texto_norm = normalizar_texto(texto)

            lote_paginas.append((num_pag, texto, texto_norm))

            # Identificar cabeçalhos de sinais na página
            for match in padrao_verbete.finditer(texto):
                termo_bruto = match.group(1).strip()
                # Pega apenas a última linha caso tenha capturado sujeira antes
                linhas_termo = [l.strip() for l in termo_bruto.split('\n') if l.strip()]
                if linhas_termo:
                    termo_limpo = linhas_termo[-1]
                    if 1 < len(termo_limpo) <= 30:
                        pos_inicio = max(0, match.start() - 10)
                        pos_fim = min(len(texto), match.end() + 250)
                        resumo = texto[pos_inicio:pos_fim].replace('\n', ' ')
                        lote_verbetes.append((
                            termo_limpo,
                            normalizar_texto(termo_limpo),
                            num_pag,
                            resumo
                        ))

            if len(lote_paginas) >= 150 or num_pag == total:
                cursor.executemany("INSERT OR REPLACE INTO paginas VALUES (?, ?, ?)", lote_paginas)
                cursor.executemany(
                    "INSERT INTO verbetes (termo, termo_normalizado, pagina, resumo) VALUES (?, ?, ?, ?)",
                    lote_verbetes
                )
                conn.commit()
                lote_paginas.clear()
                lote_verbetes.clear()

                if progress_callback:
                    progress_callback(num_pag, total)

        conn.close()

    def buscar_termo(self, termo: str, max_resultados: int = 15) -> list:
        """
        Busca primeiro nos Verbetes Principais (alta precisão) e depois
        nas menções gerais, sem repetir a mesma página.
        """
        termo_norm = normalizar_texto(termo)
        if not termo_norm:
            return []

        # Se ainda não estiver indexado, faz busca rápida nas páginas
        if not self.esta_indexado():
            return self._busca_fallback_sem_indice(termo, max_resultados)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        resultados = []
        paginas_vistas = set()

        # 1. Busca Exata no Verbete Principal (Ex: "à toa")
        cursor.execute("""
            SELECT v.termo, v.pagina, p.texto_completo
            FROM verbetes v
            JOIN paginas p ON v.pagina = p.pagina
            WHERE v.termo_normalizado = ?
            ORDER BY v.pagina ASC
        """, (termo_norm,))
        for termo_enc, pag, txt in cursor.fetchall():
            if pag not in paginas_vistas:
                paginas_vistas.add(pag)
                resultados.append({
                    'pagina': pag,
                    'tipo': f"🎯 Verbete Exato: '{termo_enc.upper()}'",
                    'texto_completo': txt
                })

        # 2. Busca Parcial em Verbetes Principais (Começa com o termo)
        if len(resultados) < max_resultados:
            cursor.execute("""
                SELECT v.termo, v.pagina, p.texto_completo
                FROM verbetes v
                JOIN paginas p ON v.pagina = p.pagina
                WHERE v.termo_normalizado LIKE ?
                ORDER BY length(v.termo_normalizado) ASC, v.pagina ASC
                LIMIT ?
            """, (f"{termo_norm}%", max_resultados))
            for termo_enc, pag, txt in cursor.fetchall():
                if pag not in paginas_vistas:
                    paginas_vistas.add(pag)
                    resultados.append({
                        'pagina': pag,
                        'tipo': f"📌 Verbete: '{termo_enc.upper()}'",
                        'texto_completo': txt
                    })

        # 3. Busca no corpo do texto (apenas se ainda houver espaço na lista)
        if len(resultados) < max_resultados:
            restante = max_resultados - len(resultados)
            cursor.execute("""
                SELECT pagina, texto_completo
                FROM paginas
                WHERE texto_normalizado LIKE ?
                ORDER BY pagina ASC
                LIMIT ?
            """, (f"%{termo_norm}%", restante + 10))
            for pag, txt in cursor.fetchall():
                if pag not in paginas_vistas and len(resultados) < max_resultados:
                    paginas_vistas.add(pag)
                    resultados.append({
                        'pagina': pag,
                        'tipo': "📄 Menção na página",
                        'texto_completo': txt
                    })

        conn.close()
        return resultados

    def _busca_fallback_sem_indice(self, termo: str, max_resultados: int) -> list:
        """Caso o usuário busque antes de indexar"""
        termo_norm = normalizar_texto(termo)
        resultados = []
        for idx in range(len(self.doc)):
            txt = self.doc[idx].get_text("text")
            if termo_norm in normalizar_texto(txt):
                resultados.append({
                    'pagina': idx + 1,
                    'tipo': "📄 Página encontrada",
                    'texto_completo': txt
                })
                if len(resultados) >= max_resultados:
                    break
        return resultados

    def extrair_texto_pagina(self, numero_pagina: int) -> str:
        idx = max(0, min(numero_pagina - 1, len(self.doc) - 1))
        return self.doc[idx].get_text("text")

    def renderizar_pagina(self, numero_pagina: int, zoom: float = 2.0) -> Image.Image:
        idx = max(0, min(numero_pagina - 1, len(self.doc) - 1))
        page = self.doc[idx]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        return Image.open(io.BytesIO(pix.tobytes("png")))

    def extrair_parametros_sinal(self, texto: str, termo_foco: str = "") -> dict:
        """
        Extrai a descrição entre parênteses do sinal focado na página
        Ex: (Mão em A, palma para a esquerda, dedo mínimo distendido...)
        """
        if not texto:
            return None

        texto_limpo = re.sub(r'\s+', ' ', texto)
        descricao_foco = texto_limpo

        # Se sabemos qual é o termo buscado, focamos no trecho a partir dele
        if termo_foco:
            padrao_pos = re.search(re.escape(termo_foco.strip()), texto_limpo, re.IGNORECASE)
            if padrao_pos:
                inicio = padrao_pos.start()
                descricao_foco = texto_limpo[inicio:inicio + 1200]

        # Tentar pegar a descrição anatômica entre parênteses típica do Capovilla
        match_parenteses = re.search(
            r'\(([^)]*(?:mão|mãos|palma|dedo|dedos|braço|queixo|testa|peito|ombro|boca)[^)]*)\)',
            descricao_foco,
            re.IGNORECASE
        )

        if match_parenteses:
            desc_final = match_parenteses.group(1).strip()
        else:
            desc_final = descricao_foco[:600].strip()

        # Inferência simples de orientação e ponto de articulação
        desc_lower = desc_final.lower()
        orientacao = "Palma para cima"
        if "palma para baixo" in desc_lower:
            orientacao = "Palma para baixo"
        elif "palma para a frente" in desc_lower or "palma para frente" in desc_lower:
            orientacao = "Palma para frente"
        elif "palma para trás" in desc_lower or "palma para o corpo" in desc_lower:
            orientacao = "Palma para trás"
        elif "palma para a esquerda" in desc_lower or "palma para a direita" in desc_lower or "palma para dentro" in desc_lower:
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
            'configuracao_mao': [],
            'orientacao': orientacao,
            'ponto_articulacao': ponto,
            'movimento': [],
            'descricao_completa': desc_final
        }


class PDFConfiguracaoMaoExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = str(pdf_path)
        self.doc = fitz.open(self.pdf_path)

    def get_total_paginas(self) -> int:
        return len(self.doc)

    def renderizar_pagina(self, numero_pagina: int, zoom: float = 2.0) -> Image.Image:
        idx = max(0, min(numero_pagina - 1, len(self.doc) - 1))
        page = self.doc[idx]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        return Image.open(io.BytesIO(pix.tobytes("png")))