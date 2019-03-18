import pymongo
import config
import utils
import validators
import pytz
import operator
from datetime import datetime
from calendar import month_name
from collections import Counter

# Interaction with the MongoDB cluster

db_client = pymongo.MongoClient(config.mongo_address())
database = db_client[config.database_name()]
user_collection = database[config.user_collection_name()]
server_collection = database[config.server_collection_name()]

class Server:
    def __init__(self, server_object, guild):
        self.id = server_object['id'] # int
        self.bday_channel_id = server_object['birthday_channel_id'] # int
        self.everyone_mentioned = server_object['mention_everyone'] # bool
        self.users = get_users_in_server(guild)

    def birthday_count(self):
        return len(self.users)

    def avg_age(self):
        age_list = [user.age() for user in self.users]
        length = len(age_list)

        if length > 0:
            return sum(age_list) / length

        return None

    def birthdays_now(self):
        users = [user for user in self.users if user.has_birthday()]
        users.sort(key=lambda x: utils.tomorrow_midnight(x.local_time()) - x.local_time())
        return users

    def upcoming_birthdays(self):
        users = [user for user in self.users if validators.upcoming_birthday(user.next_birthday())]
        users.sort()
        return users

    def recent_birthdays(self):
        users = [user for user in self.users if validators.recent_birthday(user.prev_birthday())]
        users.sort(reverse=True)
        return users

    def birthdays_in_month(self, month):
        users = [user for user in self.users if user.birthdate.month == month]
        users.sort(key=lambda x: x.birthdate.day)
        return users

    def month_with_most_birthdays(self):
        if len(self.users) == 0:
            return None

        month_list = [user.birthdate.month for user in self.users]
        counts = Counter(month_list)
        month = counts.most_common(1)[0][0]

        return month_name[month] 


class User:
    def __init__(self, user_object):
        self.id = user_object['id'] # int
        self.birthdate = user_object['birth_date'] # datetime
        self.timezone = user_object['time_zone'] # str
        self.hidden_age = user_object['hide_age'] # bool
        self.is_mentioned = user_object['mention'] # bool

    def age(self):
        now = datetime.now()
        if self.next_birthday().year > now.year: # If the user's birthday has passed already this year
            return now.year - self.birthdate.year
        return now.year - self.birthdate.year - 1

    def local_time(self):
        return datetime.now(tz=pytz.timezone(self.timezone))

    def has_birthday(self):
        now = datetime.now(tz=pytz.timezone(self.timezone))
        return now.month == self.birthdate.month and now.day == self.birthdate.day

    def next_birthday(self):
        now = datetime.now(tz=pytz.timezone(self.timezone))
        date = self.birthdate

        if date.month < now.month or (date.month == now.month and date.day < now.day) or self.has_birthday():
            if date.month == 2 and date.day == 29:
                year = utils.closest_next_leap_year(now.year)
            else:
                year = now.year + 1
        else:
            if date.month == 2 and date.day == 29:
                year = utils.closest_leap_year(now.year)
            else:
                year = now.year
        
        return datetime(year, date.month, date.day, 0, 0, 0, tzinfo=pytz.timezone(self.timezone))

    def prev_birthday(self):
        now = datetime.now(tz=pytz.timezone(self.timezone))
        date = self.birthdate

        if date.month > now.month or (date.month == now.month and date.day > now.day) or self.has_birthday():
            if date.month == 2 and date.day == 29:
                year = utils.last_prev_leap_year(now.year)
            else:
                year = now.year - 1
        else:
            if date.month == 2 and date.day == 29:
                year = utils.last_leap_year(now.year)
            else:
                year = now.year

        return datetime(year, date.month, date.day, 0, 0, 0, tzinfo=pytz.timezone(self.timezone))

    # Users are sorted by the time delta between the current time to their next birthday
    def __lt__(self, other):
        return self.next_birthday() < other.next_birthday()

    def __gt__(self, other):
        return self.next_birthday() > other.next_birthday()

# Returns a list of User objects
def get_all_users():
    users = []
    cursor = user_collection.find()

    for user_object in cursor:
        users.append(User(user_object))

    return users

# Returns a User object
def get_user(id):
    user_object = user_collection.find_one({'id' : id})
    
    if user_object is not None:
        return User(user_object)

    return None

def user_count():
    return user_collection.find().count()

def user_exists(id):
    return user_collection.find_one({'id' : id}) is not None

def insert_user(id, birth_date, time_zone, hide_age, mention):
    user_object = {'id' : id, 'birth_date' : birth_date, 'time_zone' : time_zone, 'hide_age' : hide_age, 'mention' : mention, 'server_ids' : []}
    user_collection.insert_one(user_object)

def update_birthday(user_id, date):
    user_collection.update_one({'id' : user_id}, {'$set' : {'birth_date' : date}})

def update_timezone(user_id, zone):
    user_collection.update_one({'id' : user_id}, {'$set' : {'time_zone' : zone}})

def hide_age(user_id):
    user_collection.update_one({'id' : user_id}, {'$set' : {'hide_age' : True}})

def show_age(user_id):
    user_collection.update_one({'id' : user_id}, {'$set' : {'hide_age' : False}})

def toggle_mention(user_id):
    mention = user_collection.find_one({'id' : user_id})['mention']
    mention = not mention
    user_collection.update_one({'id' : user_id}, {'$set' : {'mention' : mention}})
    return mention

def get_all_server_objects():
    return server_collection.find()

# Returns a Server object
def get_server(guild):
    server_object = server_collection.find_one({'id' : guild.id})

    if server_object is not None:
        return Server(server_object, guild)

    return None

def get_server_object(id):
    return server_collection.find_one({'id' : id})

def server_count():
    return server_collection.find().count()

def server_exists(id):
    return server_collection.find_one({'id' : id}) is not None

def insert_server(id : int, birthday_channel_id: int, mention_everyone : bool):
    server_object = {'id' : id, 'birthday_channel_id' : birthday_channel_id, 'mention_everyone' : mention_everyone, 'user_ids' : []}
    server_collection.insert_one(server_object)

def remove_server(id):
    server_collection.delete_one({'id' : id})

def get_birthday_channel_id(server_id):
    return server_collection.find_one({'id' : server_id})['birthday_channel_id']

def update_birthday_announcement_channel(server_id, new_channel_id):
    server_collection.update_one({'id' : server_id}, {'$set' : {'birthday_channel_id' : new_channel_id}})

def toggle_everyone(server_id):
    mention_everyone = server_collection.find_one({'id' : server_id})['mention_everyone']
    mention_everyone = not mention_everyone
    server_collection.update_one({'id' : server_id}, {'$set' : {'mention_everyone' : mention_everyone}})
    return mention_everyone

# Returns a list of User objects
def get_users_in_server(guild):
    users = []

    for user in get_all_users():
        if guild.get_member(user.id) is not None:
            users.append(user)

    return users