
## Deployment backend


```bash
  cd backend
```

```bash
  python -m venv venv

  source venv/Scripts/activate

  pip install -r requirements.txt

  touch .env
  # dán vào env: DB_URL = "mysql+pymysql://{db_user_name}:{db_password}@localhost:3306/{db_name}"

  uvicorn app.main:app --reload --log-level debug
```



## Deployment frontend

```bash
  cd frontend

  yarn install

  yarn dev
```
