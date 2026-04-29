from flask import Flask, request, render_template, redirect, url_for, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import io
import PyPDF2
import docx
import time
from google import genai
from utils.bert_processor import extract_key_info
from dotenv import load_dotenv

load_dotenv(dotenv_path="models/.env")

AI_LOCK_KEY = os.getenv("AI_LOCK_KEY")
MODEL_NAME = "models/gemini-2.5-flash"
MAX_TEXT_LENGTH = 12000

LANGUAGE_MAP = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
    "ta": "Tamil",
    "kn": "Kannada",
    "ml": "Malayalam"
}

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

client = genai.Client(api_key=AI_LOCK_KEY)

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    hashed = generate_password_hash(password)
    try:
        c.execute("INSERT INTO users VALUES (NULL, ?, ?)", (username, hashed))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row and check_password_hash(row[0], password)


def read_pdf(file):
    reader = PyPDF2.PdfReader(file)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def read_docx(file):
    document = docx.Document(file)
    return "\n".join(p.text for p in document.paragraphs)


def read_txt(file):
    return file.read().decode("utf-8")


def extract_text(uploaded_file):
    name = uploaded_file.filename.lower()
    if name.endswith(".pdf"):
        return read_pdf(uploaded_file)
    elif name.endswith(".docx"):
        return read_docx(uploaded_file)
    elif name.endswith(".txt"):
        return read_txt(uploaded_file)
    else:
        raise ValueError("Unsupported file format")


def build_analysis_prompt(contract_text, language):
    return f"""
Respond ONLY in {language}.

Explain the contract in simple {language}.

1. Contract overview
2. Risky clauses
3. Responsibilities
4. Payment, termination & liability

CONTRACT:
{contract_text}
"""


def build_chat_prompt(contract_text, question, language):
    return f"""
Answer ONLY in {language}.

CONTRACT:
{contract_text}

QUESTION:
{question}
"""


def safe_generate(prompt):
    for _ in range(3):
        try:
            return client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            ).text
        except Exception as e:
            if "429" in str(e):
                time.sleep(20)
            else:
                raise e
    return "AI busy. Try later."


def analyze_contract(contract_text, language):
    trimmed_text = contract_text[:MAX_TEXT_LENGTH]
    bert_result = extract_key_info(trimmed_text)
    combined_text = f"{bert_result}\n\n{trimmed_text}"
    prompt = build_analysis_prompt(combined_text, language)
    return safe_generate(prompt)


def chat_with_ai(contract_text, question, language):
    trimmed_text = contract_text[:MAX_TEXT_LENGTH]
    prompt = build_chat_prompt(trimmed_text, question, language)
    return safe_generate(prompt)


@app.route("/")
def home():
    return redirect(url_for("index")) if "username" in session else redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""
    if request.method == "POST":
        if add_user(request.form["username"], request.form["password"]):
            return redirect(url_for("login"))
        msg = "Username already exists"
    return render_template("register.html", message=msg)


@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        if verify_user(request.form["username"], request.form["password"]):
            session["username"] = request.form["username"]
            return redirect(url_for("index"))
        msg = "Invalid credentials"
    return render_template("login.html", message=msg)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/index", methods=["GET", "POST"])
def index():
    if "username" not in session:
        return redirect(url_for("login"))

    analysis = ""
    contract_text = ""
    selected_language = "en"

    if request.method == "POST":
        file = request.files.get("file")
        selected_language = request.form.get("language", "en")

        if file:
            try:
                contract_text = extract_text(file)
                analysis = analyze_contract(contract_text, LANGUAGE_MAP[selected_language])
            except Exception as e:
                analysis = str(e)
        else:
            analysis = "No file uploaded"

    return render_template(
        "index.html",
        analysis=analysis,
        languages=LANGUAGE_MAP,
        selected_language=selected_language,
        contract_text=contract_text
    )


@app.route("/download", methods=["POST"])
def download():
    content = request.form.get("analysis_content", "")
    return send_file(
        io.BytesIO(content.encode()),
        download_name="contract_analysis.txt",
        as_attachment=True
    )


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    lang = LANGUAGE_MAP.get(data.get("language", "en"), "English")

    answer = chat_with_ai(
        data.get("contract_text", ""),
        data.get("question", ""),
        lang
    )

    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(debug=True)