import os
import bcrypt
import pymysql
import base64

from mangum import Mangum
from fastapi import FastAPI, Request, Form, Depends, Response, UploadFile, File , HTTPException , status 
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
app.add_middleware(SessionMiddleware, secret_key="clinica", max_age=20)  #10 segundos

# Configuração de arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuração de templates Jinja2
templates = Jinja2Templates(directory="templates/pages")

# Configuração do banco de dados
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1234",
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
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)
    #return RedirectResponse(url="/login.html", status_code=303)
    return templates.TemplateResponse("prodIncluir.html", {
        "request": request,
    })

@app.get("/usuarios/{usuario_id}", response_class=HTMLResponse)
async def listar_usuarios(usuario_id: int, request: Request, db = Depends(get_db)):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # Buscar informações do usuário
            cursor.execute("SELECT * FROM Usuario WHERE ID = %s", (usuario_id,))
            usuarios = cursor.fetchall()
            
            if not usuarios:
                return HTMLResponse(content="Usuário não encontrado", status_code=404)
                
            usuario = usuarios[0]  # Pega o primeiro usuário
            
            # Buscar compras do usuário com detalhes de endereço
            cursor.execute("""
                SELECT
                    c.ID_Compra,
                    c.Data_Compra,
                    c.Status,
                    c.Forma_Pagamento,
                    c.Rua_entrega,
                    c.Numero_entrega,
                    c.Bairro_entrega,
                    c.Cidade_entrega,
                    c.CEP_entrega
                FROM Compra c
                WHERE c.ID_Usuario = %s AND c.Status = 'fechada'
                ORDER BY c.Data_Compra DESC
            """, (usuario_id,))
            compras = cursor.fetchall()

            # Para cada compra, busca os produtos comprados
            for compra in compras:
                cursor.execute("""
                    SELECT 
                        p.Nome_Produto,
                        p.Preco_prod,
                        qp.Qtn_Produto,
                        (p.Preco_prod * qp.Qtn_Produto) as Subtotal
                    FROM QTD_Produto qp
                    JOIN Produto p ON p.ID_Produto = qp.fk_Produto_ID_Produto
                    WHERE qp.fk_Compra_ID_Compra = %s
                """, (compra["ID_Compra"],))
                compra["produtos"] = cursor.fetchall()
                
                # Calcula o total da compra
                compra["total"] = sum(item["Subtotal"] for item in compra["produtos"])

        return templates.TemplateResponse("listar_usuarios.html", {
            "request": request,
            "usuarios": usuarios,
            "compras": compras,
            "single_user_view": True
        })
            
    except Exception as e:
        print("Erro ao recuperar usuários:", e)
        return HTMLResponse(content=f"Erro ao carregar dados do usuário: {str(e)}", status_code=500)
    finally:
        db.close()

