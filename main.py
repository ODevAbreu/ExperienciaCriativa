import pymysql
import base64

from mangum import Mangum
from fastapi import FastAPI, Request, Form, Depends, UploadFile, File , HTTPException , status 
from fastapi.responses import HTMLResponse, RedirectResponse 
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Query
from starlette.middleware.sessions import SessionMiddleware
from datetime import date, datetime
from typing import Annotated
from typing import List
from passlib.context import CryptContext

app = FastAPI()

# Criação do contexto de criptografia
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Criptografa a senha usando bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha fornecida corresponde à senha criptografada"""
    return pwd_context.verify(plain_password, hashed_password)

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
    "database": "coffee"
}




# Função para obter conexão com MySQL
def get_db():
    return pymysql.connect(**DB_CONFIG)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if request.session.get("user_logged_in"):
        return RedirectResponse(url="/index", status_code=303)

    login_error = request.session.pop("login_error", None)
    show_login_modal = request.session.pop("show_login_modal", False)
    nome_usuario = request.session.get("nome_usuario", None)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "login_error": login_error,
        "show_login_modal": "block" if show_login_modal else "none",
        "nome_usuario": nome_usuario
    })


@app.get("/login")
async def login(
    request: Request
):
    print("chamou................ @app.get(/login)")
    #return RedirectResponse(url="/login.html", status_code=303)
    # Renderiza o template 'medListar.html' com os dados dos médicos
    return templates.TemplateResponse("login.html", {
        "request": request,
    })
    
@app.get("/index")
async def index(
    request: Request
):
    print("chamou................ @app.get(/login)")
    #return RedirectResponse(url="/login.html", status_code=303)
    # Renderiza o template 'medListar.html' com os dados dos médicos
    return templates.TemplateResponse("index.html", {
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
    return templates.TemplateResponse("prodIncluir.html", {
        "request": request,
    })

@app.get("/usuarios/{usuario_id}", response_class=HTMLResponse)
async def listar_usuarios(usuario_id:int, request: Request, db = Depends(get_db)):
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM Usuario WHERE ID = %s", (usuario_id,))
            columns = [col[0] for col in cursor.description]
            usuarios = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return templates.TemplateResponse("listar_usuarios.html", {"request": request, "usuarios": usuarios})
    except Exception as e:
        print("Erro ao recuperar usuários:", e)
        return HTMLResponse(content="Erro ao carregar a lista de usuários.", status_code=500)
    finally:
        db.close()



@app.get("/deletar_usuario/{usuario_id}")
async def deletar_usuario(usuario_id: int, db=Depends(get_db)):
    try:
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM Usuario WHERE ID = %s", (usuario_id,))
            db.commit()
        return RedirectResponse(url="/usuarios", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        print("Erro ao deletar usuário:", e)
        return HTMLResponse(content="Erro ao deletar o usuário.", status_code=500)
    finally:
        db.close()



@app.post("/login")
async def login(
    request: Request,
    Login: str = Form(...),
    Senha: str = Form(...),
    db = Depends(get_db)
):
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM Usuario WHERE Email = %s", (Login,))
            user = cursor.fetchone()

            if user:
                (_, nome_usuario, email_usuario, senha_hash, _, _, _, adm) = user
                if verify_password(Senha, senha_hash):
                    request.session["user_logged_in"] = True
                    request.session["nome_usuario"] = nome_usuario
                    request.session["ADM"] = adm
                    request.session["Id"] = user[0]  # Armazena o ID do usuário na sessão
                     
                    cursor.execute("""    
                        SELECT ID_Compra FROM Compra
                        WHERE ID_Usuario = %s
                        ORDER BY ID_Compra DESC
                        LIMIT 1
                    """, (user[0],))
                    compra = cursor.fetchone()

                    if compra:
                        request.session["id_compra"] = compra[0]
                    else:
                        request.session["id_compra"] = None  # ou nem criar esse campo ainda
                        
                    return RedirectResponse(url="/index", status_code=303)
                else:
                    return templates.TemplateResponse("login.html", {
                        "request": request,
                        "erro": "Senha incorreta"
                    })
            else:
                return templates.TemplateResponse("login.html", {
                    "request": request,
                    "erro": "Usuário não encontrado"
                })

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
    nome: Annotated[str, Form(...)],
    email: Annotated[str, Form(...)],
    senha: Annotated[str, Form(...)],
    dt_nasc: Annotated[str, Form(...)],
    telefone: Annotated[str, Form(...)],
    cpf: Annotated[str, Form(...)],
    db = Depends(get_db)
):
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT 1 FROM Usuario WHERE Email=%s OR CPF=%s", (email, cpf))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email ou CPF já cadastrados.")
            try:
                data_nascimento = datetime.strptime(dt_nasc, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Data de nascimento inválida. Use o formato YYYY-MM-DD.")

            senha_hash = hash_password(senha)

            cursor.execute("""
                INSERT INTO Usuario (Nome, Email, Senha, Dt_Nasc, Telefone, CPF, ADM)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (nome, email, senha_hash, data_nascimento, telefone, cpf,False))
            db.commit()

    except HTTPException:     
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/editar_usuario/{usuario_id}", response_class=HTMLResponse)
async def editar_usuario_form(usuario_id: int, request: Request, db=Depends(get_db)):
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM Usuario WHERE Id = %s", (usuario_id,))
            usuario = cursor.fetchone()

            if not usuario:
                return HTMLResponse("Usuário não encontrado", status_code=404)

            # transforma a tupla em dict
            colunas = [d[0] for d in cursor.description]
            usuario_dict = dict(zip(colunas, usuario))

            return templates.TemplateResponse(
                "editar_usuario.html",            #  <-- seu template do formulário
                {
                    "request": request,
                    "usuario": usuario_dict       #  <-- passa os dados
                }
            )

    except Exception as e:
        print("Erro ao buscar usuário:", e)
        return HTMLResponse("Erro ao carregar usuário.", status_code=500)
    finally:
        db.close()




