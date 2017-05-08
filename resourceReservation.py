import webapp2
import os
import jinja2
import logging

from google.appengine.ext import ndb
from google.appengine.api import users

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Resource(ndb.Model):
    user = ndb.StringProperty()
    resourceName = ndb.StringProperty(indexed = True)
    availableStartTime = ndb.StringProperty()
    availableEndTime = ndb.StringProperty()
    tags = ndb.StringProperty(repeated=True)
    #capacity = ndb.IntegerProperty()
    #lastReservationMadeTime = ndb.DateTimeProperty(auto_now_add=False)
    
class Reservation(ndb.Model):
    user = ndb.StringProperty()
    resourceName = ndb.StringProperty(indexed = True)
    reservationDate = ndb.StringProperty()
    reservationStartTime = ndb.StringProperty()
    duration = ndb.StringProperty()

class DeleteReservation(ndb.Model):
    def post(self):
        resourceName = self.request.get("resourceName")
        
        self.redirect("/")

class CreateResource(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('createResource.html')
        template_values = {
                
            }
        self.response.write(template.render(template_values))
        
    def post(self):
        #Getting the values filed in the Create Resource page
        newResourceName = self.request.get("resourceNameInput")
        #newResourceAvailableDate = self.request.get("availableDateInput")
        newResourceAvailableStartTime = self.request.get("availableStartTimeInput")
        newResourceAvailableEndTime = self.request.get("availableEndTimeInput")
        newResourceTags = self.request.get("tags").split(",")

        #Error checking and Validation of Data Entered
        #TODO
        
        
        resource = Resource(parent=ndb.Key('Resource', "MyKey"))
        resource.user = users.get_current_user().email()
        resource.resourceName = newResourceName
        #resource.availableDate = newResourceAvailableDate
        resource.availableStartTime = newResourceAvailableStartTime
        resource.availableEndTime = newResourceAvailableEndTime
        resource.tags = newResourceTags
        
        resource.put()
        self.redirect("/")     

class EditResource(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('editResource.html')
        resourceName = self.request.get('val')
        resource = Resource.query(Resource.resourceName == resourceName).fetch()
        template_values = {
                'resourceName' : resourceName,
                'availableStartTime' : resource[0].availableStartTime,
                'availableEndTime' : resource[0].availableEndTime,
                'tags' : resource[0].tags,
                'val' : resourceName
            }
        
        self.response.write(template.render(template_values))
        
    def post(self):
        resourceName = self.request.get('val')
        resource = Resource.query(Resource.resourceName == resourceName).fetch()
        
        newResourceName = self.request.get("resourceNameInput")
        newResourceAvailableStartTime = self.request.get("availableStartTimeInput")
        newResourceAvailableEndTime = self.request.get("availableEndTimeInput")
        newResourceTags = self.request.get("tags").split(",")
        
        #Error checking and Validation of Data Entered
        #TODO
        
        resource[0].resourceName = newResourceName
        resource[0].availableStartTime = newResourceAvailableStartTime
        resource[0].availableEndTime = newResourceAvailableEndTime
        resource[0].tags = newResourceTags
        resource[0].user = users.get_current_user().email()
        
        resource[0].put()
        self.redirect("/")
        
class Tag(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('tag.html')
        tag = self.request.get('val')
        
        allResources = Resource.query(ancestor=ndb.Key('Resource', "MyKey")).fetch()
        allResourcesOfThisTag = []
        for resource in allResources:
            if tag in resource.tags :
                allResourcesOfThisTag.append(resource)
        
        template_values = {
                'tag' : tag,
                'allResourcesOfThisTag' : allResourcesOfThisTag
            }
        self.response.write(template.render(template_values))
        
class ResourceInfo(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('resource_Info_Edit_Reserve.html')
        resourceName = self.request.get('val')
        resource = Resource.query(Resource.resourceName == resourceName).fetch()
        allowedToEdit = "NO"
        if(users.get_current_user().email() == resource[0].user):
            allowedToEdit = "YES"
            
        resourceReservation = Reservation.query(Reservation.resourceName == resourceName).fetch()
            
        template_values = {
                'resource' : resource,
                'allowedToEdit' : allowedToEdit,
                'resourceReservation' : resourceReservation
            }
        self.response.write(template.render(template_values))
        
class ReserveResource(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('reserveResource.html')
        resourceName = self.request.get('val')
        resource = Resource.query(Resource.resourceName == resourceName).fetch()
        
        template_values = {
                'resource' : resource,
                'resourceName' : resourceName,
                'availableStartTime' : resource[0].availableStartTime
            }
        self.response.write(template.render(template_values))
        
    def post(self):
        resourceName = self.request.get("val")
        reservationStartTime = self.request.get("availableStartTimeInput")
        reservationDuration = self.request.get("reservationDurationInput")
        reservationDate = self.request.get("availableDateInput")

        reservation = Reservation(parent=ndb.Key('Reservation', "MyKey"))
        
        reservation.resourceName = resourceName
        reservation.reservationDate = reservationDate
        reservation.reservationStartTime = reservationStartTime
        reservation.duration = reservationDuration
        reservation.user = users.get_current_user().email()
        
        reservation.put()
        self.redirect("/")
        
class UserInfo(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('UserInfo.html')
        userEmail = self.request.get('val')
        #logging.info(userEmail)
        resource = Resource.query(Resource.user == userEmail).fetch()
        userReservations = Reservation.query(Reservation.user == userEmail).fetch()    
        template_values = {
                'resource' : resource,
                'userEmail' : userEmail,
                'userReservations' : userReservations
            }
        self.response.write(template.render(template_values))
        
class RSS(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('rss.html')
        resourceName = self.request.get('val')
        resource = Resource.query(Resource.resourceName == resourceName).fetch()
        resourceReservation = Reservation.query(Reservation.resourceName == resourceName).fetch()
        
        template_values = {
                'resource' : resource,
                'resourceReservation' : resourceReservation
            }    
        self.response.write(template.render(template_values))
        
        
class MainPage(webapp2.RequestHandler):
    def get(self):
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            allResources = Resource.query(ancestor=ndb.Key('Resource', "MyKey")).fetch()
            userResources= Resource.query(Resource.user == users.get_current_user().email()).fetch()
            userReservations = Reservation.query(Reservation.user == users.get_current_user().email()).fetch()
            currentUser = users.get_current_user().email()
            
            template_values = {
                'user': users.get_current_user(),
                'url': url,
                'url_linktext': url_linktext,
                'allResources': allResources,
                'userResources': userResources,
                'userReservations': userReservations,
                'currentUser' :  currentUser
            }
            
            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))
            
        else:
            url = users.create_login_url(self.request.uri)
            #url_linktext = 'Login'
            self.redirect(url)

application = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/createResource', CreateResource),
  ('/tag', Tag),
  ('/resource_Info_Edit_Reserve', ResourceInfo),
  ('/editResource', EditResource),
  ('/reserveResource', ReserveResource),
  ('/deleteResource', DeleteReservation),
  ('/UserInfo', UserInfo),
  ('/rss', RSS)
], debug=True)

def main():
    application.RUN()

if __name__ == '__main__':
    main()