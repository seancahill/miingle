"""FACEBOOK_APP_ID = "252388944775500"
FACEBOOK_APP_SECRET = "e16a213a22c8610474013d6ba9794064"""
FACEBOOK_APP_ID = "143983939014671"
FACEBOOK_APP_SECRET = "b9c25530ea5e790933595565ea21924f"

from google.appengine.ext.db import BadKeyError

import base64
import cgi
import Cookie
import email.utils
import hashlib
import hmac
import os.path
import time
import wsgiref.handlers

import urllib
import logging
import urllib2
import os
from datetime import date
from datetime import timedelta
from math import *
from models import *

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '1.2')
from django.utils import simplejson as json
from django.http import HttpResponse
#import easy to use xml parser called minidom:
from xml.dom.minidom import parseString

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import mail
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app


class MainPage(webapp.RequestHandler):
    def get(self):

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'

        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            return self.redirect(users.create_login_url(self.request.uri))

        locations = OwnerLocations.all().filter('owner = ', users.get_current_user())

        user=users.get_current_user()
        if locations.count() == 0:
            locations = {}

        message_body = """
          Welcome to the miingle app
        """
        mail.send_mail(
              sender='sean.cahill@student.ncirl.ie',
              to='sean@nmm.ie',
              subject='welcome to miingle',
              body=message_body)

        template_values = {
            'locations': locations,
            'userdisplay' : user.nickname(),
            'url': url,
            'url_linktext': url_linktext,
        }

        path = os.path.join(os.path.dirname(__file__), 'searchlocations.html')
        self.response.out.write(template.render(path, template_values))
          
class Guestbook(webapp.RequestHandler):
    def get(self):
       logging.info('in Guestbook get')
    def post(self):
      guestbook_name = self.request.get('guestbook_name')
      greeting = Greeting(parent=guestbook_key(guestbook_name))

      if users.get_current_user():
        greeting.author = users.get_current_user()

      greeting.content = self.request.get('content')
      greeting.put()
      self.redirect('/?' + urllib.urlencode({'guestbook_name': guestbook_name}))
      
class MarketingController(webapp.RequestHandler):
    def get(self):
        logging.info('in marketing controller get')
        location_name = self.request.get('location_name')
        event_name = self.request.get('event')
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            locations = Locations.all().filter('owner', users.get_current_user())
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        user = users.get_current_user()

        if user:
            mem_keys = ['location_name','event']
            try:
                mem_summaries = memcache.get_multi(mem_keys,key_prefix=user.nickname())
                location_name = mem_summaries['location_name']
                event_name = mem_summaries['event']
            except KeyError:
                errorMessage="Problem with marketing, location not provided!!"
                template_values = {
                'errorMess': errorMessage,
                'url' : '/geo',
                'errorNo': 500,
                }
                path = os.path.join(os.path.dirname(__file__), 'exception.html')
                self.response.out.write(template.render(path, template_values))
                return

            delete_keys = memcache.delete_multi(mem_keys,key_prefix=user.nickname())
            if not delete_keys:
                logging_info('failed to delete memcache')
            
            template_values = {
                'location': location_name,
                'event': event_name,
                'userdisplay' : user.nickname(),
                'url': url,
                'url_linktext': url_linktext,
            }

            path = os.path.join(os.path.dirname(__file__), 'marketing.html')
            self.response.out.write(template.render(path, template_values))
        else:
            logging_info('not logged in')
            self.redirect("/geo")

class LocationController(webapp.RequestHandler):
    def get(self):
        logging.info('in location controller get')
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            locations = Locations.all().filter('owner', users.get_current_user())
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'locations': locations,
            'url': url,
            'url_linktext': url_linktext,
        }

        path = os.path.join(os.path.dirname(__file__), 'searchlocations.html')
        self.response.out.write(template.render(path, template_values))
 

    def post(self):
        """

        """
        if users.get_current_user():
            try:
                organizer = users.get_current_user()
                ln = self.request.get('location_name')
                lat = self.request.get('lat')
                lon = self.request.get('lon')
                event_date = self.request.get('date')
                sd = event_date.split('/')
                db_date = date(int(sd[2]),int(sd[0]),int(sd[1]))
                days = int(self.request.get('duration'))
                num_days = days - 1
                end_event = db_date + timedelta(days=num_days)
                event_details = self.request.get('event_details')
                owner_locations = OwnerLocations.all().filter('owner', users.get_current_user()).filter('location_name',ln)
                if owner_locations.count() == 0:
                    owner_location = OwnerLocations(owner = organizer,location_name = ln,date = db_date,geolocation = db.GeoPt(lat,lon))
                    owner_location.put()
                location = Locations(owner = organizer,location_name = ln,date = db_date,end_date = end_event, event = event_details,geolocation = db.GeoPt(lat,lon))
                location.put()
            except db.Error, exStr:
                logging.error("Error while reading from db:% s"% exStr)
        else:
            return self.redirect(users.create_login_url(self.request.get_full_path()))

        event_summary = {'location_name': ln,'event': event_details}
        failed_keys = memcache.set_multi(event_summary,key_prefix=organizer.nickname())
        if failed_keys:
            logging.info('memcache failed')
        self.redirect('/marketing')

