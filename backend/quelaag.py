import boto3
from botocore.exceptions import ClientError

from flask import Flask, request, g, jsonify
from form_helpers import FormReader, FormWriter, build_availability
import queries as q

import sqlite3
import datetime

import os

app = Flask(__name__)
form_writer = FormWriter()
LOCAL_DB_PATH = "./db/quelaag.db"


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
    q.add_event_info(db, input_json, form_id, expiration_time)

    return jsonify(success=True, form_url=form_url)


@app.route("/set_tz", methods=["POST"])
def set_tz():

    req = request.get_json()

    db = get_db()
    q.set_user_tz(db, req)

    return jsonify(success=True)


@app.route("/get_tz", methods=["POST"])
def get_tz():

    req = request.get_json()

    db = get_db()
    res = q.get_user_tz(db, req)

    if res is None:
        return jsonify(tz=-100)

    else:
        return jsonify(tz=res[1])


@app.route("/check_closing", methods=["GET"])
def check_closing():

    right_now = datetime.datetime.utcnow().timestamp()

    db = get_db()
    new_events = q.get_events(db, right_now)

    events = []
    for (
        guild_id,
        channel_id,
        id,
        name,
        event_start,
        event_end,
        event_length,
        timezone,
    ) in new_events:

        event_form = FormReader(id)
        event_form.read_form()

        schedule_time = build_availability(
            event_form.parsed_results,
            event_start,
            event_end,
            event_length,
        )

        q.set_event_as_scheduled(db, id)
        events.append(
            {
                "guild_id": guild_id,
                "channel_id": channel_id,
                "name": name,
                "schedule_time": schedule_time,
                "event_length": event_length,
                "timezone": timezone,
            }
        )

    return jsonify(events)


@app.route("/sync_db", methods=["GET"])
def sync_db():

    if "s3_client" not in g:
        g.s3_client = boto3.client("s3")

    g.s3_client.upload_file(LOCAL_DB_PATH, "lordran-bot", "quelaag.db")

    return jsonify(success=True)


def get_db():

    # If there's not already a database connection.
    if "db" not in g:
        g.db = sqlite3.connect(LOCAL_DB_PATH)

        if "s3_client" not in g:
            g.s3_client = boto3.client("s3")

        try:
            g.s3_client.download_file("lordran-bot", "quelaag.db", LOCAL_DB_PATH)
            os.chmod(LOCAL_DB_PATH, os.stat.S_IRWXU)
        except ClientError as e:
            if int(e.response["Error"]["Code"]) == 404:
                q.init_tables(g.db)
            else:
                raise e

    return g.db
