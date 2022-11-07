from re import T
from chat_downloader import ChatDownloader, errors
from youtubesearchpython import Video
from os import listdir
import datetime
from flask import Flask, render_template, request

from flask import Flask, redirect, url_for, render_template, request

from os import listdir
import json
from urllib import parse

app = Flask(__name__)


@app.route("/", methods=["POST", "GET"])
def clip_finder():
    # take input from a text box id = " input"
    if request.method == "GET":
        return render_template("index.html", result=False)

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
    superchat_ammounts = []
    superchat_messages = []
    superchat_users_images = []
    chat_count = 0
    message_count = {}
    known_types = listdir("message_types")
    video_link = request.form["video_link"]
    key_word = request.form["keywords"].split(",")
    key_word = [_.lower().strip() for _ in key_word]

    if not video_link:
        return "Please enter a video link to make this work... like https://www.youtube.com/watch?v=E1YVSxKXidc"
    if not key_word:
        return "Please enter Keyword(s) to make this work..."

    parsed_link = parse.urlparse(video_link)
    try:
        video_id = parse.parse_qs(parsed_link.query)["v"][0]
    except KeyError:
        return "Please pass a proper youtube video link... like https://www.youtube.com/watch?v=E1YVSxKXidc . Sharing links are not allowed till now."
    if not video_id:
        return "Please Parse a actual livestream link like  https://www.youtube.com/watch?v=E1YVSxKXidc"

    video_data = Video.get(video_id)
    if not video_data["isLiveContent"]:
        return "Please Parse a actual livestream link like  https://www.youtube.com/watch?v=E1YVSxKXidc"
    if video_data["isLiveNow"]:
        return "Please wait till the stream get over to prevent issues."
    try:
        video_direct_link = video_data["streamingData"]["formats"][-1]["url"]
    except KeyError:
        return "Please wait till the stream get rendered properly from yotube side to prevent issues."

    embed_link = "https://www.youtube.com/embed/" + video_id
    title = video_data["title"]
    duration = str(
        datetime.timedelta(seconds=int(video_data["duration"]["secondsText"]))
    )
    description = video_data["description"]
    thumbnail_link = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
    video_link = video_data["link"]
    print(listdir("previous_attempts"))
    message_data = []
    if video_id + ".json" in listdir("previous_attempts"):
        with open("previous_attempts/" + video_id + ".json", "r") as f:
            data = json.load(f)
            cached = True
        print("Already Cached")
    else:
        try:
            data = ChatDownloader().get_chat(
                video_id, message_types=["all"]
            )  # get chat
        except errors.NoChatReplay:
            return "Please wait till the stream get rendered properly from yotube side to prevent issues."

    for message in data:
        if not cached:
            message_data.append(message)

        if message["message_type"] + ".json" not in known_types:
            known_types.append(message["message_type"] + ".json")
            with open("message_types/" + message["message_type"] + ".json", "w") as f:
                f.write(json.dumps(message, indent=4))

        if message["message_type"] in ["paid_message", "paid_sticker"]:
            superchat_users.append(message["author"]["name"])
            superchat_users_images.append(message["author"]["images"][-1]["url"])
            superchat_ammounts.append(message["money"]["text"])
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
                continue # ignore messages without text
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
                if (word in message_content) or (
                    word in username.lower()
                ):
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

    return render_template(
        "index.html",
        title=title,
        duration=duration,
        description=description,
        video_link=video_link,
        embed_link=embed_link,
        thumbnail_link=thumbnail_link,
        video_direct_link=video_direct_link,
        links=links,
        chats=chats,
        images=images,
        names=names,
        timestamps=timestamps,
        top_chatter_name=top_chatter_name,
        top_chatter_count=top_chatter_count,
        chat_count=chat_count,
        new_members=new_members,
        new_members_m=new_members_m,
        new_members_images=new_members_images,
        superchat_ammounts=superchat_ammounts,
        superchat_users=superchat_users,
        superchat_messages=superchat_messages,
        superchat_users_images=superchat_users_images,
        income_count=income_count,
        result=True,
    )


app.run(debug=False, host="0.0.0.0", port=8080)
