import time
import warnings
import orjson
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pathlib import Path
from collections import Counter

# code to for emulating YouTube mobile on broswer (google chrome)
# this gives us access to the https://m.youtube.com/
mobile_emulation = {
    "deviceMetrics": {"width": 360, "height": 640, "pixelRatio": 3.0},
    "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19",
}

# constant variables for network throttling
latencyInMilliseconds = 5
downloadLimitMbps = 9
uploadLimitMbps = 9

# this constant stores the time the script will be sleeping when
# a call to time.sleep is made - usage is later in the script
TIME_TO_SLEEP = float(2 / downloadLimitMbps)

# to ignore any browser-specific Deprecation Warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
# chrome instances for all main video URLs were spawned without
# the headless option being True
chrome_options.headless = False
# this list stores errors (of several types) reported by the script
error_list = []
# this toggles the auto-play button off
auto_play_toggle = False


def most_frequent(List):
    '''
    This function takes a list and returns count of the most occuring
    element
    '''
    occurence_count = Counter(List)
    return occurence_count.most_common(1)[0][0]


def to_seconds(timestr: str):
    '''
    This function takes a timestamp and splits it by ':'
    and returns the seconds stored in it by doing the necessary conversions
    ,i.e., converting minutes into seconds and returning the cumulative total
    '''
    seconds = 0
    for part in timestr.split(":"):
        # converting minutes into seconds and adding it to the
        # cumulative total
        seconds = seconds * 60 + int(part, 10)
    # returning the number of seconds
    return seconds


def enable_stats_for_nerds(driver: webdriver.Chrome):
    # finding the settings button on YouTube's video player
    settings = driver.find_element_by_xpath(
        "/html/body/ytm-app/ytm-mobile-topbar-renderer/header/div/ytm-menu/button"
    )
    # clicking the settings button
    settings.click()

    # locating the "Playback Settings" option on the pop-up
    playback_settings = driver.find_element_by_xpath(
        "/html/body/div[2]/div/ytm-menu-item[3]/button"
    )

    # clicking on it
    playback_settings.click()

    try:
        # locating the stats for nerds option using the generated xml path
        stats_for_nerds = driver.find_element_by_xpath(
            "/html/body/div[2]/dialog/div[2]/ytm-menu-item[2]/button"
        )
        # clicking on it
        stats_for_nerds.click()
    except:
        # if there is an error generated using xml
        try:
            # execute this javascript code that finds the stats for nerds option
            # using classnames, and clicks on it
            stats_for_nerds = driver.execute_script(
                "document.getElementsByClassName('menu-item-button')[1].click()"
            )
        except Exception as e:
            # catching the exception if any
            raise e

    # exiting the settings option to view the stats for nerds option clearly
    exit_dialog = driver.find_element_by_xpath(
        "/html/body/div[2]/dialog/div[3]/c3-material-button/button"
    )
    # clicking on the exit dialog
    exit_dialog.click()


def start_playing_video(driver: webdriver.Chrome):
    # fetching the state of the player by executing the JS code in the chrome browser
    player_state = driver.execute_script(
        "return document.getElementById('movie_player').getPlayerState()"
    )
    # printing the player state for confirmation
    print("Player State: ", player_state)
    # if the video is queued, and isnt playing, then click on the large play button on the video player
    # and click on it so the video starts playing
    if player_state == 5:
        driver.execute_script(
            "document.getElementsByClassName('ytp-large-play-button ytp-button')[0].click()"
        )
    # if the video has started playing
    if player_state == 1:
        # return from the function since it is already playing
        return


def play_video_if_not_playing(driver: webdriver.Chrome):
    # fetch the player state using the same JS code in the web browser's console
    player_state = driver.execute_script(
        "return document.getElementById('movie_player').getPlayerState()"
    )
    # if the player state is 0 meaning the video has ended, simply return
    if player_state == 0:
        return
    # if the video has not started yet, then locate the relevant HTML5-embedded class
    if player_state == -1:
        # execute the script
        driver.execute_script(
            "document.getElementsByClassName('video-stream html5-main-video')[0].play()"
        )
    # if any other state except for 1 (player state 1 implies the video is already playing)
    if player_state != 1:
        # locate the embedded class names using JS and play the video
        driver.execute_script(
            "document.getElementsByClassName('video-stream html5-main-video')[0].play()"
        )


