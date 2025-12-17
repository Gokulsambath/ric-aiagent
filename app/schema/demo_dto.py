from pydantic import BaseModel
from datetime import  date, time

class Demo(BaseModel):
    title : str
    demo_date : date
    demo_time : time
    notes : str
    participants : list[str]
    presenter : str
    status : str

    customer_id : int