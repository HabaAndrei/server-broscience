from typing import Union
from fastapi import FastAPI
from generators import fitness_guide
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Union


app = FastAPI()
fitness_guide = fitness_guide.FitnessGuide()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specific: ["http://localhost:8081"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import Union

class NutritionRequest(BaseModel):
    gender: str
    workouts: str
    height: Union[int, str]
    weight: Union[int, str]
    age: Union[int, str]
    goal: str


@app.post("/nutrition-plan")
async def generate_nutrition_plan(data: NutritionRequest):
    result = await fitness_guide.generate_nutrition_plan(
        gender=data.gender,
        workouts=data.workouts,
        height=data.height,
        weight=data.weight,
        age=data.age,
        goal=data.goal
    )
    return result

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}