import os
import json
from flask import Flask, render_template, request
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

client = genai.Client(api_key=API_KEY)

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    concept = ""
    result = ""
    quiz = None
    score = None

    if request.method == "POST":

        topic = request.form.get("topic", "").strip()
        action = request.form.get("action", "")
        language = request.form.get("language", "").strip()
        concept_text = request.form.get("concept_text", "").strip()

        try:
            # 1️⃣ Generate Concept
            if action == "generate" and topic:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"Explain the concept of {topic} clearly in detail."
                )
                concept = response.text

            # 2️⃣ Summarize
            elif action == "summarize" and concept_text:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"Provide a concise summary of:\n\n{concept_text}"
                )
                result = response.text
                concept = concept_text

            # 3️⃣ Translate
            elif action == "translate" and concept_text and language:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"Translate the following into {language}:\n\n{concept_text}"
                )
                result = response.text
                concept = concept_text

            # 4️⃣ Generate Quiz (INDEX BASED)
            elif action == "quiz" and concept_text:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"""
                    Based on this content, generate 5 MCQs in STRICT JSON format:

                    [
                      {{
                        "question": "Question text",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "answer_index": 0
                      }}
                    ]

                    IMPORTANT:
                    - answer_index must be 0, 1, 2, or 3
                    - Do NOT return answer text
                    - Return only valid JSON
                    - No explanation outside JSON

                    Content:
                    {concept_text}
                    """
                )

                raw = response.text.strip()
                raw = raw.replace("```json", "").replace("```", "")

                quiz = json.loads(raw)
                concept = concept_text

            # 5️⃣ Check Quiz (INDEX COMPARISON)
            elif action == "check_quiz":
                quiz_data = json.loads(request.form.get("quiz_data"))
                score = 0
                total = len(quiz_data)

                for i, q in enumerate(quiz_data):
                    selected = request.form.get(f"q{i}")

                    if selected is not None and int(selected) == q["answer_index"]:
                        score += 1

                concept = concept_text
                quiz = quiz_data
                result = f"You scored {score} out of {total}"

        except Exception as e:
            result = f"Error: {str(e)}"

    return render_template(
        "index.html",
        concept=concept,
        result=result,
        quiz=quiz,
        score=score
    )

if __name__ == "__main__":
    app.run(debug=True)