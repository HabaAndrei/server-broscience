from providers.openai_client import Openai
from pydantic import BaseModel

openai_client = Openai()

class FitnessGuide:

    async def generate_nutrition_plan(self, gender='',workouts='',height='',weight='',age='',goal=''):
        system_prompt = ('''
            You are a nutritionist and fitness expert.
            Based on the user's profile and goals, generate a personalized daily nutrition plan.
            The plan should include the total number of calories, grams of protein, carbs, fats, and a health score
            rating from 1 to 10 indicating how balanced and healthy the plan is.
        ''')

        user_prompt = (f'''
            User details:
                - Gender: {gender}
                - Workouts per week: {workouts}
                - Height (cm): {height}
                - Weight (kg): {weight}
                - Age: {age}
                - Goal: {goal}
            Please generate a daily nutrition plan following the format: calories, protein, carbs, fats, health_score.
        ''')

        class Plan(BaseModel):
            calories: int
            protein: int
            carbs: int
            fats: int
            health_score: int
        result = await openai_client.retry_generate_schema(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_schema=Plan
        )
        return result


