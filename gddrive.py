import base64, gzip, requests, hashlib, base64, json, random, string, zlib, os, getpass
from datetime import datetime

def log(message, level, function=""):
    now = datetime.now()

    if function != "":
        if level == 0:
            print(f"[{now.strftime('%H:%M:%S')}] {function}: " + message)
        elif level == 1:
            print(f"[{now.strftime('%H:%M:%S')}] [WARNING] {function}: " + message)
        elif level == 2:
            print(f"[{now.strftime('%H:%M:%S')}] [ERROR] {function}: " + message)
    else:
        if level == 0:
            print(f"[{now.strftime('%H:%M:%S')}] " + message)
        elif level == 1:
            print(f"[{now.strftime('%H:%M:%S')}] [WARNING] " + message)
        elif level == 2:
            print(f"[{now.strftime('%H:%M:%S')}] [ERROR] " + message)

headers = {
    "User-Agent": ""
}

characters = string.ascii_letters + string.digits
start_of_level = "kS38,1_40_2_125_3_255_11_255_12_255_13_255_4_-1_6_1000_7_1_15_1_18_0_8_1|1_0_2_102_3_255_11_255_12_255_13_255_4_-1_6_1001_7_1_15_1_18_0_8_1|1_0_2_102_3_255_11_255_12_255_13_255_4_-1_6_1009_7_1_15_1_18_0_8_1|1_255_2_255_3_255_11_255_12_255_13_255_4_-1_6_1002_5_1_7_1_15_1_18_0_8_1|1_40_2_125_3_255_11_255_12_255_13_255_4_-1_6_1013_7_1_15_1_18_0_8_1|1_40_2_125_3_255_11_255_12_255_13_255_4_-1_6_1014_7_1_15_1_18_0_8_1|1_0_2_200_3_255_11_255_12_255_13_255_4_-1_6_1005_5_1_7_1_15_1_18_0_8_1|1_0_2_125_3_255_11_255_12_255_13_255_4_-1_6_1006_5_1_7_1_15_1_18_0_8_1|,kA13,0,kA15,0,kA16,0,kA14,,kA6,0,kA7,0,kA25,0,kA17,0,kA18,0,kS39,0,kA2,0,kA3,0,kA8,0,kA4,0,kA9,0,kA10,0,kA22,0,kA23,0,kA24,0,kA27,1,kA40,1,kA48,1,kA41,1,kA42,1,kA28,0,kA29,0,kA31,1,kA32,1,kA36,0,kA43,0,kA44,0,kA45,1,kA46,0,kA47,0,kA33,1,kA34,1,kA35,0,kA37,1,kA38,1,kA39,1,kA19,0,kA26,0,kA20,0,kA21,0,kA11,0;"


used_keys = [1, 6, 7, 8, 9, 10, 12, 20, 21, 22, 23, 24, 25, 28, 29, 33, 34, 45, 46, 47, 50, 51, 54, 61, 63, 68, 69, 71, 72, 73, 75, 76, 77, 80, 84, 85, 90, 91, 92, 95, 97, 105, 107, 108, 113, 114, 115]

def xor_cipher(text, key):
    result = []

    for i, ch in enumerate(text):
        byte = ord(ch)
        x_key = ord(key[i % len(key)])
        result.append(chr(byte ^ x_key))

    return "".join(result)

def generate_gjp2(password: str = "", salt: str = "mI29fmAnxgTs") -> str:
    password += salt
    hash = hashlib.sha1(password.encode()).hexdigest()

    return hash

def generate_chk(values: [int, str] = [], key: str = "", salt: str = "") -> str:
    values.append(salt)

    string = ("").join(map(str, values))

    hashed = hashlib.sha1(string.encode()).hexdigest()
    xored = xor_cipher(hashed, key)
    final = base64.urlsafe_b64encode(xored.encode()).decode()

    return final

def generate_upload_seed(data: str, chars: int = 50) -> str:
    if len(data) < chars:
        return data
    step = len(data) // chars
    return data[::step][:chars]

