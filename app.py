from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-moi-en-une-longue-phrase-aleatoire-1234"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

CODES_ACCES = {"Arthur": "1234", "Pacome": "1234", "Ludo": "1234"}

connectes = {}        # pseudo -> id de session
cles_publiques = {}   # pseudo -> cle publique (le serveur ne voit QUE les cles publiques)

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@socketio.on("login")
def login(data):
    pseudo = data.get("pseudo", "")
    code = data.get("code", "")
    cle = data.get("cle", "")
    if CODES_ACCES.get(pseudo) != code:
        emit("login_refuse")
        return
    connectes[pseudo] = request.sid
    if cle:
        cles_publiques[pseudo] = cle

    emit("login_ok", {"pseudo": pseudo})

    # donner au nouveau la liste des cles publiques des autres
    emit("cles", {p: c for p, c in cles_publiques.items() if p != pseudo})
    # annoncer sa cle a tout le monde + qui est en ligne
    for p, sid in connectes.items():
        socketio.emit("en_ligne", list(connectes.keys()), to=sid)
        if p != pseudo and cle:
            socketio.emit("nouvelle_cle", {"pseudo": pseudo, "cle": cle}, to=sid)

@socketio.on("demande_cle")
def demande_cle(data):
    p = data.get("pseudo", "")
    if p in cles_publiques:
        emit("nouvelle_cle", {"pseudo": p, "cle": cles_publiques[p]})

@socketio.on("message")
def message(data):
    dest = data.get("dest", "")

    msg = {
        "de": data["de"],
        "texte": data["texte"]
    }

    if dest in connectes:
        socketio.emit("message", msg, to=connectes[dest])
    else:
        if dest not in messages_hors_ligne:
            messages_hors_ligne[dest] = []

        messages_hors_ligne[dest].append(msg)

@socketio.on("disconnect")
def deconnexion():
    pseudo = None
    for p, sid in connectes.items():
        if sid == request.sid:
            pseudo = p
    if pseudo:
        del connectes[pseudo]
        for p, sid in connectes.items():
            socketio.emit("en_ligne", list(connectes.keys()), to=sid)

print("[*] Serveur lance sur https://127.0.0.1:5555")
socketio.run(app, host="0.0.0.0", port=5555,
             ssl_context=("certificat.crt", "cle.key"),
             allow_unsafe_werkzeug=True, debug=False)
