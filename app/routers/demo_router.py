from fastapi import APIRouter, Depends
#from app.schema.demo_dto import Demo as DemoDTO
from app.repository.demo_repo import Demo as DemoRep
from app.services.demo_serv import Demo as DemoServ
from app.configs.dependencies import get_service_factory

demoRoutes = APIRouter(prefix="/demos", tags=["demos"])

demo_service_dep = get_service_factory(DemoServ, DemoRep)

@demoRoutes.get("/{demo_id}")
def find_demo(demo_id: int, service: DemoServ = Depends(demo_service_dep)):
    result = service.findDemo(demo_id)
    return result
