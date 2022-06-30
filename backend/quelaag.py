from flask import Flask, request, g, jsonify
from form_helpers import FormReader, FormWriter, build_availability

import sqlite3
import datetime

app = Flask(__name__)
form_writer = FormWriter()


@app.route("/create_form", methods=["POST"])
def create_form():

    input_json = request.get_json()

    expiration_time = int(
        (
            datetime.datetime.utcnow()
            + datetime.timedelta(seconds=3600 * input_json["expiration_time"])
        ).timestamp()
    )

    form_id, form_url = form_writer.create_form(input_json)

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            input_json["guild_id"],
            input_json["channel_id"],
            form_id,
            input_json["name"],
            input_json["event_length"],
            input_json["time_of_day"][0],
            input_json["time_of_day"][1],
            expiration_time,
            0,  # Not scheduled yet
        ),
    )

    date_list = [(form_id, dt) for dt in input_json["dates"]]
    cur.executemany("INSERT INTO event_dates VALUES (?, ?)", date_list)

    db.commit()

    return jsonify(success=True, form_url=form_url)


@app.route("/set_tz", methods=["POST"])
def set_tz():

    req = request.get_json()

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO time_zones VALUES (?, ?)", (req["user_id"], req["utc_offset"])
    )
    db.commit()

    return jsonify(success=True)


@app.route("/get_tz", methods=["POST"])
def get_tz():

    req = request.get_json()

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT * FROM time_zones WHERE uid = :uid", {"uid": req["user_id"]}
    )
    res = cur.fetchone()

    if res is None:
        return jsonify(tz=-100)

    else:
        return jsonify(tz=res[1])


@app.route("/check_closing", methods=["GET"])
def check_closing():

    right_now = datetime.datetime.utcnow().timestamp()

    db = get_db()
    cur = db.cursor()
    cur.execute(
        """
        SELECT guild_id, channel_id, form_id, name, time_range_start, time_range_end, event_length
        FROM events 
        WHERE expiration_time <= :now 
        AND scheduled = 0;
        """, 
        {"now": right_now}
    )

    new_events = cur.fetchall()
    
    events = []
    for guild_id, channel_id, id, name, event_start, event_end, event_length in new_events:
        
        event_form = FormReader(id)
        event_form.read_form()
        
        schedule_time = build_availability(
            event_form.parsed_results,
            event_start,
            event_end,
            event_length,
        )

        cur.execute(
            """
            UPDATE events
            SET scheduled = 1
            WHERE form_id = :id
            """,
            {"id": id}
        )
        events.append({
            "guild_id": guild_id,
            "channel_id": channel_id,
            "name": name,
            "schedule_time": schedule_time,
            "event_length": event_length,
        })

    return jsonify(events)


def get_db():

    # If there's not already a database connection.
    if "db" not in g:
        g.db = sqlite3.connect("./db/quelaag.db")

        cur = g.db.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                guild_id text,
                channel_id text,
                form_id text,
                name text, 
                event_length real, 
                time_range_start text, 
                time_range_end text, 
                expiration_time integer,
                scheduled integer
            );
            """
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS event_dates (form_id text, date text);"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS time_zones (uid integer, tz integer);"
        )

        g.db.commit()

    return g.db


app.run()
