#!/usr/bin/env python

import json
import os.path
import re
from collections import OrderedDict
from datetime import datetime

import pytz
import requests
import spacy
from word2number import w2n

nlp = spacy.load("en_core_web_sm")

BEARER_TOKEN = os.environ["BEARER_TOKEN"]

# Fetch City dataset 
cities_json = open("resources/Indiacities_india_cities_database.json")
cities_data = json.loads(cities_json.read())

# Convert to a dictionary format to be able to search easily
CITIES_DICT = {x["ascii_name"].lower(): 0 for x in cities_data['results']}


def search_city_in_tweet(tweet):
    confusing_cities = ["nagar"]
    tweet_words = [x.lower() for x in tweet.split() if len(x) > 2]
    for tweet_word in tweet_words:
        try:
            temp = CITIES_DICT[tweet_word]
            if tweet_word in confusing_cities:
                continue
            return tweet_word
        except KeyError:
            pass


def remove_words_start_with(letters, tweet):
    words = tweet.split()
    word_result = words
    for word in words:
        for letter in letters:
            if word.startswith(letter):
                word_result.remove(word)
    return " ".join(word_result)


def extract_bed_count(tweet):
    bed_info = {}
    # print(tweet)
    icu_bed_patterns = ["icu beds:", "icu beds-", "icu beds -", "icu beds available:", "icu beds availabile",
                        "icu beds availability:",
                        "icu beds availability", "icu beds"]
    oxygen_bed_patterns = ["oxygen beds:", "oxygen beds-", "oxygen beds -", "oxygen beds available:",
                           "oxygen beds availabile", "oxygen beds availability:",
                           "oxygen beds availability", "oxygen beds"]

    generic_bed_patterns = ["beds:", "bed available:", "bed available", "beds available:", "beds available", "beds"]
    found = False
    for pattern in icu_bed_patterns:
        before_word, cur_word, after_word = tweet.partition(pattern)
        if not before_word or not after_word:
            continue
        try:
            bed_count = int(after_word.split()[0])
            bed_info["ICU"] = int(bed_count)
            found = True
            break
        except:
            try:
                bed_info["ICU"] = w2n.word_to_num(after_word.split()[0])
                found = True
            except:
                pass
        try:
            bed_count = int(before_word.split()[-1])
            bed_info["ICU"] = int(bed_count)
            found = True
            break
        except:
            try:
                bed_info["ICU"] = w2n.word_to_num(before_word.split()[-1])
                found = True
            except:
                pass

    for pattern in oxygen_bed_patterns:
        before_word, cur_word, after_word = tweet.partition(pattern)
        if not before_word or not after_word:
            continue
        try:
            bed_count = int(after_word.split()[0])
            bed_info["Oxygen Beds"] = int(bed_count)
            found = True
            break
        except:
            try:
                bed_info["Oxygen Beds"] = w2n.word_to_num(after_word.split()[0])
                found = True
            except:
                pass
        try:
            bed_count = int(before_word.split()[-1])
            bed_info["Oxygen Beds"] = int(bed_count)
            found = True
            break
        except:
            try:
                bed_info["Oygen Beds"] = w2n.word_to_num(before_word.split()[-1])
                found = True
            except:
                pass

    if found:
        # print(bed_info)
        return bed_info, True
    for pattern in generic_bed_patterns:
        before_word, cur_word, after_word = tweet.partition(pattern)
        if not before_word or not after_word:
            continue
        try:
            bed_count = int(after_word.split()[0])
            bed_info["COVID Beds"] = int(bed_count)
            found = True
            break
        except:
            try:
                bed_info["COVID Beds"] = w2n.word_to_num(after_word.split()[0])
                found = True
            except:
                pass
        try:
            bed_count = int(before_word.split()[-1])
            bed_info["COVID Beds"] = int(bed_count)
            found = True
            break
        except:
            try:
                bed_info["COVID Beds"] = w2n.word_to_num(before_word.split()[-1])
                found = True
            except:
                pass
    return bed_info, found


def fetch_relevant_tweets(data):
    ip_data = data
    relevant_tweets = []
    for tweet in ip_data["statuses"]:
        if "retweeted_status" in tweet.keys():
            text = tweet["retweeted_status"]["full_text"]
        else:
            text = tweet["full_text"]
        res_text = str.replace(text, "\n", " ")
        res_text = " ".join(filter(lambda x: x[0] != '#', res_text.split()))
        res_text = " ".join(filter(lambda x: x[0] != '@', res_text.split()))
        res_text = res_text.translate(str.maketrans(' ', ' ', ","))
        if res_text not in relevant_tweets:
            relevant_tweets.append(res_text)
    return relevant_tweets


def search_for_contact(tweet):
    match_num = re.findall(r'[6-9]\d{9}', tweet)
    if len(match_num) > 0:
        return match_num[0]


def run_api():
    # Run API to fetch tweets
    headers = {"Authorization": BEARER_TOKEN}
    relevant_tweets = []
    for city in cities_data["results"]:
        if city["name"] in ["Bengaluru", "Coimbatore", "Chennai", "Mumbai", "Kolkata", "Hyderabad", "Patna"]:
            latitude = city["latitude"]
            longitude = city["longitude"]
            url = "https://api.twitter.com/1.1/search/tweets.json?q=%23BedsAvailable&count=100&result_type=recent&tweet_mode=extended&lang=en&geocode={},{},200km".format(
                latitude, longitude)
            resp = requests.get(url, headers=headers)
            data = resp.json()
            relevant_tweets += fetch_relevant_tweets(data)

    return list(set(relevant_tweets))


def process_api_info(input_city_name=None, **query_args):
    relevant_tweets = run_api()
    tz_ist = pytz.timezone('Asia/Kolkata')
    current_datetime = datetime.now(tz_ist).strftime("%Y-%m-%d %H:%M:%S")
    results = []
    for tweet in relevant_tweets:
        doc = nlp(tweet)

        res_dict = OrderedDict({"COVID Beds": 0, "ICU": 0, "Name": "", "Last Update": current_datetime,
                                "Oxygen Beds": 0, "Sheet Name": "", "URL": ""})
        facility = ""
        phone_num = ""
        bed_info, bed_info_status = extract_bed_count(tweet.lower())
        if bed_info_status:
            res_dict.update(bed_info)
        for entity in doc.ents:
            if entity.label_ == "CARDINAL":
                try:
                    if len(entity.text) == 10:
                        if phone_num != "":
                            phone_num += ",{}".format(entity.text)
                        else:
                            phone_num = entity.text
                except:
                    pass
            if entity.label_ == "FAC" or entity.label_ == "ORG":
                if "oxygen" in entity.text.lower():
                    continue
                if facility == "":
                    facility = entity.text
                else:
                    facility += ",{}".format(entity.text)
        if phone_num == "":
            number_found = search_for_contact(tweet)
            if number_found:
                res_dict["Contact"] = number_found
        else:
            res_dict["Contact"] = phone_num
        if facility == "":
            continue
        res_dict["Name"] = facility
        city_name = search_city_in_tweet(tweet)
        if input_city_name:
            print("inside input city name")
            if city_name and city_name.lower() == input_city_name.lower():
                print("inside condition")
                res_dict["Sheet Name"] = city_name.title() + " Beds"
            else:
                continue
        else:
            if city_name:
                res_dict["Sheet Name"] = city_name.title() + " Beds"
            else:
                continue
        results.append(res_dict)
    #print(results)
    json_data = json.dumps(results, indent=4)
    return json_data
    #with open("../outputs/cowin_output.json", "w") as f:
    #    json_data = json.dumps(results, indent=4)
    #    f.write(json_data)