import json
import os
from typing import Optional, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="Nutrition AI Backend")

class RecommendationRequest(BaseModel):
    goal: str
    dietType: str
    allergy: str
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    
class Nutrients(BaseModel):
    protein_g: int = Field(ge=0, le=500)
    carbs_g: int = Field(ge=0, le=800)
    fiber_g: int = Field(ge=0, le=200)


class RecommendationResponse(BaseModel):
    breakfast: str
    lunch: str
    dinner: str
    totalCalories: int = Field(ge=0, le=6000)
    nutrients: Nutrients

class IngredientRecipeRequest(BaseModel):
    ingredient: str
    goal: Optional[str] = None
    dietType: Optional[str] = None
    allergy: Optional[str] = None
    servings: Optional[int] = 1


class RecipeItem(BaseModel):
    name: str
    ingredients: List[str]
    steps: List[str]
    calories: int = Field(ge=0, le=3000)
    nutrients: Nutrients


class IngredientRecipeResponse(BaseModel):
    ingredient: str
    recipes: List[RecipeItem]


@app.get("/")
def root():
    return {
        "ok": True,
        "message": "Nutrition AI Backend is running",
        "endpoints": ["/health", "/recommendations","/recipes-by-ingredient", "/docs"]
    }

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/recommendations", response_model=RecommendationResponse)
def recommendations(req: RecommendationRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    client = OpenAI(api_key=api_key)

    system_msg = (
    "You are a nutrition assistant. Respect dietary preferences and avoid allergens. "
    "Provide practical, balanced meals. Do not provide medical diagnosis. "
    "Ensure nutrient values are realistic and consistent with calories "
    "(protein ≈ 4 kcal/g, carbs ≈ 4 kcal/g, fiber ≈ 2 kcal/g)."
)


    user_msg = f"""
Create a 1-day meal plan.

User:
- goal: {req.goal}
- dietType: {req.dietType}
- allergy: {req.allergy}
- age: {req.age}
- gender: {req.gender}
- height: {req.height}
- weight: {req.weight}

Return JSON EXACTLY in this format (no extra text, no markdown):

{{
"breakfast": "...",
"lunch": "...",
"dinner": "...",
"totalCalories": 0,
"nutrients": {{
    "protein_g": 0,
    "carbs_g": 0,
    "fiber_g": 0
}}
}}
"""

    text = ""
    try:
        r = client.responses.create(
            model="gpt-4.1-mini"
,
            input=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            text={"format": {"type": "json_object"}},
        )

        if hasattr(r, "output_text") and r.output_text:
            text = r.output_text
        else:
            for item in r.output:
                if item.type == "output_text":
                    text += item.text

        data = json.loads(text)
        return RecommendationResponse(**data)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"AI did not return valid JSON. Raw: {text[:300]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # ----------------------------
# NEW endpoint: recipes by ingredient
# ----------------------------
@app.post("/recipes-by-ingredient", response_model=IngredientRecipeResponse)
def recipes_by_ingredient(req: IngredientRecipeRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    client = OpenAI(api_key=api_key)

    system_msg = (
        "You are a helpful nutrition + recipe assistant. "
        "Respect dietary preferences and avoid allergens. "
        "Provide practical recipes using the given ingredient. "
        "Nutrients should be realistic and consistent with calories "
        "(protein ≈ 4 kcal/g, carbs ≈ 4 kcal/g, fiber ≈ 2 kcal/g)."
    )

    # f-string -> escape braces
    user_msg = f"""
Generate 3 recipe ideas that include this ingredient: {req.ingredient}
Constraints:
- goal: {req.goal}
- dietType: {req.dietType}
- allergy: {req.allergy}
- servings: {req.servings}

Return JSON ONLY in this exact format (no extra text, no markdown):

{{
"ingredient": "{req.ingredient}",
"recipes": [
    {{
    "name": "...",
    "ingredients": ["...", "..."],
    "steps": ["...", "..."],
    "calories": 0,
    "nutrients": {{
        "protein_g": 0,
        "carbs_g": 0,
        "fiber_g": 0
    }}
    }}
]
}}
"""
    text = ""
    try:
        r = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            text={"format": {"type": "json_object"}},
        )

        if hasattr(r, "output_text") and r.output_text:
            text = r.output_text
        else:
            for item in r.output:
                if item.type == "output_text":
                    text += item.text

        data = json.loads(text)
        return IngredientRecipeResponse(**data)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"AI did not return valid JSON. Raw: {text[:300]}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

