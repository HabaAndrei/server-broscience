from pydantic import BaseModel, Field
from typing import List, Literal


class NutritionRequest(BaseModel):
    gender: str
    workouts: str | int | float
    height: int | str
    weight: int | str
    age: int | str
    goal: str


class AnalyzeImageRequest(BaseModel):
    image: str


class Ingredient(BaseModel):
    name: str = Field(description="Always start with an uppercase letter.")
    quantity: int = Field(description="The quantity of the ingredient in grams.")
    preparation: Literal["raw", "boiled", "fried", "baked", "grilled", "steamed", "roasted"] = Field(
        description="The cooking method used for the ingredient. Use one of: raw, boiled, fried, baked, grilled, steamed, roasted."
    )


class FoodGeneralDetails(BaseModel):
    name: str
    total_quantity: int = Field(description="Total quantity of the food in grams.")
    ingredients: List[Ingredient]
    is_food: bool
    health_score: int = Field(description="A health score for the food (1-10)")


class Nutrients(BaseModel):
    calories: int
    protein: int
    carbs: int
    fats: int