def parse_level(level_string: str):
    file_bytes = bytearray()

    level_objects = level_string.split(";")[1:]

    for object in level_objects:
        split_object = object.split(",")

        for i in range(0, len(split_object), 2):
            try:
                if int(split_object[i]) in used_keys:
                    if int(split_object[i]) != 1:
                        if int(split_object[i + 1]) > 255:
                            file_bytes.append(255)
                        elif int(split_object[i + 1]) < 0:
                            file_bytes.append(0)
                        else:
                            if i + 1 >= len(split_object):
                                continue

                            file_bytes.append(int(split_object[i + 1]))
                    else:
                        if int(split_object[i + 1]) > 255:
                            file_bytes.append(255)
                        elif int(split_object[i + 1]) < 0:
                            file_bytes.append(0)
                        else:
                            if i + 1 >= len(split_object):
                                continue
                            
                            file_bytes.append(int(split_object[i + 1]) - 1)
            except:
                continue
    
    return file_bytes

def make_level(file_bytes: bytearray):
    current_x = 0
    current_y = 500

    i = 1

    key_on = 1
    current_object = "1," + str(file_bytes[0] + 1) + ",2,0,3,500,"
    level_string = ""
    object_count = 1

    while i != len(file_bytes) and not i > len(file_bytes):
        current_object += str(used_keys[key_on]) + "," + str(file_bytes[i])
        
        key_on += 1
        
        if key_on == len(used_keys):
            key_on = 1

            i += 1
            level_string += current_object + ";"
            current_y -= 30

            if current_y < 0:
                current_y = 500
                current_x += 30
            
            if i + 1 >= len(file_bytes):
                continue
            
            current_object = "1," + str(file_bytes[i] + 1) + ",2," + str(current_x) + ",3," + str(current_y) + ","
            object_count += 1
        else:
            current_object += (",")

        i += 1
    
    level_string += current_object + ";"
    object_count += 1

    return start_of_level + level_string, object_count

def encode_level(level_string: str, is_official_level: bool) -> str:
    gzipped = gzip.compress(level_string.encode())
    base64_encoded = base64.urlsafe_b64encode(gzipped)

    if is_official_level:
        base64_encoded = base64_encoded[13:]
    
    return base64_encoded.decode()

def decode_level(level_data: str, is_official_level: bool) -> str:
    if is_official_level:
        level_data = 'H4sIAAAAAAAAA' + level_data
    
    base64_decoded = base64.urlsafe_b64decode(level_data.encode())
    decompressed = zlib.decompress(base64_decoded, 15 | 32)

    return decompressed.decode()

def downloadLevel(id: int) -> str:
    request_data = {
        "levelID": id,
        "secret": "Wmfd2893gb7"
    }

    req = requests.post(url="https://www.boomlings.com/database/downloadGJLevel22.php", data=request_data, headers=headers)

    split_res = req.text.split("#")
    split_res2 = split_res[0].split(":")

    level_string = ""

    for i in range(0, len(split_res2), 2):
        if split_res2[i] == "4":
            level_string = split_res2[i + 1]
            break
    
    if level_string == "":
        log("Level " + str(id) + " not found!", 2)
        return ""
    else:
        log("Downloaded level " + str(id) + "!", 0)

        return decode_level(level_string, False)

def deleteLevel(id: int):
    request_data = {
        "accountID": account_id,
        "gjp2": gjp_2,
        "levelID": id,
        "secret": "Wmfv2898gc9"
    }

    req = requests.post(url="https://www.boomlings.com/database/deleteGJLevelUser20.php", data=request_data, headers=headers)

    if req.text != "-1":
        log("Level ID " + str(id) + " deleted successfully!", 0)
        return 0
    else:
        log("Could not delete level ID " + str(id) + "!", 2)
        return 1

print("Welcome to GDDrive!")

