from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RollCreate(BaseModel):
    length: float
    weight: float

class Roll(BaseModel):
    id: int
    length: float
    weight: float
    date_added: datetime
    date_removed: Optional[datetime]

    class Config:
        orm_mode = True

class RollStatistics(BaseModel):
    added_rolls_count: int
    removed_rolls_count: int
    average_length: float
    average_weight: float
    max_length: float
    min_length: float
    max_weight: float
    min_weight: float
    total_weight: float
    max_duration: float
    min_duration: float