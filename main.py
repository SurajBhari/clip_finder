from re import T
from chat_downloader import ChatDownloader, errors
from youtubesearchpython import Video

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
    thumbnail_link = "https://i.ytimg.com/vi/Fudk3KU4e4k/maxresdefault.jpg?v=" + video_id
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
    different_type = {}
    income_count = 0
    new_member = 0
    for message in chat:
        if message["message_type"] in ["paid_message", "paid_sticker"]:
            income_count += message["money"]["amount"]
            continue
        elif message["message_type"] in ["membership_item", "sponsorships_gift_redemption_announcement"]:
            new_member += 1
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
        else:
            print("Found something new message type", message["message_type"])
            try:
                different_type[message["message_type"]].append(message)
            except KeyError:
                different_type[message["message_type"]] = [message]
            with open("different_type.json", "w") as f:
                json.dump(different_type, f, indent=4)
        
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
        new_member = new_member,
        income_count = income_count,
        result=True
    )

app.run(debug=False, host="0.0.0.0", port=8080)