with open("credentials.json", "r") as credentials_file:
    data = json.load(credentials_file)

    if "gjp2" in data and "username" in data and "account_id" in data:
        log("Credentials saved, skipping login...", 0)

        username = data["username"]
        gjp_2 = data["gjp2"]
        account_id = data["account_id"]
    else:
        print("To begin, please log in to Geometry Dash.")
        username = input(" - Username: ")
        password = getpass.getpass(" - Password: ")
        account_id = input(" - Account ID: ")

        log("Generating GJP2...", 0)
        gjp_2 = generate_gjp2(password)

        log("Storing credentials...", 0)
        with open("credentials.json", "w") as credentials_file_write:
            data = {
                "gjp2": gjp_2,
                "username": username,
                "account_id": account_id
            }

            json.dump(data, credentials_file_write)

log("Loading file index...", 0)
with open("index.json", "r") as index_file:
    index_data = json.load(index_file)

while True:
    print("\nWhat would you like to do?")
    print(" 1 | View files")
    print(" 2 | Upload files")
    print(" 3 | Delete files")
    print(" 4 | Download files")
    print(" 5 | Exit\n")

    x = input("Enter your response: ")

    if x == "5":
        exit()
    elif x == "4":
        file_to_download = input("\nPlease provide the file you want to download: ")

        level_string = downloadLevel(index_data[os.path.relpath(file_to_download)]["level_id"])

        if level_string == "":
            continue
        
        file_bytes = parse_level(level_string)

        filename = os.path.basename(file_to_download)
        os.makedirs("Downloads", exist_ok=True)

        with open(os.path.join("Downloads", filename), "wb") as downloaded_file:
            downloaded_file.write(file_bytes)
            downloaded_file.flush()
    elif x == "1":
        print(str(len(index_data)) + " file(s):")
        
        for file in index_data:
            print(" - " + file + " (ID: " + str(index_data[file]["level_id"]) + ")")
    elif x == "3":
        file_to_delete = input("\nPlease provide the file you want to delete: ")

        success = deleteLevel(index_data[os.path.relpath(file_to_delete)]["level_id"])

        if success == 0:
            del index_data[file_to_delete]
        else:
            continue

        with open("index.json", "w") as index_file:
            json.dump(index_data, index_file)

    elif x == "2":
        path = input("\nPlease provide the file you want to upload: ")

        path = os.path.relpath(path)

        log("Uploading level...", 0)

        with open(path, "rb") as uploaded_file:
            level_string, object_count = make_level(uploaded_file.read())
            level_string = encode_level(level_string, False)

            path = os.path.basename(path)

            if path not in index_data:
                level_name = ''.join(random.choices(characters, k=20))
            else:
                level_name = index_data[path]["level_name"]

            data = {
                "gameVersion": 22,
                "binaryVersion": 47,
                "accountID": account_id,
                "gjp2": gjp_2,
                "userName": username,
                "levelID": 0,
                "levelName": level_name,
                "levelDesc": "",
                "levelVersion": 999,
                "levelLength": 0,
                "audioTrack": 0,
                "auto": 0,
                "password": 1,
                "original": 0,
                "twoPlayer": 0,
                "songID": 645828,
                "objects": object_count,
                "coins": 0,
                "requestedStars": 10,
                "unlisted": 2,
                "ldm": 0,
                "levelString": level_string,
                "seed2": generate_chk(key="41274", values=[generate_upload_seed(level_string)], salt="xI25fpAapCQg"),
                "secret": "Wmfd2893gb7",
                "dvs": 3
            }

            req = requests.post(url="https://www.boomlings.com/database/uploadGJLevel21.php", data=data, headers=headers)

            if req.text != "-1":
                log("Level successfully uploaded! ID: " + req.text, 0)
                log("Adding level to index...", 0)

                index_data[path] = {"level_id": int(req.text), "level_name": level_name}

                with open("index.json", "w") as index_file:
                    json.dump(index_data, index_file)

            else:
                log("Failed to upload level!", 2)
                continue
