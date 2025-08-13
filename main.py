from fastapi import FastAPI, Query
from generators import fitness_guide, food_analyzer
from fastapi.middleware.cors import CORSMiddleware
from providers.schemas import NutritionRequest, AnalyzeImageRequest
from providers.fatsecret_client import FatSecretAPI
from services import search_food_service, search_recipe_service
import json

app = FastAPI()
fitness_guide = fitness_guide.FitnessGuide()
food_analyzer = food_analyzer.FoodAnalyzer()
search_food_instance = search_food_service.SearchFood()
search_recipe_instance = search_recipe_service.SearchRecipe()
fat_secret_client = FatSecretAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specific: ["http://localhost:8081"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

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

@app.post("/analyze-image")
async def analyze_image(data: AnalyzeImageRequest):
    return await food_analyzer.analyze_image(data.image)

@app.get("/search-food")
async def search_food(input: str):
    return await search_food_instance.search(input)

@app.get("/search-recipe")
async def search_recipe(input: str, query: str = Query(...)):
    query_dict = json.loads(query)
    return await search_recipe_instance.search(input, query_dict)