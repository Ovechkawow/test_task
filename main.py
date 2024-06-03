from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional
from datetime import datetime
from fastapi.responses import RedirectResponse

from database import SessionLocal, Roll
import schemas

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")

#Создание нового рулона
@app.post("/rolls/", response_model=schemas.Roll)
def create_roll(roll: schemas.RollCreate, db: Session = Depends(get_db)):
    db_roll = Roll(length=roll.length, weight=roll.weight)
    db.add(db_roll)
    db.commit()
    db.refresh(db_roll)
    return db_roll

#Удаление рулона по айди
@app.delete("/rolls/{roll_id}", response_model=schemas.Roll)
def delete_roll(roll_id: int, db: Session = Depends(get_db)):
    db_roll = db.query(Roll).filter(Roll.id == roll_id).first()
    if db_roll is None:
        raise HTTPException(status_code=404, detail="Roll not found")
    
    db_roll.date_removed = datetime.now()
    db.commit()
    db.refresh(db_roll)
    return db_roll

#Получение списка рулонов по указанным фильтрам
@app.get("/rolls/", response_model=List[schemas.Roll])
def get_rolls(
    id: Optional[int] = None,
    min_weight: Optional[float] = None,
    max_weight: Optional[float] = None,
    min_length: Optional[float] = None,
    max_length: Optional[float] = None,
    date_added: Optional[datetime] = None,
    date_removed: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Roll)
    if id is not None:
        query = query.filter(Roll.id == id)
    if min_weight is not None:
        query = query.filter(Roll.weight >= min_weight)
    if max_weight is not None:
        query = query.filter(Roll.weight <= max_weight)
    if min_length is not None:
        query = query.filter(Roll.length >= min_length)
    if max_length is not None:
        query = query.filter(Roll.length <= max_length)
    if date_added is not None:
        query = query.filter(Roll.date_added == date_added)
    if date_removed is not None:
        query = query.filter(Roll.date_removed == date_removed)

    return query.all()

#Получение всей требуемой статистики по рулонам за указанный период
@app.get("/rolls/statistics/", response_model=schemas.RollStatistics)
def get_roll_statistics(
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db)
):
    added_rolls_count = db.query(Roll).filter(Roll.date_added.between(start_date, end_date)).count()
    removed_rolls_count = db.query(Roll).filter(Roll.date_removed.between(start_date, end_date)).count()
    
    avg_length = db.query(func.avg(Roll.length)).filter(Roll.date_added.between(start_date, end_date)).scalar()
    avg_weight = db.query(func.avg(Roll.weight)).filter(Roll.date_added.between(start_date, end_date)).scalar()
    
    max_length = db.query(func.max(Roll.length)).filter(Roll.date_added.between(start_date, end_date)).scalar()
    min_length = db.query(func.min(Roll.length)).filter(Roll.date_added.between(start_date, end_date)).scalar()
    
    max_weight = db.query(func.max(Roll.weight)).filter(Roll.date_added.between(start_date, end_date)).scalar()
    min_weight = db.query(func.min(Roll.weight)).filter(Roll.date_added.between(start_date, end_date)).scalar()
    
    total_weight = db.query(func.sum(Roll.weight)).filter(Roll.date_added.between(start_date, end_date)).scalar()
    
    durations = db.query(Roll.date_added, Roll.date_removed).filter(Roll.date_added.between(start_date, end_date)).all()
    durations = [((r.date_removed - r.date_added).total_seconds() / 3600.0) if r.date_removed else None for r in durations]
    max_duration = max([d for d in durations if d is not None], default=None)
    min_duration = min([d for d in durations if d is not None], default=None)

    return schemas.RollStatistics(
        added_rolls_count=added_rolls_count,
        removed_rolls_count=removed_rolls_count,
        average_length=avg_length,
        average_weight=avg_weight,
        max_length=max_length,
        min_length=min_length,
        max_weight=max_weight,
        min_weight=min_weight,
        total_weight=total_weight,
        max_duration=max_duration,
        min_duration=min_duration
    )