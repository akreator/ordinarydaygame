from google.appengine.ext import ndb, db
import re, urllib, random, string, hashlib, hmac


class Users(ndb.Model):
    username = ndb.StringProperty(required=True)
    password = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    pronouns = ndb.StringProperty(required=True)
    joined = ndb.DateTimeProperty(auto_now_add=True)
    last_active = ndb.DateTimeProperty(auto_now=True)
    trails_visited = ndb.StringProperty(repeated=True)
    trails_contributed = ndb.StringProperty(repeated=True) #managed in Event
    trails_created = ndb.StringProperty(repeated=True)
    trails_saved = ndb.StringProperty(repeated=True)
    events_created = ndb.KeyProperty(repeated=True)
    introduction = ndb.TextProperty()
    gender = ndb.StringProperty()
    country = ndb.StringProperty()
    hobbies = ndb.StringProperty()
    website = ndb.StringProperty()

    def get_trails_visited(self):
        trails = [Trail.get_by_title(t) for t in self.trails_visited]
        return trails

    def get_trails_contributed(self):
        trails = [Trail.get_by_title(t) for t in self.trails_contributed]
        return trails

    def get_trails_created(self):
        trails = [Trail.get_by_title(t) for t in self.trails_created]
        return trails

    def get_trails_saved(self):
        trails = [Trail.get_by_title(t) for t in self.trails_saved]
        return trails

    def get_created_events_trail(self, trail):
        return [e for e in self.events_created if e.trail == trail]

    def get_unaccepted_trails(self):
        return [t for t in self.get_trails_created() if t.get_unaccepted_events()]

    def get_edited_trails(self):
        return [t for t in self.get_trails_created() if len(t.get_edited_events()[0]) > 0]

    def get_total_visits(self):
        return sum([len(x.users_visited) for x in self.get_trails_created()])

    def record_trail_visit(self, trail):
        if trail.title not in self.trails_visited:
            self.trails_visited.append(trail.title)
            self.put()
            ud = UserData.create_user_data(self, trail)
            ud.record_event(trail.first_event.get())
            trail.users_visited.append(self.username)
        trail.put()

    def save_trail(self, trail):
        if trail not in self.trails_saved:
            self.trails_saved.append(trail.title)
            self.put()
            trail.users_saved.append(self.username)
            trail.put()

    @classmethod
    def check_valid_values(cls, username, password, email, pronouns):
        if ndb.Key(Users, username.lower()).get():
            return False
        name_re = re.compile(r"^[\w_-]{2,16}$")
        pw_re = re.compile(r"^.{3,}$")
        email_re = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
        pronouns_re = re.compile(r"^[a-zA-Z]{2,10}/[a-zA-Z]{2,10}/[a-zA-Z]{2,10}/[a-zA-Z]{2,10}$")
        if name_re.match(username) and pw_re.match(password) and email_re.match(email) and pronouns_re.match(pronouns):
            return True
        else:
            return False

    @classmethod
    @ndb.transactional
    def register_user(cls, username, password, email, pronouns):
        if cls.check_valid_values(username, password, email, pronouns):
            user = cls(username=username, pronouns=pronouns, email=email,
                       password=Users.create_secure_pw(username, password), id=username.lower())
            user.put()
            return user
        else:
            return None

    @classmethod
    def get_by_username(cls, username):
        u = Users.query(Users.username == username).fetch()
        if u:
            return u[0]

    @classmethod
    def check_password(cls, username, pw, h):
        salt = h.split(',')[1]
        #return hmac.compare_digest(h, cls.create_secure_pw(username, pw, salt))
        return h == cls.create_secure_pw(username, pw, salt)

    @classmethod
    def create_secure_pw(cls, username, pw, salt=None):
        if not salt:
            salt = ''.join(random.choice(string.letters) for x in xrange(5))
        h = hashlib.sha256(username + pw + salt).hexdigest()
        return '%s,%s' % (h, salt)

    @classmethod
    def login(cls, username, password):
        u = cls.get_by_id(username.lower())
        if u and cls.check_password(u.username, password, u.password):
            return u
        else:
            return False


