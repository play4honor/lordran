from flask import Flask, request, g, jsonify
import uuid

import sqlite3

app = Flask(__name__)

@app.route("/create_form", methods=['POST'])
def create_form():

    input_json = request.get_json()

    e_uuid = uuid.uuid4().hex

    db = get_db()
    cur = db.cursor()

    cur.execute(
        "INSERT INTO events VALUES (?, ?, ?, ?, ?)",
        (e_uuid, input_json["name"], input_json["event_length"], input_json["time_of_day"][0], input_json["time_of_day"][1])
    )

    date_list = [(e_uuid, dt) for dt in input_json["dates"]]
    cur.executemany("INSERT INTO event_dates VALUES (?, ?)", date_list)

    db.commit()

    return jsonify(success=True)

@app.route("/set_tz", methods=['POST'])
def set_tz():

    req = request.get_json()

    db = get_db()
    cur = db.cursor()

    cur.execute(
        "INSERT INTO time_zones VALUES (?, ?)", (req["user_id"], req["utc_offset"])
    )
    db.commit()

    return jsonify(success=True)

@app.route("/get_tz", methods=['POST'])
def get_tz():

    req = request.get_json()

    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT * FROM time_zones WHERE uid = :uid", {"uid": req["user_id"]}
    )
    res = cur.fetchone()

    if res is None:
        return jsonify(tz = -100)

    else:
        return jsonify(tz = res[1])

@app.route("/check_closing")
def check_closing():
    pass

def get_db():

    # If there's not already a database connection.
    if "db" not in g:
        g.db = sqlite3.connect("./db/quelaag.db")

        cur = g.db.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS events (uuid text, name text, event_length real, time_range_start text, time_range_end text);"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS event_dates (uuid text, date text);"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS time_zones (uid integer, tz integer);"
        )

        g.db.commit()
        cur.close()

    return g.db

app.run()