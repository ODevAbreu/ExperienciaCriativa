## Preparação do ambiente e execução do projeto

1. Na pasta raiz do projeto execute os comandos abaixo:

```
python -m venv .venv
.venv\Scripts\Activate.bat
pip install --upgrade -r requirements.txt
uvicorn main:app --reload
```
