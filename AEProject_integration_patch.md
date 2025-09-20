# AEProject_integration_patch.md

## 1 Разрешить CORS в dev
```python
# main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 2 Эндпоинт автокомплита (если у вас уже есть свой /api/search — оставьте свой)
```python
from fastapi import FastAPI, Query
from typing import List

app = FastAPI()

@app.get("/api/search", response_model=List[str])
async def search(q: str = Query(..., min_length=1)):
    # Здесь ваш реальный поиск/подсказки
    demo = ["тендеры", "тендерный комитет", "самара", "самоцветы", "самолет"]
    return [s for s in demo if q.lower() in s.lower()][:10]
```

## 3 Раздача прод-сборки фронта через FastAPI (опционально)
```python
import os
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "frontend_dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return {"detail": "index.html not found"}, 404
```

## 4 Как собрать и положить dist
```bash
cd frontend && npm i && npm run build
# Скопируйте dist/ в AEProject/frontend_dist
```
