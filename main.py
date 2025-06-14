from typing import Union
from fastapi import FastAPI
from config import Settings
from generators import fitness_guide

app = FastAPI()
fitness_guide = fitness_guide.FitnessGuide()


@app.post("/nutrition-plan")
async def generate_nutrition_plan(
    gender: str, workouts: str, height: int|str, weight: int|str, age: int|str, goal: str
):
    result = await fitness_guide.generate_nutrition_plan(
        gender=gender, workouts=workouts, height=height, weight=weight, age=age, goal=goal
    )
    return result

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}