class FindEvents(webapp.RequestHandler):

    def get(self):
        """
        
        """
        logging.info('in findEvents')
        distance = float(self.request.get('distance'))
        lat = float(self.request.get('lat'))
        lon = float(self.request.get('lon'))
        #q = Locations.all()
        #locations = q.filter('date <= ', date.today()).filter('end_date >= ', date.today())
        locations = Locations.gql("Where end_date >= :1",date.today())
        json_results = []
        for loc in locations:
            if (loc.date <= date.today()):
              logging.info(loc.location_name)
              geo_lat = loc.geolocation.lat
              geo_long = loc.geolocation.lon
              dist_calc = ( 6371 * acos( cos( radians(lat) ) * cos( radians( geo_lat ) ) * cos( radians( geo_long ) - radians(lon) ) + sin( radians(lat) ) * sin( radians( geo_lat ) ) ) )
              logging.info(dist_calc)
              if dist_calc < distance:
                  logging.info(loc.location_name)
                  json_results.append({"location": loc.location_name,"event": loc.event, "key": str(loc.key())})
        self.response.headers['Content-Type'] = 'application/json'
        response = json.dumps(json_results)
        self.response.out.write(response)


class FeedXml(webapp.RequestHandler):
    def get(self):
       logging.info('in feedxml get')
       try:
          newsfeed = urllib2.urlopen('http://ae-book.appspot.com/blog/atom.xml/')
          data = newsfeed.read()
          newsfeed.close()
          #parse the xml you downloaded
          dom = parseString(data)
          #retrieve the first xml tag (<tag>data</tag>) that the parser finds with name tagName:
          xmlTag = dom.getElementsByTagName('id')[0].toxml()
          #strip off the tag (<tag>data</tag>  --->   data):
          xmlData=xmlTag.replace('<id>','').replace('</id>','')
          #print out the xml tag and data in this format: <tag>data</tag>
          logging.info(xmlTag)
          #just print the data
          logging.info(xmlData)
       except urllib2.URLError, e:
          logging.info('error feedxml utl fetch')

class BaseHandler(webapp.RequestHandler):
    @property
    def current_user(self):
        """Returns the logged in Facebook user, or None if unconnected."""
        if not hasattr(self, "_current_user"):
            self._current_user = None
            user_id = parse_cookie(self.request.cookies.get("fb_user"))
            if user_id:
                self._current_user = User.get_by_key_name(user_id)
        return self._current_user


class HomeHandler(BaseHandler):
    def get(self,var):
        path = os.path.join(os.path.dirname(__file__), "oauth.html")
        try:
            event = Locations.get(var)
        except BadKeyError:
            errorMessage="Problem with location: could not find !!"
            template_values = {
            'errorMess': errorMessage,
            'url' : '/geo',
            'errorNo': 500,
            }
            path = os.path.join(os.path.dirname(__file__), 'exception.html')
            self.response.out.write(template.render(path, template_values))
            return

        user_dict = []
        the_user = self.current_user
        if the_user:
            user_checked_in_event = EventCheck.gql('where check_in = :1 and id = :2 and event = :3',date.today(),the_user.id,var)
            if user_checked_in_event.count() > 0:
                logging.info('user checked in')
            else:
                store_event = EventCheck(key_name=the_user.id, id=the_user.id,event=var)
                store_event.put()
            all_users = EventCheck.gql('where check_in = :1 and event = :2',date.today(),var)

            for user in all_users:
                user_dict.append(User.get_by_key_name(user.id))
            args = dict(current_user=the_user,event_id=var,event_name=event,users=user_dict)
            self.response.out.write(template.render(path, args))
        else:
            self.redirect("/geo")