class Trail(ndb.Model):
    title = ndb.StringProperty(required=True)
    creator = ndb.StringProperty(required=True)
    url = ndb.StringProperty(required=True)
    description = ndb.TextProperty(required=True)
    first_event = ndb.KeyProperty(required=True)
    upvotes = ndb.IntegerProperty()
    contributors = ndb.StringProperty(repeated=True)
    users_visited = ndb.StringProperty(repeated=True)
    datetime_created = ndb.DateTimeProperty(auto_now_add=True)
    datetime_updated = ndb.DateTimeProperty(auto_now=True)
    events = ndb.KeyProperty(repeated=True)
    tags = ndb.StringProperty(repeated=True)
    users_saved = ndb.StringProperty(repeated=True)
    users_visited_amt = ndb.ComputedProperty(lambda self: len(self.users_visited))

    def get_unaccepted_events(self):
        all_events = [e.get() for e in self.events]
        events = [e for e in all_events if not e.accepted and e.parent_event.get().accepted]
        return events

    def get_edited_events(self):
        events = [e.get() for e in self.events if e.get().edit]
        edits = [e.edit.get() for e in events]
        return [events, edits]

    def check_visited(self, user):
        return user.username in self.users_visited

    def accept_event(self, user, event):
        if user.username not in self.contributors:
            self.contributors.append(user.username)
            self.put()
            user.trails_contributed.append(self.title)
            user.put()
        event.accepted = True
        event.put()

    def accept_edit(self, edit):
        event = edit.parent_event.get()
        event.content = edit.content
        event.location = edit.location
        event.action = edit.action
        event.item_needed = edit.item_needed
        event.item_found = edit.item_found
        event.edit = None
        event.put()
        edit.key.delete()

    def check_new_content(self, user):
        if user.username not in self.users_visited:
            return True
        else:
            ud = UserData.get_user_data(user, self)
            return ud.last_visited < self.datetime_updated

    def update_trail(self, description, tags):
        if Trail.check_valid_values(description, tags):
            self.description = description
            self.tags = tags
            self.put()
            return True

    @classmethod
    def delete_trail(cls, trail):
        creator = Users.get_by_username(trail.creator)
        creator.trails_created.remove(trail.title)
        creator.put()
        trail.first_event.delete()
        for e in trail.events:
            e.delete()
        for u in trail.contributors:
            u = Users.get_by_username(u)
            u.trails_contributed.remove(trail.title)
            u.put()
        savers = Users.query(Users.trails_saved == trail.title).fetch()
        for u in savers:
            u.trails_saved.remove(trail.title)
            u.put()
        for u in trail.users_visited:
            u = Users.get_by_username(u)
            u.trails_visited.remove(trail.title)
            u.put()
            ud = UserData.get_user_data(u, trail)
            ud.key.delete()
        trail.key.delete()

    @classmethod
    def check_valid_values(cls, description, tags, title=""):
        if title and ndb.Key(Trail, title.lower()).get():
            return False
        text_re = re.compile(r"^[a-zA-Z0-9_' !?.\",-]{2,40}$")
        if (not title or text_re.match(title)) and len(description.replace(" ", "")) >= 5 and \
                (not tags or all(text_re.match(t) for t in tags)):
            return True
        else:
            return False

    @classmethod
    @ndb.transactional(xg=True)
    def create_trail(cls, title, creator, description, content, location, action, tags=[]):
        first_event = Event.create_first_event(content, location, action, creator)
        if first_event and len(title) > 0 and cls.check_valid_values(description, tags, title=title):
            t = cls(title=title, creator=creator.username, description=description, first_event=first_event.key,
                    upvotes=0, url=urllib.quote_plus(title.lower()), id=title.lower(), tags=tags)
            creator.trails_created.append(t.title)
            creator.put()
            first_event.trail = t.key
            first_event.put()
            t.put()
            return t
        else:
            first_event.key.delete()
            return False

    @classmethod
    def get_top_trails(cls):
        return Trail.query().order(-Trail.users_visited_amt).fetch(5)

    @classmethod
    def get_newest_trails(cls):
        return Trail.query().order(-Trail.datetime_created).fetch(5)

    @classmethod
    def get_by_title(cls, title):
        t = Trail.query(Trail.title == title).fetch()
        if t:
            return t[0]

    @classmethod
    def get_by_url(cls, url):
        title = urllib.unquote_plus(url.lower())
        return cls.get_by_id(title)


class UserData(ndb.Model):
    user = ndb.KeyProperty(kind=Users)
    trail = ndb.KeyProperty(kind=Trail)
    inventory = ndb.StringProperty(repeated=True)
    event_path = ndb.KeyProperty(repeated=True)
    last_visited = ndb.DateTimeProperty(auto_now=True)

    def add_item(self, item):
        if not self.in_inventory(item):
            self.inventory.append(item)
            self.put()

    def use_item(self, item):
        if item in self.inventory:
            self.inventory.remove(item)
            self.put()
            return True
        else:
            return False

    def in_inventory(self, item):
        if item in self.inventory:
            return True
        else:
            return False

    def record_event(self, event):
        if not self.event_path[-1] == event.key:
            self.event_path.append(event.key)
            self.put()

    @classmethod
    def create_user_data(cls, user, trail):
        u = UserData(user=user.key, trail=trail.key, inventory=[], event_path=[trail.first_event])
        u.put()
        return u

    @classmethod
    def get_user_data(cls, user, trail):
        ud = UserData.query(UserData.user == user.key, UserData.trail == trail.key).fetch()
        if ud:
            return ud[0]


