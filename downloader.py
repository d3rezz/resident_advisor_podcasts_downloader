""" RA Podcast Downloader

Examples:
    Download all podcast episodes:
    $ python downloader.py

    Limit the number of concurrent threads and set which folder to save downloads to:
    $ python downloader.py --max_threads=8 --downloads_dir=path/to/ra_downloads/
"""


import requests
import os
from bs4 import BeautifulSoup
import datetime
import re
import unidecode
from urllib.parse import urlparse
from multiprocessing.pool import ThreadPool
import functools
import argparse

DEFAULT_DOWNLOADS_DIR = "downloads/"
PODCASTS_LIST_DIR = "https://www.residentadvisor.net/podcast.aspx"
PODCASTS_BASE_DIR = "https://www.residentadvisor.net"
MP3_TEMPLATE_URL = "http://audio.ra.co/podcast/RA{}_{}_{}-residentadvisor.net.mp3"


# Check if url points to downloadable media (only checks header)
def check_downloadable_file(url):
    try:
        h = requests.head(url, allow_redirects=True)
    except requests.exceptions.RequestException:
        # print("Connection error while checking if file is downloadable", url)
        return False
    
    header = h.headers
    content_type = header.get('content-type')
    
    if 'text' in content_type.lower():
        return False
    if 'html' in content_type.lower():
        return False
    return True


# Get url to mp3 in page. Each page can have several links i.e. RA500
def get_mp3_urls(url):
    try:
        r = requests.get(url, allow_redirects=True)
    except requests.exceptions.RequestException:
        return []

    data = r.text
    soup = BeautifulSoup(data, features="html5lib")

    # find mp3 urls in page
    mp3_urls = soup.findAll('a', href=re.compile("\.mp3$"))     #bs4 supports regex
    mp3_urls = [a["href"] for a in mp3_urls]

    # if link to mp3 is no longer shown, try to build link
    if len(mp3_urls)==0:
        title = soup.select("#sectionHead > h1:nth-child(2)")[0].text        
        
        # number and artist
        matches = re.search(r"^RA\.([0-9]+) (.*)$", title)
        podcast_num = int(matches.group(1))
        podcast_artist = matches.group(2)
        podcast_artist = unidecode.unidecode(podcast_artist.strip().replace(".", "").replace(" ", "-"))

        # date
        date_str = soup.select("ul.clearfix > li:nth-child(1)")[0].text.split("/")[1]
        date = datetime.datetime.strptime(date_str, "%d %b %Y")    #28 Dec 2015
        podcast_date = date.strftime("%y%m%d")  #151228
    
        # build link
        mp3_urls = [MP3_TEMPLATE_URL.format(podcast_num, podcast_date, podcast_artist)]
   
    return mp3_urls


# Download file in chunks
def download_file(url, path):
    try:
        r = requests.get(url, stream=True)
    except requests.exceptions.RequestException:
        return False

    if r.status_code == 200:
        with open(path, 'wb') as f:
            for chunk in r:
                f.write(chunk)
        return True
    
    return False


# Download podcast episode in url to output_dir
def check_and_download_podcast(url, output_dir):
    full_url = PODCASTS_BASE_DIR + url
    mp3_urls = get_mp3_urls(full_url)

    for url in mp3_urls:
        # Get filename
        mp3_filename = os.path.basename(urlparse(url).path)

        # Check if mp3 is downloadable
        if not check_downloadable_file(url):
            print("Can't download", mp3_filename)
            continue

        # Check if already downloaded
        if os.path.exists(os.path.join(output_dir, mp3_filename)):
            print("Skiping {} (already downloaded)".format(mp3_filename))
            continue

        # Download
        print("Downloading", mp3_filename)
        download_file(url, os.path.join(output_dir, mp3_filename))
    

if __name__=="__main__":

    parser = argparse.ArgumentParser(description="RA Podcast Downloader")
    parser.add_argument('--max_threads', type=int, default=4, help='Max number of concorrent threads')
    parser.add_argument('--downloads_dir', type=str, default=DEFAULT_DOWNLOADS_DIR, help='Directory where to save downloaded podcasts')
    args = parser.parse_args()

    print("Getting list of RA Podcasts...")
    try:
        r = requests.get(PODCASTS_LIST_DIR, allow_redirects=True)
    except requests.exceptions.RequestException:
        print("Connection error while getting list of RA Podcasts.")
        exit()

    data = r.text
    soup = BeautifulSoup(data, features="html5lib")

    # Urls in the top of the RA Podcasts page
    podcast_urls = soup.select(".music-border > li:nth-child(1) > section:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > ul:nth-child(1) > li > article:nth-child(1) > a:nth-child(1)")
    podcast_urls = [a['href'] for a in podcast_urls]

    # Urls in the list in bottom of RA Podcasts page
    podcast_urls2 = soup.select("html body#body form#Form1 main ul.content-list.music-border li.alt section.content.clearfix div.plus8 div.col2.fl:first-child div.pr8 div.col2 ul.list li.ptb2 article a")
    podcast_urls2 = [a['href'] for a in podcast_urls2]

    podcast_urls = podcast_urls+podcast_urls2

    print("There are {} RA Podcasts.".format(len(podcast_urls)))

    print("Saving downloaded podcasts to", args.downloads_dir)    
    if not os.path.exists(args.downloads_dir):
        os.makedirs(args.downloads_dir)

    pool = ThreadPool(args.max_threads)
    pool.map(functools.partial(check_and_download_podcast, output_dir=args.downloads_dir), podcast_urls )
   
    print("Finished downloading podcasts.")