def record_ad_buffer(driver: webdriver.Chrome, movie_id):
    # this function keeps track of the ad buffer recorded every second the ad video progresses
    ad_buffer_list = []
    # this captures a singaling value whether the ad is playing or not
    ad_playing = driver.execute_script(
        "return document.getElementsByClassName('ad-showing').length"
    )
    # this string stores the id of the ad stored in the URL of the ad id
    ad_id = ""
    ad_skippable = []
    # stores the skip duration of the ads
    all_numbers = []
    # while the ad is playing
    while ad_playing:
        # get the ad buffer in seconds and convert it into a floating point value
        ad_buffer = float(
            driver.execute_script(
                'return document.getElementsByClassName("html5-video-info-panel-content")[0].children[10].children[1].textContent.split(" ")[1]'
            )
        )
        # capture the resolution on which the ad is playing
        res = driver.execute_script(
            'return document.getElementsByClassName("html5-video-info-panel-content")[0].children[2].children[1].textContent.replace(" ","").split("/")[0]'
        )
        # this looping variable keeps on incrementing until the current time the ad has played so far is fetched
        current_time_retry = 0
        while current_time_retry < 10:
            try:
                # capturing the current running time of the advertisement playing
                ad_played = float(
                    driver.execute_script(
                        "return document.getElementsByClassName('video-stream html5-main-video')[0].currentTime"
                    )
                )
                # break from the while loop if the time has been fetched
                break
            except:
                # increment the looping variable and try again
                current_time_retry += 1

        try:
            # feth the ad id using the following JS code
            ad_id_temp = driver.execute_script(
                'return document.getElementsByClassName("html5-video-info-panel-content")[0].children[0].children[1].textContent.replace(" ","").split("/")[0]'
            )
            # if the ad id is not equal to the id passed to the function
            if str(ad_id_temp).strip() != str(movie_id).strip():
                # set the ad it equal to the ad id fetched in the above JS code (right before the current if statement)
                ad_id = ad_id_temp
        except:
            pass

        try:
            # fetch the skip duration of the ad if the ad is skippable
            skip_duration = driver.execute_script(
                'return document.getElementsByClassName("ytp-ad-text ytp-ad-preview-text")[0].innerText'
            )
            # convert the skip duration into an integer by doing the necessary string manipulation
            numba = int(skip_duration.split(" ")[-1])
            all_numbers.append(numba)
        except:
            # simply append -2 if there is an error fetching the skip duration for the current ad being played
            all_numbers.append(-2)

        ad_played_in_seconds = ad_played
        ad_buffer_list.append((ad_buffer, ad_played_in_seconds, res))
        # after extracting all the relevant information, it checks if the ad is still playing or not and updates the
        # looping variable
        ad_playing = driver.execute_script(
            "return document.getElementsByClassName('ad-showing').length"
        )
        # this returns a boolean representing whether the ad is skippable or not
        skippable = int(driver.execute_script(
            "return document.getElementsByClassName('ytp-ad-skip-button-container').length"
        ))
        # if the ad is skippable, append the value to the ad_skippable list
        ad_skippable.append(skippable)
        # call this function if the ad is not playing or it has stopped due to some reason
        play_video_if_not_playing(driver)

    skippable = most_frequent(ad_skippable)
    # this captures the skip duration at various instances and returns the max of this list
    # this was observed to be 5 seconds for every run
    skip_dur = max(all_numbers)
    return ad_id, skippable, ad_buffer_list, skip_dur