class Event(ndb.Model):
    content = ndb.TextProperty(required=True)
    location = ndb.StringProperty(required=True)
    action = ndb.StringProperty(required=True)
    trail = ndb.KeyProperty(kind=Trail)
    item_needed = ndb.StringProperty()
    item_found = ndb.StringProperty()
    datetime_created = ndb.DateTimeProperty(auto_now_add=True)
    accepted = ndb.BooleanProperty(required=True)
    creator = ndb.StringProperty(required=True)
    child_events = ndb.KeyProperty(repeated=True)
    parent_event = ndb.KeyProperty()
    edit = ndb.KeyProperty()

    def update_event(self, user, content, location, action, item_needed="", item_found=""):
        if not self.accepted or user.username == self.trail.get().creator:
            if Event.check_valid_values(self.user, content, location, action, item_needed, item_found):
                self.content = content
                self.location = location
                self.action = action
                self.item_needed = item_needed
                self.item_found = item_found
                self.put()
                return True
        elif user.username == self.creator or Event.check_valid_values(user, content, location, action, item_needed, item_found):
            e = EditedEvent(content=content, location=location, action=action, item_needed=item_needed,
                            item_found=item_found, parent_event=self.key)
            e.put()
            if self.edit:
                self.edit.delete()
            self.edit = e.key
            self.put()
            return True

    def get_child_events(self):
        e = [e.get() for e in self.child_events]
        return e

    @classmethod
    def delete_event(cls, event):
        for e in event.child_events:
            Event.delete_event(e.get())
        trail = event.trail.get()
        trail.events.remove(event.key)
        trail.put()
        users = Users.query(Users.trails_visited == trail.title).fetch()
        for u in users:
            ud = UserData.get_user_data(u, trail)
            if event.key in ud.event_path:
                ud.event_path = ud.event_path[:ud.event_path.index(event.key)]
                ud.put()
        event.key.delete()

    @classmethod
    def check_valid_values(cls, creator, content, location, action, item_needed="", item_found="", parent_event=""):
        """if parent_event:
            sibling_events = [e.get() for e in parent_event.child_events]
            if action in [e.action for e in sibling_events if e.creator == creator.username]:
                return False"""
        short_re = re.compile(r"^[a-zA-Z0-9_' !?.\",-]{0,25}$")
        long_re = re.compile(r"^[a-zA-Z0-9_' !?.\",-]{2,40}$")
        return long_re.match(location) and long_re.match(action) and len(content) <= 3000 and \
            len(content.replace(" ", "")) > 2 and short_re.match(item_needed) and short_re.match(item_found)

    @classmethod
    @ndb.transactional
    def create_event(cls, parent_event, content, location, action, creator, trail, item_needed="", item_found=""):
        if cls.check_valid_values(creator, content, location, action, item_needed, item_found, parent_event):
            e = cls(content=content, location=location, action=action, trail=trail.key,
                    creator=creator.username, item_needed=item_needed, item_found=item_found,
                    accepted=(creator.username == trail.creator), parent_event=parent_event.key)
            e.put()
            parent_event.child_events.append(e.key)
            parent_event.put()
            creator.events_created.append(e.key)
            creator.put()
            trail.events.append(e.key)
            trail.put()
            return e
        else:
            return False

    @classmethod
    def create_first_event(cls, content, location, action, creator):
        if cls.check_valid_values(creator, content, location, action):
            e = cls(content=content, location=location, action=action, creator=creator.username, accepted=True)
            e.put()
            creator.events_created.append(e.key)
            creator.put()
            return e


class EditedEvent(ndb.Model):
    content = ndb.TextProperty(required=True)
    location = ndb.StringProperty(required=True)
    action = ndb.StringProperty(required=True)
    trail = ndb.KeyProperty(kind=Trail)
    item_needed = ndb.StringProperty()
    item_found = ndb.StringProperty()
    parent_event = ndb.KeyProperty(required=True)


class Feedback(ndb.Model):
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    feedback = ndb.TextProperty(required=True)

    @classmethod
    def log_feedback(cls, name, email, feedback):
        email_re = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
        if email_re.match(email):
            f = Feedback(name=name, email=email, feedback=feedback)
            f.put()
            return f
        else:
            return False


class Comment(ndb.Model):
    content = ndb.TextProperty(required=True)
    user = ndb.StringProperty(required=True)
    likes = ndb.IntegerProperty(required=True)
    related_event = ndb.KeyProperty(kind=Event)
    related_trail = ndb.KeyProperty(kind=Trail)


class Secret(ndb.Model):
    secret = ndb.TextProperty(required=True)

    @classmethod
    def get_secret(cls):
        return Secret.query().fetch()[0].secret
