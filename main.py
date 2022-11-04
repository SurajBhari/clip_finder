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

@app.route('/', methods=["POST", "GET"])
def clip_finder():
    # take input from a text box id = " input"
    if request.method == "GET":
        return render_template(
            "index.html",
            result=False
        )

    video_link =  request.form["video_link"]
    key_word =  request.form["keywords"].split(",")
    if not video_link:
        return "Please enter a video link to make this work... like https://www.youtube.com/watch?v=E1YVSxKXidc"
    
    key_word = [_.lower().strip() for _ in key_word]
    if not key_word:
        return "Please enter Keyword(s) to make this work..."
    print(key_word)
    parsed_link = parse.urlparse(video_link)
    try:
        video_id = parse.parse_qs(parsed_link.query)['v'][0]
    except KeyError:
        return "Please pass a proper youtube video link... like https://www.youtube.com/watch?v=E1YVSxKXidc . Sharing links are not allowed till now."
    print(video_id)
    if not video_id:
        return "Please Parse a actual livestream link like  https://www.youtube.com/watch?v=E1YVSxKXidc"
    
    string = ""
    links = []
    chats = []
    images = []
    names = []
    video_data = Video.get(video_id)
    embed_link = "https://www.youtube.com/embed/"+video_id

    if not video_data["isLiveContent"]:
        return "Please Parse a actual livestream link like  https://www.youtube.com/watch?v=E1YVSxKXidc"
    title = video_data["title"]
    duration = int(video_data["duration"]["secondsText"])
    duration = datetime.timedelta(seconds=duration)
    duration = str(duration)
    description = video_data["description"]
    thumbnail_link = "https://i.ytimg.com/vi/" + video_id + "/maxresdefault.jpg"
    if video_data["isLiveNow"]:
        return "Please wait till the stream get over to prevent issues."
    try:
        video_direct_link = video_data["streamingData"]["formats"][-1]["url"]
    except KeyError:
        return "Please wait till the stream get rendered properly from yotube side to prevent issues."
    video_link = video_data["link"]
    try:
        chat = ChatDownloader().get_chat(video_id, message_types=['all']) # get chat
    except errors.NoChatReplay:
        return "Please wait till the stream get rendered properly from yotube side to prevent issues."
    chat_count = 0
    message_count = {}
    known_types = listdir('message_types')
    print("known message types are" + "\n".join(known_types))
    income_count = 0
    new_members = []
    new_members_m = []
    for message in chat:
        if message["message_type"]+".json" not in known_types:
            known_types.append(message["message_type"]+".json")
            with open("message_types/"+message["message_type"]+".json", "w") as f:
                f.write(json.dumps(message, indent=4))
        if message["message_type"] in ["paid_message", "paid_sticker"]:
            income_count += message["money"]["amount"]
            continue
        elif message["message_type"] in ["membership_item", "sponsorships_gift_redemption_announcement"]:
            if message["message_type"] == "membership_item":
                new_members.append(message["author"]["name"])
                new_members_m.append(message["header_secondary_text"])
            elif message["message_type"] == "sponsorships_gift_redemption_announcement":
                new_members.append(message["author"]["name"])
                new_members_m.append(message["message"])
            continue
        elif message["message_type"] in ["viewer_engagement_message", "ticker_paid_sticker_item", "ticker_sponsor_item", "ticker_paid_message_item", "sponsorships_gift_purchase_announcement"]:
            continue # ignore these messagestypes
        elif message["message_type"] == "text_message":
            for word in key_word:
                if ((word in message['message'].lower().split()) or (word in message['author']['name'].lower())):
                    link = "https://youtu.be/"+video_id+"?t="+str(int(message['time_in_seconds']))
                    image_link = message['author']['images'][1]['url']
                    chat = message['message']
                    name = message['author']['name']
                    string += '</br>' + f"<img src = \"{image_link}\"> {name} " "<a href=\"" + link + f"\"> "+ "."*100 + f"  {link} - </a> " + chat
                    names.append(name)
                    chats.append(chat)
                    images.append(image_link)
                    links.append(link)
                try:
                    message_count[message['author']['name']] += 1
                except KeyError:
                    message_count[message['author']['name']] = 1
                chat_count += 1
        
    message_count = sorted(message_count.items(), key=lambda x: x[1], reverse=True)[:5]
    top_chatter_count = []
    top_chatter_name = []

    for x,y in message_count:
        top_chatter_name.append(x)
        top_chatter_count.append(y)

    return render_template(
        "index.html",
        title=title,
        duration=duration,
        description=description,
        video_link = video_link,
        embed_link = embed_link,
        thumbnail_link=thumbnail_link,
        video_direct_link=video_direct_link,
        links=links, 
        chats=chats, 
        images=images, 
        names=names,
        top_chatter_name=top_chatter_name,
        top_chatter_count=top_chatter_count,
        chat_count = chat_count,
        new_members = new_members,
        new_members_m = new_members_m,
        income_count = income_count,
        result=True
    )

app.run(debug=False, host="0.0.0.0", port=8080)