@app.get("/deletar_usuario/{usuario_id}", name="deletar_usuario")
async def deletar_usuario(request: Request, usuario_id: int, db=Depends(get_db)):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)
    try:
        with db.cursor() as cursor: 
            cursor.execute("DELETE FROM Usuario WHERE ID = %s", (usuario_id,))
            db.commit()
        
        request.session["icon"] = "success" 
        request.session["mensagem_header"] = "Sucesso!"
        request.session["mensagem"] = "Usuário deletado com sucesso."
        
        return RedirectResponse(url="/index", status_code=status.HTTP_302_FOUND)
    except pymysql.Error as db_err: 
        print(f"Erro de banco de dados ao deletar usuário: {db_err}")
        request.session["icon"] = "error"
        request.session["mensagem_header"] = "Erro de Banco de Dados!"
        request.session["mensagem"] = "Não foi possível deletar o usuário devido a um problema no banco de dados."
        referer_url = request.headers.get("referer", "/index") 
        return RedirectResponse(url=referer_url, status_code=status.HTTP_302_FOUND)
    except Exception as e:
        print(f"Erro geral ao deletar usuário: {e}")
        request.session["icon"] = "error"
        request.session["mensagem_header"] = "Erro!"
        request.session["mensagem"] = f"Não foi possível deletar o usuário. Detalhes: {str(e)}"
        referer_url = request.headers.get("referer", "/index")
        return RedirectResponse(url=referer_url, status_code=status.HTTP_302_FOUND)
    finally:
        if db: 
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
            # Verifica se o e-mail já está cadastrado
                        # Verifica e-mail
            cursor.execute("SELECT 1 FROM Usuario WHERE Email = %s", (email,))
            email_existe = cursor.fetchone()

            # Verifica CPF
            cursor.execute("SELECT 1 FROM Usuario WHERE CPF = %s", (cpf,))
            cpf_existe = cursor.fetchone()

            if email_existe:
                raise HTTPException(status_code=400, detail="Email já cadastrado.")
            if cpf_existe:
                raise HTTPException(status_code=400, detail="CPF já cadastrado.")
            try:
                data_nascimento = datetime.strptime(dt_nasc, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Data de nascimento inválida. Use o formato YYYY-MM-DD.")

            senha_hash = hash_password(senha)

            cursor.execute("""
                INSERT INTO Usuario (Nome, Email, Senha, Dt_Nasc, Telefone, CPF, ADM)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (nome, email, senha_hash, data_nascimento, telefone, cpf, False))
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
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)
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
                "editar_usuario.html",            # <-- nome do template
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
    request: Request,
    usuario_id: int,
    nome: str = Form(...),
    email: str = Form(...),
    dt_nasc: str = Form(...),
    telefone: str = Form(...),
    senha_antiga: str = Form(None),
    senha_nova: str = Form(None),
    db=Depends(get_db)
):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT Senha FROM Usuario WHERE Id = %s", (usuario_id,))
            resultado = cursor.fetchone()

            if not resultado:
                return HTMLResponse(content="Usuário não encontrado.", status_code=404)

            senha_atual_hash = resultado[0]

            if senha_nova:
                if not senha_antiga:
                    return HTMLResponse("Você precisa informar a senha atual para mudar a senha.", status_code=400)
                if not verify_password(senha_antiga, senha_atual_hash):
                    return HTMLResponse("Senha atual incorreta.", status_code=401)

                nova_senha_hash = hash_password(senha_nova)
                cursor.execute("""
                    UPDATE Usuario
                    SET Nome = %s, Email = %s, Dt_Nasc = %s, Telefone = %s, Senha = %s
                    WHERE Id = %s
                """, (nome, email, dt_nasc, telefone, nova_senha_hash, usuario_id))
            else:
                cursor.execute("""
                    UPDATE Usuario
                    SET Nome = %s, Email = %s, Dt_Nasc = %s, Telefone = %s
                    WHERE Id = %s
                """, (nome, email, dt_nasc, telefone, usuario_id))

            db.commit()
        return RedirectResponse(url="/login", status_code=302)

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
    imagem: UploadFile = File(None),  
    db = Depends(get_db)
):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)
    
    try:
        imagem_bytes = None
        if imagem:
            imagem_bytes = await imagem.read()
        
        with db.cursor() as cursor:
            sql = """
                INSERT INTO Produto 
                (Nome_Produto, Descr_Produto, Preco_prod, Tipo_prod, Qtn_Produto, Img_Produto) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (nome, descr, preco, tipo, qtd, imagem_bytes))
            db.commit()
            request.session["icon"] = "sucess"
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

@app.get("/imagem_produto/{produto_id}")
async def get_imagem_produto(produto_id: int, db = Depends(get_db)):
    with db.cursor() as cursor:
        cursor.execute("SELECT Img_Produto FROM Produto WHERE ID_Produto = %s", (produto_id,))
        result = cursor.fetchone()
        if result and result[0]:
            return Response(content=result[0], media_type="image/jpeg")
        # Retorna uma imagem padrão se não houver imagem no banco
        default_image_path = os.path.join("static", "imagens", "coffe.jpeg")
        with open(default_image_path, "rb") as f:
            default_image = f.read()
        return Response(content=default_image, media_type="image/jpeg")


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
            p.Qtn_Produto,
            p.Img_Produto
        FROM produto p
    """

    if filtros:
        sql += " WHERE " + " AND ".join(filtros)

    print("SQL gerado:", sql)
    print("Valores dos filtros:", valores)

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(sql, valores)
        produtos = cursor.fetchall()

        produtos_carrinho_ids = set()
        id_compra = request.session.get("id_compra")

        if id_compra:
        # Verifica se a compra ainda está aberta
            cursor.execute("SELECT status FROM Compra WHERE ID_Compra = %s", (id_compra,))
            compra = cursor.fetchone()

            if compra and compra["status"] == "aberta":
                # Se a compra estiver aberta, busca os produtos no carrinho
                cursor.execute("""
                    SELECT fk_Produto_ID_Produto FROM QTD_Produto
                    WHERE fk_Compra_ID_Compra = %s
                """, (id_compra,))
                produtos_carrinho = cursor.fetchall()
                produtos_carrinho_ids = {item['fk_Produto_ID_Produto'] for item in produtos_carrinho}

    # Marca no_carrinho como True ou False com base no filtro acima
    for prod in produtos:
        prod["no_carrinho"] = prod["ID_Produto"] in produtos_carrinho_ids
            

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    return templates.TemplateResponse("catalogo.html", {
        "request": request,
        "produtos": produtos,
        "produtos_carrinho_ids": produtos_carrinho_ids,
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

@app.get("/prodexcluir_exe/{id}")
async def prodexcluir_exe(request: Request, id: int, db = Depends(get_db)):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            sql_delete = "DELETE FROM Produto WHERE ID_Produto = %s"
            cursor.execute(sql_delete, (id,))
            db.commit()

            request.session["mensagem_header"] = "Exclusão de Produto"
            request.session["mensagem"] = "Produto excluído com sucesso."
    except Exception as e:
        request.session["mensagem_header"] = "Erro ao excluir"
        request.session["mensagem"] = str(e)
    finally:
        db.close()

    # Redireciona diretamente para o catálogo
    return RedirectResponse(url="/catalogo", status_code=303)

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
    imagem: UploadFile = File(None),  
    db=Depends(get_db)
):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)

    try:
        imagem_bytes = None
        if imagem:
            imagem_bytes = await imagem.read()

        with db.cursor() as cursor:
            sql = """
                UPDATE Produto
                SET Nome_Produto = %s,
                    Descr_Produto = %s,
                    Preco_prod = %s,
                    Tipo_prod = %s,
                    Qtn_Produto = %s,
                    Img_Produto = %s
                WHERE ID_Produto = %s
            """
            cursor.execute(sql, (nome, descr, preco, tipo, qtd, imagem_bytes, id))
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
    mensagem_header = request.session.pop("mensagem_header", None)
    mensagem = request.session.pop("mensagem", None)

    if not request.session.get("user_logged_in"):   
        return RedirectResponse(url="/", status_code=303)

    id_cliente = request.session.get("Id")
    id_compra = request.session.get("id_compra")

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        sql_remove_zerados = """
            DELETE FROM qtd_produto
            WHERE fk_Compra_ID_Compra = %s
              AND fk_Produto_ID_Produto IN (
                  SELECT ID_Produto FROM produto WHERE Qtn_Produto = 0
              )
        """
        cursor.execute(sql_remove_zerados, (id_compra,))
        db.commit()
        
        
        # Produtos no carrinho
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
                c.ID_Usuario = %s  
                AND c.ID_Compra = %s
                AND c.Status = 'aberta'
                AND p.Qtn_Produto > 0;
        """
        cursor.execute(sql, (id_cliente, id_compra))
        produtos = cursor.fetchall()
        tem_prod = len(produtos) > 0

        # Busca os endereços do cliente
        sql_endereco = """
            SELECT 
                ID_Endereco, Rua, Numero, Cidade, CEP, Bairro
            FROM 
                endereco
            WHERE 
                fk_ID_Usuario = %s
        """
        cursor.execute(sql_endereco, (id_cliente,))
        enderecos = cursor.fetchall()
        tem_endereco = len(enderecos) > 0
    return templates.TemplateResponse("carrinho.html", {
        "request": request,
        "produtos": produtos,
        "id_compra": id_compra,
        "mensagem_header": mensagem_header,
        "mensagem": mensagem,
        "total": sum(prod["Preco_prod"] * prod["Qtn_Produto"] for prod in produtos),
        "enderecos": enderecos,  
        "tem_endereco": tem_endereco,
        "tem_prod": tem_prod 
    })
    
@app.get("/carrinhoincluir")
async def carrinhoincluir(request: Request, id_prod: int, db=Depends(get_db)):
    id_cliente = request.session.get("Id")
    if not id_cliente:
        return RedirectResponse("/login", status_code=303)

    try:
        with db.cursor() as cursor:
            # 🔍 Busca uma compra ABERTA para o cliente
            cursor.execute("""
                SELECT ID_Compra FROM Compra
                WHERE ID_Usuario = %s AND Status = 'aberta'
                ORDER BY ID_Compra DESC LIMIT 1
            """, (id_cliente,))
            compra = cursor.fetchone()

            # 🆕 Se não tiver compra aberta, cria uma nova
            if compra:
                id_compra = compra[0]
            else:
                cursor.execute("""
                    INSERT INTO Compra (ID_Usuario, Status)
                    VALUES (%s, 'aberta')
                """, (id_cliente,))
                db.commit()
                id_compra = cursor.lastrowid

            # Salva o ID da compra na sessão
            request.session["id_compra"] = id_compra

            # ✅ Insere ou atualiza item no carrinho
            sql = """
                INSERT INTO QTD_Produto (fk_Compra_ID_Compra, fk_Produto_ID_Produto, Qtn_Produto)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE Qtn_Produto = Qtn_Produto + 1
            """
            cursor.execute(sql, (id_compra, id_prod))
            db.commit()
        request.session["icon"] = "sucess"
        request.session["mensagem_header"] = "Sucesso!"
        request.session["mensagem"] = "Produto adicionado ao carrinho!"
        return RedirectResponse("/carrinho", status_code=303)

    except Exception as e:
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
            request.session["mensagem_header"] = "Sucesso!"
            request.session["mensagem"] = "Produto removido do carrinho!"
            return RedirectResponse("/carrinho", status_code=303)

    except Exception as e:
        request.session["mensagem"] = f"Erro ao remover produto: {str(e)}"
        return RedirectResponse("/carrinho", status_code=303)

    finally:
        db.close()

from fastapi import Form

@app.post("/atualizar-quantidade/{product_id}")
async def atualizar_quantidade(product_id: int, request: Request, qtd: int = Form(...), db=Depends(get_db)):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)

    try:
        if qtd < 1:
            raise ValueError("A quantidade não pode ser menor que 1.")

        id_compra = request.session.get("id_compra")

        with db.cursor() as cursor:
            # 1. Verifica o estoque disponível
            cursor.execute("SELECT Qtn_Produto FROM Produto WHERE ID_Produto = %s", (product_id,))
            estoque = cursor.fetchone()

            if not estoque:
                raise ValueError("Produto não encontrado.")

            estoque_disponivel = estoque[0]

            # 2. Verifica se a quantidade desejada é maior que o estoque
            if qtd > estoque_disponivel:
                request.session["icon"] = "error"
                request.session["mensagem_header"] = "Erro!"
                request.session["mensagem"] = "Quantidade solicitada excede o estoque disponível."
                return RedirectResponse("/carrinho", status_code=303)

            # 3. Atualiza a quantidade no carrinho
            sql = """
                UPDATE QTD_Produto
                SET Qtn_Produto = %s
                WHERE fk_Produto_ID_Produto = %s AND fk_Compra_ID_Compra = %s
            """
            cursor.execute(sql, (qtd, product_id, id_compra))
            db.commit()

        return RedirectResponse("/carrinho", status_code=303)

    except Exception as e:
        return {"error": f"Erro ao atualizar a quantidade: {str(e)}"}


