from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/frontend/templates")

@router.get("/admin/field-mapping/{api_id}", response_class=HTMLResponse)
async def field_mapping(request: Request, api_id: str):
    return templates.TemplateResponse("admin/field_mapping.html", {"request": request, "api_id": api_id}) 