import yt_dlp
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image
import requests
from io import BytesIO
import time
import re


resolutions = []  # global list
thumbnail = None  # define thumbnail as a global variable


def abbreviate_number(number):
    if number >= 1000000000:
        return '{:.2f}{}'.format(number / 1000000000, 'B')
    elif number >= 1000000:
        return '{:.2f}{}'.format(number / 1000000, 'M')
    elif number >= 1000:
        return '{:.2f}{}'.format(number / 1000, 'K')
    else:
        return str(number)


def clear_entry():
    url_entry.delete(0, tk.END)  # delete url from input box
    menu = om['menu']  # get option menu menu
    menu.delete(0, 'end')  # delete previous option
    var.set("Quality")


def get_video():  # new function to get video info

    global resolutions, thumbnail, video_regex, playlist_regex  # global variables
    # regex to check if url is valid video
    video_regex = r"^(?:https?:\/\/)?(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-_]+)(&\S+)?$"
    # regex to check if url is a playlist
    playlist_regex = r"^.*(?:youtu.be\/|list=)([^#\&\?]*).*"
    URL = url_entry.get()
    video_match = re.match(video_regex, URL)  # match video url
    playlist_match = re.match(playlist_regex, URL)  # match playlist url
    # get the playlist id
    if playlist_match:
        playlist_id = URL.split('=')[1]
        # get the playlist info
        playlist = yt_dlp.YoutubeDL().extract_info(
            f'https://www.youtube.com/playlist?list={playlist_id}', download=False)

        # download and update the thumbnail image
        thumbnail_size = (200, 200)
        response = requests.get(playlist['entries'][0]['thumbnail'])
        img_data = response.content
        thumbnail = ImageTk.PhotoImage(Image.open(
            BytesIO(img_data)).resize(thumbnail_size))

        popup = tk.Toplevel(root)
        popup.title("Playlist Information")

        if thumbnail is not None:
            thumbnail_label = ttk.Label(popup, image=thumbnail)
            thumbnail_label.pack()

        title_label = ttk.Label(
            popup, text="Playlist Title: " + playlist['title'])
        length_label = ttk.Label(popup, text="Playlist length: " +
                                 str(len(playlist['entries'])))
        author_label = ttk.Label(
            popup, text="Channel Name: " + playlist['uploader'])
        views_label = ttk.Label(
            popup, text="Number of views: " + abbreviate_number(playlist['view_count']))

        title_label.pack()
        length_label.pack()
        author_label.pack()
        views_label.pack()

    elif video_match:
        with yt_dlp.YoutubeDL() as ydl:
            video = ydl.extract_info(URL, download=False)
            resolutions = []  # clear previous resolutions
            for stream in video['formats']:  # loop through each stream
                # check if the resolution is available
                if 'height' in stream and stream['height'] is not None and stream['height'] <= 1080:
                    # stream has 1080p resolution
                    # add the resolution to the list
                    resolutions.append(stream['format_note'])

        # download and update the thumbnail image
        thumbnail_size = (200, 200)
        response = requests.get(video['thumbnail'])
        img_data = response.content
        thumbnail = ImageTk.PhotoImage(Image.open(
            BytesIO(img_data)).resize(thumbnail_size))

        popup = tk.Toplevel(root)
        popup.title("Video Information")

        # display the thumbnail image if it exists
        if thumbnail is not None:
            thumbnail_label = ttk.Label(popup, image=thumbnail)
            thumbnail_label.pack()

        title_label = ttk.Label(popup, text="Video Title: " + video['title'])
        length_label = ttk.Label(popup, text="Video length: " +
                                 time.strftime("%H:%M:%S", time.gmtime(video['duration'])))
        author_label = ttk.Label(
            popup, text="Channel Name: " + video['uploader'])
        views_label = ttk.Label(
            popup, text="Number of views: " + abbreviate_number(video['view_count']))

        title_label.pack()
        length_label.pack()
        author_label.pack()
        views_label.pack()
        popup_button = ttk.Button(popup, text="OK", command=popup.destroy)
        popup_button.pack(pady=10)

        var.set("1080p")  # reset default value
        menu = om['menu']  # get option menu menu
        menu.delete(0, 'end')  # delete previous options
        for res in resolutions:  # loop through new resolutions
            menu.add_command(label=res, command=tk._setit(
                var, res))  # add new options


