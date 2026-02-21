import os
import json
import re
from flask import Flask, render_template, request
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

client = genai.Client(api_key=API_KEY)

app = Flask(__name__)

# ------------------------------
# SAFE JSON PARSER
# ------------------------------
def safe_json_parse(raw_text):
    try:
        cleaned = raw_text.strip()
        cleaned = cleaned.replace("```json", "").replace("```", "")

        # Extract JSON array only
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)

        return json.loads(cleaned)

    except Exception as e:
        print("🔥 JSON PARSE ERROR:", str(e))
        print("RAW OUTPUT WAS:\n", raw_text)
        return None


# ------------------------------
# MAIN ROUTE
# ------------------------------
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

        # Always restore concept
        if concept_text:
            concept = concept_text

        try:

            # ===============================
            # GENERATE CONCEPT
            # ===============================
            if action == "generate":
                if topic:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=f"Explain the concept of {topic} clearly in detail."
                    )
                    concept = response.text
                    result = ""
                    quiz = None
                    score = None

            # ===============================
            # SUMMARIZE
            # ===============================
            elif action == "summarize":
                if concept:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=f"Provide a concise summary of:\n\n{concept}"
                    )
                    result = response.text
                    quiz = None
                    score = None

            # ===============================
            # TRANSLATE
            # ===============================
            elif action == "translate":
                if not language:
                    result = "⚠️ Please enter a language."
                elif concept:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=f"Translate the following into {language}:\n\n{concept}"
                    )
                    result = response.text
                    quiz = None
                    score = None

            # ===============================
            # GENERATE QUIZ
            # ===============================
            elif action == "quiz":
                if concept:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=f"""
                        Generate 5 multiple choice questions from the content below.

                        Return ONLY a valid JSON array like this:

                        [
                          {{
                            "question": "Question text",
                            "options": ["Option A", "Option B", "Option C", "Option D"],
                            "answer_index": 0
                          }}
                        ]

                        Do NOT include explanations.
                        Do NOT include markdown.
                        Only JSON.

                        Content:
                        {concept}
                        """
                    )

                    raw_output = response.text
                    print("RAW QUIZ OUTPUT:\n", raw_output)

                    quiz = safe_json_parse(raw_output)

                    if quiz is None:
                        result = "⚠️ Quiz generation failed. Check terminal."
                        quiz = None
                    else:
                        result = ""
                        score = None

            # ===============================
            # CHECK QUIZ
            # ===============================
            elif action == "check_quiz":
                quiz_data = json.loads(request.form.get("quiz_data"))
                score = 0
                total = len(quiz_data)

                for i, q in enumerate(quiz_data):
                    selected = request.form.get(f"q{i}")
                    if selected is not None and int(selected) == q["answer_index"]:
                        score += 1

                quiz = quiz_data
                result = f"You scored {score} out of {total}"

        except Exception as e:
            result = f"⚠️ Error occurred:\n{str(e)}"
            print("🔥 GENERAL ERROR:", str(e))

    return render_template(
        "index.html",
        concept=concept,
        result=result,
        quiz=quiz,
        score=score
    )


if __name__ == "__main__":
    app.run(debug=True)