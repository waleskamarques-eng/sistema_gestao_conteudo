
import pandas as pd
import streamlit as st

from leitor_csv import listar_csvs, ler_csv
from importador_json import (
    importar_json,
    verificar_duplicidades,
    preparar_conteudo_sheets,
    validar_conteudos_para_gravacao,
)
from repositorio_sheets import (
    listar_conteudos,
    cadastrar_conteudo,
    atualizar_conteudo,
)


st.set_page_config(
    page_title="Gestão de Conteúdo | Primeira Infância",
    page_icon="📚",
    layout="wide",
)

# Autenticação Google e controle de acesso
USUARIOS_AUTORIZADOS = {
    "waleskapmarques@gmail.com",
    "leonardoaucar@gmail.com",
}

if not st.user.is_logged_in:
    st.title("Sistema de Gestão de Conteúdo")
    st.info("Entre com sua conta Google para acessar o sistema.")

    if st.button("Entrar com Google", type="primary"):
        st.login("google")

    st.stop()

email_usuario = st.user.get("email", "").strip().lower()

if email_usuario not in USUARIOS_AUTORIZADOS:
    st.error("Sua conta Google não está autorizada a acessar este sistema.")

    if st.button("Sair da conta Google"):
        st.logout()

    st.stop()

# Diagnóstico temporário da integração com Google Drive
try:
    from conexao_drive import testar_conexao_drive

    testar_conexao_drive()
    st.success("Sistema conectado ao Google Drive.")
except Exception as erro:
    st.warning(
        f"Falha na conexão com Google Drive: {type(erro).__name__}"
    )



