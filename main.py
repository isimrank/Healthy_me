import json
import os
from typing import Optional

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

class RecommendationResponse(BaseModel):
    breakfast: str
    lunch: str
    dinner: str
    totalCalories: int = Field(ge=0, le=6000)

@app.get("/")
def root():
    return {
        "ok": True,
        "message": "Nutrition AI Backend is running",
        "endpoints": ["/health", "/recommendations", "/docs"]
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
        "Provide practical, balanced meals. Do not provide medical diagnosis."
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
"totalCalories": 0
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
