## Preparação do ambiente e execução do projeto

1. Configure o banco de dados MySQL usando o script da pasta db.
2. Altere o login e senha do MySQL no arquivo main.py.
2. Na pasta raiz do projeto execute os comandos abaixo:

```
python -m venv .venv
.venv\Scripts\Activate.bat
pip install --upgrade -r requirements.txt
uvicorn main:app --reload
```