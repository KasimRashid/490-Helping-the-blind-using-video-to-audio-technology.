import json
import mysql.connector
from datetime import datetime
import getpass

DB_PASSWORD = getpass.getpass("Enter MySQL password: ")


def connect_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=DB_PASSWORD,
        database="final490project"
    )


def save_detection_to_mysql(frame_number, user_id, objects_detected, width, height):
    session_time = datetime.now().strftime("%m/%d/%y-%H:%M")

    connection = connect_database()
    cursor = connection.cursor()

    query = """
    INSERT INTO detection_logs
    (frame_number, user_id, session_time, objects_detected, width, height)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = (
        frame_number,
        user_id,
        session_time,
        json.dumps(objects_detected),
        width,
        height
    )

    cursor.execute(query, values)
    connection.commit()

    cursor.close()
    connection.close()


def save_detection_to_json(frame_number, user_id, objects_detected, width, height):
    session_time = datetime.now().strftime("%m/%d/%y-%H:%M")

    data = {
        "Frame": frame_number,
        "User": user_id,
        "Session_time": session_time,
        "Objects_detected": objects_detected,
        "Resolution": {
            "width": width,
            "height": height
        }
    }

    with open("detection_session.json", "a") as file:
        json.dump(data, file, indent=4)
        file.write("\n")