def download_video():
    # get the title of the video
    URL = url_entry.get()
    common_opts = {
        'extractor-args': 'youtube:player_client=android',
        'noplaylist': True,
    }

    ydl = yt_dlp.YoutubeDL(common_opts)
    title = ydl.extract_info(URL, download=False)['title']

    # replace invalid characters in the title
    title = "".join(x for x in title if x.isalnum() or x in [" ", "-", "_"])

    if playlist_regex:
        ydl = yt_dlp.YoutubeDL({
            **common_opts,
            'outtmpl': f'{title}%(playlist_index)s - %(title)s.%(ext)s',
        })

        resolution = var.get()  # get selected resolution from variable
        print(f"Downloading playlist with resolution {resolution}")

        with ydl:
            ydl.download([URL])

    elif video_regex:
        ydl = yt_dlp.YoutubeDL({
            **common_opts,
            'outtmpl': f'{title}.mp4',
            'noplaylist': False,
        })

        resolution = var.get()  # get selected resolution from variable
        print(f"Downloading video with resolution {resolution}")

        with ydl:
            stream = ydl.extract_info(URL, download=False)['formats'][0]
            for f in ydl.extract_info(URL, download=False)['formats']:
                if f['format_note'] == resolution:
                    stream = f
                    break

            filename = ydl.prepare_filename(stream)
            ydl.download([stream['url']])

    elif checkbox_var.get() == 'Yes':
        print("Downloading audio only")

        ydl = yt_dlp.YoutubeDL({
            **common_opts,
            'outtmpl': f'{title}.mp4',
            'format': 'bestaudio',
        })

        with ydl:
            ydl.extract_info(URL, download=True)

    print("Download complete!")

    # create a pop-up window to indicate that the download has finished
    popup = tk.Toplevel(root)
    popup.title("Download Complete")
    popup.geometry("200x100")
    popup_label = tk.Label(popup, text="The video has finished downloading!")
    popup_label.pack(pady=20)
    popup_button = ttk.Button(popup, text="OK", command=popup.destroy)
    popup_button.pack(pady=10)


root = tk.Tk()
style = ttk.Style()
style.theme_use("vista")
root.title("Youtube Video Downloader")
checkbox_var = tk.StringVar(value='No')  # Audio only checkbox variable
is_playlist_var = tk.StringVar(value='No')  # Playlist checkbox variable
# Creating a label for url entry
url_example = tk.Label(
    root, text="Example Single Video URL: https: //www.youtube.com/watch?v=fSjc8vLMg8c\nExample Playlist URL: "
               "https://www.youtube.com/playlist?list=PLRfY4Rc-GWzhdCvSPR7aTV0PJjjiSAGMs")
url_example.grid(row=0, column=0, columnspan=4)
# Enter youtube video url here
url_label = tk.Label(root, text="Enter url for youtube video:")
url_label.grid(row=1, column=0)

url_entry = ttk.Entry(root)
url_entry.grid(row=1, column=1)
# Retrieve video info
get_button = ttk.Button(root, text="Get Video Info", command=get_video)
get_button.grid(row=1, column=2)

var = tk.StringVar(root)
var.set("Quality")

om = ttk.OptionMenu(root, var, "Quality")
om.grid(row=2, column=0)

download_button = ttk.Button(
    root, text="Download Video", command=download_video)
download_button.grid(row=2, column=1)
# Clear input
clear_button = ttk.Button(root, text="Clear Input", command=clear_entry)
clear_button.grid(row=2, column=2)

audio_only_checkbox = ttk.Checkbutton(
    root, text="Download only Audio", variable=checkbox_var, onvalue="Yes", offvalue="No")
audio_only_checkbox.grid(row=3, columnspan=4)

root.mainloop()
