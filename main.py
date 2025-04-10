import pymysql
import base64

from mangum import Mangum
from fastapi import FastAPI, Request, Form, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from datetime import date, datetime

app = FastAPI()

# Configuração de sessão (chave secreta para cookies de sessão)
app.add_middleware(SessionMiddleware, secret_key="clinica")

# Configuração de arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuração de templates Jinja2
templates = Jinja2Templates(directory="templates/pages")

# Configuração do banco de dados
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "PUC@1234",
    "database": "coffe"
}


# Função para obter conexão com MySQL
def get_db():
    return pymysql.connect(**DB_CONFIG)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if request.session.get("user_logged_in"):
        return RedirectResponse(url="/catalogo", status_code=303)

    login_error = request.session.pop("login_error", None)
    show_login_modal = request.session.pop("show_login_modal", False)
    nome_usuario = request.session.get("nome_usuario", None)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "login_error": login_error,
        "show_login_modal": "block" if show_login_modal else "none",
        "nome_usuario": nome_usuario
    })

@app.post("/login")
async def login(
    request: Request,
    Login: str = Form(...),
    Senha: str = Form(...),
    db = Depends(get_db)
):
    try:
        with db.cursor() as cursor:

            cursor.execute("SELECT * FROM Usuario WHERE Login = %s AND Senha = MD5(%s)", (Login, Senha))
            user = cursor.fetchone()

            if user:
                request.session["user_logged_in"] = True
                request.session["nome_usuario"] = user[1]
                return RedirectResponse(url="/medListar", status_code=303)
            else:
                request.session["login_error"] = "Usuário ou senha inválidos."
                request.session["show_login_modal"] = True
                return RedirectResponse(url="/", status_code=303)
    finally:
        db.close()

@app.get("/logout")
async def logout(request: Request):
    # Encerra a sessão do usuário e retorna à página inicial.
    request.session.clear()  # remove todos os dados de sessão
    return RedirectResponse(url="/", status_code=303)

@app.post("/cadastro", name="cadastro")
async def cadastrar_usuario(
    request: Request,
    nome: str = Form(...),
    Login: str = Form(...),
    Celular: str = Form(...),
    Senha1: str = Form(...),
    db = Depends(get_db)
):
    try:
        with db.cursor() as cursor:

            cursor.execute("SELECT ID_Usuario FROM Usuario WHERE Login = %s", (Login,))
            if cursor.fetchone():
                request.session["nao_autenticado"] = True
                request.session["mensagem_header"] = "Cadastro"
                request.session["mensagem"] = "Erro: Este login já está em uso!"
                return RedirectResponse(url="/", status_code=303)

            sql = "INSERT INTO Usuario (Nome, Celular, Login, Senha) VALUES (%s, %s, %s, MD5(%s))"
            cursor.execute(sql, (nome, Celular, Login, Senha1))
            db.commit()

            request.session["nao_autenticado"] = True
            request.session["mensagem_header"] = "Cadastro"
            request.session["mensagem"] = "Registro cadastrado com sucesso! Você já pode realizar login."
            return RedirectResponse(url="/", status_code=303)

    except Exception as e:
        request.session["nao_autenticado"] = True
        request.session["mensagem_header"] = "Cadastro"
        request.session["mensagem"] = f"Erro ao cadastrar: {str(e)}"
        return RedirectResponse(url="/", status_code=303)

    finally:
        db.close()

@app.get("/catalogo.html", name="medListar", response_class=HTMLResponse)
async def listar_medicos(request: Request, db=Depends(get_db)):
    # if not request.session.get("user_logged_in"):
    #     return RedirectResponse(url="/", status_code=303)

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        # Consulta SQL unindo Medico e Especialidade, ordenando por nome
        sql = """
            SELECT p.ID_Produto, p.Nome_Produto FROM produto p
        """
        cursor.execute(sql)
        produtos = cursor.fetchall()  # lista de dicts com dados dos médicos

    # Processa os dados (calcula idade e converte foto para base64 se necessário)
    hoje = date.today()
    for prod in produtos:
        Nome_Produto = prod["Nome_Produto"]


    # nome_usuario = request.session.get("nome_usuario", None)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Renderiza o template 'medListar.html' com os dados dos médicos
    return templates.TemplateResponse("catalogo.html", {
        "request": request,
        "produtos": produtos,
        "hoje": agora,
        # "nome_usuario": nome_usuario
    })

@app.get("/medIncluir", response_class=HTMLResponse)
async def medIncluir(request: Request, db=Depends(get_db)):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)

    # Obter especialidades do banco para o combo
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT ID_Espec, Nome_Espec FROM Especialidade")
        especialidades = cursor.fetchall()
    db.close()

    # Dados para o template (incluindo data/hora e nome do usuário)
    nome_usuario = request.session.get("nome_usuario", None)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return templates.TemplateResponse("medIncluir.html", {
        "request": request,
        "especialidades": especialidades,
        "hoje": agora,
        "nome_usuario": nome_usuario
    })

