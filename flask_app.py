from flask import Flask, redirect, render_template, request, url_for
from dotenv import load_dotenv
import os
import git
import hmac
import hashlib
from db import db_read, db_write
from auth import login_manager, authenticate, register_user
from flask_login import login_user, logout_user, login_required, current_user
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Load .env variables
load_dotenv()
W_SECRET = os.getenv("W_SECRET")

# Init flask app
app = Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = "supersecret"

# Init auth
login_manager.init_app(app)
login_manager.login_view = "login"

# DON'T CHANGE
def is_valid_signature(x_hub_signature, data, private_key):
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)

# DON'T CHANGE
@app.post('/update_server')
def webhook():
    x_hub_signature = request.headers.get('X-Hub-Signature')
    if is_valid_signature(x_hub_signature, request.data, W_SECRET):
        repo = git.Repo('./mysite')
        origin = repo.remotes.origin
        origin.pull()
        return 'Updated PythonAnywhere successfully', 200
    return 'Unathorized', 401

# Auth routes
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        user = authenticate(
            request.form["username"],
            request.form["password"]
        )

        if user:
            login_user(user)
            return redirect(url_for("index"))

        error = "Benutzername oder Passwort ist falsch."

    return render_template(
        "auth.html",
        title="In dein Konto einloggen",
        action=url_for("login"),
        button_label="Einloggen",
        error=error,
        footer_text="Noch kein Konto?",
        footer_link_url=url_for("register"),
        footer_link_label="Registrieren"
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        ok = register_user(username, password)
        if ok:
            return redirect(url_for("login"))

        error = "Benutzername existiert bereits."

    return render_template(
        "auth.html",
        title="Neues Konto erstellen",
        action=url_for("register"),
        button_label="Registrieren",
        error=error,
        footer_text="Du hast bereits ein Konto?",
        footer_link_url=url_for("login"),
        footer_link_label="Einloggen"
    )

# App routes
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # GET
    if request.method == "GET":
        todos = db_read("SELECT id, content, due FROM todos WHERE user_id=%s ORDER BY due", (current_user.id,))
        return render_template("main_page.html", todos=todos)

    # POST
    content = request.form["contents"]
    due = request.form["due_at"]
    db_write("INSERT INTO todos (user_id, content, due) VALUES (%s, %s, %s)", (current_user.id, content, due, ))
    return redirect(url_for("index"))

@app.post("/complete")
@login_required
def complete():
    todo_id = request.form.get("id")
    db_write("DELETE FROM todos WHERE user_id=%s AND id=%s", (current_user.id, todo_id,))
    return redirect(url_for("index"))

@app.route("/dbexplorer", methods=["GET", "POST"])
@login_required
def dbexplorer():
    # Alle Tabellennamen holen
    tables_raw = db_read("SHOW TABLES")
    all_tables = [next(iter(row.values())) for row in tables_raw]  # erste Spalte jedes Dicts

    selected_tables = []
    limit = 50  # Default
    results = {}

    if request.method == "POST":
        # Gewählte Tabellen einsammeln
        selected_tables = request.form.getlist("tables")

        # Limit aus Formular lesen
        limit_str = request.form.get("limit") or ""
        try:
            limit = int(limit_str)
        except ValueError:
            limit = 50

        # Limit ein bisschen absichern
        if limit < 1:
            limit = 1
        elif limit > 1000:
            limit = 1000

        allowed = set(all_tables)

        # Pro gewählter Tabelle Daten abfragen
        for table in selected_tables:
            if table in allowed:  # einfache Absicherung gegen SQL-Injection
                rows = db_read(f"SELECT * FROM `{table}` LIMIT %s", (limit,))
                results[table] = rows

    return render_template(
        "dbexplorer.html",
        all_tables=all_tables,
        selected_tables=selected_tables,
        results=results,
        limit=limit,
    )

# --- add somewhere with your other routes ---
@app.route("/newroom", methods=["GET", "POST"])
@login_required
def newroom():
    # Raumtypen für Auswahl
    room_types = db_read(
        "SELECT raumtyp_id, bezeichnung FROM Raumtyp ORDER BY bezeichnung"
    )

    message = None

    if request.method == "POST":
        zimmernummer = request.form.get("zimmernummer")
        kapazitaet = request.form.get("kapazitaet") or None
        raumtyp_id = request.form.get("raumtyp_id") or None

        # prüfen ob Zimmer existiert
        existing = db_read(
            "SELECT zimmer_id FROM Zimmer WHERE zimmernummer = %s",
            (zimmernummer,),
            single=True
        )

        if existing:
            # Alternative Ablauf: Update
            db_write(
                """
                UPDATE Zimmer
                SET
                    kapazitaet = COALESCE(%s, kapazitaet),
                    raumtyp_id = COALESCE(%s, raumtyp_id)
                WHERE zimmernummer = %s
                """,
                (kapazitaet, raumtyp_id, zimmernummer)
            )
            message = "Zimmer existierte bereits – Daten wurden aktualisiert."
        else:
            # Normalablauf: neues Zimmer
            db_write(
                """
                INSERT INTO Zimmer (zimmernummer, kapazitaet, raumtyp_id, stockwerk)
                VALUES (%s, %s, %s, 0)
                """,
                (zimmernummer, kapazitaet, raumtyp_id)
            )
            message = "Neues Zimmer wurde erfolgreich angelegt."

    # Übersicht aller Zimmer
    rooms = db_read(
        """
        SELECT
            z.zimmernummer,
            z.kapazitaet,
            r.bezeichnung AS raumtyp
        FROM Zimmer z
        LEFT JOIN Raumtyp r ON z.raumtyp_id = r.raumtyp_id
        ORDER BY z.zimmernummer
        """
    )

    return render_template(
        "newroom.html",
        room_types=room_types,
        rooms=rooms,
        message=message
    )


@app.route("/booking", methods=["GET", "POST"])
@login_required
def booking():
    message = None

    # Alle Zimmer anzeigen
    rooms = db_read(
        """
        SELECT
            z.zimmer_id,
            z.zimmernummer,
            z.kapazitaet,
            r.bezeichnung AS raumtyp
        FROM Zimmer z
        JOIN Raumtyp r ON z.raumtyp_id = r.raumtyp_id
        ORDER BY z.zimmernummer
        """
    )

    if request.method == "POST":
        zimmer_id = request.form.get("zimmer_id")
        startdatum = request.form.get("startdatum")
        enddatum = request.form.get("enddatum")

        # prüfen ob Zimmer im Zeitraum belegt ist
        conflict = db_read(
            """
            SELECT buchung_id FROM Buchung
            WHERE zimmer_id = %s
              AND NOT (enddatum < %s OR startdatum > %s)
            """,
            (zimmer_id, startdatum, enddatum),
            single=True
        )

        if conflict:
            message = "❌ Dieses Zimmer ist im gewählten Zeitraum bereits gebucht."
        else:
            db_write(
                """
                INSERT INTO Buchung (startdatum, enddatum, zimmer_id, nutzer_id)
                VALUES (%s, %s, %s, %s)
                """,
                (startdatum, enddatum, zimmer_id, current_user.id)
            )
            message = "✅ Buchung erfolgreich gespeichert."

    # Buchungen des aktuellen Gasts anzeigen
    bookings = db_read(
        """
        SELECT
            b.startdatum,
            b.enddatum,
            z.zimmernummer
        FROM Buchung b
        JOIN Zimmer z ON b.zimmer_id = z.zimmer_id
        WHERE b.nutzer_id = %s
        ORDER BY b.startdatum
        """,
        (current_user.id,)
    )

    return render_template(
        "booking.html",
        rooms=rooms,
        bookings=bookings,
        message=message
    )

from datetime import date

@app.route("/cancelation", methods=["GET", "POST"])
@login_required
def cancelation():
    message = None

    # POST → Buchung stornieren
    if request.method == "POST":
        booking_id = request.form.get("booking_id")

        # Prüfen: gehört die Buchung dem User & liegt in der Zukunft
        booking = db_read(
            """
            SELECT startdatum
            FROM Buchung
            WHERE buchung_id = %s AND nutzer_id = %s
            """,
            (booking_id, current_user.id),
            single=True
        )

        if not booking:
            message = "Zugriff verweigert."
        elif booking["startdatum"] < date.today():
            message = "Vergangene Buchungen können nicht storniert werden."
        else:
            db_write(
                "DELETE FROM Buchung WHERE buchung_id = %s",
                (booking_id,)
            )
            message = "Buchung wurde erfolgreich storniert."

    # GET → Buchungen anzeigen
    bookings = db_read(
        """
        SELECT
            b.buchung_id,
            z.zimmernummer,
            b.startdatum,
            b.enddatum
        FROM Buchung b
        JOIN Zimmer z ON b.zimmer_id = z.zimmer_id
        WHERE b.nutzer_id = %s
        ORDER BY b.startdatum
        """,
        (current_user.id,)
    )

    return render_template(
        "cancelation.html",
        bookings=bookings,
        today=date.today(),
        message=message
    )

@app.route("/registration", methods=["GET", "POST"])
def registration():
    from flask_login import UserMixin, login_user

    # Dummy-User für Flask-Login
    class DummyUser(UserMixin):
        def __init__(self, id, role):
            self.id = id
            self.role = role

    if request.method == "POST":
        role = request.form.get("role")  # "gast" oder "mitarbeiter"
        username = request.form.get("username")  # beliebig
        password = request.form.get("password")  # beliebig

        # IDs passend zu deiner Datenbank (1 = Gast, 2 = Mitarbeiter)
        user_id = 1 if role == "gast" else 2

        # Immer erfolgreich anmelden
        user = DummyUser(id=user_id, role=role)
        login_user(user)

        return redirect(url_for("index"))

    return render_template("registration.html")


from flask_login import logout_user, login_required
from flask import render_template

@app.route("/logout", methods=["GET"])
@login_required
def logout():
    """
    Use Case: Benutzer abmelden
    Kurzbeschreibung: Der Nutzer meldet sich vom System ab
    Beteiligte Akteure: Gast oder Mitarbeiter
    Auslöser: Der Nutzer möchte die Sitzung beenden
    Vorbedingungen: Nutzer ist angemeldet
    Normalablauf: Nutzer klickt auf “Logout”, System beendet die Sitzung
    Alternative Abläufe: -
    Ergebnis: Nutzer ist abgemeldet
    Bemerkungen: -
    """
    logout_user()  # Ends the session
    return render_template("logout.html")  # Show confirmation page



@app.route("/db-visualization", methods=["GET"])
@login_required  # remove if you want it public

def db_visualization():
    # Schema per TODOS.sql: todos.user_id -> users.id
    users = db_read("SELECT id, username FROM users ORDER BY id")
    todos = db_read("SELECT id, user_id, content, due FROM todos ORDER BY user_id, id")

    # Build a Hierarchical Edge Bundling dataset:
    # [{ name: "db.users.user_1", imports: ["db.todos.todo_7", ...] }, ...]
    # We'll do: todo -> user (because todo row contains FK user_id)
    graph_data = []

    # user leaf nodes
    for u in users:
        graph_data.append({
            "name": f"db.users.user_{u['id']}",
            "label": u["username"],
            "type": "user",
            "imports": []
        })

    # todo leaf nodes + FK edges (todo imports its referenced user)
    for t in todos:
        label = (t.get("content") or "").strip() or f"todo #{t['id']}"
        graph_data.append({
            "name": f"db.todos.todo_{t['id']}",
            "label": label,
            "type": "todo",
            "imports": [f"db.users.user_{t['user_id']}"]  # FK edge
        })

    return render_template("db_visualization.html", graph_data=graph_data)


if __name__ == "__main__":
    app.run(debug=True)  # optional for local testing, PythonAnywhere ignores this







