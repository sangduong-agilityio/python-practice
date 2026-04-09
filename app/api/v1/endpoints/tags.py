from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.tag import TagCreate, TagResponse
from app.services.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["tags"])

# Tạo hàm helper để inject TagService dễ dàng qua cơ chế dependency injection
def get_tag_service(db: DbSession) -> TagService:
    return TagService(db)

@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate, 
    current_user: CurrentUser, 
    service: TagService = Depends(get_tag_service)
) -> TagResponse:
    tag = await service.create(data)
    return tag  


@router.get("", response_model=list[TagResponse])
async def list_tags(
    current_user: CurrentUser, 
    service: TagService = Depends(get_tag_service)
) -> list[TagResponse]:
    tags = await service.list_all()
    return tags  
