from pydantic import BaseModel

class InputData(BaseModel):
    x: float
    y: float
    z: float