import base64
import gzip
import hashlib
import json
import os
import random
import string
import zlib
from datetime import datetime
from functools import wraps

import requests
from flask import Flask, jsonify, request, send_from_directory

# conf
CREDENTIALS_FILE = "credentials.json"
INDEX_FILE = "index.json"
DOWNLOADS_DIR = "Downloads"
STATIC_DIR = "static"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = Flask(__name__, static_folder=STATIC_DIR)


HEADERS = {"User-Agent": ""}

CHARACTERS = string.ascii_letters + string.digits

START_OF_LEVEL = (
    "kS38,1_40_2_125_3_255_11_255_12_255_13_255_4_-1_6_1000_7_1_15_1_18_0_8_1|"
    "1_0_2_102_3_255_11_255_12_255_13_255_4_-1_6_1001_7_1_15_1_18_0_8_1|"
    "1_0_2_102_3_255_11_255_12_255_13_255_4_-1_6_1009_7_1_15_1_18_0_8_1|"
    "1_255_2_255_3_255_11_255_12_255_13_255_4_-1_6_1002_5_1_7_1_15_1_18_0_8_1|"
    "1_40_2_125_3_255_11_255_12_255_13_255_4_-1_6_1013_7_1_15_1_18_0_8_1|"
    "1_40_2_125_3_255_11_255_12_255_13_255_4_-1_6_1014_7_1_15_1_18_0_8_1|"
    "1_0_2_200_3_255_11_255_12_255_13_255_4_-1_6_1005_5_1_7_1_15_1_18_0_8_1|"
    "1_0_2_125_3_255_11_255_12_255_13_255_4_-1_6_1006_5_1_7_1_15_1_18_0_8_1|,"
    "kA13,0,kA15,0,kA16,0,kA14,,kA6,0,kA7,0,kA25,0,kA17,0,kA18,0,kS39,0,"
    "kA2,0,kA3,0,kA8,0,kA4,0,kA9,0,kA10,0,kA22,0,kA23,0,kA24,0,kA27,1,"
    "kA40,1,kA48,1,kA41,1,kA42,1,kA28,0,kA29,0,kA31,1,kA32,1,kA36,0,kA43,0,"
    "kA44,0,kA45,1,kA46,0,kA47,0,kA33,1,kA34,1,kA35,0,kA37,1,kA38,1,kA39,1,"
    "kA19,0,kA26,0,kA20,0,kA21,0,kA11,0;"
)

USED_KEYS = [
    1, 6, 7, 8, 9, 10, 12, 20, 21, 22, 23, 24, 25, 28, 29, 33, 34,
    45, 46, 47, 50, 51, 54, 61, 63, 68, 69, 71, 72, 73, 75, 76, 77,
    80, 84, 85, 90, 91, 92, 95, 97, 105, 107, 108, 113, 114, 115
]


def xor_cipher(text: str, key: str) -> str:
    return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text))


def generate_gjp2(password: str = "", salt: str = "mI29fmAnxgTs") -> str:
    return hashlib.sha1((password + salt).encode()).hexdigest()


def generate_chk(values: list, key: str = "", salt: str = "") -> str:
    values = list(values) + [salt]
    raw = "".join(map(str, values))
    hashed = hashlib.sha1(raw.encode()).hexdigest()
    xored = xor_cipher(hashed, key)
    return base64.urlsafe_b64encode(xored.encode()).decode()


def generate_upload_seed(data: str, chars: int = 50) -> str:
    if len(data) < chars:
        return data
    step = len(data) // chars
    return data[::step][:chars]


def parse_level(level_string: str) -> bytearray:
    file_bytes = bytearray()
    level_objects = level_string.split(";")[1:]
    for obj in level_objects:
        parts = obj.split(",")
        for i in range(0, len(parts), 2):
            try:
                key = int(parts[i])
                if key not in USED_KEYS:
                    continue
                if i + 1 >= len(parts):
                    continue
                val = int(parts[i + 1])
                val = max(0, min(255, val))
                if key == 1:
                    val = max(0, val - 1)
                file_bytes.append(val)
            except Exception:
                continue
    return file_bytes