@app.post("/finalizar_compra/{id_compra}")
async def finalizar(
    request: Request,
    id_compra: int,
    id_endereco: int = Form(...),
    pagamento: str = Form(...),
    db=Depends(get_db)
):
    id_cliente = request.session.get("Id")

    if not id_cliente:
        return RedirectResponse("/login", status_code=303)

    if not id_endereco:
        request.session["mensagem_header"] = "Erro"
        request.session["mensagem"] = "Selecione um endereço para finalizar a compra."
        return RedirectResponse("/carrinho", status_code=303)

    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # Pega os dados do endereço selecionado
            sql_endereco = """
                SELECT Rua, Numero, Bairro, Cidade, CEP
                FROM endereco
                WHERE ID_Endereco = %s AND fk_ID_Usuario = %s
            """
            cursor.execute(sql_endereco, (id_endereco, id_cliente))
            endereco = cursor.fetchone()
            
            
            cursor.execute("""
                SELECT p.ID_Produto, p.Qtn_Produto AS estoque_atual, qp.Qtn_Produto AS qtd_solicitada, p.Nome_Produto
                FROM produto p
                JOIN qtd_produto qp ON p.ID_Produto = qp.fk_Produto_ID_Produto
                WHERE qp.fk_Compra_ID_Compra = %s
            """, (id_compra,))
            produtos = cursor.fetchall()

            for produto in produtos:
                if produto["qtd_solicitada"] > produto["estoque_atual"]:
                    request.session["mensagem_header"] = "Estoque insuficiente"
                    request.session["mensagem"] = (
                        f"Produto '{produto['Nome_Produto']}' possui apenas "
                        f"{produto['estoque_atual']} unidades em estoque, "
                        f"mas você solicitou {produto['qtd_solicitada']}."
                    )
                    return RedirectResponse("/carrinho", status_code=303)
            
            
            
            # Atualizar a compra com os dados do endereço e forma de pagamento
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql_update_compra = """
                UPDATE compra
                SET 
                    Status = 'fechada',
                    Data_Compra = %s,
                    Forma_Pagamento = %s,
                    Rua_entrega = %s,
                    Numero_entrega = %s,
                    Bairro_entrega = %s,
                    Cidade_entrega = %s,
                    CEP_entrega = %s
                WHERE ID_Compra = %s AND ID_Usuario = %s
            """
            cursor.execute(sql_update_compra, (
                data_atual,
                pagamento,
                endereco["Rua"],
                endereco["Numero"],
                endereco["Bairro"],
                endereco["Cidade"],
                endereco["CEP"],
                id_compra,
                id_cliente
            ))
            db.commit()

            # Atualizar o estoque dos produtos
            sql_update_estoque = """ 
                UPDATE produto
                SET Qtn_Produto = Qtn_Produto - (
                    SELECT Qtn_Produto
                    FROM qtd_produto
                    WHERE qtd_produto.fk_Compra_ID_Compra = %s 
                      AND qtd_produto.fk_Produto_ID_Produto = produto.ID_Produto
                )
                WHERE ID_Produto IN (
                    SELECT fk_Produto_ID_Produto
                    FROM qtd_produto
                    WHERE fk_Compra_ID_Compra = %s
                )
            """
            cursor.execute(sql_update_estoque, (id_compra, id_compra))
            db.commit()

            # Encerrar a sessão da compra
            request.session["id_compra"] = None
            request.session["mensagem_header"] = "Compra finalizada"
            request.session["mensagem"] = "Compra finalizada com sucesso!"
            return RedirectResponse("/carrinho", status_code=303)

    except Exception as e:
        request.session["mensagem_header"] = "Erro"
        request.session["mensagem"] = f"Erro ao finalizar a compra: {str(e)}"
        return RedirectResponse("/carrinho", status_code=303)

    finally:
        db.close()
        
