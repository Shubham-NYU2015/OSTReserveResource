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
    resourceReservedAt = ndb.DateTimeProperty(auto_now_add=False)
    reservationCount = ndb.IntegerProperty()
    
class Reservation(ndb.Model):
    user = ndb.StringProperty()
    resourceName = ndb.StringProperty(indexed = True)
    reservationDate = ndb.StringProperty()
    reservationStartTime = ndb.StringProperty()
    reservationEndTime = ndb.StringProperty()
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
        newResourceAvailableStartTime = self.request.get("availableStartTimeInput")
        newResourceAvailableEndTime = self.request.get("availableEndTimeInput")
        newResourceTags = self.request.get("tags").split(",")

        newResourceTags_ = []
        for tag in newResourceTags:
            newResourceTags_.append(tag.strip())

        if(newResourceAvailableStartTime > newResourceAvailableEndTime):
            Error = "Yes"
            template = JINJA_ENVIRONMENT.get_template('createResource.html')
            template_values = {
                    'Error' : Error,
                    'resourceName': newResourceName,
                    'tags' : newResourceTags_
                }
            self.response.write(template.render(template_values))
            return
        
        
        resource = Resource(parent=ndb.Key('Resource', "MyKey"))
        resource.user = users.get_current_user().email()
        resource.resourceName = newResourceName
        resource.availableStartTime = newResourceAvailableStartTime
        resource.availableEndTime = newResourceAvailableEndTime
        resource.tags = newResourceTags_
        resource.reservationCount = 0;
        resource.resourceReservedAt = datetime.datetime.now()
        
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
        
        newResourceTags_ = []
        for tag in newResourceTags:
            newResourceTags_.append(tag.strip())
              
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
        resource[0].tags = newResourceTags_
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
        
        currentDatefull = datetime.datetime.now() - datetime.timedelta(hours=4)
        currentTime = ('%02d:%02d'%(currentDatefull.hour,currentDatefull.minute))
            
        userReservations_ = []   
        currentDate = datetime.datetime.strftime(currentDatefull,'%Y-%m-%d')
        for res in resourceReservation:
            reserveDatefull = datetime.datetime.strptime(res.reservationDate, '%Y-%m-%d')
            reserveDate = datetime.datetime.strftime(reserveDatefull,'%Y-%m-%d')
                
            if((reserveDate > currentDate) or (reserveDate == currentDate and res.reservationEndTime > currentTime)):
                userReservations_.append(res)
            
        template_values = {
                'resource' : resource,
                'allowedToEdit' : allowedToEdit,
                'resourceReservation' : userReservations_
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
        
        #If reservation date is less than the current date
        currentDatefull = datetime.datetime.now() - datetime.timedelta(hours=4)        
        currentDate = datetime.datetime.strftime(currentDatefull,'%Y-%m-%d')

        reserveDatefull = datetime.datetime.strptime(reservationDate, '%Y-%m-%d')
        reserveDate = datetime.datetime.strftime(reserveDatefull,'%Y-%m-%d')
        
        if(reserveDate < currentDate):
            Error0 = "Yes"
            template = JINJA_ENVIRONMENT.get_template('reserveResource.html')
            template_values = {
                    'Error0' : Error0,
                    'resourceName': resourceName,
                    'availableStartTime' : reservationStartTime,
                    'reservationDate' : reservationDate,
                    'reservationDuration' : reservationDuration
                }
            self.response.write(template.render(template_values))
            return
        
        #If Reservation Start time is less than the current time
        currentTime = ('%02d:%02d'%(currentDatefull.hour,currentDatefull.minute))
        if(reserveDate == currentDate and reservationStartTime < currentTime):
            Error01 = "Yes"
            template = JINJA_ENVIRONMENT.get_template('reserveResource.html')
            template_values = {
                    'Error01' : Error01,
                    'resourceName': resourceName,
                    'availableStartTime' : resource[0].availableStartTime,
                    'reservationDate' : reservationDate,
                    'reservationDuration' : reservationDuration
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
                    'availableStartTime' : resource[0].availableStartTime,
                    'reservationDate' : reservationDate,
                    'reservationDuration' : reservationDuration
                }
            self.response.write(template.render(template_values))
            return
        
        #If the reservation end time is more than the resource available time
        allowedDuration = datetime.datetime.strptime(resource[0].availableEndTime, '%H:%M') - datetime.datetime.strptime(resource[0].availableStartTime, '%H:%M')
        allowedDuration_min = hms_to_minutes(str(allowedDuration))
        
        if(reservationStartTime >= resource[0].availableStartTime and allowedDuration_min < int(reservationDuration)):
            Error1 = "Yes"
            template = JINJA_ENVIRONMENT.get_template('reserveResource.html')
            template_values = {
                    'Error1' : Error1,
                    'resourceName': resourceName,
                    'availableStartTime' : reservationStartTime,
                    'reservationDate' : reservationDate
                }
            self.response.write(template.render(template_values))
            return
        
        reservation = Reservation(parent=ndb.Key('Reservation', "MyKey"))
        reservation.resourceName = resourceName
        reservation.reservationDate = reservationDate
        reservation.reservationStartTime = reservationStartTime
        reservation.duration = reservationDuration
        reservation.user = users.get_current_user().email()
        reservation.reservationID = resourceName + reservationDate + reservationStartTime + reservationDuration + users.get_current_user().email()
        
        temp = datetime.datetime.strptime(reservation.reservationStartTime, '%H:%M') + datetime.timedelta(minutes=int(reservation.duration))
        reservation.reservationEndTime = ('%02d:%02d'%(temp.hour,temp.minute))
        
        resource[0].resourceReservedAt = datetime.datetime.now()

        temp = resource[0].reservationCount
        resource[0].reservationCount = temp + 1
        
        mail.send_mail(sender="shubham.bits08@gmail.com", 
                       to=reservation.user,
                       subject="Reservation Confirmation",
                       body='''Hi! 
                       Your Reservation is booked. Reservation Details as follows:
                       Reservation of: ''' + reservation.resourceName +
                       '''Date: ''' + reservation.reservationDate +
                       '''Start Time: ''' + reservation.reservationStartTime +
                       '''Duration: ''' + reservation.duration)
        
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
        
        currentDatefull = datetime.datetime.now() - datetime.timedelta(hours=4)
        currentTime = ('%02d:%02d'%(currentDatefull.hour,currentDatefull.minute))
            
        userReservations_ = []   
        currentDate = datetime.datetime.strftime(currentDatefull,'%Y-%m-%d')
        for res in userReservations:
            reserveDatefull = datetime.datetime.strptime(res.reservationDate, '%Y-%m-%d')
            reserveDate = datetime.datetime.strftime(reserveDatefull,'%Y-%m-%d')
                
            if((reserveDate > currentDate) or (reserveDate == currentDate and res.reservationEndTime > currentTime)):
                userReservations_.append(res)
            
        template_values = {
                'resource' : resource,
                'userEmail' : userEmail,
                'userReservations' : userReservations_
            }
        self.response.write(template.render(template_values))
        
class RSS(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('rss.html')
        resourceName = self.request.get('val')
        resource = Resource.query(Resource.resourceName == resourceName).fetch()
        resourceReservation = Reservation.query(Reservation.resourceName == resourceName).fetch()    
        
        currentDatefull = datetime.datetime.now() - datetime.timedelta(hours=4)
        currentTime = ('%02d:%02d'%(currentDatefull.hour,currentDatefull.minute))
            
        userReservations_ = []   
        currentDate = datetime.datetime.strftime(currentDatefull,'%Y-%m-%d')
        for res in resourceReservation:
            reserveDatefull = datetime.datetime.strptime(res.reservationDate, '%Y-%m-%d')
            reserveDate = datetime.datetime.strftime(reserveDatefull,'%Y-%m-%d')
                
            if((reserveDate > currentDate) or (reserveDate == currentDate and res.reservationEndTime > currentTime)):
                userReservations_.append(res)    
        
        template_values = {
                'resource' : resource,
                'resourceReservation' : userReservations_
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
        searchCriteria_startTime = self.request.get("availableStartTimeInput")
        searchCriteria_duration = self.request.get("DurationInput")
        
        if(searchCriteria_startTime and searchCriteria_duration):
            temp = datetime.datetime.strptime(searchCriteria_startTime, '%H:%M') + datetime.timedelta(minutes=int(searchCriteria_duration))
            searchCrtiteria_endTime = ('%02d:%02d'%(temp.hour,temp.minute))
            
        if(not searchCriteria_resourceName and not searchCriteria_startTime and not searchCriteria_duration):
            Error0 = "Yes"
            template = JINJA_ENVIRONMENT.get_template('search.html')
            template_values = {
                    'Error0' : Error0
                }
            self.response.write(template.render(template_values))
            return
        
        if(searchCriteria_resourceName and searchCriteria_startTime and searchCriteria_duration):
            Error1 = "Yes"
            template = JINJA_ENVIRONMENT.get_template('search.html')
            template_values = {
                    'Error1' : Error1
                }
            self.response.write(template.render(template_values))
            return
        
        if(not searchCriteria_resourceName):
            if not(searchCriteria_startTime and searchCriteria_duration):
                Error2 = "Yes"
                template = JINJA_ENVIRONMENT.get_template('search.html')
                template_values = {
                        'Error2' : Error2
                    }
                self.response.write(template.render(template_values))
                return
        
        if(searchCriteria_resourceName):
            resource = Resource.query(Resource.resourceName == searchCriteria_resourceName).fetch()
            template = JINJA_ENVIRONMENT.get_template('search.html')
            template_values = {
                    'resource' : resource,
                    'resourceName' : searchCriteria_resourceName
                }
            self.response.write(template.render(template_values))
            
        elif(searchCriteria_startTime and searchCriteria_duration):
            allresources = Resource.query(ancestor=ndb.Key('Resource', "MyKey")).fetch()
            available_resources = []
            
            for res in allresources:
                if(res.availableStartTime <= searchCriteria_startTime and res.availableEndTime >= searchCrtiteria_endTime):
                    available_resources.append(res)
            
            template = JINJA_ENVIRONMENT.get_template('search.html')
            template_values = {
                    'resource' : available_resources,
                    'availableStartTime' : searchCriteria_startTime,
                    'DurationInput' : searchCriteria_duration
                }
            self.response.write(template.render(template_values))
            
class MainPage(webapp2.RequestHandler):
    def get(self):
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            allResources = Resource.query(ancestor=ndb.Key('Resource', "MyKey")).order(-Resource.resourceReservedAt).fetch()
            userResources= Resource.query(Resource.user == users.get_current_user().email()).order(-Resource.resourceReservedAt).fetch()
            
            currentDatefull = datetime.datetime.now() - datetime.timedelta(hours=4)
            currentTime = ('%02d:%02d'%(currentDatefull.hour,currentDatefull.minute))
            
            userReservations = Reservation.query(Reservation.user == users.get_current_user().email()).order(Reservation.reservationDate).order(Reservation.reservationStartTime).fetch()
            
            userReservations_ = []   
            currentDate = datetime.datetime.strftime(currentDatefull,'%Y-%m-%d')
            for res in userReservations:
                reserveDatefull = datetime.datetime.strptime(res.reservationDate, '%Y-%m-%d')
                reserveDate = datetime.datetime.strftime(reserveDatefull,'%Y-%m-%d')
                
                if((reserveDate > currentDate) or (reserveDate == currentDate and res.reservationEndTime > currentTime)):
                    userReservations_.append(res)
            
            template_values = {
                'user': users.get_current_user(),
                'url': url,
                'url_linktext': url_linktext,
                'allResources': allResources,
                'userResources': userResources,
                'userReservations': userReservations_
            }
            
            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))
            
        else:
            url = users.create_login_url(self.request.uri)
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