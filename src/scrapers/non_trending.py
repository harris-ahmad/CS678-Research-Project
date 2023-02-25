'''
Problems in this script:
1. We cannot get the video category list for specific countries whose data we want to use.
   Examples of non-supported countries are: PK (Pakistan), IN (India), AUS (Australia), VN (Vietnam), Japan (JP).
   Examples of supported countries are: US (United States), UK (United Kingdom), ZA (South Africa), Singapore (SG). 
'''

# for accessing the YouTube Data API
from googleapiclient.discovery import build
import random  # for randomizing the category id

# Set up the YouTube Data API client
API_KEY = "AIzaSyBB2yybtEmSZ_sq2Ri74uOW4fETYX2thjA"
youtube = build("youtube", "v3", developerKey=API_KEY)


def get_video_categories():
    '''
    This function returns a list of video categories for a specific country.
    '''
    categories = []
    request = youtube.videoCategories().list(
        part='snippet',
        regionCode='US'
    )
    response = request.execute()
    for item in response['items']:
        categories.append(item['id'])
    return categories


def get_nontrending_videos():
    '''
    This function returns a list of trending videos for a specific country.
    '''
    categories = get_video_categories()
    category_id = random.choice(categories)
    request = youtube.videos().list(
        part='snippet',
        # chart='mostPopular',  # excluding this would mean we want to get non trending videos
        maxResults=5,
        videoCategoryId=category_id
    )
    response = request.execute()
    videos = []
    for item in response['items']:
        video = {
            'title': item['snippet']['title'],
            'channel': item['snippet']['channelTitle'],
            'url': f'<https://www.youtube.com/watch?v={item["id"]}>'
        }
        videos.append(video)
    return videos


def main():
    '''
    This function prints the title, channel, and URL of trending videos.
    '''
    videos = get_nontrending_videos()
    for video in videos:
        print(f'Title: {video["title"]}')
        print(f'Channel: {video["channel"]}')
        print(f'URL: {video["url"]}')


if __name__ == '__main__':
    main()
