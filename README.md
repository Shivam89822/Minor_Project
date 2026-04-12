# Minor_Project

## Quick setup

1. Clone the repository.
2. Backend:
   ```powershell
   cd Backend/Server
   python -m venv .venv
   & .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   python -m uvicorn main:app --reload
   ```
3. Frontend (new terminal):
   ```powershell
   cd Frontend
   npm install
   npm run dev
   ```

## Notes

- The backend runs on `http://127.0.0.1:8000`.
- The frontend usually runs on `http://localhost:5173` or `http://localhost:5174`.
- Use `Ctrl+C` to stop the servers.
- If you want a single pip install entrypoint, use:
  ```powershell
  cd /d D:\Minor_Project
  python -m venv Backend\Server\.venv
  & Backend\Server\.venv\Scripts\Activate.ps1
  pip install --upgrade pip
  pip install -r requirements.txt
  ```