def make_level(file_bytes: bytearray):
    current_x = 0
    current_y = 500
    i = 1
    key_on = 1

    current_object = f"1,{file_bytes[0] + 1},2,0,3,500,"
    level_string = ""
    object_count = 1

    while i < len(file_bytes):
        current_object += f"{USED_KEYS[key_on]},{file_bytes[i]}"
        key_on += 1

        if key_on == len(USED_KEYS):
            key_on = 1
            i += 1
            level_string += current_object + ";"
            current_y -= 30
            if current_y < 0:
                current_y = 500
                current_x += 30
            if i + 1 >= len(file_bytes):
                i += 1
                continue
            current_object = f"1,{file_bytes[i] + 1},2,{current_x},3,{current_y},"
            object_count += 1
        else:
            current_object += ","

        i += 1

    level_string += current_object + ";"
    object_count += 1
    return START_OF_LEVEL + level_string, object_count


def encode_level(level_string: str) -> str:
    return base64.urlsafe_b64encode(gzip.compress(level_string.encode())).decode()


def decode_level(level_data: str) -> str:
    raw = base64.urlsafe_b64decode(level_data.encode())
    return zlib.decompress(raw, 15 | 32).decode()


def gd_download_level(level_id: int) -> str:
    resp = requests.post(
        "https://www.boomlings.com/database/downloadGJLevel22.php",
        data={"levelID": level_id, "secret": "Wmfd2893gb7"},
        headers=HEADERS,
        timeout=15,
    )
    parts = resp.text.split("#")[0].split(":")
    level_string = ""
    for i in range(0, len(parts), 2):
        if parts[i] == "4":
            level_string = parts[i + 1]
            break
    if not level_string:
        return ""
    return decode_level(level_string)


def gd_delete_level(account_id: str, gjp2: str, level_id: int) -> bool:
    resp = requests.post(
        "https://www.boomlings.com/database/deleteGJLevelUser20.php",
        data={
            "accountID": account_id,
            "gjp2": gjp2,
            "levelID": level_id,
            "secret": "Wmfv2898gc9",
        },
        headers=HEADERS,
        timeout=15,
    )
    return resp.text != "-1"


def gd_upload_level(account_id: str, gjp2: str, username: str,
                    level_name: str, level_string_enc: str, object_count: int) -> str:
    seed2 = generate_chk(
        key="41274",
        values=[generate_upload_seed(level_string_enc)],
        salt="xI25fpAapCQg",
    )
    data = {
        "gameVersion": 22, "binaryVersion": 47,
        "accountID": account_id, "gjp2": gjp2, "userName": username,
        "levelID": 0, "levelName": level_name, "levelDesc": "",
        "levelVersion": 1, "levelLength": 0, "audioTrack": 0,
        "auto": 0, "password": 1, "original": 0, "twoPlayer": 0,
        "songID": 645828, "objects": object_count, "coins": 0,
        "requestedStars": 10, "unlisted": 2, "ldm": 0,
        "levelString": level_string_enc, "seed2": seed2,
        "secret": "Wmfd2893gb7", "dvs": 3,
    }
    resp = requests.post(
        "https://www.boomlings.com/database/uploadGJLevel21.php",
        data=data, headers=HEADERS, timeout=30,
    )
    return resp.text  # level ID string or -1


# helpers

def load_credentials():
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    with open(CREDENTIALS_FILE) as f:
        data = json.load(f)
    if all(k in data for k in ("gjp2", "username", "account_id")):
        return data
    return None


def save_credentials(username: str, gjp2: str, account_id: str):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump({"gjp2": gjp2, "username": username, "account_id": account_id}, f)


def load_index():
    if not os.path.exists(INDEX_FILE):
        return {}
    with open(INDEX_FILE) as f:
        return json.load(f)


def save_index(data: dict):
    with open(INDEX_FILE, "w") as f:
        json.dump(data, f)


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        creds = load_credentials()
        if not creds:
            return jsonify({"error": "Not logged in"}), 401
        return f(*args, creds=creds, **kwargs)
    return decorated


def ts():
    return datetime.now().strftime("%H:%M:%S")


# auth

@app.route("/api/status")
def api_status():
    creds = load_credentials()
    if creds:
        return jsonify({"logged_in": True, "username": creds["username"], "account_id": creds["account_id"]})
    return jsonify({"logged_in": False})


