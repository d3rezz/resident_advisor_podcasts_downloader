import requests
import os
from bs4 import BeautifulSoup
import datetime
import re
import unidecode
from urllib.parse import urlparse
from multiprocessing.pool import ThreadPool


DOWNLOADS_DIR = "downloads/"

PODCASTS_LIST_DIR = "https://www.residentadvisor.net/podcast.aspx"
PODCASTS_BASE_DIR = "https://www.residentadvisor.net"
MP3_TEMPLATE_LINK = "http://audio.ra.co/podcast/RA{}_{}_{}-residentadvisor.net.mp3"


# Check if url points to downloadable media (only checks header)
def check_downloadable_file(url):
    h = requests.head(url, allow_redirects=True)
    header = h.headers
    content_type = header.get('content-type')
    if 'text' in content_type.lower():
        return False
    if 'html' in content_type.lower():
        return False
    return True


# Get link to mp3 in page. Each page can have several links i.e. RA500
def get_mp3_links(url):
    r = requests.get(url, allow_redirects=True)
    data = r.text
    soup = BeautifulSoup(data, features="html5lib")


    # find mp3 links in page
    mp3_links = soup.findAll('a', href=re.compile("\.mp3$"))     #bs4 supports regex
    mp3_links = [a["href"] for a in mp3_links]

    # if link to mp3 is no longer available, try to build link
    if len(mp3_links)==0:
        title = soup.select("#sectionHead > h1:nth-child(2)")[0].text        
        matches = re.search(r"^RA\.([0-9]+) (.*)$", title)
        podcast_num = int(matches.group(1))
        podcast_artist = matches.group(2)
        podcast_artist = unidecode.unidecode(podcast_artist.strip().replace(".", "").replace(" ", "-"))

        # date
        date_str = soup.select("ul.clearfix > li:nth-child(1)")[0].text.split("/")[1]
        date = datetime.datetime.strptime(date_str, "%d %b %Y")    #28 Dec 2015
        podcast_date = date.strftime("%y%m%d")  #151228
    
        # build link
        mp3_links = [MP3_TEMPLATE_LINK.format(podcast_num, podcast_date, podcast_artist)]
   
    return mp3_links


# Download file in chunks
def download_file(url, path):
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(path, 'wb') as f:
            for chunk in r:
                f.write(chunk)
    return path


if __name__=="__main__":


    print("Getting list of RA Podcasts...")
    r = requests.get(PODCASTS_LIST_DIR, allow_redirects=True)
    data = r.text
    soup = BeautifulSoup(data, features="html5lib")

    # Links in the top of the RA Podcasts page
    podcast_links = soup.select(".music-border > li:nth-child(1) > section:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > ul:nth-child(1) > li > article:nth-child(1) > a:nth-child(1)")
    podcast_links = [a['href'] for a in podcast_links]

    # Links in the list in bottom of RA Podcasts page
    podcast_links2 = soup.select("html body#body form#Form1 main ul.content-list.music-border li.alt section.content.clearfix div.plus8 div.col2.fl:first-child div.pr8 div.col2 ul.list li.ptb2 article a")
    podcast_links2 = [a['href'] for a in podcast_links2]

    podcast_links = podcast_links+podcast_links2

    print("There are {} RA Podcasts.".format(len(podcast_links)))

    print("Checking which mp3 links are valid... (might take a few minutes)")
    if not os.path.exists(DOWNLOADS_DIR):
        os.makedirs(DOWNLOADS_DIR)


    valid_links = []
    for link in podcast_links:
        full_link = PODCASTS_BASE_DIR + link

        mp3_links = get_mp3_links(full_link)
        
        for link in mp3_links:
            # Check if mp3 is downloadable
            if check_downloadable_file(link):
                valid_links.append(link)
            
    print("{} mp3 links are still valid.".format(len(valid_links)))      

    # Download from valid links
    # Get filename
    for link in valid_links:
        mp3_filename = os.path.basename(urlparse(link).path)

        # Check if already downloaded
        if os.path.exists(os.path.join(DOWNLOADS_DIR, mp3_filename)):
            print("{} already downloaded, skipping.".format(mp3_filename))
            continue

        # Download
        print("Downloading", mp3_filename)
        download_file(link, os.path.join(DOWNLOADS_DIR, mp3_filename))
    
    print("Finished downloading podcasts.")













