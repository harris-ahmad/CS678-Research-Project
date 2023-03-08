from selenium import webdriver  # For controlling the browser
from selenium.webdriver.common.keys import Keys  # For sending keys to the browser
# For setting up chrome options
from selenium.webdriver.chrome.options import Options
# For finding elements such as buttons, links, etc.
from selenium.webdriver.common.by import By
# For installing the chrome driver
from webdriver_manager.chrome import ChromeDriverManager
# For eliminating deprication warnings
from selenium.webdriver.chrome.service import Service as ChromeService
import time  # For waiting
import os
import json  # For parsing the logs
import colorlog  # For logging
import logging  # For logging
from typing import List, Tuple, Dict  # For type hinting
from pathlib import Path
import orjson


class Measurement:
    def __init__(self, video_list):
        # Set up chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--start-maximized")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.set_capability(
            "loggingPrefs", {'performance': 'ALL'})

        # Set up chrome service to eliminate deprication warnings from the script
        self.chrome_service = ChromeDriverManager(
            version='110.0.5481.77',  name='chromedriver', os_type='linux64', path=os.getcwd()).install()

        self.chrome_service = ChromeService(
            executable_path=self.chrome_service)

        # Set up chrome driver
        self.driver = webdriver.Chrome(
            service=self.chrome_service, options=self.chrome_options)

        # Set up logger for debugging
        self.logger = colorlog.getLogger()
        self.logger.setLevel(logging.DEBUG)

        self.videos_to_stream: List[str] = []
        self.ad_buffer: List[str] = []

        self.current_ad_id: str = ""
        self.add_skippable: List[str] = []
        self.all_numbers: List[int] = []

        # fill this with the video ids of the videos you want to stream before running the script
        self.list_of_videos: List[str] = video_list

        self.mobile_emulation = {
            "deviceMetrics": {"width": 360, "height": 640, "pixelRatio": 3.0},
            "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19",
        }

        self.latencyInMilliseconds = 5
        self.downloadLimitMbps = 9
        self.uploadLimitMbps = 9

        self.TIME_TO_SLEEP: int = int(2 // self.downloadLimitMbps)

        self.error_list = []
        self.auto_play_toggle: bool = True

    def enable_stats_for_nerds(self):
        '''
        This function enables the stats for nerds option in the youtube settings
        '''
        # Open the youtube settings
        self.driver.find_element(
            by=By.XPATH, value="/html/body/ytm-app/ytm-mobile-topbar-renderer/header/div/ytm-menu/button").click()
        self.logger.info("Opened the youtube settings")
        # Click on the Playback settings
        self.driver.find_element(
            by=By.XPATH, value="/html/body/div[2]/div/ytm-menu-item[3]/button")
        self.logger.info("Opened the playback settings")

        try:
            # Click on the stats for nerds option
            self.driver.find_element(
                by=By.XPATH, value="/html/body/div[2]/dialog/div[2]/ytm-menu-item[2]/button").click()
            self.logger.info("Clicked on the stats for nerds option")
        except:
            try:
                # In case the stats for nerds option is not available, click on the stats for nerds option using javascript
                self.driver.execute_script(
                    "document.getElementsByClassName('menu-item-button')[1].click()"
                )
                self.logger.info(
                    "Clicked on the stats for nerds option using javascript")
            except Exception as e:
                self.logger.error(e)
        # Click on the close button to exit the dialog
        self.driver.find_element(
            by=By.XPATH, value="/html/body/div[2]/dialog/div[3]/c3-material-button/button").click()

        self.logger.info("Stats for nerds enabled")

    def start_video(self):
        self.logger.info("Started the video")
        player_state: int = self.driver.execute_script(
            "return document.getElementById('movie_player').getPlayerState()"
        )
        self.logger.info(f'Player State: {player_state}')

        if player_state == 1:
            self.logger.info("Video is already playing")
            return
        elif player_state == 2:
            self.logger.info("Video is paused")
            self.driver.execute_script(
                "document.getElementById('movie_player').playVideo()"
            )
            self.logger.info("Video is playing now")
        elif player_state == 5:
            self.logger.info("Video is cued")
            self.driver.execute_script(
                "document.getElementsByClassName('ytp-large-play-button ytp-button')[0].click()"
            )
            self.logger.info("Video is playing now")
        else:
            self.logger.info("Video is not playing")
            self.driver.execute_script(
                "document.getElementsByClassName('ytp-large-play-button ytp-button')[0].click()"
            )
            self.logger.info("Video is playing now")

    def start_video_if_paused(self):
        self.logger.info("Started the video")
        player_state: int = self.driver.execute_script(
            "return document.getElementById('movie_player').getPlayerState()"
        )
        self.logger.info(f'Player State: {player_state}')

        if player_state == 1:
            self.logger.info("Video is already playing")
            return
        elif player_state == 0:
            self.logger.info("Video is ended")
            return
        elif player_state == 2:
            self.logger.info("Video is paused")
            self.driver.execute_script(
                "document.getElementById('movie_player').playVideo()"
            )
            self.logger.info("Video is playing now")
        elif player_state == -1:
            self.driver.execute_script(
                "document.getElementsByClassName('video-stream html5-main-video')[0].play()"
            )
        else:
            self.logger.info("Video is not playing")
            self.driver.execute_script(
                "document.getElementsByClassName('video-stream html5-main-video')[0].play()"
            )
            self.logger.info("Video is playing now")

    def get_ad_buffer(self, video_id: str):
        all_numbers: List[int] = []
        ad_buffer_list: List[Tuple[float, float, str]] = []
        ad_skippable: List[int] = []
        ad_id: str = ""
        ad_played: float = 0.0
        ad_playing: int = self.driver.execute_script(
            "return document.getElementsByClassName('ad-showing').length"
        )

        while ad_playing:
            ad_buffer: float = float(self.driver.execute_script(
                "return document.getElementsByClassName('ad-showing')[0].getElementsByClassName('ytp-ad-skip-button ytp-button')[0].innerText"
            ))
            resolution: str = str(self.driver.execute_script(
                'return document.getElementsByClassName("html5-video-info-panel-content")[0].children[2].children[1].textContent.replace(" ","").split("/")[0]'
            )).split("x")[0]

            current_time_retry = 0
            # loop until the current time of the video is fetched
            while current_time_retry < 10:
                try:
                    # capturing the current running time of the advertisement playing
                    ad_played = float(
                        self.driver.execute_script(
                            "return document.getElementsByClassName('video-stream html5-main-video')[0].currentTime"
                        )
                    )
                    # if the current time is fetched, break the loop
                    if ad_played:
                        break
                except:
                    # increment the looping variable and try again
                    current_time_retry += 1

            try:
                # feth the ad id using the following JS code
                ad_id_temp: str = self.driver.execute_script(
                    'return document.getElementsByClassName("html5-video-info-panel-content")[0].children[0].children[1].textContent.replace(" ","").split("/")[0]'
                )
                # if the ad id is not equal to the id passed to the function
                if str(ad_id_temp).strip() != str(video_id).strip():
                    # set the ad it equal to the ad id fetched in the above JS code (right before the current if statement)
                    ad_id = ad_id_temp
            except:
                pass

            try:
                # fetch the skip duration of the ad if the ad is skippable
                skip_duration: str = str(self.driver.execute_script(
                    'return document.getElementsByClassName("ytp-ad-text ytp-ad-preview-text")[0].innerText'
                ))
                # convert the skip duration into an integer by doing the necessary string manipulation
                numba = int(skip_duration.split(" ")[-1])
                all_numbers.append(numba)
            except:
                # simply append -2 if there is an error fetching the skip duration for the current ad being played
                all_numbers.append(-2)

            ad_played_in_seconds = ad_played
            # append the ad buffer, ad played and resolution to the ad_buffer_list
            ad_buffer_list.append(
                (ad_buffer, ad_played_in_seconds, resolution))
            # after extracting all the relevant information, it checks if the ad is still playing or not and updates the
            # looping variable
            ad_playing: int = self.driver.execute_script(
                "return document.getElementsByClassName('ad-showing').length"
            )
            # this returns a boolean representing whether the ad is skippable or not
            skippable: int = int(self.driver.execute_script(
                "return document.getElementsByClassName('ytp-ad-skip-button-container').length"
            ))
            # if the ad is skippable, append the value to the ad_skippable list
            ad_skippable.append(skippable)
            # call this function if the ad is not playing or it has stopped due to some reason
            self.start_video_if_paused()

        skippable = self.most_frequent(ad_skippable)
        # this captures the skip duration at various instances and returns the max of this list
        # this was observed to be 5 seconds for every run
        skip_dur = max(all_numbers)
        return ad_id, skippable, ad_buffer_list, skip_dur

    def most_frequent(self, list: List[int]):
        '''
        This function takes a list of integers and returns the count of the most frequent integer in the list
        '''
        return max(set(list), key=list.count)

    def get_video_duration(self):
        '''
        This function returns the duration of the video
        '''
        video_duration = self.driver.execute_script(
            'return document.getElementById("movie_player").getDuration()'
        )
        return video_duration

    def run(self):
        for index, url in enumerate(self.list_of_videos):
            global error_log
            video_info_details = {}
            ad_buffer_information = {}
            error_log = []
            unique_ad_count: int = 0
            ad_just_played: bool = False
            buffer_list = []
            actual_buffer_reads = []
            buffer_size_with_ad = []
            video_res_per_second = []
            main_resolution_all = []
            previous_ad_id: str = url.split("=")[1]
            movie_id: str = url.split("=")[1]
            new_dir = "./" + str(index+1)

            try:
                self.driver.get(url)
                self.logger.info(f"Clicked on video {index+1}")
                time.sleep(2)
                retry: int = 0
                while retry < 5:
                    try:
                        self.enable_stats_for_nerds()
                        break
                    except:
                        retry += 1
                self.start_video()
                self.logger.info(f"Video is playing now: {url}")
                time.sleep(self.TIME_TO_SLEEP)
                ad_playing = self.driver.execute_script(
                    "return document.getElementsByClassName('ad-showing').length"
                )
                if ad_playing:
                    self.logger.info("Ad is playing at the start of the video")

                    ad_id, skippable, ad_buffer_details, skip_duration = self.get_ad_buffer(
                        video_id=movie_id)

                    if not skippable:
                        self.logger.info(
                            "Ad is not skippable. Setting the skip duration to 999")
                        skip_duration = 999

                    self.logger.info(
                        f"Ad id: {ad_id}, Skippable: {skippable}, Skip duration: {skip_duration}")

                    unique_ad_count += 1

                    video_info_details[ad_id] = {
                        "count": 1,
                        "skippable": skippable,
                        "skip_duration": skip_duration
                    }

                    buffer_size_with_ad.append(
                        # setting the buffer size to 0.0 for the first ad because it is not possible to calculate the buffer size for the first ad
                        [ad_id, 0.0, 0.0]
                    )

                    previous_ad_id = ad_id

                    ad_buffer_information[ad_id] = {
                        "buffer": ad_buffer_details
                    }

                    self.logger.info(
                        f'Advertisement {unique_ad_count} Data Collected')

                video_dur_in_seconds: int = self.get_video_duration()

                Path(new_dir).mkdir(parents=False, exist_ok=True)

                video_playing: int = int(self.driver.execute_script(
                    "return document.getElementById('movie_player').getPlayerState()"
                ))

                ad_playing: float = float(self.driver.execute_script(
                    "return document.getElementsByClassName('ad-showing').length"
                ))

                if not self.auto_play_toggle:
                    try:
                        # fetching the classname of the autoplay button on YouTube's player and turning it off
                        self.driver.execute_script(
                            "document.getElementsByClassName('ytm-autonav-toggle-button-container')[0].click()"
                        )
                        self.auto_play_toggle = True
                    except Exception as e:
                        self.logger.error(
                            f"Error while turning off autoplay: {e}")

                # turning off volume
                try:
                    self.driver.execute_script(
                        "document.getElementsByClassName('video-stream html5-main-video')[0].volume=0"
                    )
                except Exception as e:
                    self.logger.error(f"Error while turning off volume: {e}")

                while True:
                    self.start_video_if_paused()

                    video_playing = self.driver.execute_script(
                        "return document.getElementById('movie_player').getPlayerState()"
                    )
                    # checking if the ad is playing or not
                    ad_playing = self.driver.execute_script(
                        "return document.getElementsByClassName('ad-showing').length"
                    )
                    # getting the duration of the video played in seconds
                    video_played_in_seconds = self.driver.execute_script(
                        'return document.getElementById("movie_player").getCurrentTime()'
                    )

                    if ad_playing:
                        ad_just_played = True
                        ad_id, skippable, ad_buffer_details, skip_duration = self.get_ad_buffer(
                            video_id=movie_id)

                        if not skippable:
                            self.logger.info(
                                "Ad is not skippable. Setting the skip duration to 999")
                            skip_duration = 999

                        self.logger.info(
                            f"Ad id: {ad_id}, Skippable: {skippable}, Skip duration: {skip_duration}")

                        if str(ad_id).strip() != str(movie_id).strip():
                            if ad_id != previous_ad_id:
                                self.logger.info(f'New Ad id: {ad_id}')

                                previous_ad_id = ad_id

                                if len(actual_buffer_reads) >= 1:
                                    buffer_size_with_ad.append(
                                        [
                                            ad_id,
                                            actual_buffer_reads[-1],
                                            video_played_in_seconds
                                        ]
                                    )
                                else:
                                    buffer_size_with_ad.append(
                                        [
                                            ad_id,
                                            0.0,
                                            video_played_in_seconds
                                        ]
                                    )

                                if ad_id not in video_info_details.keys():
                                    unique_ad_count += 1
                                    video_info_details[ad_id] = {
                                        "count": 1,
                                        "skippable": skippable,
                                        "skip_duration": skip_duration
                                    }

                                    ad_buffer_information[ad_id] = {
                                        "buffer": ad_buffer_details
                                    }

                                    self.logger.info(
                                        f'Advertisement {unique_ad_count} Data Collected')
                                else:
                                    current_value = video_info_details[ad_id]['count']
                                    video_info_details[ad_id]['count'] = current_value + 1
                                    name = f'{ad_id}_{video_info_details[ad_id]["count"]}'
                                    ad_buffer_information[name] = {
                                        "buffer": ad_buffer_details
                                    }
                                    self.logger.warning(
                                        f'Repeated Ad id: {ad_id}')
                    elif video_playing == 0:
                        # Video has ended
                        # this text file stores generic detauls regarding the main video
                        file_dir: str = f'{new_dir}/stream_details.txt"'
                        # this file stores the details regarding the buffer captured at every second
                        file_dir_two = f'{new_dir}/buffer_details.txt'
                        # this text file stores the details of any errors that may have occured during
                        # the data collection run of a given video
                        file_dir_three = f'{new_dir}/error_details.txt'
                        # this file saves details regarding the buffer captured of the advertisement
                        file_dir_five = f'{new_dir}/ad_buffer_details.txt'
                        file_dir_six = f'{new_dir}/ad_info_details.txt'
                        # fetching the resolution of the main video
                        Main_res = max(main_resolution_all,
                                       key=main_resolution_all.count)
                        # storing the captured information regarding the main video in the
                        # video_info_details dictionary
                        video_info_details["Main_Video"] = {
                            "Url": url,
                            "Total Duration": video_dur_in_seconds,
                            "UniqueAds": unique_ad_count,
                            "Resolution": Main_res,
                        }

                        with open(file_dir, "wb+") as f:
                            f.write(orjson.dumps(video_info_details))

                        with open(file_dir_two, "wb+") as f:
                            f.write(orjson.dumps(actual_buffer_reads))

                        with open(file_dir_three, "wb+") as f:
                            f.write(orjson.dumps(self.error_list))

                        with open(file_dir_five, "wb+") as f:
                            f.write(orjson.dumps(buffer_size_with_ad))

                        with open(file_dir_six, "wb+") as f:
                            f.write(orjson.dumps(ad_buffer_information))

                        video_info_details.clear()
                        unique_ad_count = 0

                        self.logger.info('Video Ended')
                        break
                    else:
                        # Video is playing normally
                        # Record Resolution at each second
                        resolution = self.driver.execute_script(
                            'return document.getElementsByClassName("html5-video-info-panel-content")[0].children[2].children[1].textContent.replace(" ","").split("/")[0]'
                        )
                        # creating a tuple with the resolution at a given second and the time (in seconds) at which the
                        # resolution is captured at
                        new_data_point = (resolution, video_played_in_seconds)
                        # appending the data point to the main list
                        main_resolution_all.append(resolution)
                        # appending the video resolution datapoint to the relevant data structure
                        video_res_per_second.append(new_data_point)

                        # Get Current Buffer of the main video using Selenium and JS
                        current_buffer = float(
                            self.driver.execute_script(
                                'return document.getElementsByClassName("html5-video-info-panel-content")[0].children[10].children[1].textContent.split(" ")[1]'
                            )
                        )
                        # Actual Buffer
                        # [ID,Last Buffer Before Ad, How much video played when ad played, Buffer after ad finished]
                        if ad_just_played:
                            for i in range(len(buffer_size_with_ad)):
                                if len(buffer_size_with_ad[i]) <= 2:
                                    buffer_size_with_ad[i].append(
                                        current_buffer)

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
                                / (video_dur_in_seconds - video_played_in_seconds)
                            )
                        except:
                            # if an error during collection, set the buffer_ratio to 0 (reset)
                            buffer_ratio = 0

                        buffer_list.append(buffer_ratio)
                        previous_ad_id = url.split("=")[1]
            except Exception as e:
                self.logger.error(f'Error: {e}')
                self.error_list.append(e)
                with open("faultyVideos.txt", "a") as f:
                    to_write = str(url) + "\n"
                    f.write(to_write)
                continue

    def stop(self):
        self.driver.quit()


if __name__ == "__main__":
    list_of_urls: List[str] = []  # fill this up
    mt = Measurement(list_of_urls)
    mt.run()
    mt.stop()
