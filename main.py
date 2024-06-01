from download import download
from torrentool.api import Torrent
import requests
import os
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import re
from bs4 import BeautifulSoup
import urllib.parse

# Telegram bot to download files from the internet on the server


def telegram_bot_token():
    try:
        with open("telegram.token", "r") as token:
            return token.read().strip()
    except FileNotFoundError:
        print("File telegram.token not found")

telegram_token = telegram_bot_token()


def download_file(update, context):
    print("/download called", context.args)
    
    file_ending = context.args[0].split(".")[-1]
    
    if len(context.args) ==0 or len(context.args) > 2:
        return update.message.reply_text("Usage: /download <url> <optional: file_name>")
    else:
        url = context.args[0]
        
        if len(context.args) == 2:
            file_name = context.args[1]
            if file_ending not in file_name:
                file_name += "." + file_ending
        else:
            file_name = url.split("/")[-1]
            
        
        url_regex = r"^(https?|ftp)://[^\s/$.?#].[^\s]*$"
        magnet_url = r"^magnet:\?xt=urn:btih:[0-9a-fA-F]{40,}.*$"
        
        if not re.match(url_regex, url) and not re.match(magnet_url, url):
            return update.message.reply_text("Invalid URL")
        
        if re.match(magnet_url, url):
            try:
                torrent = Torrent.from_string(str(url).strip())
                file_name = torrent.name + ".torrent"
            except Exception as e:
                print(e)
                return update.message.reply_text("Invalid magnet URL: " + str(e))
            
            torrent.download(destination="C:\\tmp\\" + file_name)
            return update.message.reply_text("Torrent downloaded as " + file_name)
        try:
            download(url, "C:\\tmp\\" + file_name)
            
        except Exception as e:
            print(e)
            return update.message.reply_text("Invalid URL")
        
        return update.message.reply_text("File downloaded as " + file_name)


def downlaod_media_from_website(update, context):
    if len(context.args) != 1:
        return update.message.reply_text("Usage: /download_website <url>")
    
    website_url = context.args[0]
    
    r = requests.get(website_url)
    try:
        website_name = website_url[website_url.find("//")+2:].split("/")[0]
        website_name_readable = urllib.parse.unquote(website_url[website_url.find("//")+2:].replace("/", "_"))
        
        banned_windows_chars = ["<", ">", ":", "\"", "/", "\\", "|", "?", "*"]
        
        for char in banned_windows_chars:
            website_name_readable = website_name_readable.replace(char, "_")
        
        if os.path.exists("C:\\tmp\\" + website_name_readable):
            i = 0
            while True:
                i += 1
                if os.path.exists("C:\\tmp\\" + website_name_readable + "_" + str(i)):
                    continue
                else:
                    website_name_readable = website_name_readable + "_" + str(i)
                    break
        os.mkdir("C:\\tmp\\" + website_name_readable)
        
        if r.status_code != 200:
            return update.message.reply_text("Invalid URL " + r.status_code)
        
        image_links = []
        video_links = []
        
        
        for link in BeautifulSoup(r.text, "html.parser").find_all("img"):
            if "src" in link.attrs:
                image_links.append(link.attrs["src"])
                
        
        for link in BeautifulSoup(r.text, "html.parser").find_all("video"):
            if "src" in link.attrs:
                video_links.append(link.attrs["src"])
        
        
        
        all_links = image_links + video_links
        
        print(len(all_links))
        
        
        for link in all_links:
            download_link = "https:" + link if link.startswith("//") else link
            download_link = website_url + link if download_link.startswith("/") else download_link
            file_name = link.split("/")[-1]
            
            if file_name.split(".")[-1] not in ["jpg", "png", "jpeg", "mp4", "webm"]:
                continue
            
            for char in banned_windows_chars:
                file_name = file_name.replace(char, "_")
            
            try:
                download(download_link, "C:\\tmp\\" + website_name_readable + "\\" + file_name)
                print("Downloaded " + link)
            except:
                print("Failed to download " + download_link)
                continue
    except Exception as e:
        print(e)
        return update.message.reply_text("Invalid: " + str(e))


def print_usage(update, context):
    help_str = "Welcome to MixoMax's Telegram download bot\n\nto download a file or magnet use /download <url> <optional: file_name>\n\nto download all media from a website use /download_website <url>"
    
    return update.message.reply_text(help_str)
    


def main():
    application = Application.builder().token(telegram_token).build()
    
    application.add_handler(CommandHandler("download", download_file))
    application.add_handler(CommandHandler("download_website", downlaod_media_from_website))
    application.add_handler(CommandHandler("help", print_usage))
    application.run_polling()

if __name__ == "__main__":
    main()