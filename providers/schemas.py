from pydantic import BaseModel, Field
from typing import List


class NutritionRequest(BaseModel):
    gender: str
    workouts: str
    height: int | str
    weight: int | str
    age: int | str
    goal: str


class AnalyzeImageRequest(BaseModel):
    image: str


class Ingredient(BaseModel):
    name: str = Field(description="Always start with an uppercase letter.")


class IngredientNutrients(BaseModel):
    name: str
    calories: int
    protein: int
    carbs: int
    fats: int
    health_score: int
    grams_quantity: int


class MealIngredients(BaseModel):
    name: str
    ingredients: List[Ingredient]
    grams_quantity: int
    health_score: int
    is_food: bool


class IngredientDetails(BaseModel):
    ingredients: List[IngredientNutrients]