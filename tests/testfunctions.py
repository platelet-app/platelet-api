import json
import random
import string

def is_json(js):
    try:
        json_object = json.loads(js)
    except Exception as e:
        return False
    return True

def get_user_id(js):
    return json.loads(js)['id']

def random_string(length = 10):
    return ''.join(random.choice(string.ascii_letters) for m in range(length))
