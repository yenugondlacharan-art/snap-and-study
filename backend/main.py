from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from PIL import Image
import pytesseract
import os
import json

from dotenv import load_dotenv
from google import genai


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found in .env file"
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# TESSERACT OCR CONFIGURATION
# ============================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Snap & Study"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HOME ROUTE
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Welcome to Snap & Study!"
    }


# ============================================================
# UPLOAD IMAGE
# ============================================================

@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...)
):

    try:

        # ----------------------------------------------------
        # 1. OPEN IMAGE
        # ----------------------------------------------------

        image = Image.open(file.file)


        # ----------------------------------------------------
        # 2. OCR - EXTRACT TEXT
        # ----------------------------------------------------

        extracted_text = pytesseract.image_to_string(
            image
        )


        # ----------------------------------------------------
        # 3. CHECK OCR RESULT
        # ----------------------------------------------------

        if not extracted_text.strip():

            return {
                "filename": file.filename,

                "extracted_text": "",

                "ai_response": {
                    "topic": "Topic not detected",

                    "what_is_it":
                        "The text could not be detected from the image. Please upload a clearer study image.",

                    "how_does_it_work": [],

                    "simple_example": "",

                    "real_world_examples": [],

                    "important_terms": [],

                    "quick_revision": [],

                    "quiz_questions": []
                }
            }


        # ----------------------------------------------------
        # 4. AI TEACHER PROMPT
        # ----------------------------------------------------

        prompt = f"""
You are an AI teacher inside a study application
called Snap & Study.

The student uploads an image containing study material.

Your job is to identify the MAIN TOPIC from the
study material and teach that topic to a beginner.

============================================================
IMPORTANT RULES
============================================================

1. Identify the main topic first.

2. Do NOT simply copy or summarize the OCR text.

3. Explain what the main topic actually means.

4. Assume the student is learning this topic
   for the first time.

5. Use very simple English.

6. Explain the topic step by step.

7. Explain difficult technical words in simple language.

8. Give one simple example.

9. Give 3 to 5 relevant real-world examples.

10. Give important terms with simple meanings.

11. Give quick revision points.

12. Create exactly 5 multiple-choice quiz questions.

13. Each quiz question must have exactly 4 options.

14. Each question must have ONE correct answer.

15. The "answer" must exactly match one of the
    four options.

16. Do not create ambiguous questions.

17. Do not provide an explanation for the answer.

18. Keep the explanation focused on the main topic.

19. Do not add unrelated information.

20. If the image contains only keywords,
    use those keywords to identify the main topic
    and teach the topic using accurate general knowledge.

21. Do not invent information about the source,
    institution, author, or image.

22. Make the explanation useful for a college student
    preparing for exams.

============================================================
VERY IMPORTANT JSON RULE
============================================================

Return ONLY valid JSON.

DO NOT return:

- Markdown
- ```json
- ```
- Text before JSON
- Text after JSON
- Explanations outside JSON

============================================================
JSON STRUCTURE
============================================================

{{
    "topic": "Main topic name",

    "what_is_it": "Simple beginner-friendly explanation",

    "how_does_it_work": [
        "Step 1",
        "Step 2",
        "Step 3",
        "Step 4"
    ],

    "simple_example": "One simple example",

    "real_world_examples": [
        "Real-world example 1",
        "Real-world example 2",
        "Real-world example 3",
        "Real-world example 4"
    ],

    "important_terms": [
        {{
            "term": "Term 1",
            "meaning": "Simple meaning"
        }},
        {{
            "term": "Term 2",
            "meaning": "Simple meaning"
        }},
        {{
            "term": "Term 3",
            "meaning": "Simple meaning"
        }}
    ],

    "quick_revision": [
        "Revision point 1",
        "Revision point 2",
        "Revision point 3",
        "Revision point 4"
    ],

    "quiz_questions": [
        {{
            "question": "Question 1",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "answer": "Option B"
        }},
        {{
            "question": "Question 2",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "answer": "Option A"
        }},
        {{
            "question": "Question 3",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "answer": "Option C"
        }},
        {{
            "question": "Question 4",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "answer": "Option D"
        }},
        {{
            "question": "Question 5",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "answer": "Option B"
        }}
    ]
}}

============================================================
STUDY MATERIAL EXTRACTED FROM IMAGE
============================================================

{extracted_text}
"""


        # ----------------------------------------------------
        # 5. SEND REQUEST TO GEMINI
        # ----------------------------------------------------

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )


        # ----------------------------------------------------
        # 6. GET GEMINI RESPONSE
        # ----------------------------------------------------

        ai_text = response.text.strip()


        # ----------------------------------------------------
        # 7. REMOVE MARKDOWN CODE FENCES
        # ----------------------------------------------------

        if ai_text.startswith("```json"):

            ai_text = ai_text[
                len("```json"):
            ].strip()


        elif ai_text.startswith("```"):

            ai_text = ai_text[
                len("```"):
            ].strip()


        if ai_text.endswith("```"):

            ai_text = ai_text[
                :-3
            ].strip()


        # ----------------------------------------------------
        # 8. CONVERT JSON TEXT INTO PYTHON DICTIONARY
        # ----------------------------------------------------

        try:

            ai_result = json.loads(
                ai_text
            )

        except json.JSONDecodeError:

            print(
                "Gemini returned invalid JSON:"
            )

            print(ai_text)


            return {
                "filename": file.filename,

                "extracted_text": extracted_text,

                "ai_response": {
                    "topic": "AI response error",

                    "what_is_it":
                        "Gemini returned an unexpected response format.",

                    "how_does_it_work": [],

                    "simple_example": "",

                    "real_world_examples": [],

                    "important_terms": [],

                    "quick_revision": [],

                    "quiz_questions": []
                },

                "raw_ai_response": ai_text
            }


        # ----------------------------------------------------
        # 9. BASIC VALIDATION
        # ----------------------------------------------------

        if "topic" not in ai_result:
            ai_result["topic"] = "Topic not found"


        if "what_is_it" not in ai_result:
            ai_result["what_is_it"] = ""


        if "how_does_it_work" not in ai_result:
            ai_result["how_does_it_work"] = []


        if "simple_example" not in ai_result:
            ai_result["simple_example"] = ""


        if "real_world_examples" not in ai_result:
            ai_result["real_world_examples"] = []


        if "important_terms" not in ai_result:
            ai_result["important_terms"] = []


        if "quick_revision" not in ai_result:
            ai_result["quick_revision"] = []


        if "quiz_questions" not in ai_result:
            ai_result["quiz_questions"] = []


        # ----------------------------------------------------
        # 10. RETURN FINAL RESPONSE
        # ----------------------------------------------------

        return {
            "filename": file.filename,

            "extracted_text": extracted_text,

            "ai_response": ai_result
        }


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        print(
            "ERROR:",
            str(e)
        )

        return {
            "error": str(e)
        }