@app.route("/api/login", methods=["POST"])
def api_login():
    body = request.get_json(force=True)
    username = body.get("username", "").strip()
    password = body.get("password", "").strip()
    account_id = body.get("account_id", "").strip()

    if not all([username, password, account_id]):
        return jsonify({"error": "All fields required"}), 400

    gjp2 = generate_gjp2(password)
    save_credentials(username, gjp2, account_id)
    return jsonify({"ok": True, "username": username})


@app.route("/api/logout", methods=["POST"])
def api_logout():
    if os.path.exists(CREDENTIALS_FILE):
        os.remove(CREDENTIALS_FILE)
    return jsonify({"ok": True})


# files

@app.route("/api/files")
@require_auth
def api_list_files(creds):
    index = load_index()
    files = [
        {"name": name, "level_id": meta["level_id"], "level_name": meta["level_name"]}
        for name, meta in index.items()
    ]
    return jsonify({"files": files, "count": len(files)})


@app.route("/api/upload", methods=["POST"])
@require_auth
def api_upload(creds):
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    filename = f.filename or "unnamed"
    file_bytes = bytearray(f.read())

    if not file_bytes:
        return jsonify({"error": "Empty file"}), 400

    index = load_index()

    if filename in index:
        level_name = index[filename]["level_name"]
    else:
        level_name = "".join(random.choices(CHARACTERS, k=20))

    try:
        level_string, object_count = make_level(file_bytes)
        level_string_enc = encode_level(level_string)
    except Exception as e:
        return jsonify({"error": f"Encoding failed: {e}"}), 500

    try:
        result = gd_upload_level(
            creds["account_id"], creds["gjp2"], creds["username"],
            level_name, level_string_enc, object_count,
        )
    except Exception as e:
        return jsonify({"error": f"GD upload failed: {e}"}), 502

    if result == "-1":
        return jsonify({"error": "GD server rejected upload (-1). Check credentials."}), 502

    try:
        level_id = int(result)
    except ValueError:
        return jsonify({"error": f"Unexpected GD response: {result}"}), 502

    index[filename] = {"level_id": level_id, "level_name": level_name}
    save_index(index)

    return jsonify({"ok": True, "filename": filename, "level_id": level_id})


@app.route("/api/download")
@require_auth
def api_download(creds):
    filename = request.args.get("name", "")
    if not filename:
        return jsonify({"error": "Missing ?name= parameter"}), 400

    index = load_index()
    if filename not in index:
        return jsonify({"error": "File not found in index"}), 404

    level_id = index[filename]["level_id"]
    try:
        level_string = gd_download_level(level_id)
    except Exception as e:
        return jsonify({"error": f"GD download failed: {e}"}), 502

    if not level_string:
        return jsonify({"error": "Level not found on GD servers"}), 404

    file_bytes = parse_level(level_string)

    # Save locally too
    safe_name = os.path.basename(filename)
    out_path = os.path.join(DOWNLOADS_DIR, safe_name)
    with open(out_path, "wb") as fp:
        fp.write(file_bytes)

    from flask import Response
    return Response(
        bytes(file_bytes),
        mimetype="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@app.route("/api/delete", methods=["POST"])
@require_auth
def api_delete(creds):
    body = request.get_json(force=True)
    filename = body.get("name", "")
    if not filename:
        return jsonify({"error": "Missing 'name' field"}), 400

    index = load_index()
    if filename not in index:
        return jsonify({"error": "File not found in index"}), 404

    level_id = index[filename]["level_id"]
    try:
        success = gd_delete_level(creds["account_id"], creds["gjp2"], level_id)
    except Exception as e:
        return jsonify({"error": f"GD request failed: {e}"}), 502

    if not success:
        return jsonify({"error": "GD server rejected deletion (-1)"}), 502

    del index[filename]
    save_index(index)
    return jsonify({"ok": True})


# very advanced frontend wow

@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


# run

if __name__ == "__main__":
    port = 5000
    for i in range(6):
        print(">")
    print("> GDDrive WS")
    print("> running on http://localhost:", port)
    for i in range(2):
        print(">")
    app.run(host="0.0.0.0", port=port, debug=True)