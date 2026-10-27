"""
Gerenciador de PDFs com download automático do Google Drive
Para uso em Streamlit Community Cloud
"""
import os
import gdown
from pathlib import Path
import streamlit as st


class PDFManager:
    """Gerencia download e cache de PDFs do Google Drive"""

    # IDs dos arquivos no Google Drive (extraídos da URL compartilhada)
    # Formato: https://drive.google.com/file/d/FILE_ID/view
    GOOGLE_DRIVE_FILES = {
        "Dicionario capovilla completo.pdf": {
            "folder_id": "1GyE1k4Qb5Of2mAhIIYMaD3TOaJnLSB1-",
            "filename": "Dicionario capovilla completo.pdf",
            "size_mb": 212
        },
        "configuraçao de mao.pdf": {
            "folder_id": "1GyE1k4Qb5Of2mAhIIYMaD3TOaJnLSB1-",
            "filename": "configuraçao de mao.pdf",
            "size_mb": 33
        }
    }

    def __init__(self, base_dir: str = "data/pdfs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_pdf_path(self, nome_arquivo: str) -> str:
        """Retorna o caminho local do PDF"""
        return str(self.base_dir / nome_arquivo)

    def pdf_existe(self, nome_arquivo: str) -> bool:
        """Verifica se o PDF já existe localmente"""
        caminho = self.get_pdf_path(nome_arquivo)
        return Path(caminho).exists()

    def baixar_pdf_gdrive(self, nome_arquivo: str) -> bool:
        """
        Baixa um PDF específico do Google Drive

        Args:
            nome_arquivo: Nome do arquivo a baixar

        Returns:
            True se download bem-sucedido, False caso contrário
        """
        if nome_arquivo not in self.GOOGLE_DRIVE_FILES:
            st.error(f"❌ Arquivo '{nome_arquivo}' não configurado")
            return False

        info = self.GOOGLE_DRIVE_FILES[nome_arquivo]
        caminho_destino = self.get_pdf_path(nome_arquivo)

        try:
            # URL da pasta compartilhada do Google Drive
            folder_url = f"https://drive.google.com/drive/folders/{info['folder_id']}"

            st.info(f"📥 Baixando '{nome_arquivo}' ({info['size_mb']} MB) do Google Drive...")
            st.info(f"⏳ Isso pode levar alguns minutos na primeira execução...")

            # Baixar o arquivo da pasta compartilhada
            # Nota: gdown.download_folder baixa todos os arquivos da pasta
            # Vamos baixar a pasta inteira e depois mover os arquivos
            temp_folder = "temp_gdrive_download"

            # Tentar baixar diretamente por ID se disponível
            # Se não, baixar toda a pasta
            gdown.download_folder(
                url=folder_url,
                output=temp_folder,
                quiet=False,
                use_cookies=False
            )

            # Mover arquivo da pasta temporária para o destino
            temp_file = Path(temp_folder) / nome_arquivo
            if temp_file.exists():
                import shutil
                shutil.move(str(temp_file), caminho_destino)

                # Limpar pasta temporária
                if Path(temp_folder).exists():
                    shutil.rmtree(temp_folder)

                st.success(f"✅ Download concluído: {nome_arquivo}")
                return True
            else:
                st.error(f"❌ Arquivo não encontrado na pasta do Google Drive")
                return False

        except Exception as e:
            st.error(f"❌ Erro ao baixar '{nome_arquivo}': {str(e)}")
            st.info("💡 Verifique se a pasta do Google Drive está configurada como 'Qualquer pessoa com o link'")
            return False

    def baixar_pdf_direto(self, nome_arquivo: str, file_id: str) -> bool:
        """
        Baixa PDF diretamente por File ID (alternativa mais simples)

        Args:
            nome_arquivo: Nome do arquivo
            file_id: ID do arquivo no Google Drive

        Returns:
            True se sucesso
        """
        caminho_destino = self.get_pdf_path(nome_arquivo)

        try:
            url = f"https://drive.google.com/uc?id={file_id}"

            st.info(f"📥 Baixando '{nome_arquivo}' do Google Drive...")

            gdown.download(url, caminho_destino, quiet=False)

            if Path(caminho_destino).exists():
                st.success(f"✅ Download concluído: {nome_arquivo}")
                return True
            else:
                st.error(f"❌ Falha no download de '{nome_arquivo}'")
                return False

        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")
            return False

    def garantir_pdfs_disponiveis(self) -> dict:
        """
        Garante que todos os PDFs necessários estejam disponíveis
        Baixa do Google Drive se necessário

        Returns:
            Dicionário com status de cada PDF
        """
        status = {}

        for nome_arquivo in self.GOOGLE_DRIVE_FILES.keys():
            if self.pdf_existe(nome_arquivo):
                status[nome_arquivo] = {
                    "disponivel": True,
                    "caminho": self.get_pdf_path(nome_arquivo),
                    "origem": "local"
                }
            else:
                # Tentar baixar do Google Drive
                st.warning(f"⚠️ PDF não encontrado localmente: {nome_arquivo}")
                st.info("🌐 Tentando baixar do Google Drive...")

                # Aqui você precisará configurar os IDs específicos de cada arquivo
                # Por enquanto, retornar como indisponível e instruir o usuário
                status[nome_arquivo] = {
                    "disponivel": False,
                    "caminho": None,
                    "origem": "indisponivel"
                }

                st.error(f"❌ Configure o File ID do Google Drive para '{nome_arquivo}'")
                st.info("""
                **Como configurar:**
                1. Vá para o Google Drive
                2. Clique com botão direito no arquivo → Compartilhar
                3. Mude para "Qualquer pessoa com o link"
                4. Copie o link (formato: https://drive.google.com/file/d/FILE_ID/view)
                5. Extraia o FILE_ID e adicione no código
                """)

        return status

    def configurar_file_ids(self, file_ids: dict):
        """
        Configura os IDs específicos dos arquivos no Google Drive

        Args:
            file_ids: Dicionário {nome_arquivo: file_id}
        """
        for nome, file_id in file_ids.items():
            if nome in self.GOOGLE_DRIVE_FILES:
                self.GOOGLE_DRIVE_FILES[nome]["file_id"] = file_id

    def baixar_todos_pdfs(self, file_ids: dict = None) -> bool:
        """
        Baixa todos os PDFs necessários

        Args:
            file_ids: Dicionário opcional com {nome_arquivo: file_id}

        Returns:
            True se todos foram baixados com sucesso
        """
        if file_ids:
            self.configurar_file_ids(file_ids)

        sucesso_total = True

        for nome_arquivo, info in self.GOOGLE_DRIVE_FILES.items():
            if not self.pdf_existe(nome_arquivo):
                if "file_id" in info:
                    if not self.baixar_pdf_direto(nome_arquivo, info["file_id"]):
                        sucesso_total = False
                else:
                    st.error(f"❌ File ID não configurado para '{nome_arquivo}'")
                    sucesso_total = False

        return sucesso_total

    def listar_pdfs_disponiveis(self) -> list:
        """Lista PDFs que estão disponíveis localmente"""
        disponiveis = []
        for nome_arquivo in self.GOOGLE_DRIVE_FILES.keys():
            if self.pdf_existe(nome_arquivo):
                disponiveis.append(nome_arquivo)
        return disponiveis

    def get_tamanho_cache(self) -> float:
        """Retorna o tamanho total em MB dos PDFs em cache"""
        total_mb = 0
        for nome_arquivo in self.GOOGLE_DRIVE_FILES.keys():
            caminho = self.get_pdf_path(nome_arquivo)
            if Path(caminho).exists():
                total_mb += Path(caminho).stat().st_size / (1024 * 1024)
        return round(total_mb, 2)
