from chat_downloader import ChatDownloader, errors
import yt_dlp
from os import listdir
import datetime
from flask import Flask, render_template, request, jsonify
from pathlib import Path
from flask import Flask, redirect, url_for, render_template, request
from math import floor
from os import listdir
import json
from urllib import parse
from currency_converter import CurrencyConverter


app = Flask(__name__)
currency = CurrencyConverter()


def process(video_link, key_word, cookies):
    cached = False
    string = ""
    links = []
    chats = []
    images = []
    names = []
    timestamps = []
    income_count = 0
    new_members = []
    new_members_m = []
    new_members_images = []
    superchat_users = []
    superchat_amounts = []
    superchat_messages = []
    superchat_users_images = []
    chat_count = 0
    message_count = {}
    known_types = listdir("message_types")

    if not video_link:
        return "Please enter a video link to make this work... like https://www.youtube.com/watch?v=kHGP5ABZfqM"
    if not key_word:
        return "Please enter Keyword(s) to make this work..."

    parsed_link = parse.urlparse(video_link)
    try:
        video_id = parse.parse_qs(parsed_link.query)["v"][0]
    except KeyError:
        return "Please pass a proper youtube video link... like https://www.youtube.com/watch?v=kHGP5ABZfqM . Sharing links are not allowed as of now."
    if not video_id:
        return "Please Parse a actual livestream link like  https://www.youtube.com/watch?v=kHGP5ABZfqM"
    params = {
                "skip_download": True,
                "format": "best",
            }
    if cookies:        
        # for some reason we get 2 \n after every line. so we get rid of one. i have tried replace \n\n with \n. but that doesn't work.
        with open("temp_cookies.txt", "w+") as f:
            for line in cookies.split("\n"):
                f.write(line)
        params["cookiefile"] = str(Path(__file__).parent / "temp_cookies.txt")
    try:
        # get metadata and use highest format and skip-download True    
        video_data = yt_dlp.YoutubeDL(params).extract_info(video_id, download=False)
    except Exception as e:
        return str(e)
    
    if not video_data["was_live"]:
        return "Please Parse a actual livestream link like  https://www.youtube.com/watch?v=kHGP5ABZfqM"
    if video_data["is_live"]:
        return "Please wait till the stream get over to prevent issues."
    try:
        video_data["subtitles"]["live_chat"][0]["url"]
    except KeyError:
        return "Please wait till the stream get rendered properly from yotube side to prevent issues."
    video_direct_link = video_data["url"]
    embed_link = "https://www.youtube.com/embed/" + video_id
    title = video_data["title"]
    duration = str(datetime.timedelta(seconds=int(video_data["duration"])))
    description = video_data["description"]
    thumbnail_link = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
    video_link = video_data["webpage_url"]
    print(listdir("previous_attempts"))
    message_data = []
    if video_id + ".json" in listdir("previous_attempts"):
        with open("previous_attempts/" + video_id + ".json", "r") as f:
            data = json.load(f)
            cached = True
        print("Already Cached")
    else:
        try:
            data = ChatDownloader(cookies="temp_cookies.txt").get_chat(
                video_id, message_types=["all"]
            )  # get chat
        except errors.NoChatReplay:
            return "Please wait till the stream get rendered properly from yotube side to prevent issues."
    
    with open("temp_cookies.txt", "w+") as f:
        f.write("")
    # we remove temp_cookies.txt as we don't need it anymore.
    for message in data:
        if not cached:
            message_data.append(message)

        if message["message_type"] + ".json" not in known_types:
            known_types.append(message["message_type"] + ".json")
            with open("message_types/" + message["message_type"] + ".json", "w") as f:
                f.write(json.dumps(message, indent=4))

        if message["message_type"] in ["paid_message", "paid_sticker"]:
            try:
                inr_amount = floor(
                    currency.convert(
                        message["money"]["amount"], message["money"]["currency"], "INR"
                    )
                )
            except ValueError:
                continue
            superchat_users.append(message["author"]["name"])
            superchat_users_images.append(message["author"]["images"][-1]["url"])
            superchat_amounts.append("\u20b9" + str(inr_amount))
            if message["message_type"] == "paid_sticker":
                superchat_messages.append(message["sticker_images"][-2]["url"])
            else:
                superchat_messages.append(message["message"])
            income_count += message["money"]["amount"]
            continue

        elif message["message_type"] in [
            "membership_item",
            "sponsorships_gift_redemption_announcement",
        ]:
            new_members.append(message["author"]["name"])
            new_members_images.append(message["author"]["images"][-1]["url"])
            if message["message_type"] == "membership_item":
                new_members_m.append(message["header_secondary_text"])
            elif message["message_type"] == "sponsorships_gift_redemption_announcement":
                new_members_m.append(message["message"])
            continue

        elif message["message_type"] in [
            "viewer_engagement_message",
            "ticker_paid_sticker_item",
            "ticker_sponsor_item",
            "ticker_paid_message_item",
            "sponsorships_gift_purchase_announcement",
        ]:
            continue  # ignore these messagestypes

        elif message["message_type"] == "text_message":
            try:
                message_content = message["message"].lower()
            except KeyError:
                continue  # ignore messages without text
            try:
                username = message["author"]["name"]
            except KeyError:
                username = ""

            chat_count += 1
            try:
                message_count[username] += 1
            except KeyError:
                message_count[username] = 1
            for word in key_word:
                if (word in message_content) or (word in username.lower()):
                    link = (
                        "https://youtu.be/"
                        + video_id
                        + "?t="
                        + str(int(message["time_in_seconds"]))
                    )
                    image_link = message["author"]["images"][2]["url"]
                    chat = message["message"]
                    name = message["author"]["name"]
                    timestamp = message["time_text"]
                    string += (
                        "</br>" + f'<img src = "{image_link}"> {name} '
                        '<a href="'
                        + link
                        + f'"> '
                        + "." * 100
                        + f"  {link} - </a> "
                        + chat
                    )
                    names.append(name)
                    chats.append(chat)
                    images.append(image_link)
                    links.append(link)
                    timestamps.append(timestamp)
                continue

    if not cached:
        with open("previous_attempts/" + video_id + ".json", "w") as f:
            json.dump(message_data, f, indent=4)

    message_count = sorted(message_count.items(), key=lambda x: x[1], reverse=True)[:5]
    top_chatter_count = []
    top_chatter_name = []

    for x, y in message_count:
        top_chatter_name.append(x)
        top_chatter_count.append(y)
    # construct the json to be sent to the frontend
    data = {
        "code": 200,
        "meta": {
            "title": title,
            "duration": duration,
            "description": description,
            "thumbnail_link": thumbnail_link,
            "video_link": video_link,
            "embed_link": embed_link,
            "video_direct_link": video_direct_link,
            "income_count": "\u20b9" + str(income_count),
            "message_count": chat_count,
            "new_members_count": len(new_members),
        },
        "superchat": {},
        "new_members": {},
        "top_chatters": {},
        "chats": {},
    }

    for x in range(len(superchat_users)):
        data["superchat"][x] = {
            "name": superchat_users[x],
            "avatar": superchat_users_images[x],
            "amount": superchat_amounts[x],
            "message": superchat_messages[x],
        }

    for x in range(len(new_members)):
        data["new_members"][x] = {
            "name": new_members[x],
            "avatar": new_members_images[x],
            "message": new_members_m[x],
        }

    for x in range(len(top_chatter_name)):
        data["top_chatters"][x] = {
            "name": top_chatter_name[x],
            "count": top_chatter_count[x],
        }

    for x in range(len(names)):
        data["chats"][x] = {
            "name": names[x],
            "avatar": images[x],
            "message": chats[x],
            "link": links[x],
            "timestamp": timestamps[x],
        }
    return data


@app.route("/", methods=["POST", "GET"])
def clip_finder():
    # take input from a text box id = " input"
    if request.method == "GET":
        return render_template("index.html", result=False, data={"code": 204})

    video_link = request.form["video_link"]
    key_word = request.form["keywords"].split(",")
    key_word = [_.lower().strip() for _ in key_word]
    try:
        cookies = request.form["cookies"]
    except KeyError:
        cookies = ""
    data = process(video_link, key_word, cookies)
    if type(data) == dict:
        return render_template("index.html", result=True, data=data, error=False)
    else:
        return render_template("index.html", result=False, data=data, error=True)


@app.route("/api/<video_link>/<key_word>")
def api(video_link, key_word):
    key_word = key_word.split(",")
    key_word = [_.lower().strip() for _ in key_word]
    data = process("https://youtube.com/watch?v=" + video_link, key_word)
    try:
        if data["code"] == 200:
            return jsonify(data)
    except KeyError:
        return jsonify({"code": 400, "message": "Invalid video link"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
