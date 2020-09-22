"""
Module to check performance of various json Libraries

    Running the checker:
        python json_checker

    Output:

        Metris for Json Descriptor
        ---------------------------
        Library=json, Calls/sec=174637.95, Totsecs=5.7261
        Library=simplejson, Calls/sec=258163.15, Totsecs=3.8735
        Library=orjson, Calls/sec=331984.88, Totsecs=3.0122
        Library=rapidjson, Calls/sec=293092.15, Totsecs=3.4119
        Library=ujson, Calls/sec=320544.06, Totsecs=3.1197

        ---------------------------
        Metris for Json decode
        ---------------------------
        Library=json, Calls/sec=10147947.02, Totsecs=0.9854
        Library=simplejson, Calls/sec=10614215.27, Totsecs=0.9421
        Library=orjson, Calls/sec=10880575.33, Totsecs=0.9191
        Library=rapidjson, Calls/sec=9631618.67, Totsecs=1.0382
        Library=ujson, Calls/sec=10224613.19, Totsecs=0.978

        ---------------------------
        Metris for Json encode
        ---------------------------
        Library=json, Calls/sec=10156937.33, Totsecs=0.9845
        Library=simplejson, Calls/sec=10601908.1, Totsecs=0.9432
        Library=orjson, Calls/sec=10982923.24, Totsecs=0.9105
        Library=rapidjson, Calls/sec=10612736.89, Totsecs=0.9423
        Library=ujson, Calls/sec=8416063.72, Totsecs=1.1882

"""

import cProfile
import io
import json as pyjson
import os
import pstats
import timeit

import orjson
import rapidjson
import simplejson
import ujson


def get_json_node(json_data, item, strict=True):
    # The config can be a dot separated value in its heirarchy. Split it by
    config_pieces = item.split(".")

    def get_from_config(pieces, config, start):
        if config is None:
            if strict:
                # If strict mode is enabled raise Attribute error if config is not found
                raise AttributeError
            return

        if len(pieces) == 1:
            try:
                return config[pieces[0]]
            except KeyError:
                if strict:
                    raise AttributeError
                else:
                    return None

        start += 1
        return get_from_config(config_pieces[start:], config.get(pieces[0]), start)

    config_value = get_from_config(config_pieces, json_data, start=0)

    return config_value


class Descriptor:
    def __init__(self, path, *args, **kwargs):
        self.path = path  # Json Path

    def __get__(self, instance, item):
        if instance is None:
            return self

        json_data_str = instance.json_data
        if json_data_str:
            try:
                return get_json_node(json.loads(json_data_str), self.path)
            except json.JSONDecodeError:
                raise


class CustomerModel:
    name = Descriptor("cus.name")
    address = Descriptor("cus.address")


class LeadModel:
    source = Descriptor("lead.source")


class Data(CustomerModel, LeadModel):

    def __init__(self, json_file):
        with open(json_file) as f:
            self.json_data = f.read()


def time_it(func):
    def inner(*args, **kwargs):
        func_name = func.__name__
        t = timeit.Timer(lambda: func(*args, **kwargs), globals=globals())
        number = 100000
        secs = t.timeit(number)
        print("Library={}, Calls/sec={}, Totsecs={}".format(args[0].__name__, round(number / secs, 2), round(secs, 4)))

    return inner


@time_it
def benchmark(json_module):
    global json
    json = json_module
    data = Data(os.path.join("json_checker", "data.json"))
    consolidated = f"{data.name}"


def profile():
    for json_module in (json,):
        print(f"Stats for {json_module} \n")
        profile = cProfile.Profile()
        profile.enable()
        benchmark(json_module)
        profile.disable()
        s = io.StringIO()
        ps = pstats.Stats(profile, stream=s).sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats()
        print(s.getvalue())


def metrics_json_as_descriptor():
    print("Metris for Json Descriptor")
    print("---------------------------")
    for json_module in (pyjson, simplejson, orjson, rapidjson, ujson):
        global json
        json = json_module
        benchmark(json_module)


def metrics_json_decode(number):
    print("\n---------------------------")
    print("Metris for Json decode")
    print("---------------------------")
    with open(os.path.join("json_checker", "data.json")) as f:
        data = f.read()
    for json_module in (pyjson, simplejson, orjson, rapidjson, ujson):
        secs = timeit.timeit(lambda: json_module.loads(data), number=number)
        print("Library={}, Calls/sec={}, Totsecs={}".format(json_module.__name__, round(number / secs, 2), round(secs, 4)))


def metrics_json_encode(number, large_dict):
    print("\n---------------------------")
    print("Metris for Json encode")
    print("---------------------------")
    for json_module in (pyjson, simplejson, orjson, rapidjson, ujson):
        secs = timeit.timeit(lambda: json_module.dumps(large_dict), number=number)
        print("Library={}, Calls/sec={}, Totsecs={}".format(json_module.__name__, round(number / secs, 2), round(secs, 4)))


def main():
    large_dict = {str(i): str(i) for i in range(10000)}
    number = 100000
    metrics_json_as_descriptor()
    # metrics_json_decode(number)
    # metrics_json_encode(number, large_dict)

    
if __name__ == "__main__":
    main()
