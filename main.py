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
# import json
# import os
# import base64
# from typing import Optional, List

# from dotenv import load_dotenv
# from fastapi import FastAPI, HTTPException, UploadFile, File
# from openai import OpenAI
# from pydantic import BaseModel, Field

# load_dotenv()

# app = FastAPI(title="Nutrition AI Backend")

# # ----------------------------
# # Models
# # ----------------------------
# class RecommendationRequest(BaseModel):
#     goal: str
#     dietType: str
#     allergy: str
#     age: Optional[int] = None
#     gender: Optional[str] = None
#     height: Optional[int] = None
#     weight: Optional[int] = None


# class Nutrients(BaseModel):
#     protein_g: int = Field(ge=0, le=500)
#     carbs_g: int = Field(ge=0, le=800)
#     fiber_g: int = Field(ge=0, le=200)


# class RecommendationResponse(BaseModel):
#     breakfast: str
#     lunch: str
#     dinner: str
#     totalCalories: int = Field(ge=0, le=6000)
#     nutrients: Nutrients


# class IngredientRecipeRequest(BaseModel):
#     ingredient: str
#     goal: Optional[str] = None
#     dietType: Optional[str] = None
#     allergy: Optional[str] = None
#     servings: Optional[int] = 1


# class RecipeItem(BaseModel):
#     name: str
#     ingredients: List[str]
#     steps: List[str]
#     calories: int = Field(ge=0, le=3000)
#     nutrients: Nutrients


# class IngredientRecipeResponse(BaseModel):
#     ingredient: str
#     recipes: List[RecipeItem]


# # ----------------------------
# # NEW: Objective 2 - Image scan models
# # ----------------------------
# class ScanRecipeItem(BaseModel):
#     name: str
#     ingredients: List[str]
#     steps: List[str]


# class ScanFoodResponse(BaseModel):
#     detectedFood: str
#     estimatedCalories: int = Field(ge=0, le=3000)
#     nutrients: Nutrients
#     healthierAlternative: str
#     recipes: List[ScanRecipeItem]


# # ----------------------------
# # Routes
# # ----------------------------
# @app.get("/")
# def root():
#     return {
#         "ok": True,
#         "message": "Nutrition AI Backend is running",
#         "endpoints": [
#             "/health",
#             "/recommendations",
#             "/recipes-by-ingredient",
#             "/scan-food",
#             "/docs",
#         ],
#     }


# @app.get("/health")
# def health():
#     return {"ok": True}


# @app.post("/recommendations", response_model=RecommendationResponse)
# def recommendations(req: RecommendationRequest):
#     api_key = os.getenv("OPENAI_API_KEY")
#     if not api_key:
#         raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

#     client = OpenAI(api_key=api_key)

#     system_msg = (
#         "You are a nutrition assistant. Respect dietary preferences and avoid allergens. "
#         "Provide practical, balanced meals. Do not provide medical diagnosis. "
#         "Ensure nutrient values are realistic and consistent with calories "
#         "(protein ≈ 4 kcal/g, carbs ≈ 4 kcal/g, fiber ≈ 2 kcal/g)."
#     )

#     # f-string -> JSON braces must be escaped with {{ and }}
#     user_msg = f"""
# Create a 1-day meal plan.

# User:
# - goal: {req.goal}
# - dietType: {req.dietType}
# - allergy: {req.allergy}
# - age: {req.age}
# - gender: {req.gender}
# - height: {req.height}
# - weight: {req.weight}

# Return JSON EXACTLY in this format (no extra text, no markdown):

# {{
#   "breakfast": "...",
#   "lunch": "...",
#   "dinner": "...",
#   "totalCalories": 0,
#   "nutrients": {{
#     "protein_g": 0,
#     "carbs_g": 0,
#     "fiber_g": 0
#   }}
# }}
# """

#     text = ""
#     try:
#         r = client.responses.create(
#             model="gpt-4.1-mini",
#             input=[
#                 {"role": "system", "content": system_msg},
#                 {"role": "user", "content": user_msg},
#             ],
#             text={"format": {"type": "json_object"}},
#         )

#         if getattr(r, "output_text", None):
#             text = r.output_text
#         else:
#             for item in r.output:
#                 if item.type == "output_text":
#                     text += item.text

#         data = json.loads(text)
#         return RecommendationResponse(**data)