@app.post("/cadastrar_endereco_exe")
async def cadastrar_endereco_exe(
    request: Request,
    rua: str = Form(...),
    num: str = Form(...),
    bairro: str = Form(...),
    cidade: str = Form(...),
    cep: str = Form(...),
    db=Depends(get_db)
):
    id_cliente = request.session.get("Id")

    if not id_cliente:
        return RedirectResponse("/login", status_code=303)

    try:
        with db.cursor() as cursor:
            # Inserir novo endereço vinculado ao usuário
            sql_insert_endereco = """
                INSERT INTO endereco (Rua, Numero, Cidade, CEP, Bairro, fk_ID_Usuario)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_insert_endereco, (rua, num, cidade, cep, bairro, id_cliente))
            db.commit()
            id_endereco = cursor.lastrowid
            print("Endereço adicionado com ID:", id_endereco)
            
            request.session["mensagem_header"] = "Endereço cadastrado"
            request.session["mensagem"] = "Endereço cadastrado com sucesso!"
            return RedirectResponse("/carrinho", status_code=303)
    except Exception as e:
        request.session["mensagem_header"] = "Erro"
        request.session["mensagem"] = f"Erro ao cadastrar endereço: {str(e)}"
        return RedirectResponse("/carrinho", status_code=303)

    finally:
        db.close()

@app.get("/cadastrar_endereco")
async def incluirproduto(
    request: Request
):
    #return RedirectResponse(url="/login.html", status_code=303)
    return templates.TemplateResponse("enderecoIncluir.html", {
        "request": request,
    })
@app.get("/editar_endereco/{id_endereco}")
async def editar_endereco(
    request: Request,
    id_endereco: int,
    db=Depends(get_db)
):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)
    id_cliente = request.session.get("Id")
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM endereco WHERE ID_Endereco = %s AND fk_ID_Usuario = %s", (id_endereco,id_cliente))
            endereco = cursor.fetchone()

            if not endereco:
                return HTMLResponse("Endereço não encontrado", status_code=404)

            return templates.TemplateResponse("enderecoatualizar.html", {
                "request": request,
                "endereco": endereco
            })

    except Exception as e:
        print("Erro ao buscar endereço:", e)
        return HTMLResponse("Erro ao carregar endereço.", status_code=500)
    finally:
        db.close()
        
@app.post("/editar_endereco_exe/{id_endereco}")
async def editar_endereco_exe(
    id_endereco: int,
    request: Request,
    rua: str = Form(...),
    num: str = Form(...),
    bairro: str = Form(...),
    cidade: str = Form(...),
    cep: str = Form(...),
    db=Depends(get_db)
):
    id_cliente = request.session.get("Id")

    if not id_cliente:
        return RedirectResponse("/login", status_code=303)

    try:
        with db.cursor() as cursor:
            # Atualiza o endereço apenas se ele pertencer ao usuário logado
            sql = """
                UPDATE endereco
                SET Rua = %s, Numero = %s, Cidade = %s, CEP = %s, Bairro = %s
                WHERE ID_Endereco = %s AND fk_ID_Usuario = %s
            """
            cursor.execute(sql, (rua, num, cidade, cep, bairro, id_endereco, id_cliente))
            db.commit()

            request.session["mensagem_header"] = "Endereço atualizado"
            request.session["mensagem"] = "Endereço atualizado com sucesso!"
            return RedirectResponse("/carrinho", status_code=303)

    except Exception as e:
        request.session["mensagem_header"] = "Erro"
        request.session["mensagem"] = f"Erro ao atualizar endereço: {str(e)}"
        return RedirectResponse("/carrinho", status_code=303)

    finally:
        db.close()

@app.get("/endereco_excluir/{id_endereco}")
async def endereco_excluir(
    id_endereco: int,
    request: Request,
    db=Depends(get_db)
):
    id_cliente = request.session.get("Id")

    if not id_cliente:
        return RedirectResponse("/login", status_code=303)

    try:
        with db.cursor() as cursor:
            sql = """
                DELETE FROM endereco
                WHERE ID_Endereco = %s AND fk_ID_Usuario = %s
            """
            cursor.execute(sql, (id_endereco, id_cliente))
            db.commit()

            request.session["mensagem_header"] = "Endereço removido"
            request.session["mensagem"] = "Endereço excluído com sucesso!"
            return RedirectResponse("/carrinho", status_code=303)

    except Exception as e:
        request.session["mensagem_header"] = "Erro"
        request.session["mensagem"] = f"Erro ao excluir endereço: {str(e)}"
        return RedirectResponse("/carrinho", status_code=303)

    finally:
        db.close()



@app.post("/reset_session")
async def reset_session(request: Request):
    request.session.pop("mensagem_header", None)
    request.session.pop("mensagem", None)
    return {"status": "ok"}

handler = Mangum(app)