@app.post("/editar_usuario/{usuario_id}")
async def salvar_edicao_usuario(
    usuario_id: int,
    nome: str = Form(...),
    email: str = Form(...),
    dt_nasc: str = Form(...),
    telefone: str = Form(...),
    db=Depends(get_db)
):
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                UPDATE Usuario
                SET Nome = %s, Email = %s, Dt_Nasc = %s, Telefone = %s
                WHERE Id = %s
            """, (nome, email, dt_nasc, telefone, usuario_id))
            db.commit()
        return RedirectResponse(url="/usuarios", status_code=302)

    except Exception as e:
        print("Erro ao editar usuário:", e)
        return HTMLResponse(content="Erro ao salvar edição.", status_code=500)
    finally:
        db.close()

# opcional: rota de logout
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

        
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
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)
    try:
        with db.cursor() as cursor:
            sql = "INSERT INTO Produto (Nome_Produto, Descr_Produto, Preco_prod, Tipo_prod, Qtn_Produto) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (nome, descr, preco, tipo, qtd))
            db.commit()
            request.session["mensagem_header"] = "Cadastro de Produto"
            request.session["mensagem"] = f"Produto cadastrado com sucesso."
            return RedirectResponse(url="/catalogo", status_code=303)

    except Exception as e:
        request.session["mensagem_header"] = "Erro ao Cadastrar Produto"
        request.session["mensagem"] = str(e)

    finally:
        db.close()
    return templates.TemplateResponse("prodincluir_exe.html", {
        "request": request,
        "mensagem_header": request.session.get("mensagem_header", ""),
        "mensagem": request.session.get("mensagem", "")
    })

@app.get("/catalogo", name="catalogo", response_class=HTMLResponse)
async def listar_prod(
    request: Request,
    nome: str = Query(None),
    tipo: List[str] = Query(default=[]),
    db=Depends(get_db)
):
    print(">>> FUNÇÃO listar_prod FOI CHAMADA <<<")
    filtros = []
    valores = []

    if nome:
        filtros.append("p.Nome_Produto LIKE %s")
        valores.append(f"%{nome}%")

    if tipo:
        filtros.append("p.Tipo_prod IN (%s)" % ",".join(["%s"] * len(tipo)))
        valores.extend(tipo)

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

    if filtros:
        sql += " WHERE " + " AND ".join(filtros)

    print("SQL gerado:", sql)
    print("Valores dos filtros:", valores)

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(sql, valores)
        produtos = cursor.fetchall()

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    return templates.TemplateResponse("catalogo.html", {
        "request": request,
        "produtos": produtos,
        "hoje": agora,
        "nome": nome or "",
        "tipos_selecionados": tipo
    })

@app.get("/prodexcluir", response_class=HTMLResponse)
async def prodexcluir(request: Request, id: int, db=Depends(get_db)):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)
    
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
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)
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
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)
    try:
        with db.cursor() as cursor:
            sql = """UPDATE Produto
                     SET Nome_Produto=%s, Descr_Produto=%s, Preco_prod=%s, Tipo_prod=%s, Qtn_Produto=%s 
                     WHERE ID_Produto=%s"""
            cursor.execute(sql, ( nome, descr, preco, tipo, qtd, id))
            db.commit()
            request.session["mensagem_header"] = "Alterar Produto"
            request.session["mensagem"] = f"Produto alterado com sucesso."
            return RedirectResponse(url="/catalogo", status_code=303)
    except Exception as e:
        request.session["mensagem_header"] = "Erro ao atualizar"
        request.session["mensagem"] = str(e)
    finally:
        db.close()

 

    return templates.TemplateResponse("prodatualizar_exe.html", {
        "request": request,
        "mensagem_header": request.session.get("mensagem_header", ""),
        "mensagem": request.session.get("mensagem", ""),
    })
    
@app.get("/carrinho")
async def carrinho(
    request: Request,
    db=Depends(get_db)
):
    if not request.session.get("user_logged_in"):   
        return RedirectResponse(url="/", status_code=303)
    id_cliente = request.session.get("Id")
    id_compra = request.session.get("id_compra")
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        # Consulta SQL unindo Medico e Especialidade, ordenando por nome
        sql = """
            SELECT
                p.ID_Produto,
                p.Nome_Produto,
                p.Descr_Produto,
                p.Preco_prod,
                p.Tipo_prod,
                qp.Qtn_Produto
            FROM 
                Produto p
            JOIN 
                QTD_Produto qp ON p.ID_Produto = qp.fk_Produto_ID_Produto
            JOIN 
                Compra c ON qp.fk_Compra_ID_Compra = c.ID_Compra
            WHERE 
                c.ID_Usuario = %s  -- ID do usuário, passaremos isso no cursor
                AND c.ID_Compra = %s;  -- ID da compra, se necessário para filtrar compras abertas
        """
        cursor.execute(sql, (id_cliente, id_compra))
        produtos = cursor.fetchall() 
    return templates.TemplateResponse("carrinho.html", {
        "request": request,
        "produtos": produtos
    })
    
@app.get("/carrinhoincluir")
async def carrinhoincluir(request: Request, id_prod: int, db=Depends(get_db)):
    id_cliente = request.session.get("Id")
    if not id_cliente:
        return RedirectResponse("/login", status_code=303)

    try:
        with db.cursor() as cursor:
            # Verifica se já há compra em aberto
            id_compra = request.session.get("id_compra")

            if not id_compra:
                cursor.execute("INSERT INTO Compra (ID_Usuario) VALUES (%s)", (id_cliente,))
                db.commit()
                id_compra = cursor.lastrowid
                request.session["id_compra"] = id_compra

            # Adiciona ou atualiza produto na QTD_Produto
            sql = """
                INSERT INTO QTD_Produto (fk_Compra_ID_Compra, fk_Produto_ID_Produto, Qtn_Produto)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE Qtn_Produto = Qtn_Produto + 1
            """
            cursor.execute(sql, (id_compra, id_prod, 1))
            db.commit()

        request.session["mensagem"] = "Produto adicionado ao carrinho!"
        print("deuboa", request.session["mensagem"])
        return RedirectResponse("/carrinho", status_code=303)

    except Exception as e:
        print(f"Erro ao adicionar produto no carrinho: {str(e)}")
        request.session["mensagem"] = f"Erro: {str(e)}"
        return RedirectResponse("/carrinho", status_code=303)

    finally:
        db.close()

@app.get("/carrinho/remover/{id_prod}")
async def carrinho_remover(request: Request, id_prod: int, db=Depends(get_db)):
    id_cliente = request.session.get("Id")
    if not id_cliente:
        return RedirectResponse("/login", status_code=303)

    try:
        with db.cursor() as cursor:
            # Verifica se já há uma compra em aberto
            id_compra = request.session.get("id_compra")

            if not id_compra:
                request.session["mensagem"] = "Não há carrinho de compras aberto."
                return RedirectResponse("/carrinho", status_code=303)

            # Remove o produto do carrinho
            cursor.execute("DELETE FROM QTD_Produto WHERE fk_Compra_ID_Compra = %s AND fk_Produto_ID_Produto = %s", (id_compra, id_prod))
            db.commit()

            request.session["mensagem"] = "Produto removido do carrinho!"
            return RedirectResponse("/carrinho", status_code=303)

    except Exception as e:
        request.session["mensagem"] = f"Erro ao remover produto: {str(e)}"
        return RedirectResponse("/carrinho", status_code=303)

    finally:
        db.close()

@app.post("/atualizar-quantidade/{product_id}")
async def atualizar_quantidade(product_id: int, request: Request, db=Depends(get_db)):
    # Verifica se o usuário está logado
    qtd: int = Form(...)
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)
    try:
        # Verifica se a quantidade é válida (não pode ser menor que 1)
        if qtd < 1:
            raise ValueError("A quantidade não pode ser menor que 1.")
        
        # Atualiza a quantidade do produto no banco de dados
        with db.cursor() as cursor:
            sql = """
                UPDATE QTD_Produto
                SET Qtn_Produto = %s
                WHERE fk_Produto_ID_Produto = %s AND fk_Compra_ID_Compra = %s
            """
            id_compra = request.session.get("id_compra")
            cursor.execute(sql, (qtd, product_id, id_compra))
            db.commit()

        return RedirectResponse("/carrinho", status_code=303)
    except Exception as e:
        return {"error": f"Erro ao atualizar a quantidade: {str(e)}"} 

@app.post("/reset_session")
async def reset_session(request: Request):
    request.session.pop("mensagem_header", None)
    request.session.pop("mensagem", None)
    return {"status": "ok"}

handler = Mangum(app)