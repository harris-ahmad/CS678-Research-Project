'''
Connect to your designated developing country using Linux terminal's NordVPN client and run the script. 
Script Usage (in the context of our study):
-------------------------------------------
This script naviagtes to the mentioned links in the links_to_scrape_from (line 25) list iteratively
and scrapes off all YouTube video URLs (excluding YouTube shorts) present on the current trending page 
and writes them to a text file.

Note: This script is the unedited version of the script used in the study. It is not optimized for
        reusability and is only meant to be used for the purpose of the study.
'''

from selenium import webdriver
import time
import warnings
from bs4 import BeautifulSoup as BS
import time
import random

# preliminary code to ignore any browser-specific deprication warnings that might result
# due to Automated Testing services like Selenium
warnings.filterwarnings("ignore", category=DeprecationWarning)
# initializing chrome's webdriver instance
options = webdriver.ChromeOptions()
# spawning a chrome instance without headless for manual verification - whether all links
# are being visited correctly (as per the script)
options.headless = False

# this speeds up the optimization by stopping the images from loading
options.add_argument('--blank-settings=imagesEnabled=false')
options.add_experimental_option("excludeSwitches", ["enable-logging"])

# list of urls from where the list scrapes all the URLs
links_to_scrape_from = [
    # Now
    "https://www.youtube.com/feed/trending",
    # Music
    "https://www.youtube.com/feed/trending?bp=4gINGgt5dG1hX2NoYXJ0cw%3D%3D",
    # Gaming
    "https://www.youtube.com/feed/trending?bp=4gIcGhpnYW1pbmdfY29ycHVzX21vc3RfcG9wdWxhcg%3D%3D",
    # Movies
    "https://www.youtube.com/feed/trending?bp=4gIKGgh0cmFpbGVycw%3D%3D",
]


def scrapeFromLink(driver: webdriver.Chrome, url: str):
    # using selenium's .get() method to visit the url (from the
    # links_to_scrape_from list) passed to the function.
    driver.get(url)
    sleep_time = 10
    print(f'-- sleeping for {sleep_time} seconds --')
    # sleeping for 10 seconds to let the broswer load all it's underlying
    # HTML5 elements.
    time.sleep(sleep_time)
    # this list stores python dictionaries with keys title and url
    # storing the title and url of the main video respectively
    data: list = []
    # initiating a BeautifulSoup object and passing in the source of our page
    soup = BS(driver.page_source, features="lxml")
    # list of all anchor tags and their relevant html5 objects
    trending_videos: list = soup.find_all('a', id='video-title')
    # visiting every anchor tag and fetching the title of the video and it's
    # corresponding URL from the href attribute
    for vid in trending_videos:
        # storing the fetched information in the form of a JSON (python dictionary).
        data.append({'title': vid['title'], 'url': vid['href']})

    time.sleep(2)

    final_data = []
    # looping over all dictionaries stored in the list
    for vid in data:
        # if the url of the video contains the phrase "/shorts"
        if vid['url'][0:7] == '/shorts':
            # skip the current url
            continue
        # if the url is a regular (not-a-short) video
        temp_url = vid['url']
        # create a formatted url
        temp = f'https://www.youtube.com{temp_url}'
        # save the title of the video along with the formatted URL
        final_data.append({"title": vid['title'], "url": temp})

    # list that contains URLs of videos less than 3600 seconds
    videos_not_so_long = []
    # list with videos longer than 3600 seconds
    long_videos = []

    # iterating over all videos in the final_data list
    for vid in final_data:
        url = vid['url']
        # visiting every url of the main video using Selenium's .get() method
        driver.get(url)
        # fetching the duration of the main video
        video_duration = driver.execute_script(
            'return document.getElementById("movie_player").getDuration()'
        )
        # if the duration exceeds 3600 seconds
        if video_duration >= 3600:
            print(f'Video {url} skipped for being too long!')
            # store the video in the long_videos list
            long_videos.append(url)
            # keep iterating
            continue
        # if less than 3600 seconds, append in the usable list
        videos_not_so_long.append(url)

    return videos_not_so_long, long_videos


