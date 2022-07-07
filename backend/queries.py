def init_tables(db):

    cur = db.cursor()

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
            utc_offset integer,
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

    db.commit()


def get_events(db, current_time):

    cur = db.cursor()

    cur.execute(
        """
        SELECT 
            guild_id, 
            channel_id, 
            form_id, 
            name, 
            time_range_start, 
            time_range_end, 
            event_length,
            utc_offset
        FROM events 
        WHERE expiration_time <= :now 
        AND scheduled = 0;
        """, 
        {"now": current_time}
    )

    new_events = cur.fetchall()

    return new_events


def set_event_as_scheduled(db, event_id):

    cur = db.cursor()

    cur.execute(
        """
        UPDATE events
        SET scheduled = 1
        WHERE form_id = :id
        """,
        {"id": event_id}
    )

    db.commit()


def add_event_info(db, input_json, form_id, expiration_time):
    
    cur = db.cursor()
    
    cur.execute(
        "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            input_json["guild_id"],
            input_json["channel_id"],
            form_id,
            input_json["name"],
            input_json["event_length"],
            input_json["time_of_day"][0],
            input_json["time_of_day"][1],
            expiration_time,
            input_json["timezone"],
            0,  # Not scheduled yet
        ),
    )

    date_list = [(form_id, dt) for dt in input_json["dates"]]
    cur.executemany("INSERT INTO event_dates VALUES (?, ?)", date_list)

    db.commit()
    

def set_user_tz(db, req):
    cur = db.cursor()
    cur.execute(
        "INSERT INTO time_zones VALUES (?, ?)", (req["user_id"], req["utc_offset"])
    )
    db.commit()


def get_user_tz(db, req):
    cur = db.cursor()
    cur.execute(
        "SELECT * FROM time_zones WHERE uid = :uid", {"uid": req["user_id"]}
    )
    res = cur.fetchone()
    return res