@app.post("/medIncluir_exe")
async def medIncluir_exe(
    request: Request,
    Nome: str = Form(...),
    CRM: str = Form(...),
    Especialidade: str = Form(...),
    DataNasc: str = Form(None),
    Imagem: UploadFile = File(None),
    db=Depends(get_db)
):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)

    foto_bytes = None
    if Imagem and Imagem.filename:
        foto_bytes = await Imagem.read()

    try:
        with db.cursor() as cursor:
            sql = """INSERT INTO Medico (Nome, CRM, ID_Espec, Dt_Nasc, Foto)
                     VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(sql, (Nome, CRM, Especialidade, DataNasc, foto_bytes))
            db.commit()

        request.session["mensagem_header"] = "Inclusão de Novo Médico"
        request.session["mensagem"] = "Registro cadastrado com sucesso!"
    except Exception as e:
        request.session["mensagem_header"] = "Erro ao cadastrar"
        request.session["mensagem"] = str(e)
    finally:
        db.close()

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    nome_usuario = request.session.get("nome_usuario", None)

    return templates.TemplateResponse("medIncluir_exe.html", {
        "request": request,
        "mensagem_header": request.session.get("mensagem_header", ""),
        "mensagem": request.session.get("mensagem", ""),
        "hoje": agora,
        "nome_usuario": nome_usuario
    })

@app.get("/medExcluir", response_class=HTMLResponse)
async def med_excluir(request: Request, id: int, db=Depends(get_db)):

    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        sql = ("SELECT M.ID_Medico, M.Nome, M.CRM, M.Dt_Nasc, E.Nome_Espec "
               "FROM Medico M JOIN Especialidade E ON M.ID_Espec = E.ID_Espec "
               "WHERE M.ID_Medico = %s")
        cursor.execute(sql, (id,))
        medico = cursor.fetchone()
    db.close()

    # Formatar data (YYYY-MM-DD para dd/mm/aaaa)
    data_nasc = medico["Dt_Nasc"]
    if isinstance(data_nasc, str):
        ano, mes, dia = data_nasc.split("-")
    else:
        ano, mes, dia = data_nasc.year, f"{data_nasc.month:02d}", f"{data_nasc.day:02d}"
    data_formatada = f"{dia}/{mes}/{ano}"

    hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
    nome_usuario = request.session.get("nome_usuario", None)

    return templates.TemplateResponse("medExcluir.html", {
        "request": request,
        "med": medico,
        "data_formatada": data_formatada,
        "hoje": hoje,
        "nome_usuario": nome_usuario
    })

@app.post("/medExcluir_exe")
async def med_excluir_exe(request: Request, id: int = Form(...), db=Depends(get_db)):

    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)

    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:

            sql_delete = "DELETE FROM Medico WHERE ID_Medico = %s"
            cursor.execute(sql_delete, (id,))
            db.commit()

            request.session["mensagem_header"] = "Exclusão de Médico"
            request.session["mensagem"] = f"Médico excluído com sucesso."

    except Exception as e:
        request.session["mensagem_header"] = "Erro ao excluir"
        request.session["mensagem"] = str(e)
    finally:
        db.close()

    # Redireciona para a página de resultado da exclusão
    return templates.TemplateResponse("medExcluir_exe.html", {
        "request": request,
        "mensagem_header": request.session.get("mensagem_header", ""),
        "mensagem": request.session.get("mensagem", ""),
        "hoje": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "nome_usuario": request.session.get("nome_usuario", None)
    })

@app.get("/medAtualizar", response_class=HTMLResponse)
async def med_atualizar(request: Request, id: int, db=Depends(get_db)):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT * FROM Medico WHERE ID_Medico = %s", (id,))
        medico = cursor.fetchone()
        cursor.execute("SELECT ID_Espec, Nome_Espec FROM Especialidade")
        especialidades = cursor.fetchall()
    db.close()

    hoje = datetime.now().strftime("%d/%m/%Y %H:%M")

    return templates.TemplateResponse("medAtualizar.html", {
        "request": request,
        "med": medico,
        "especialidades": especialidades,
        "hoje": hoje
    })

@app.post("/medAtualizar_exe")
async def med_atualizar_exe(
    request: Request,
    id: int = Form(...),
    Nome: str = Form(...),
    CRM: str = Form(...),
    Especialidade: str = Form(...),
    DataNasc: str = Form(None),
    Imagem: UploadFile = File(None),
    db=Depends(get_db)
):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)

    foto_bytes = None
    if Imagem and Imagem.filename:
        foto_bytes = await Imagem.read()

    try:
        with db.cursor() as cursor:
            if foto_bytes:
                sql = """UPDATE Medico 
                         SET Nome=%s, CRM=%s, Dt_Nasc=%s, ID_Espec=%s, Foto=%s
                         WHERE ID_Medico=%s"""
                cursor.execute(sql, (Nome, CRM, DataNasc, Especialidade, foto_bytes, id))
            else:
                sql = """UPDATE Medico 
                         SET Nome=%s, CRM=%s, Dt_Nasc=%s, ID_Espec=%s
                         WHERE ID_Medico=%s"""
                cursor.execute(sql, (Nome, CRM, DataNasc, Especialidade, id))
            db.commit()

        request.session["mensagem_header"] = "Atualização de Médico"
        request.session["mensagem"] = "Registro atualizado com sucesso!"

    except Exception as e:
        request.session["mensagem_header"] = "Erro ao atualizar"
        request.session["mensagem"] = str(e)
    finally:
        db.close()

    return templates.TemplateResponse("medAtualizar_exe.html", {
        "request": request,
        "mensagem_header": request.session.get("mensagem_header", ""),
        "mensagem": request.session.get("mensagem", ""),
        "hoje": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "nome_usuario": request.session.get("nome_usuario", None)
    })

@app.post("/reset_session")
async def reset_session(request: Request):
    request.session.pop("mensagem_header", None)
    request.session.pop("mensagem", None)
    return {"status": "ok"}

Mangum(app)