def driver_code(driver: webdriver.Chrome):
    # this list comprises of the URLs that were scraped off of the trending
    # pages using the webscraper.py file
    list_of_urls = [
        # "https://www.youtube.com/watch?v=ec1vg-gv9Dk",
        # 'https://www.youtube.com/watch?v=0OCUjgwOua8',
        # 'https://www.youtube.com/watch?v=8ogj6nRLhNg',
        # 'https://www.youtube.com/watch?v=5T4QIbOe7Vw',
        # 'https://www.youtube.com/watch?v=XX7fJZBZtoE',
        # 'https://www.youtube.com/watch?v=gsop4R3-Ci8',
    ]
    # iterating over the enumerated list of urls
    for index, url in enumerate(list_of_urls):
        global error_list
        global auto_play_toggle
        # this dictionary stores the information related to the video being played
        video_info_details = {}
        # this dictionary stores all the necessary information related to the advertisement's buffer
        ad_buffer_information = {}
        # this keeps track of all the errors that arose during the data collection
        error_list = []
        # this variable keeps a count of all the unique ads (both in-stream skippable and non-skippable)
        # that were displayed during the interval the main video was being played
        unique_ad_count = 0
        # boolean that flags to true if an ad recently started playing between the video -- mid-roll ads
        ad_just_played = False
        # this stores all information related to the main video's buffer
        buffer_list = []
        actual_buffer_reads = []
        buffer_size_with_ad = []
        # this list stores the resolution of the video being played at each second
        vid_res_at_each_second = []
        main_res_all = []
        # id of the recently streamed ads
        previous_ad_id = url.split("=")[1]
        # id of the main video streamed
        movie_id = url.split("=")[1]
        # name of the directory in which all the files related to a video are stored
        new_dir = "./" + str(index + 24)

        try:
            # visiting the main video's URL using Selenium's .get() method
            driver.get(url)
            # Enable Stats
            time.sleep(2)
            retry_count = 0
            # this loop keeps incrementing until stats for nerds
            # has been toggled on successfully.
            while retry_count < 5:
                try:
                    enable_stats_for_nerds(driver)
                    break
                except:
                    retry_count += 1

            # Start Playing the main video
            start_playing_video(driver)

            # Check If ad played at start
            time.sleep(TIME_TO_SLEEP)
            # this variable stores a numeral that confirms if an ad is currently playing
            ad_playing = driver.execute_script(
                "return document.getElementsByClassName('ad-showing').length"
            )
            print("Playing Video: ", movie_id)
            # if an ad is playing at the start of the video
            if ad_playing:
                # print a confirmation message on the terminal
                print("ad at start of video!")
                # get all buffer-related information by calling the record_ad_buffer function
                # navigate to the definition of the function for self-explanatory comments
                # on the working methodologies of the function
                ad_id, skippable, ad_buf_details, skip_duration = record_ad_buffer(
                    driver, movie_id)
                # to keep things static and homogenous, set the skip duration equal to 999 in the event
                # the ad is non-skippable
                if not (skippable):
                    skip_duration = 999

                # printing the buffer information fetched to the console screen for authenticity
                print(
                    "Ad ID: ",
                    ad_id,
                    "Skippable? ",
                    skippable,
                    " Skip Duration: ",
                    skip_duration,
                )
                # incrementing the unique_ad_count by 1
                unique_ad_count += 1
                # storing the scraped information regarding the ad into the video_info_details dictionary
                # that will be later written to a text file (used in analysis part of the study)
                video_info_details[ad_id] = {
                    # this key represents the count of the ad
                    "Count": 1,
                    "Skippable": skippable,
                    "SkipDuration": skip_duration,
                }
                # at the start of the ad, the buffer of the main video will be 0 (none has been downloaded
                # since the video has not progressed)
                buffer_size_with_ad.append(
                    # Start of video. Main Buffer will be 0s.
                    [ad_id, 0.0, 0.0]
                )
                previous_ad_id = ad_id
                # storing the buffer details of the advertisement
                to_write = {"buffer": ad_buf_details}
                ad_buffer_information[ad_id] = to_write
                # printing a confirmation message to the terminal implying that all data related to
                # the given ad has been collected
                print("Advertisement " + str(unique_ad_count) + " Data collected.")
            # fetching the duration of the main video
            video_duration_in_seconds = driver.execute_script(
                'return document.getElementById("movie_player").getDuration()'
            )
            # if the video duration is greater than 3600 seconds
            if video_duration_in_seconds >= 3600:
                # video_info_details dictionary is reset
                video_info_details = {}
                print(
                    video_duration_in_seconds,
                    " Seconds. Video Skipped for being too Long!",
                )
                # move to the next video in the list
                continue
            # making the directory in which we will be saving all our files
            Path(new_dir).mkdir(parents=False, exist_ok=True)

            # fetching the player state of YouTube and storing in the the variable
            # this confirms if the video is playing or not
            video_playing = driver.execute_script(
                "return document.getElementById('movie_player').getPlayerState()"
            )
            # this checks if the ad is still playing or not
            ad_playing = driver.execute_script(
                "return document.getElementsByClassName('ad-showing').length"
            )
            # Turning off Autoplay
            if not auto_play_toggle:
                try:
                    # fetching the classname of the autoplay button on YouTube's player and turning it off
                    driver.execute_script(
                        "document.getElementsByClassName('ytm-autonav-toggle-button-container')[0].click()"
                    )
                    # updating the status of the variable to True
                    auto_play_toggle = True
                except:
                    pass

            # Turning off Volume -- not related to data collection (was done entirely for convenience).
            try:
                driver.execute_script(
                    "document.getElementsByClassName('video-stream html5-main-video')[0].volume=0"
                )
            except:
                pass

            # loop infinitely to collect information of the main video
            while True:
                # play the video if not curretly playing
                play_video_if_not_playing(driver)
                # fetching YouTube player's state
                video_playing = driver.execute_script(
                    "return document.getElementById('movie_player').getPlayerState()"
                )
                # checking if the ad is playing or not
                ad_playing = driver.execute_script(
                    "return document.getElementsByClassName('ad-showing').length"
                )
                # getting the duration of the video played in seconds
                video_played_in_seconds = driver.execute_script(
                    'return document.getElementById("movie_player").getCurrentTime()'
                )
                # if the ad is playing -- mid-roll ad
                if ad_playing:
                    # ad_just_played gets updated to True
                    ad_just_played = True
                    print("Ad Playing")
                    # fetch all buffer-related information regarding ad being played currently
                    ad_id, skippable, ad_buf_details, skip_duration = record_ad_buffer(
                        driver, movie_id
                    )
                    # if the ad is not skippable
                    if not (skippable):
                        # set the skip_duration to a sentinel value
                        skip_duration = 999

                    print(
                        "Ad ID: ",
                        ad_id,
                        "Skippable? ",
                        skippable,
                        " Skip Duration: ",
                        skip_duration,
                    )
                    # if the ad id is not the same as the movie id fetched earlier
                    if (str(ad_id).strip()) != (str(movie_id).strip()):
                        # if the ad is not equal to the recent-most ad played
                        if ad_id != previous_ad_id:
                            print("Ad id is: ", ad_id)
                            # update the previous_ad_id to the id of the new ad
                            previous_ad_id = ad_id

                            # Appends the last recorded main_video_buffer when ad was played.
                            if len(actual_buffer_reads) >= 1:
                                buffer_size_with_ad.append(
                                    [
                                        ad_id,
                                        actual_buffer_reads[-1],
                                        video_played_in_seconds,
                                    ]
                                )  # Append last buffer value to keep track.
                            else:
                                # a buffer value of 0.0 signifies that the ad was at the start
                                buffer_size_with_ad.append(
                                    [ad_id, 0.0, video_played_in_seconds]
                                )  # Ad was at the start.

                            # Ads video information to document.
                            # this if statement checks if the ad being played is a unique ad or not
                            # i.e., it is present in the video_info_details list. if already present,
                            # this implies the ad is not unique
                            if ad_id not in video_info_details.keys():
                                # if the ad is unique, increment the unique_ad_count
                                unique_ad_count += 1
                                # store the details of the ad in the video_info_details dictionary
                                video_info_details[ad_id] = {
                                    "Count": 1,
                                    "Skippable": skippable,
                                    "SkipDuration": skip_duration,
                                }
                                # store the details of the ad buffer in the dictionary
                                to_write = {
                                    "buffer": ad_buf_details,
                                }
                                # save the buffer-details with the relevant ad's id
                                ad_buffer_information[ad_id] = to_write
                                # print a confirmation message to the terminal highlighting
                                # that all information regarding the current ad has been
                                # collected
                                print(
                                    "Advertisement "
                                    + str(unique_ad_count)
                                    + " Data collected."
                                )
                            else:
                                # if the ad is not unique
                                # get the count of the ad using the ad_id as a key -- same ad
                                # being displayed more than once in the main video
                                current_value = video_info_details[ad_id]["Count"]
                                # increment the count of the ad
                                video_info_details[ad_id]["Count"] = current_value + 1
                                # create a new formatted name with the ad id along with its
                                # count appended
                                name = (
                                    ad_id
                                    + "_"
                                    + str(video_info_details[ad_id]["Count"])
                                )
                                # buffer details of the current ad
                                to_write = {
                                    "buffer": ad_buf_details,
                                }
                                # appending to the relevant maintained data structure
                                ad_buffer_information[name] = to_write
                                print("Repeated Ad! Information Added!")
                # all data regarding all ads and the main video has been collected
                # now is the time to write all gathered data to the relevant text files
                elif video_playing == 0:
                    # Video has ended
                    # this text file stores generic detauls regarding the main video
                    file_dir = new_dir + "/stream_details.txt"
                    # this file stores the details regarding the buffer captured at every second
                    file_dir_two = new_dir + "/buffer_details.txt"
                    # this text file stores the details of any errors that may have occured during
                    # the data collection run of a given video
                    file_dir_three = new_dir + "/error_details.txt"
                    # this file saves details regarding the buffer captured of the advertisement
                    file_dir_five = new_dir + "/BufferAdvert.txt"
                    file_dir_six = new_dir + "/AdvertBufferState.txt"
                    # fetching the resolution of the main video
                    Main_res = max(main_res_all, key=main_res_all.count)
                    # storing the captured information regarding the main video in the
                    # video_info_details dictionary
                    video_info_details["Main_Video"] = {
                        "Url": url,
                        "Total Duration": video_duration_in_seconds,
                        "UniqueAds": unique_ad_count,
                        "Resolution": Main_res,
                    }
                    # writing data to the respective files
                    # using orjson instead of json since it is vectorized
                    # and helps in faster writing to the files
                    with open(file_dir, "wb+") as f:
                        f.write(orjson.dumps(video_info_details))

                    with open(file_dir_two, "wb+") as f:
                        f.write(orjson.dumps(actual_buffer_reads))

                    with open(file_dir_three, "wb+") as f:
                        f.write(orjson.dumps(error_list))

                    with open(file_dir_five, "wb+") as f:
                        f.write(orjson.dumps(buffer_size_with_ad))

                    with open(file_dir_six, "wb+") as f:
                        f.write(orjson.dumps(ad_buffer_information))
                    # video info details set to empty and now the loop is ready for the next iteration
                    video_info_details = {}
                    unique_ad_count = 0
                    # printing a confirmation message to the terminal
                    print("Video Finished and details written to files!")
                    break
                else:
                    # Video is playing normally
                    # Record Resolution at each second
                    res = driver.execute_script(
                        'return document.getElementsByClassName("html5-video-info-panel-content")[0].children[2].children[1].textContent.replace(" ","").split("/")[0]'
                    )
                    # creating a tuple with the resolution at a given second and the time (in seconds) at which the
                    # resolution is captured at
                    new_data_point = (res, video_played_in_seconds)
                    # appending the data point to the main list
                    main_res_all.append(res)
                    # appending the video resolution datapoint to the relevant data structure
                    vid_res_at_each_second.append(new_data_point)

                    # Get Current Buffer of the main video using Selenium and JS
                    current_buffer = float(
                        driver.execute_script(
                            'return document.getElementsByClassName("html5-video-info-panel-content")[0].children[10].children[1].textContent.split(" ")[1]'
                        )
                    )
                    # Actual Buffer
                    # [ID,Last Buffer Before Ad, How much video played when ad played, Buffer after ad finished]
                    if ad_just_played:
                        for i in range(len(buffer_size_with_ad)):
                            if len(buffer_size_with_ad[i]) <= 2:
                                buffer_size_with_ad[i].append(current_buffer)

                        ad_just_played = False

                    # Tuple (Buffer, Video Played in seconds timestamp)
                    actual_buffer_reads.append(
                        (current_buffer, video_played_in_seconds))
                    # Current Buffer/(Video Left)
                    try:
                        # get the ratio of the total buffer collected so far to the video left to stream
                        # in seconds
                        buffer_ratio = float(
                            current_buffer
                            / (video_duration_in_seconds - video_played_in_seconds)
                        )
                    except:
                        # if an error during collection, set the buffer_ratio to 0 (reset)
                        buffer_ratio = 0

                    buffer_list.append(buffer_ratio)
                    previous_ad_id = url.split("=")[1]
        except Exception as e:
            # if an error occurs because of a corrupted Video URL
            # print the error to the terminal
            print(e)
            print("Error occured while collecting data! Moving to next video!")
            print("Video: ", url)
            # store the faulty url to the designated text files
            with open("faultyVideos.txt", "a") as f:
                to_write = str(url) + "\n"
                f.write(to_write)
            # continue to the next url in list_of_urls maintained
            continue


# DRIVER CODE
if __name__ == '__main__':
    # creating an instance of chrome driver
    driver = webdriver.Chrome(options=chrome_options)
    # throttling the network by setting all manual conditions
    driver.set_network_conditions(
        offline=False,
        latency=latencyInMilliseconds,
        download_throughput=downloadLimitMbps * 125000,  # Mbps to bytes per second
        upload_throughput=uploadLimitMbps * 125000,  # Mbps to bytes per second
    )
    # quitting the driver once done
    driver_code(driver)
    driver.quit()