# Identidade visual do protótipo. Não altera a lógica de dados.
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.8rem; padding-bottom: 2.5rem; max-width: 1250px;}
      h1, h2, h3 {letter-spacing: -0.025em;}
      h1 {color: #17365d; font-weight: 750;}
      [data-testid="stSidebar"] {background: #f1f6fb;}
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {color: #17365d;}
      [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #dbe6f1;
        border-radius: 14px;
        padding: 1.1rem 1.25rem;
        box-shadow: 0 3px 12px rgba(22, 54, 93, 0.05);
      }
      [data-testid="stMetricLabel"] {color: #4e647c;}
      [data-testid="stMetricValue"] {color: #17365d;}
      div.stButton > button[kind="primary"],
      div.stFormSubmitButton > button[kind="primary"] {border-radius: 9px;}
      [data-testid="stDataFrame"] {border-radius: 10px; overflow: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("### Primeira Infância")
st.sidebar.caption("Gestão editorial de conteúdos")
st.sidebar.divider()

st.title("Sistema de Gestão de Conteúdo")
st.caption("PRIMEIRA INFÂNCIA  •  Ambiente de demonstração  •  Google Sheets")

pagina = st.sidebar.radio(
    "Navegação",
    [
        "Início",
        "Conteúdos",
        "Indicadores",
        "Importação JSON",
        "Revisões",
        "Exportação CSV",
    ],
)

# Exibe uma notificação após recarregar a página.
if "mensagem_sucesso" in st.session_state:
    mensagem = st.session_state.pop("mensagem_sucesso")
    st.toast(mensagem, icon="✅")

try:
    conteudos = listar_conteudos()
except Exception as erro:
    st.error(
        f"Não foi possível acessar o Google Sheets: {erro}"
    )
    st.stop()


if pagina == "Início":
    st.subheader("Visão geral")
    st.write(
        "Acompanhe o andamento dos conteúdos editoriais do projeto, "
        "desde o cadastro até a aprovação."
    )
    st.divider()
    st.markdown("#### Resumo dos conteúdos")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Conteúdos cadastrados",
        len(conteudos),
    )

    col2.metric(
        "Em revisão",
        sum(
            c["status"] == "Em revisão"
            for c in conteudos
        ),
    )

    col3.metric(
        "Aprovados",
        sum(
            c["status"] == "Aprovado"
            for c in conteudos
        ),
    )

    st.success("Sistema conectado ao Google Sheets.")
    st.markdown("#### Como funciona")
    st.write(
        "**1. Cadastrar** um conteúdo e associar um CSV  →  "
        "**2. Revisar** o texto  →  "
        "**3. Aprovar** o registro  →  "
        "**4. Exportar** os conteúdos aprovados."
    )
    st.caption(
        "Protótipo em evolução: login individual, permissões e histórico "
        "de alterações ainda não estão disponíveis."
    )


elif pagina == "Conteúdos":
    st.subheader("Cadastro de conteúdos")

    # Upload fora do formulário para mostrar a prévia imediatamente.
    arquivo_csv_upload = st.file_uploader(
        "Enviar CSV para teste (opcional)",
        type=["csv"],
        help="O arquivo fica disponível apenas nesta sessão; não é armazenado na nuvem.",
        key="upload_csv_cadastro",
    )

    nome_csv_upload = ""
    if arquivo_csv_upload is not None:
        try:
            arquivo_csv_upload.seek(0)
            df_upload = pd.read_csv(arquivo_csv_upload)
            if df_upload.empty:
                st.warning("O CSV não contém registros e não será associado.")
            else:
                nome_csv_upload = arquivo_csv_upload.name
                st.success(f"CSV carregado: {nome_csv_upload}")
                st.write(f"Total de registros: {len(df_upload)}")
                st.dataframe(df_upload.head(10), hide_index=True)
                st.warning(
                    "Teste: ao salvar, apenas o nome do CSV será registrado no "
                    "Google Sheets. O arquivo não ficará armazenado no Streamlit Cloud."
                )
        except (ValueError, UnicodeError, pd.errors.ParserError, OSError) as erro:
            st.error(f"Erro ao ler CSV: {erro}")

    with st.form("cadastro", clear_on_submit=True):
        id_projeto = st.text_input(
            "ID do projeto",
            value="PRIMEIRA-INFANCIA",
        )

        id_conteudo = st.text_input(
            "ID do conteúdo",
            placeholder="CONT-003",
        )

        titulo = st.text_input("Título")

        descricao = st.text_area("Descrição")

        texto = st.text_area(
            "Texto analítico",
            height=180,
        )

        status = st.selectbox(
            "Status",
            ["Rascunho", "Em revisão", "Aprovado"],
        )

        opcoes_csv_cadastro = [""] + listar_csvs()
        if nome_csv_upload and nome_csv_upload not in opcoes_csv_cadastro:
            opcoes_csv_cadastro.append(nome_csv_upload)

        csv_associado = st.selectbox(
            "CSV associado (opcional)",
            options=opcoes_csv_cadastro,
            index=(
                opcoes_csv_cadastro.index(nome_csv_upload)
                if nome_csv_upload else 0
            ),
            format_func=lambda nome: (
                "Nenhum CSV associado" if nome == "" else nome
            ),
        )

        fonte_texto = st.text_area(
            "Origem do texto",
            placeholder="Informe a fonte ou a procedência do conteúdo",
            help="Registre a origem das informações utilizadas no texto.",
        )

        salvar = st.form_submit_button("Salvar conteúdo")

    if salvar:
        dados = {
            "id_projeto": id_projeto.strip(),
            "id_conteudo": id_conteudo.strip(),
            "titulo": titulo.strip(),
            "descricao": descricao.strip(),
            "texto": texto,
            "status": status,
            "csv_associado": csv_associado.strip(),
            "fonte_texto": fonte_texto.strip(),
        }

        if not all(
            [
                dados["id_projeto"],
                dados["id_conteudo"],
                dados["titulo"],
                dados["descricao"],
                dados["fonte_texto"],
            ]
        ):
            st.error(
                "Preencha os IDs, o título, a descrição "
                "e a origem do texto."
            )
        else:
            try:
                cadastrar_conteudo(dados)

                st.session_state["mensagem_sucesso"] = (
                    "Conteúdo salvo no Google Sheets!"
                )
                st.rerun()

            except Exception as erro:
                st.error(str(erro))

    st.divider()
    st.subheader("Consultar conteúdos")

    if conteudos:
        busca = st.text_input(
            "Buscar por título ou ID"
        )

        filtrados = [
            c
            for c in conteudos
            if busca.lower()
            in (
                str(c["titulo"])
                + " "
                + str(c["id_conteudo"])
            ).lower()
        ]

        # Formata a data apenas para exibição.
        df_consulta = pd.DataFrame(filtrados)

        if (
            not df_consulta.empty
            and "atualizado_em" in df_consulta.columns
        ):
            datas = pd.to_datetime(
                df_consulta["atualizado_em"],
                errors="coerce",
                utc=True,
            )

            df_consulta["atualizado_em"] = (
                datas.dt.tz_convert("America/Sao_Paulo")
                .dt.strftime("%d/%m/%Y %H:%M")
                .fillna("")
            )

        st.dataframe(
            df_consulta,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()
        st.subheader("Editar conteúdo")

        opcoes = {
            (
                f"{c['id_projeto']} | "
                f"{c['id_conteudo']} - "
                f"{c['titulo']}"
            ): c
            for c in conteudos
        }

        escolha = st.selectbox(
            "Selecione um conteúdo",
            list(opcoes.keys()),
        )

        atual = opcoes[escolha]

        # Guarda a versão original ao abrir a edição.
        chave_registro = (
            f"{atual['id_projeto']}|"
            f"{atual['id_conteudo']}"
        )

        chave_original = (
            f"original_{chave_registro}"
        )

        if (
            st.session_state.get("registro_selecionado")
            != chave_registro
        ):
            st.session_state["registro_selecionado"] = (
                chave_registro
            )
            st.session_state[chave_original] = atual.copy()

        registro_original = (
            st.session_state[chave_original]
        )

        with st.form(f"edicao_{chave_registro}"):
            novo_titulo = st.text_input(
                "Editar título",
                value=registro_original["titulo"],
            )

            nova_descricao = st.text_area(
                "Editar descrição",
                value=registro_original["descricao"],
            )

            novo_texto = st.text_area(
                "Editar texto",
                value=registro_original["texto"],
                height=180,
            )

            status_opcoes = [
                "Rascunho",
                "Em revisão",
                "Aprovado",
            ]

            status_atual = str(
                registro_original["status"]
            )

            if status_atual not in status_opcoes:
                status_atual = "Rascunho"

            novo_status = st.selectbox(
                "Editar status",
                status_opcoes,
                index=status_opcoes.index(status_atual),
            )

            csv_atual = str(
                registro_original.get("csv_associado", "") or ""
            ).strip()

            opcoes_csv = [""] + listar_csvs()

            if csv_atual and csv_atual not in opcoes_csv:
                opcoes_csv.append(csv_atual)

            novo_csv = st.selectbox(
                "Editar CSV associado",
                options=opcoes_csv,
                index=opcoes_csv.index(csv_atual),
                format_func=lambda nome: (
                    "Nenhum CSV associado" if nome == "" else nome
                ),
            )

            nova_fonte_texto = st.text_area(
                "Editar origem do texto",
                value=str(
                    registro_original.get("fonte_texto", "")
                ),
                help=(
                    "Informe a origem das informações "
                    "utilizadas no texto."
                ),
            )

            atualizar = st.form_submit_button(
                "Atualizar conteúdo"
            )

        if atualizar:
            if (
                not novo_titulo.strip()
                or not nova_descricao.strip()
            ):
                st.error(
                    "Título e descrição são obrigatórios."
                )

            elif (
                str(
                    registro_original.get("fonte_texto", "")
                ).strip()
                and not nova_fonte_texto.strip()
            ):
                st.error(
                    "A origem do texto já cadastrada "
                    "não pode ficar vazia."
                )

            else:
                dados_atualizados = {
                    "id_projeto": atual["id_projeto"],
                    "id_conteudo": atual["id_conteudo"],
                    "titulo": novo_titulo.strip(),
                    "descricao": nova_descricao.strip(),
                    "texto": novo_texto,
                    "status": novo_status,
                    "csv_associado": novo_csv.strip(),
                    "fonte_texto": nova_fonte_texto.strip(),
                }

                try:
                    atualizar_conteudo(
                        dados_atualizados,
                        registro_original,
                    )

                    st.session_state.pop(
                        chave_original,
                        None,
                    )
                    st.session_state.pop(
                        "registro_selecionado",
                        None,
                    )

                    st.session_state["mensagem_sucesso"] = (
                        "Conteúdo atualizado no Google Sheets!"
                    )

                    st.rerun()

                except ValueError as erro:
                    st.error(str(erro))

                except Exception as erro:
                    st.error(
                        f"Erro ao atualizar: {erro}"
                    )

    else:
        st.info("Nenhum conteúdo encontrado.")


elif pagina == "Indicadores":
    st.subheader("Indicadores da Primeira Infância")

    st.write(
        "Consulte os CSVs gerados pelos pipelines do projeto."
    )

    try:
        arquivos = listar_csvs()

        if arquivos:
            arquivo_selecionado = st.selectbox(
                "Selecione um arquivo CSV:",
                arquivos,
            )

            dados = ler_csv(arquivo_selecionado)

            st.success(
                f"Arquivo carregado: {arquivo_selecionado}"
            )

            st.write(
                f"Total de registros: {len(dados)}"
            )

            st.dataframe(
                dados,
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("Nenhum CSV encontrado.")

    except (
        FileNotFoundError,
        ValueError,
        OSError,
        UnicodeError,
        pd.errors.ParserError,
    ) as erro:
        st.error(
            f"Não foi possível carregar os CSVs: {erro}"
        )


elif pagina == "Importação JSON":
    st.subheader("Importação de conteúdos por JSON")

    st.write(
        "Carregue e valide os conteúdos padronizados "
        "antes de importá-los para o sistema."
    )

    arquivo_json = st.file_uploader(
        "Selecione um arquivo JSON",
        type=["json"],
    )

    if arquivo_json is not None:
        import tempfile
        from pathlib import Path

        caminho_temporario = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".json",
                delete=False,
            ) as arquivo:
                arquivo.write(arquivo_json.getvalue())
                caminho_temporario = Path(arquivo.name)

            dados = importar_json(caminho_temporario)

            st.success("JSON validado com sucesso!")

            st.write(
                "Projeto:",
                dados["projeto"]["id_projeto"],
            )

            st.write(
                "Total de conteúdos:",
                len(dados["conteudos"]),
            )

            st.dataframe(
                pd.DataFrame(dados["conteudos"]),
                width="stretch",
                hide_index=True,
            )

            # Compara o JSON com o Google Sheets.
            st.subheader("Verificação de duplicidades")

            novos, existentes = verificar_duplicidades(
                dados,
                conteudos,
            )

            col1, col2 = st.columns(2)

            col1.metric(
                "Conteúdos novos",
                len(novos),
            )

            col2.metric(
                "Já cadastrados",
                len(existentes),
            )

            if novos:
                st.write("Conteúdos novos:")

                st.dataframe(
                    pd.DataFrame(novos),
                    width="stretch",
                    hide_index=True,
                )

            if existentes:
                st.warning(
                    "Estes conteúdos já existem no Google Sheets "
                    "e não devem ser cadastrados novamente."
                )

                st.dataframe(
                    pd.DataFrame(existentes),
                    width="stretch",
                    hide_index=True,
                )

            if not novos:
                st.info(
                    "Não há conteúdos novos para importar."
                )

            else:
                try:
                    validar_conteudos_para_gravacao(
                        dados,
                        novos,
                    )

                except ValueError as erro:
                    st.warning(
                        "Gravação bloqueada: " + str(erro)
                    )

                else:
                    st.write(
                        "A importação adicionará somente os conteúdos "
                        "novos. Os registros existentes serão preservados."
                    )

                    confirmar = st.checkbox(
                        "Confirmo que revisei os conteúdos e autorizo "
                        "a gravação no Google Sheets",
                        key="confirmar_importacao_json",
                    )

                    if st.button(
                        "Importar conteúdos novos",
                        type="primary",
                        disabled=not confirmar,
                    ):
                        try:
                            registros_atuais = listar_conteudos()

                            novos_atuais, _ = verificar_duplicidades(
                                dados,
                                registros_atuais,
                            )

                            if not novos_atuais:
                                st.info(
                                    "Todos os conteúdos já estão "
                                    "cadastrados. Nenhum registro foi criado."
                                )

                            else:
                                validar_conteudos_para_gravacao(
                                    dados,
                                    novos_atuais,
                                )

                                id_projeto = dados[
                                    "projeto"
                                ]["id_projeto"]

                                importados = 0

                                for conteudo in novos_atuais:
                                    registro = preparar_conteudo_sheets(
                                        id_projeto,
                                        conteudo,
                                    )

                                    cadastrar_conteudo(registro)
                                    importados += 1

                                st.session_state[
                                    "mensagem_sucesso"
                                ] = (
                                    f"{importados} conteúdo(s) "
                                    "importado(s) para o Google Sheets!"
                                )

                                st.rerun()

                        except Exception as erro:
                            st.error(
                                "A importação foi interrompida: "
                                f"{erro}. Confira os registros na planilha "
                                "antes de tentar novamente; alguns podem "
                                "ter sido gravados."
                            )

            st.caption(
                "A pré-visualização não altera a planilha. "
                "A gravação só ocorre após confirmação."
            )

        except (
            ValueError,
            OSError,
            UnicodeError,
        ) as erro:
            st.error(
                f"Erro na importação: {erro}"
            )

        finally:
            if caminho_temporario is not None:
                caminho_temporario.unlink(
                    missing_ok=True
                )


elif pagina == "Revisões":
    st.subheader("Controle de revisões")

    em_revisao = [
        c
        for c in conteudos
        if c["status"] == "Em revisão"
    ]

    if em_revisao:
        st.dataframe(
            pd.DataFrame(em_revisao),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "Nenhum conteúdo em revisão."
        )


elif pagina == "Exportação CSV":
    st.subheader("Exportação de conteúdos aprovados")

    aprovados = [
        conteudo
        for conteudo in conteudos
        if str(
            conteudo.get("status", "")
        ).strip().casefold() == "aprovado"
    ]

    st.metric(
        "Conteúdos aprovados disponíveis",
        len(aprovados),
    )

    if aprovados:
        df = pd.DataFrame(aprovados)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Baixar conteúdos aprovados (CSV)",
            data=df.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name="conteudos_aprovados.csv",
            mime="text/csv",
        )

    else:
        st.info(
            "Nenhum conteúdo aprovado disponível para exportação."
        )
