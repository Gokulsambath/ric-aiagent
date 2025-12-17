from app.schema.demo_dto import Demo as DemoDTO
from app.models.demo_model import Demo as DemoModel
from app.repository.base_repo import BaseRepository

class Demo(BaseRepository[DemoModel]):
    def __init__(self):
        super().__init__(DemoModel)

    def findDemo(self, demo_id: int):
        db = self._get_db()
        demo : DemoDTO = db.get(DemoModel, demo_id)
        db.close()

        return demo