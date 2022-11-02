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
        return render_template("index.html")


    video_link =  request.form["video_link"]
    key_word =  request.form["keywords"].split(",")
    if not video_link:
        return "Please enter a video link to make this work... like https://www.youtube.com/watch?v=E1YVSxKXidc"
    
    key_word = [_.lower() for _ in key_word]
    if not key_word:
        return "Please enter Keyword(s) to make this work..."
    
    parsed_link = parse.urlparse(video_link)
    video_id = parse.parse_qs(parsed_link.query)['v'][0]
    
    if not video_id:
        return "Please Parse a actual livestream link like  https://www.youtube.com/watch?v=E1YVSxKXidc"
    
    string = ""
    links = []
    chats = []
    images = []
    names = []
    video_data = Video.get(video_id)
    if not video_data["isLiveContent"]:
        return "Please Parse a actual livestream link like  https://www.youtube.com/watch?v=E1YVSxKXidc"
    title = video_data["title"]
    duration = int(video_data["duration"]["secondsText"])
    duration = datetime.timedelta(seconds=duration)
    duration = str(duration)
    description = video_data["description"]
    thumbnail_link = video_data["thumbnails"][-1]["url"]
    if video_data["isLiveNow"]:
        return "Please wait till the stream get over to prevent issues."
    video_direct_link = video_data["streamingData"]["formats"][-1]["url"]
    video_link = video_data["link"]
    chat = ChatDownloader().get_chat(video_id)

    for message in chat:
        for word in key_word:
            if word in message['message'].lower().split():
                link = "https://youtu.be/"+video_id+"?t="+str(int(message['time_in_seconds']))
                image_link = message['author']['images'][1]['url']
                chat = message['message']
                name = message['author']['name']
                string += '</br>' + f"<img src = \"{image_link}\"> {name} " "<a href=\"" + link + f"\"> "+ "."*100 + f"  {link} - </a> " + chat
                names.append(name)
                chats.append(chat)
                images.append(image_link)
                links.append(link)
                


    if not string:
        return "No data found"
    return render_template(
        "index.html",
        title=title,
        duration=duration,
        description=description,
        video_link = video_link,
        thumbnail_link=thumbnail_link,
        video_direct_link=video_direct_link,
        links=links, 
        chats=chats, 
        images=images, 
        names=names
    )

app.run(debug=True)