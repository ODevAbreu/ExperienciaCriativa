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
    "password": "",
    "database": "coffee"
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


@app.get("/paginaLogin")
async def login(
    request: Request
):
    print("chamou................ @app.get(/login)")
    #return RedirectResponse(url="/login.html", status_code=303)
    # Renderiza o template 'medListar.html' com os dados dos médicos
    return templates.TemplateResponse("login.html", {
        "request": request,
    })
    
@app.get("/cadastro")
async def cadastro(
    request: Request
):
    print("chamou................ @app.get(/cadastro)")
    #return RedirectResponse(url="/login.html", status_code=303)
    # Renderiza o template 'medListar.html' com os dados dos médicos
    return templates.TemplateResponse("cadastro.html", {
        "request": request,
    })

@app.get("/incluirproduto")
async def incluirproduto(
    request: Request
):
    #return RedirectResponse(url="/login.html", status_code=303)
    # Renderiza o template 'medListar.html' com os dados dos médicos
    return templates.TemplateResponse("prodIncluir.html", {
        "request": request,
    })


@app.post("/login")
async def login(
    request: Request,
    Login: str = Form(...),
    Senha: str = Form(...),
    db = Depends(get_db)
):
    print("chamou................ @app.get(/flogin)")
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
        
@app.post("/prodincluir_exe", name="prodincluir_exe")
async def prodincluir_exe(
    request: Request,
    nome: str = Form(...),
    descr: str = Form(...),
    tipo: str = Form(...),
    preco: str = Form(...),
    qtd: str = Form(...),
    db = Depends(get_db)
):
    print("chamou................ @app.get(/incluir)")
    try:
        with db.cursor() as cursor:
            sql = "INSERT INTO Produto (Nome_Produto, Descr_Produto, Preco_prod, Tipo_prod, Qtn_Produto) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (nome, descr, preco, tipo, qtd))
            db.commit()
            return RedirectResponse(url="catalogo", status_code=303)

    except Exception as e:
        return RedirectResponse(url="catalogo", status_code=303)

    finally:
        db.close()

@app.get("/catalogo", name="catalogo", response_class=HTMLResponse)
async def listar_prod(request: Request, db=Depends(get_db)):
    # if not request.session.get("user_logged_in"):
    #     return RedirectResponse(url="/", status_code=303)

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        # Consulta SQL unindo Medico e Especialidade, ordenando por nome
        sql = """
            SELECT
                p.ID_Produto,
                p.Nome_Produto,
                p.Descr_Produto,
                p.Preco_prod,
                p.Tipo_prod,
                p.Qtn_Produto
                FROM produto p
        """
        cursor.execute(sql)
        produtos = cursor.fetchall()  # lista de dicts com dados dos médicos

    # Processa os dados (calcula idade e converte foto para base64 se necessário)
    hoje = date.today()
    for prod in produtos:
        Nome_Produto = prod["Nome_Produto"]
        Descr_Produto = prod["Descr_Produto"]
        Preco_prod = prod["Preco_prod"] 
        Tipo_prod = prod["Tipo_prod"]
        Qtn_Produto = prod["Qtn_Produto"]
        ID_Produto = prod["ID_Produto"]

    # nome_usuario = request.session.get("nome_usuario", None)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Renderiza o template 'medListar.html' com os dados dos médicos
    return templates.TemplateResponse("catalogo.html", {
        "request": request,
        "produtos": produtos,
        "hoje": agora,
        # "nome_usuario": nome_usuario
    })


@app.get("/prodexcluir", response_class=HTMLResponse)
async def prodexcluir(request: Request, id: int, db=Depends(get_db)):
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        sql = ("SELECT * FROM Produto p WHERE p.ID_Produto = %s")
        cursor.execute(sql, (id,))
        produto = cursor.fetchone()
    db.close()


    return templates.TemplateResponse("prodexcluir.html", {
        "request": request,
        "prod": produto
    })

@app.post("/prodexcluir_exe")
async def prodexcluir_exe(request: Request, id: int = Form(...), db=Depends(get_db)):

    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:

            sql_delete = "DELETE FROM Produto WHERE ID_Produto = %s"
            cursor.execute(sql_delete, (id,))
            db.commit()

            request.session["mensagem_header"] = "Exclusão de Produto"
            request.session["mensagem"] = f"Produto excluído com sucesso."

    except Exception as e:
        request.session["mensagem_header"] = "Erro ao excluir"
        request.session["mensagem"] = str(e)
    finally:
        db.close()

    # Redireciona para a página de resultado da exclusão
    return templates.TemplateResponse("prodexcluir_exe.html", {
        "request": request,
        "mensagem_header": request.session.get("mensagem_header", ""),
        "mensagem": request.session.get("mensagem", "")
    })

@app.get("/prodatualizar", response_class=HTMLResponse)
async def prodatualizar(request: Request, id: int, db=Depends(get_db)):

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT * FROM Produto p WHERE p.ID_Produto = %s", (id,))
        produto = cursor.fetchone()

    db.close()

    return templates.TemplateResponse("prodatualizar.html", {
        "request": request,
        "p": produto,	
    })

@app.post("/prodatualizar_exe")
async def prodatualizar_exe(
    request: Request,
    id: int = Form(...),
    nome: str = Form(...),
    descr: str = Form(...),
    tipo: str = Form(...),
    preco: str = Form(...),
    qtd: str = Form(...),
    db=Depends(get_db)
):
    # if not request.session.get("user_logged_in"):
    #     return RedirectResponse(url="/", status_code=303)
    try:
        with db.cursor() as cursor:
            sql = """UPDATE Produto
                     SET Nome_Produto=%s, Descr_Produto=%s, Preco_prod=%s, Tipo_prod=%s, Qtn_Produto=%s 
                     WHERE ID_Produto=%s"""
            cursor.execute(sql, ( nome, descr, preco, tipo, qtd, id))
            db.commit()

    except Exception as e:
        request.session["mensagem_header"] = "Erro ao atualizar"
        request.session["mensagem"] = str(e)
    finally:
        db.close()

    return RedirectResponse(url="catalogo", status_code=303)

    # return templates.TemplateResponse("prodatualizar_exe.html", {
    #     "request": request,
    #     "mensagem_header": request.session.get("mensagem_header", ""),
    #     "mensagem": request.session.get("mensagem", ""),
    # })

@app.post("/reset_session")
async def reset_session(request: Request):
    request.session.pop("mensagem_header", None)
    request.session.pop("mensagem", None)
    return {"status": "ok"}

Mangum(app)