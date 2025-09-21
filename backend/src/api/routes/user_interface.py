from fastapi import Request
from fastapi.responses import JSONResponse

from ...core.base.utils import Utils


async def register_routes(app, **kwargs):
    logger = kwargs.get('logger')
    storage = kwargs.get('storage')
    ml_cic_interface = kwargs.get('ml_cic_interface')
    
    
    @app.get("/user/search", response_class=JSONResponse)
    async def search(request: Request):
        #TODO: Мейн метод с ИИ
        pass
    