class LoginHandler(BaseHandler):
    def get(self,var):
        verification_code = self.request.get("code")
        args = dict(client_id=FACEBOOK_APP_ID, redirect_uri=self.request.path_url)
        args2 = dict(client_id=FACEBOOK_APP_ID, redirect_uri=self.request.path_url)
        if self.request.get("code"):
            args["client_secret"] = FACEBOOK_APP_SECRET
            args["code"] = self.request.get("code")

            response = cgi.parse_qs(urllib2.urlopen(
                "https://graph.facebook.com/oauth/access_token?" +
                urllib.urlencode(args)).read())
            access_token = response["access_token"][-1]

            # Download the user profile and cache a local instance of the
            # basic profile info
            profile = json.load(urllib2.urlopen(
                "https://graph.facebook.com/me?" +
                urllib.urlencode(dict(access_token=access_token))))
            books = json.load(urllib2.urlopen(
                "https://graph.facebook.com/me/books?" +
                urllib.urlencode(dict(access_token=access_token))))
            likes = json.load(urllib2.urlopen(
                "https://graph.facebook.com/me/likes?" +
                urllib.urlencode(dict(access_token=access_token))))
            movies = json.load(urllib2.urlopen(
                "https://graph.facebook.com/me/movies?" +
                urllib.urlencode(dict(access_token=access_token))))
            music = json.load(urllib2.urlopen(
                "https://graph.facebook.com/me/music?" +
                urllib.urlencode(dict(access_token=access_token))))
            
            user = User(key_name=str(profile["id"]), id=str(profile["id"]),
                        name=profile["name"], access_token=access_token,
                        profile_url=profile["link"],bio=profile["bio"],email=profile["email"])
            user.put()
            set_cookie(self.response, "fb_user", str(profile["id"]),
                       expires=time.time() + 30 * 86400)
            self.redirect('/checkedin/'+ var)
        else:
            ## request permission to extract users email from profile
            args2["scope"] = "email,user_interests,user_activities,user_about_me"
            self.redirect("https://www.facebook.com/dialog/oauth?" +
                urllib.urlencode(args2) + "&display=touch")


class LogoutHandler(BaseHandler):
    def get(self):
        set_cookie(self.response, "fb_user", "", expires=time.time() - 86400)
        self.redirect("/geo")


def set_cookie(response, name, value, domain=None, path="/", expires=None):
    """Generates and signs a cookie for the give name/value"""
    timestamp = str(int(time.time()))
    value = base64.b64encode(value)
    signature = cookie_signature(value, timestamp)
    cookie = Cookie.BaseCookie()
    cookie[name] = "|".join([value, timestamp, signature])
    cookie[name]["path"] = path
    if domain: cookie[name]["domain"] = domain
    if expires:
        cookie[name]["expires"] = email.utils.formatdate(
            expires, localtime=False, usegmt=True)
    response.headers._headers.append(("Set-Cookie", cookie.output()[12:]))


def parse_cookie(value):
    """Parses and verifies a cookie value from set_cookie"""
    if not value: return None
    parts = value.split("|")
    if len(parts) != 3: return None
    if cookie_signature(parts[0], parts[1]) != parts[2]:
        logging.warning("Invalid cookie signature %r", value)
        return None
    timestamp = int(parts[1])
    if timestamp < time.time() - 30 * 86400:
        logging.warning("Expired cookie %r", value)
        return None
    try:
        return base64.b64decode(parts[0]).strip()
    except:
        return None


def cookie_signature(*parts):
    """Generates a cookie signature.
    """
    hash = hmac.new(FACEBOOK_APP_SECRET, digestmod=hashlib.sha1)
    for part in parts: hash.update(part)
    return hash.hexdigest()

class GeoPosition(webapp.RequestHandler):
    def get(self):
        logging.info('in find events')
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'url': url,
            'url_linktext': url_linktext
        }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
       logging.info('in geoposition get')
       try:
        geolocs = urllib2.urlopen('http://localhost:3000/locations/findlocations.json?distance=0.5&lon=-6.243164&lat=53.348867')
        geodata=geolocs.read()
        objs = json.loads(geodata)
        for o in objs:
          logging.info(o['location']['location_name'])
       except urllib2.URLError, e:
          logging.info('error geoposition utl fetch')
          
class QRCode(webapp.RequestHandler):
    def get(self):
       logging.info('in qr code get')
       try:
        qrinfo = urllib2.urlopen('http://www.sparqcode.com/qrgen?qt=url&data=http://www.nmm.ie&cap=New Event')
        qrdata=geolocs.read()        
       except urllib2.URLError, e:
          logging.info('error geoposition utl fetch')
          
class AddTwoNumbers(webapp.RequestHandler):      
    def get(self):         
        try:             
            first = int(self.request.get('first'))             
            second = int(self.request.get('second'))              
            self.response.out.write("<html><body><p>%d + %d = %d</p></body></html>" % (first, second, first + second))         
        except (TypeError, ValueError):             
            self.response.out.write("<html><body><p>Invalid inputs</p></body></html>")

class NotFoundPageHandler(webapp.RequestHandler):
    def get(self):
        self.error(404)
        template_values = {
        }
        path = os.path.join(os.path.dirname(__file__), '404error.html')
        self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                     ('/sign', Guestbook),
                                     ('/geo',GeoPosition),
                                     ('/add',AddTwoNumbers),
                                     ('/event',LocationController),
                                     ('/marketing',MarketingController),
                                     ('/locations',FindEvents),
                                     ('/checkedin/(.*)',HomeHandler),
                                     ('/checkin/(.*)',LoginHandler),
                                     ('/QR',QRCode),
                                     (r"/auth/login/(.*)", LoginHandler),
                                     (r"/auth/logout", LogoutHandler),
                                     ('/.*', NotFoundPageHandler)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()