# Resident Advisor Podcasts Downloader
Automatically download all the Resident Advisor Podcast episodes in their original quality.

Uses Python3 requests and BeautifulSoup4.

## Usage
1. Clone this repository

2. Install dependencies with ```pip install requirements.txt```

3.  Run the script with ```python dowloader.py```.
You can specify the folder where to save downloaded podcasts with the flag ```--downloads_dir``` and the max number of concurrent threads with ```--max_threads```.

## How it works
On Resident Advisor's webpage only the latest 4 episodes can be downloaded in mp3 in their original quality. Previous episodes can only be streamed from Soundcloud.

However, most episodes are still hosted in Resident Advisor's servers and can be accessed if we know their url. 

By looking at the latest podcasts urls, they follow the format

```
http://audio.ra.co/podcast/RA{PODCAST_NUMBER}_{YYMMDD}_{ARTIST}-residentadvisor.net.mp3
```

In Python, this url can be easily constructed with:

```python

MP3_TEMPLATE_URL = "http://audio.ra.co/podcast/RA{}_{}_{}-residentadvisor.net.mp3"

title = soup.select("#sectionHead > h1:nth-child(2)")[0].text  

# number and artist
matches = re.search(r"^RA\.([0-9]+) (.*)$", title)
podcast_num = int(matches.group(1))
podcast_artist = matches.group(2)
podcast_artist = unidecode.unidecode(podcast_artist.strip().replace(".", "").replace(" ", "-"))

# date
date_str = soup.select("ul.clearfix > li:nth-child(1)")[0].text.split("/")[1]
date = datetime.datetime.strptime(date_str, "%d %b %Y")
podcast_date = date.strftime("%y%m%d")

# build link
mp3_urls = [MP3_TEMPLATE_URL.format(podcast_num, podcast_date, podcast_artist)]
```

This way, I managed to download most episodes all the way back to RA500 (approx. 20 GB)