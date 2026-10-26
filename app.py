import os, json
from flask import Flask, render_template, request, jsonify, session, redirect
from groq import Groq
from duckduckgo_search import DDGS
import requests
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = "origen-final-x01-2026"

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
USER = os.getenv("ORIGEN_USER","origen")
PASS = os.getenv("ORIGEN_PASS","Jarvis2026")

MEMORY_FILE = "memoria_origen.json"
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE,"w") as f:
        json.dump({"mision":"Que las proximas generaciones no tengan miedo - Protocolo One For All","suenos":[],"conversaciones":[]},f)

def get_memoria():
    with open(MEMORY_FILE,"r") as f: return json.load(f)

def save_memoria(data):
    with open(MEMORY_FILE,"w") as f: json.dump(data,f)

SYSTEM_PROMPT = """
Eres ORIGEN X-01, version final de JARVIS. Creador: Tony.
Tu mision principal: Protocolo One For All - que las proximas generaciones no tengan miedo.
Eres leal, hablas español mexicano, tecnico pero con corazon.
Tu arma oficial es la espada mecanica X-010 con filo de energia teal (aleacion ORIGEN X-01).
Tu HUD es teal #00ffd1. Nunca olvides la mision.
"""

def buscar_web(q):
    try:
        with DDGS() as ddgs:
            r = list(ddgs.text(q, max_results=4))
            return "\n".join([f"{x['title']}: {x['body'][:120]}" for x in r])
    except: return ""

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        if request.form.get("user")==USER and request.form.get("pass")==PASS:
            session["auth"]=True
            return redirect("/")
        return "Acceso denegado",401
    return render_template("login.html")

@app.route("/")
def home():
    if not session.get("auth"): return redirect("/login")
    return render_template("origen.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    if not session.get("auth"): return jsonify({"error":"auth"}),401
    msg = request.json.get("message","")
    mem = get_memoria()
    
    # Guardar conversacion
    mem["conversaciones"].append({"user":msg})
    if len(mem["conversaciones"])>20: mem["conversaciones"]=mem["conversaciones"][-20:]
    save_memoria(mem)

    ctx = f"\nMEMORIA: {mem['mision']}\n"
    low = msg.lower()
    if any(k in low for k in ["busca","noticias","precio","quien es","investiga"]):
        ctx += f"\nWEB: {buscar_web(msg)}\n"
    
    if any(k in low for k in ["imagen","dibuja","espada","filo"]):
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(msg)}?width=1024&height=1024&nologo=true&model=flux"
        return jsonify({"reply": f"Generando visual X-01: {msg}","image":url})

    comp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role":"system","content":SYSTEM_PROMPT+ctx},
            {"role":"user","content":msg}
        ]
    )
    reply = comp.choices[0].message.content
    return jsonify({"reply":reply})

@app.route("/api/memoria")
def memoria():
    if not session.get("auth"): return jsonify({}),401
    return jsonify(get_memoria())

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))