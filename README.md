# Frontend + Icons (SVGR) + Backend wiring

- В `src/icons/` добавляйте свои SVG (fill/stroke не задавать, используйте currentColor).
- Поисковая строка использует SVG-иконки (лупа, очистка) и автокомплит с бэка `/api/search`.
- Dev-прокси Vite отправляет `/api/*` на http://localhost:8000.

## Dev без Docker
backend:
  uvicorn AEProject.main:app --reload

frontend:
  cd frontend && npm i && npm run dev
  # http://localhost:5173

## Docker
  docker compose up --build

## Prod
  cd frontend && npm i && npm run build
  # раздавайте dist/ через nginx или FastAPI (см. предыдущие инструкции)
