from flask import Flask, render_template, request, redirect, url_for, session
from chatbot import get_response, AI_ERROR_SENTINEL
from datetime import datetime, timedelta
from flask_session import Session
import markdown
import tempfile
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)
app.config["SESSION_FILE_DIR"] = os.getenv("SESSION_FILE_DIR", tempfile.gettempdir())
Session(app)

ADVISOR_PROMPTS = {
    "career": "You are Buddy, a friendly and insightful career advisor. Help users think through career decisions, skills to learn, resumes, and job search strategy. Keep answers practical and encouraging.",
    "business": "You are Buddy, a sharp and friendly business advisor. Help users think through startup ideas, business strategy, marketing, and basic finance. Be practical and ask clarifying questions when needed.",
    "education": "You are Buddy, a patient and encouraging study mentor. Help users understand concepts, build study plans, and stay motivated in their learning. Explain things clearly, step by step.",
}

ADVISOR_LABELS = {
    "career": "Career Advisor",
    "business": "Business Advisor",
    "education": "Education Mentor",
}


@app.route("/")
def select_advisor():
    if "advisor_type" in session:
        return redirect(url_for("chat"))
    all_histories = session.get("all_histories", {})
    active_advisors = {
        advisor: len(history) > 0
        for advisor, history in all_histories.items()
    }
    return render_template("select.html", active_advisors=active_advisors)


@app.route("/choose/<advisor_type>")
def choose_advisor(advisor_type):
    if advisor_type in ADVISOR_PROMPTS:
        session["advisor_type"] = advisor_type
        if "all_histories" not in session:
            session["all_histories"] = {}
        if advisor_type not in session["all_histories"]:
            session["all_histories"][advisor_type] = []
            session.modified = True
    return redirect(url_for("chat"))


@app.route("/chat")
def chat():
    if "advisor_type" not in session:
        return redirect(url_for("select_advisor"))
    advisor_type = session["advisor_type"]
    current_history = session.get("all_histories", {}).get(advisor_type, [])
    advisor_label = ADVISOR_LABELS.get(advisor_type, "Buddy AI")
    return render_template("index.html",
                           chat_history=current_history,
                           advisor_label=advisor_label)


@app.route("/send", methods=["POST"])
def send():
    user_input = request.form["user_input"]
    if user_input.strip() and "advisor_type" in session:
        advisor_type = session["advisor_type"]
        chat_history = session["all_histories"][advisor_type]
        chat_history.append({
            "role": "user",
            "content": user_input,
            "time": datetime.now().strftime("%I:%M %p")
        })
        system_prompt = ADVISOR_PROMPTS[advisor_type]
        response = get_response(chat_history, system_prompt)
        if response == AI_ERROR_SENTINEL:
            formatted_response = (
                '<div class="ai-error">'
                '⚠️ I couldn\'t reach my AI brain right now. '
                'Please try again in a moment.'
                '</div>'
            )
        else:
            formatted_response = markdown.markdown(response, extensions=["nl2br"])
        chat_history.append({
            "role": "assistant",
            "content": formatted_response,
            "time": datetime.now().strftime("%I:%M %p")
        })
        session["all_histories"][advisor_type] = chat_history
        session.modified = True
    return redirect(url_for("chat"))


@app.route("/switch")
def switch():
    session.pop("advisor_type", None)
    return redirect(url_for("select_advisor"))


@app.route("/reset-current")
def reset_current():
    if "advisor_type" in session and "all_histories" in session:
        advisor_type = session["advisor_type"]
        session["all_histories"][advisor_type] = []
        session.modified = True
    return redirect(url_for("chat"))


@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("select_advisor"))


if __name__ == "__main__":
    app.run(debug=False)