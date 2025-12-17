#from app.schema.demo_dto import Demo as DemoDTO
from app.repository.demo_repo import Demo as DemoRepo

class Demo:
    def __init__(self, repo: DemoRepo):
        self.repo = repo

    def findDemo(self, demo_id: int):
        demo = self.repo.findDemo(demo_id)
        return demo