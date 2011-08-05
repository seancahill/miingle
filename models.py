__author__ = 'sean'
from google.appengine.ext import db
class Greeting(db.Model):
  """Models an individual Guestbook entry with an author, content, and date."""
  author = db.UserProperty()
  content = db.StringProperty(multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)

def guestbook_key(guestbook_name=None):
  """Constructs a datastore key for a Guestbook entity with guestbook_name."""
  return db.Key.from_path('Guestbook', guestbook_name or 'default_guestbook')

class EventCheck(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    check_in = db.DateProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    event = db.StringProperty(required=True)

class User(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    bio = db.StringProperty(required=True, multiline=True,)
    email = db.EmailProperty(required=True)
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)

class OwnerLocations(db.Model):
  """Models an individual location entry with an owner, location_name, and geolocation."""
  owner = db.UserProperty()
  location_name = db.StringProperty()
  geolocation = db.GeoPtProperty()
  def __str__(self):
        # Note use of django.utils.encoding.smart_str() here because
        # first_name and last_name will be unicode strings.
    return '%s#%s#%s' % self.location_name,str(self.geolocation.lat),str(self.geolocation.lon)
  
  def get_str(self):
        return "%s#%s#%s" % (self.location_name,str(self.geolocation.lat),str(self.geolocation.lon))

      

class Locations(db.Model):
  """Models an individual location entry with an owner, location_name, date, duration, event and geolocation."""
  owner = db.UserProperty()
  location_name = db.StringProperty()
  date = db.DateProperty()
  end_date = db.DateProperty()
  event = db.StringProperty()
  geolocation = db.GeoPtProperty()
  