import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def conectar_drive():
    """Estabelece a conexão com o Google Drive do usuário autenticado."""

    token = st.user.tokens.get("access")

    if not token:
        raise RuntimeError(
            "Token de acesso Google indisponível."
        )

    credenciais = Credentials(token=token)

    return build(
        "drive",
        "v3",
        credentials=credenciais,
        cache_discovery=False,
    )


def testar_conexao_drive():
    """Verifica a comunicação com a API do Google Drive."""

    servico = conectar_drive()

    resultado = servico.about().get(
        fields="user(displayName)"
    ).execute()

    return resultado