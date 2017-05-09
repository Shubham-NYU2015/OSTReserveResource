import webapp2
import os
import jinja2
import logging
import datetime

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import mail

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
    #resourceReservedAt = ndb.DateTimeProperty(auto_now_add=False)
    reservationCount = ndb.IntegerProperty()
    
class Reservation(ndb.Model):
    user = ndb.StringProperty()
    resourceName = ndb.StringProperty(indexed = True)
    reservationDate = ndb.StringProperty()
    reservationStartTime = ndb.StringProperty()
    duration = ndb.StringProperty()
    reservationID = ndb.StringProperty()

class DeleteReservation(webapp2.RequestHandler):
    def post(self):
        reservationID = self.request.get("reservationID")
        reservations = Reservation.query(Reservation.reservationID == reservationID).fetch()
        
        resource = Resource.query(Resource.resourceName == reservations[0].resourceName).fetch()
        temp = resource[0].reservationCount
        resource[0].reservationCount = temp - 1
        resource[0].put()
        
        for res in reservations:
            res.key.delete()
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

        if(newResourceAvailableStartTime > newResourceAvailableEndTime):
            Error = "Yes"
            template = JINJA_ENVIRONMENT.get_template('createResource.html')
            template_values = {
                    'Error' : Error,
                    'resourceName': newResourceName,
                    'tags' : newResourceTags
                }
            self.response.write(template.render(template_values))
            return
        
        
        resource = Resource(parent=ndb.Key('Resource', "MyKey"))
        resource.user = users.get_current_user().email()
        resource.resourceName = newResourceName
        #resource.availableDate = newResourceAvailableDate
        resource.availableStartTime = newResourceAvailableStartTime
        resource.availableEndTime = newResourceAvailableEndTime
        resource.tags = newResourceTags
        resource.reservationCount = 0;
        
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
          
        if(newResourceAvailableStartTime > newResourceAvailableEndTime):
            Error = "Yes"
            template = JINJA_ENVIRONMENT.get_template('createResource.html')
            template_values = {
                    'Error' : Error,
                    'resourceName': newResourceName,
                    'availableStartTime' : resource[0].availableStartTime,
                    'availableEndTime' : resource[0].availableEndTime,
                    'tags' : newResourceTags
                }
            self.response.write(template.render(template_values))
            return
        
        resource[0].resourceName = newResourceName
        resource[0].availableStartTime = newResourceAvailableStartTime
        resource[0].availableEndTime = newResourceAvailableEndTime
        resource[0].tags = newResourceTags
        resource[0].user = users.get_current_user().email()
        resource[0].reservationCount = 0
        
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
        
def hms_to_minutes(t):
    h, m, s = [int(i) for i in t.split(':')]
    return (3600*h + 60*m + s)/60

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
        resource = Resource.query(Resource.resourceName == resourceName).fetch()
        
        '''
        #If reservation date is less than the current date
        #TODO
        currentDate = datetime.datetime.now() - datetime.timedelta(hours=4)
        if(reservationDate < currentDate):
            Error0 = "Yes"
            template = JINJA_ENVIRONMENT.get_template('reserveResource.html')
            template_values = {
                    'Error' : Error0,
                    'resourceName': resourceName,
                    'availableStartTime' : reservationStartTime,
                    'reservationDate' : reservationDate
                }
            self.response.write(template.render(template_values))
            return
        
        #If the reservation time is less than the resource available time
        if(reservationStartTime < resource[0].availableStartTime):
            Error = "Yes"
            template = JINJA_ENVIRONMENT.get_template('reserveResource.html')
            template_values = {
                    'Error' : Error,
                    'resourceName': resourceName,
                    'availableStartTime' : reservationStartTime,
                    'reservationDate' : reservationDate
                }
            self.response.write(template.render(template_values))
            return
        
        #If the reservation end time is more than the resource available time
        #TODO
        
        #reservationEndTime = reservationStartTime + datetime.timedelta(minutes=reservationDuration)
        
        allowedDuration = datetime.datetime.strptime(resource[0].availableEndTime, '%H:%M') - datetime.datetime.strptime(resource[0].availableStartTime, '%H:%M')
        allowedDuration_min = hms_to_minutes(str(allowedDuration))
        
        if(reservationStartTime >= resource[0].availableStartTime and allowedDuration_min < reservationDuration):
            Error1 = "Yes"
            template = JINJA_ENVIRONMENT.get_template('reserveResource.html')
            template_values = {
                    'Error' : Error1,
                    'resourceName': resourceName,
                    'availableStartTime' : reservationStartTime,
                    'reservationDate' : reservationDate
                }
            self.response.write(template.render(template_values))
            return
        
        '''
        
        reservation = Reservation(parent=ndb.Key('Reservation', "MyKey"))
        reservation.resourceName = resourceName
        reservation.reservationDate = reservationDate
        reservation.reservationStartTime = reservationStartTime
        reservation.duration = reservationDuration
        reservation.user = users.get_current_user().email()
        reservation.reservationID = resourceName + reservationDate + reservationStartTime + reservationDuration + users.get_current_user().email()

        #resource[0].resourceReservedAt = datetime.datetime.now()

        temp = resource[0].reservationCount
        resource[0].reservationCount = temp + 1
        
        mail.send_mail(sender="shubham.bits08@gmail.com", 
                       to=reservation.user,
                       subject="Reservation Confirmation",
                       body="yoyo")
        
        resource[0].put()
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

class Search(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('search.html')
        template_values = {

            }
        self.response.write(template.render(template_values))
    
    def post(self):
        searchCriteria_resourceName = self.request.get("resourceNameInput")
        resource = Resource.query(Resource.resourceName == searchCriteria_resourceName).fetch()

        template = JINJA_ENVIRONMENT.get_template('search.html')
        template_values = {
                'resource' : resource
            }
        self.response.write(template.render(template_values))
        
class MainPage(webapp2.RequestHandler):
    def get(self):
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            allResources = Resource.query(ancestor=ndb.Key('Resource', "MyKey")).fetch()
            userResources= Resource.query(Resource.user == users.get_current_user().email()).fetch()
            userReservations = Reservation.query(Reservation.user == users.get_current_user().email()).order(Reservation.reservationDate).order(Reservation.reservationStartTime).fetch()
            
            template_values = {
                'user': users.get_current_user(),
                'url': url,
                'url_linktext': url_linktext,
                'allResources': allResources,
                'userResources': userResources,
                'userReservations': userReservations
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
  ('/deleteReservation', DeleteReservation),
  ('/UserInfo', UserInfo),
  ('/rss', RSS),
  ('/search', Search)
], debug=True)

def main():
    application.RUN()

if __name__ == '__main__':
    main()