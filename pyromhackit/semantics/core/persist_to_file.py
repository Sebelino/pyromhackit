import json


def persist_to_file(path: str):
    def decorator(original_func):
        try:
            with open(path, 'r') as f:
                cache = json.load(f)
        except (IOError, ValueError) as e:
            cache = dict()

        def new_func(cache_param: bytes, *args):
            cache_param_str = repr(cache_param)
            if cache_param_str not in cache:
                dct = original_func(cache_param, *args)
                cache[cache_param_str] = {repr(word): wordcount for word, wordcount in dct.items()}
                with open(path, "w") as f:
                    json.dump(cache, f)
            return cache[cache_param_str]

        return new_func

    return decorator
