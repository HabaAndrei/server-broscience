from fastapi import FastAPI
from generators import fitness_guide, food_analyzer
from fastapi.middleware.cors import CORSMiddleware
from providers.schemas import NutritionRequest, AnalyzeImageRequest, SearchFoodRequest
from services import search_food_service

app = FastAPI()
fitness_guide = fitness_guide.FitnessGuide()
food_analyzer = food_analyzer.FoodAnalyzer()
search_food = search_food_service.SearchFood()


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

@app.post("/analyzeImage")
async def analyze_image(data: AnalyzeImageRequest):
    return await food_analyzer.analyze_image(data.image)

@app.post("/searchFood")
async def search_food(data: SearchFoodRequest):
    return search_food.search(data.input)