#     except json.JSONDecodeError:
#         raise HTTPException(status_code=500, detail=f"AI did not return valid JSON. Raw: {text[:300]}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.post("/recipes-by-ingredient", response_model=IngredientRecipeResponse)
# def recipes_by_ingredient(req: IngredientRecipeRequest):
#     api_key = os.getenv("OPENAI_API_KEY")
#     if not api_key:
#         raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

#     client = OpenAI(api_key=api_key)

#     system_msg = (
#         "You are a helpful nutrition + recipe assistant. "
#         "Respect dietary preferences and avoid allergens. "
#         "Provide practical recipes using the given ingredient. "
#         "Nutrients should be realistic and consistent with calories "
#         "(protein ≈ 4 kcal/g, carbs ≈ 4 kcal/g, fiber ≈ 2 kcal/g)."
#     )

#     user_msg = f"""
# Generate 3 recipe ideas that include this ingredient: {req.ingredient}

# Constraints:
# - goal: {req.goal}
# - dietType: {req.dietType}
# - allergy: {req.allergy}
# - servings: {req.servings}

# Return JSON ONLY in this exact format (no extra text, no markdown):

# {{
#   "ingredient": "{req.ingredient}",
#   "recipes": [
#     {{
#       "name": "...",
#       "ingredients": ["...", "..."],
#       "steps": ["...", "..."],
#       "calories": 0,
#       "nutrients": {{
#         "protein_g": 0,
#         "carbs_g": 0,
#         "fiber_g": 0
#       }}
#     }}
#   ]
# }}
# """

#     text = ""
#     try:
#         r = client.responses.create(
#             model="gpt-4.1-mini",
#             input=[
#                 {"role": "system", "content": system_msg},
#                 {"role": "user", "content": user_msg},
#             ],
#             text={"format": {"type": "json_object"}},
#         )

#         if getattr(r, "output_text", None):
#             text = r.output_text
#         else:
#             for item in r.output:
#                 if item.type == "output_text":
#                     text += item.text

#         data = json.loads(text)
#         return IngredientRecipeResponse(**data)

#     except json.JSONDecodeError:
#         raise HTTPException(status_code=500, detail=f"AI did not return valid JSON. Raw: {text[:300]}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# # ----------------------------
# # Objective 2: Image -> detected food + recipes + nutrition + healthier alternative
# # ----------------------------
# @app.post("/scan-food", response_model=ScanFoodResponse)
# async def scan_food(image: UploadFile = File(...)):
#     api_key = os.getenv("OPENAI_API_KEY")
#     if not api_key:
#         raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

#     # Accept common image types only
#     if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
#         raise HTTPException(status_code=400, detail="Unsupported image type. Use JPG, PNG, or WEBP.")

#     img_bytes = await image.read()
#     if not img_bytes:
#         raise HTTPException(status_code=400, detail="Empty image file")

#     # Convert image bytes to base64 data URL
#     mime = image.content_type or "image/jpeg"
#     b64 = base64.b64encode(img_bytes).decode("utf-8")
#     data_url = f"data:{mime};base64,{b64}"

#     client = OpenAI(api_key=api_key)

#     system_msg = (
#         "You are a food recognition + nutrition assistant. "
#         "Identify the most likely food in the photo. Then provide 3 recipe ideas, "
#         "a realistic nutritional estimate, and one healthier alternative suggestion. "
#         "Return ONLY valid JSON. No markdown."
#     )

#     user_msg = """
# Return JSON ONLY in this exact format:

# {
#   "detectedFood": "...",
#   "estimatedCalories": 0,
#   "nutrients": { "protein_g": 0, "carbs_g": 0, "fiber_g": 0 },
#   "healthierAlternative": "...",
#   "recipes": [
#     { "name": "...", "ingredients": ["...", "..."], "steps": ["...", "..."] }
#   ]
# }
# """

#     text = ""
#     try:
#         r = client.responses.create(
#             model="gpt-4.1-mini",
#             input=[
#                 {"role": "system", "content": [{"type": "input_text", "text": system_msg}]},
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "input_text", "text": user_msg},
#                         {"type": "input_image", "image_url": data_url},
#                     ],
#                 },
#             ],
#             text={"format": {"type": "json_object"}},
#         )

#         if getattr(r, "output_text", None):
#             text = r.output_text
#         else:
#             for item in r.output:
#                 if item.type == "output_text":
#                     text += item.text

#         data = json.loads(text)
#         return ScanFoodResponse(**data)

#     except json.JSONDecodeError:
#         raise HTTPException(status_code=500, detail=f"AI did not return valid JSON. Raw: {text[:300]}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

