Demo run instructions

1. Start backend (uses included venv and fallbacks):

```powershell
cd "C:\Users\rajdi\Downloads\Energy-Optimization-Platform-main\Energy-Optimization-Platform-main\backend"
"C:\Users\rajdi\Downloads\Energy-Optimization-Platform-main\Energy-Optimization-Platform-main\.venv\Scripts\python.exe" -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

2. Open demo UI in browser:

http://127.0.0.1:8000/

3. (Optional) Run full frontend for interview demo:

- Install Node.js 18+ if not installed.

```powershell
cd "C:\Users\rajdi\Downloads\Energy-Optimization-Platform-main\Energy-Optimization-Platform-main\frontend"
npm install --legacy-peer-deps
npm run dev
```

Vite will show the local URL (usually http://127.0.0.1:5173 or http://localhost:3000). It proxies /api to the backend.

Notes:
- The backend includes dummy model fallbacks so the API starts even without trained model artifacts.
- To persist changes, commit and push to your remote repository (see below).
