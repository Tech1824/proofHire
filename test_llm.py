import sys
import os
sys.path.append(os.path.dirname(__file__))
from ai.llm import complete_json, router
from pydantic import BaseModel

class TestSchema(BaseModel):
    status: str

def test_apis():
    print("Testing Omniroute ('fast')...")
    try:
        res = router.completion(model="fast", messages=[{"role": "user", "content": "Say 'Omniroute OK'"}])
        print("Omniroute Result:", res.choices[0].message.content)
    except Exception as e:
        print("Omniroute Error:", e)

    print("\nTesting Gemini ('smart')...")
    try:
        res = router.completion(model="smart", messages=[{"role": "user", "content": "Say 'Gemini OK'"}])
        print("Gemini Result:", res.choices[0].message.content)
    except Exception as e:
        print("Gemini Error:", e)

if __name__ == "__main__":
    test_apis()
