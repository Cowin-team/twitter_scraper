#!/usr/bin/env python

import datetime
import flask
import time
from api.scrape import process_api_info

CACHE_TIMEOUT = 600  # seconds to hold a cached result
CACHE_SIZE = 50  # Size of cache. Caution: Increases memory usage if increased

app = flask.Flask(__name__)

g = flask.g
ctx = app.app_context()
ctx.push()
g.datagetter = None

class Args(object):
    """
    Empty class for later attr setting
    """
    pass


class Cacher(object):
    """
    Simple cache implementation with timeout
    """

    def __init__(self, func, timeout):
        self.func = func
        self.result = None
        self.timestamp = int(time.time())
        self.timeout = timeout
        self.cached_results = {}

    def get(self, *args):
        delta = int(time.time()) - self.timestamp
        if self.result is not None and (delta < self.timeout):
            return self.result
        self.result = self.func(*args)
        self.timestamp = int(time.time())
        return self.result

    def get_with_params(self, *args, **kwargs):
        delta = int(time.time()) - self.timestamp
        fname = self.func.__name__
        if fname in self.cached_results and (delta < self.timeout):
            for cached_inputs in self.cached_results[fname]:
                if (args, kwargs) == cached_inputs["input"]:
                    return cached_inputs["result"]
        result = self.func(*args, **kwargs)
        self.timestamp = int(time.time())
        cached_input = {"input": (args, kwargs), "result": result}
        if fname not in self.cached_results:
            self.cached_results[fname] = [cached_input]
        else:
            self.cached_results[fname].append(cached_input)
        if len(self.cached_results[fname]) > CACHE_SIZE:
            self.cached_results[fname].pop(0)
        return result

def scrape_query_by_city(city_name):
    """
    Sample: http://127.0.0.1:5000/query/scrape/chennai
    :param city_name:
    :return:
    """
    if flask.request.query_string:
        query_str = flask.request.query_string.decode()
        query_args = {x.split("=")[0]: x.split("=")[1] for x in query_str.split("&&")}
    else:
        query_args = {}
    result_json = process_api_info(input_city_name=city_name, **query_args)
    return result_json


def scrape_query():
    """
    Sample: http://127.0.0.1:5000/query/scrape
    :return:
    """
    if flask.request.query_string:
        query_str = flask.request.query_string.decode()
        query_args = {x.split("=")[0]: x.split("=")[1] for x in query_str.split("&&")}
    else:
        query_args = {}
    result_json = process_api_info(**query_args)
    return result_json


cachers = {
    "scrape_query": Cacher(scrape_query, 300),
    "scrape_query_by_city": Cacher(scrape_query_by_city, 300)
}


@app.route('/query/scrape')
def cached_scrape_query():
    return cachers["scrape_query"].get()


@app.route('/query/scrape/<city_name>')
def cached_scrape_query_by_city(city_name):
    return cachers["scrape_query_by_city"].get_with_params(city_name)

