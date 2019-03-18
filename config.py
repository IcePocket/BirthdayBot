import json

# Interaction with the configuration data

path = r''

# Getting the data from the configuration file
config_file = open(path, 'r')
config_data = json.load(config_file)
config_file.close()

def token():
    return config_data['token']

def prefix():
    return config_data['prefix']

def mongo_address():
    return config_data['mongo_address']

def dbl_token():
    return config_data['dbl_token']

def bfd_token():
    return config_data['bfd_token']

def timezones_link():
    return config_data['timezones_link']

def admin_ids():
    return [int(id) for id in config_data['admin_ids']]

def database_name():
    return config_data['database_name']

def server_collection_name():
    return config_data['server_collection_name']

def user_collection_name():
    return config_data['user_collection_name']
    
def default_color():
    return config_data['default_color']

def invite_link():
    return config_data['invite_link']

def support_link():
    return config_data['support_link']

def special_link():
    return config_data['special_link']