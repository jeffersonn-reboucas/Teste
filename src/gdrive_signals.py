"""
Conector e Indexador Leve para a pasta CAPOVILLA (A-Z) no Google Drive
Lê as subpastas A-Z e baixa sob demanda apenas o arquivo .jpg selecionado (40 KB)
"""
import os
import re
import sqlite3
import unicodedata
import requests
from pathlib import Path


def normalizar(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()


class GDriveCapovillaCatalog:
    def __init__(self, root_folder_url_or_id: str, db_path: str = "data/gdrive_capovilla.db"):
        self.root_id = self._extrair_id(root_folder_url_or_id)
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _extrair_id(self, texto: str) -> str:
        """Extrai o ID da pasta mesmo que o usuário cole o link completo do Google Drive"""
        match = re.search(r'folders/([a-zA-Z0-9_-]+)', texto)
        if match:
            return match.group(1)
        return texto.strip()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subpastas (
                letra TEXT PRIMARY KEY,
                folder_id TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS arquivos (
                file_id TEXT PRIMARY KEY,
                nome_arquivo TEXT,
                termo_limpo TEXT,
                termo_norm TEXT,
                letra TEXT,
                eh_detalhe INTEGER
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_gdrive_termo ON arquivos(termo_norm)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_gdrive_letra ON arquivos(letra)")
        conn.commit()
        conn.close()

    def _listar_itens_pasta_publica(self, folder_id: str) -> list:
        """
        Lê os itens de uma pasta pública do Google Drive via página embeddedfolderview
        (Não exige configurar conta de serviço complexa no Google Cloud!)
        """
        url = f"https://drive.google.com/embeddedfolderview?id={folder_id}#list"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        itens = []
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code != 200:
                return []

            html = resp.text
            # Padrão do embeddedfolderview: id="entry-ID" ... <div class="flip-entry-title">NOME</div>
            padrao = re.compile(
                r'id="entry-([a-zA-Z0-9_-]+)".*?<div class="flip-entry-title">([^<]+)</div>',
                re.DOTALL
            )
            for match in padrao.finditer(html):
                item_id = match.group(1)
                nome = match.group(2).strip()
                itens.append({"id": item_id, "name": nome})
        except Exception:
            pass
        return itens

    def sincronizar_pastas_principais(self) -> list:
        """Mapeia as pastas A, B, C... da raiz CAPOVILLA"""
        itens = self._listar_itens_pasta_publica(self.root_id)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        letras_encontradas = []
        for item in itens:
            nome = item["name"].strip().upper()
            if len(nome) <= 3:  # Pastas A, B, C...
                cur.execute(
                    "INSERT OR REPLACE INTO subpastas VALUES (?, ?)",
                    (nome, item["id"])
                )
                letras_encontradas.append(nome)
        conn.commit()
        conn.close()
        return sorted(letras_encontradas)

    def obter_letras_sincronizadas(self) -> list:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT letra FROM subpastas ORDER BY letra ASC")
        letras = [r[0] for r in cur.fetchall()]
        conn.close()
        if not letras:
            return self.sincronizar_pastas_principais()
        return letras

    def carregar_letra(self, letra: str, forcar_atualizacao: bool = False) -> list:
        """
        Lista todos os sinais (.jpg/.png) dentro da pasta da letra escolhida (ex: 'A')
        e salva no SQLite para buscas instantâneas.
        """
        letra = letra.upper().strip()
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        if not forcar_atualizacao:
            cur.execute(
                "SELECT file_id, nome_arquivo, termo_limpo, eh_detalhe FROM arquivos WHERE letra = ? ORDER BY termo_norm ASC",
                (letra,)
            )
            existentes = cur.fetchall()
            if existentes:
                conn.close()
                return [
                    {"file_id": r[0], "nome_arquivo": r[1], "termo": r[2], "eh_detalhe": bool(r[3])}
                    for r in existentes
                ]

        cur.execute("SELECT folder_id FROM subpastas WHERE letra = ?", (letra,))
        row = cur.fetchone()
        if not row:
            self.sincronizar_pastas_principais()
            cur.execute("SELECT folder_id FROM subpastas WHERE letra = ?", (letra,))
            row = cur.fetchone()

        if not row:
            conn.close()
            return []

        folder_id = row[0]
        itens = self._listar_itens_pasta_publica(folder_id)

        novos_registros = []
        resultado_lista = []

        for item in itens:
            nome_arq = item["name"]
            if not nome_arq.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue

            stem = Path(nome_arq).stem
            eh_detalhe = 1 if stem.endswith(" D") else 0
            termo_limpo = stem[:-2].strip() if eh_detalhe else stem.strip()

            novos_registros.append((
                item["id"],
                nome_arq,
                termo_limpo,
                normalizar(termo_limpo),
                letra,
                eh_detalhe
            ))
            resultado_lista.append({
                "file_id": item["id"],
                "nome_arquivo": nome_arq,
                "termo": termo_limpo,
                "eh_detalhe": bool(eh_detalhe)
            })

        if novos_registros:
            cur.executemany(
                "INSERT OR REPLACE INTO arquivos VALUES (?, ?, ?, ?, ?, ?)",
                novos_registros
            )
            conn.commit()

        conn.close()
        return resultado_lista

    def buscar_sinal_drive(self, termo: str) -> list:
        """
        Se o usuário digitar 'à frente', descobre automaticamente que começa com 'A',
        sincroniza a pasta 'A' se ainda não estiver no SQLite e retorna o arquivo exato!
        """
        termo_n = normalizar(termo)
        if not termo_n:
            return []

        primeira_letra = termo_n[0].upper()
        if primeira_letra.isalpha():
            self.carregar_letra(primeira_letra, forcar_atualizacao=False)

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT file_id, nome_arquivo, termo_limpo, letra, eh_detalhe
            FROM arquivos
            WHERE termo_norm LIKE ?
            ORDER BY eh_detalhe ASC, length(termo_norm) ASC
            LIMIT 25
        """, (f"%{termo_n}%",))
        rows = cur.fetchall()
        conn.close()

        return [
            {
                "file_id": r[0],
                "nome_arquivo": r[1],
                "termo": r[2],
                "letra": r[3],
                "eh_detalhe": bool(r[4])
            }
            for r in rows
        ]

    def baixar_imagem_sinal(self, file_id: str, nome_arquivo: str) -> str:
        """Baixa apenas o JPG leve (40 KB) selecionado para a pasta local de referências"""
        pasta_dest = Path("assets/referencias/gdrive")
        pasta_dest.mkdir(parents=True, exist_ok=True)

        nome_seguro = re.sub(r'[^a-zA-Z0-9_.-]', '_', nome_arquivo)
        caminho_local = pasta_dest / f"{file_id[:8]}_{nome_seguro}"

        if caminho_local.exists() and caminho_local.stat().st_size > 1000:
            return str(caminho_local)

        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=25)
        if resp.status_code == 200 and len(resp.content) > 500:
            with open(caminho_local, "wb") as f:
                f.write(resp.content)
            return str(caminho_local)
        return ""