def removeDuplicates(lst: list):
    '''
    This function takes a list and removes any duplicate values
    it contains.
    '''
    # converting the list passed as an argument to the dict.fromkeys()
    # that removes any duplicate elements from the list.
    to_return = list(dict.fromkeys(lst))
    # returning the list (with only unique elements)
    return to_return


def writeToFile(filename: str, urls: list):
    '''
    This function takes the name of the file in which we are 
    writing our final list of the main video URLs using Python's
    file reading and writing mechanisms.
    urls: list is a list of all the final urls that we have used in the
    data collection part of the study.
    '''
    print(f'-- WRITING TO {filename} --')
    with open(filename, 'w+') as f:
        # looping over all the urls
        for url in urls:
            # writing the url to the text file using .write() method
            f.write(f"'{url}',\n")


def main(driver: webdriver.Chrome):
    '''
    This function is the main handler that is responsible for calling
    the above functions on the provided urls and maintain a systematic flow.
    '''
    # links of all the trending pages (Now, Music, Gaming & Movies)
    # from where the main video URLs are scraped
    links_to_scrape_from = [
        # Now
        "https://www.youtube.com/feed/trending",
        # Music
        "https://www.youtube.com/feed/trending?bp=4gINGgt5dG1hX2NoYXJ0cw%3D%3D",
        # Gaming
        "https://www.youtube.com/feed/trending?bp=4gIcGhpnYW1pbmdfY29ycHVzX21vc3RfcG9wdWxhcg%3D%3D",
        # Movies
        "https://www.youtube.com/feed/trending?bp=4gIKGgh0cmFpbGVycw%3D%3D",
    ]

    print('-- NOW TRENDING --')
    # scraping urls from the "Now" trending page
    now_trending, _ = scrapeFromLink(
        driver, links_to_scrape_from[0])

    print('-- MUSIC ONLY --')
    # scraping urls from the "Music" trending page
    music_trending, _ = scrapeFromLink(
        driver, links_to_scrape_from[1])

    print('-- GAMING ONLY --')
    # scraping URLs from the Gaming trending page
    gaming_trending, _ = scrapeFromLink(
        driver, links_to_scrape_from[2])

    print('-- MOVIES ONLY--')
    # scraping URLs from the movies trending page
    movies_trending, _ = scrapeFromLink(
        driver, links_to_scrape_from[3])

    # maintaing separate text files for all four categories
    # calling removeDuplicates function to remove duplicate main video
    # URLs from every list
    music_trending = removeDuplicates(music_trending)
    gaming_trending = removeDuplicates(gaming_trending)
    movies_trending = removeDuplicates(movies_trending)
    now_trending = removeDuplicates(now_trending)

    # skipped videos
    # writing separate text files for every category of
    # the trending page
    writeToFile('music_only.txt', music_trending)
    writeToFile('gaming_only.txt', gaming_trending)
    writeToFile('films_only.txt', movies_trending)
    writeToFile('general_urls.txt', now_trending)

    # take a random sample of 15 videos from every category adding up to a total of
    # 60 videos in total
    temp_list = random.sample(music_trending, 15) + random.sample(gaming_trending, 15) + \
        random.sample(movies_trending, 15) + random.sample(now_trending, 15)

    # removing duplicate URLs from the final list
    temp_list = removeDuplicates(temp_list)
    # shuffling the final list to remove any imbalance in the
    # data
    random.shuffle(temp_list)
    final_list = temp_list
    # these are the URLs that will be used in the final (second) phase of data collection
    writeToFile('usable.txt', final_list)


# Drive code
if __name__ == '__main__':
    # creating a webdriver instance from Google Chrome
    driver = webdriver.Chrome(
        executable_path="./chromedriver", options=options)
    main(driver)
    # once everything has been done, close the driver's instance
    driver.quit()
    print('-- all videos have been scraped :)) --')
