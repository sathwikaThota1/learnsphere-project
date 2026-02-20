from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    response = None

    if request.method == "POST":
        topic = request.form["topic"]
        response = f"You entered: {topic}"

    return render_template("index.html", response=response)

if __name__== "__main__":
    app.run(debug=True)