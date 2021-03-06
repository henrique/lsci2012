import webapp2
import logging
import json
from google.appengine.ext import db
from google.appengine.api import memcache
from vm import *
from job import *


class MainPage(webapp2.RequestHandler):
  def get(self):
      self.response.headers['Content-Type'] = 'text/html'
      file = open('index.html')
      self.response.out.write(file.read())


class GetJob(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        logging.info("get single job received")
        
        # GET a not running& not finished& not requested job from DB
        q = Job.all()
        q.filter("running =", False)
        q.filter("finished =", False)
        q.filter("counter <", 1)
        job = q.get()
        if job == None:
            logging.info('no not running job found that was not requested already, abort')
            self.error(500)
            return
        
        l = { 'jobs': [job.getJSON()]}
        content = json.dumps(l, indent=2)
        logging.info(content)
        self.response.out.write(content)
        # increment job counter
        job.counter += 1
        job.put()


class GetVm(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        logging.info("get single vm received")
        
        # GET VM with same request.remote_addr
        q = VM.all()
        q.filter("ip =", self.request.remote_addr)

        vm = q.get()
        if vm == None:
            logging.info('no vm found for this ip: '+str(self.request.remote_addr)+', abort')
            self.error(500)
            return
        
        l = { 'vms': [vm.getJSON()]}
        content = json.dumps(l, indent=2)
        logging.info(content)
        self.response.out.write(content)
       
        
class GetAllJobs(webapp2.RequestHandler):
    cachekey = 'alljobs'

    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        data = memcache.get(self.cachekey)
        if data is None:
            data = self.getFromDB()
            if memcache.set(self.cachekey, data, 300): #5min
                logging.info("adding to cache: " + self.cachekey)
        
        logging.info(data)
        self.response.out.write(data)
    
    
    def getFromDB(self):
        #l = {}
        #cur_iter = Job.currentIteration()
        logging.info("get all jobs from db")
        #l['iteration'] = cur_iter
        
        
        # GET a not running job from DB
        jobs = db.GqlQuery("Select * "
                           "FROM Job "
                           #"WHERE iteration = :1 "
                           "ORDER BY iteration, jobId")#, cur_iter)
        countJobs = jobs.count()
        logging.info("countJobs: "+str(countJobs))
        if countJobs > 0:
           l = { 'jobs': [job.getJSON() for job in jobs]}
        else:
           l = { 'jobs': []}
          
        content = json.dumps(l, indent=2)
        return content


class GetAllVms(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        logging.info("get all vms received")
        
        # GET a not running job from DB
        vms = db.GqlQuery("Select * "
                           "FROM VM "
                           "ORDER BY ip")
        countVms = vms.count()
        logging.info("countVms: "+str(countVms))
        if countVms > 0:
           l = { 'vms': [vm.getJSON() for vm in vms]}
        else:
           l = { 'vms': []}
          
        content = json.dumps(l, indent=2)
        logging.info(content)
        self.response.out.write(content)


class PutAllJobs(webapp2.RequestHandler):
    def put(self):
        memcache.delete(GetAllJobs.cachekey)
        logging.info('put all jobs received')
        
        data_string = self.request.body
        decoded = json.loads(data_string)
        decoded2 = json.dumps(decoded, indent=2)
        logging.info(decoded2)
        
        if decoded.has_key('jobs'): 
            count_jobs = len(decoded['jobs'])
            logging.info('count jobs: '+str(count_jobs))
            jobs = []
            for job in decoded['jobs']:
                temp = Job(key_name=str(job['jobId']))
                temp.set(job)
                jobs.append(temp)
            
            for job in jobs:
                job.put()
                logging.info('put job['+str(job.jobId)+'] into datastore')
                
      
      
class PutAllVms(webapp2.RequestHandler):
  def put(self):
   
    logging.info('put all vms received')
   
    data_string = self.request.body
    decoded = json.loads(data_string)
    decoded2 = json.dumps(decoded, indent=2)
    
    logging.info(decoded2)
   
    if decoded.has_key('vms'):
        count_vms = len(decoded['vms'])
        logging.info('count vms: '+str(count_vms))
        vms = []
        for vm in decoded['vms']:
            temp = VM(key_name=vm['ip'])
            temp.set(vm)
            temp.ip = vm['ip']
            vms.append(temp)
        
        for vm in vms:
            vm.put()
            logging.info('put vm['+vm.ip+'] into datastore')
    
    else:
        logging.info('no key vms defined')
        self.error(500)
        return
        


class PutJob(webapp2.RequestHandler):
  def put(self):
      
    logging.info('put single job received')
    data_string = self.request.body
    decoded = json.loads(data_string)
    if decoded.has_key('jobs'): 
        count_jobs = len(decoded['jobs'])
        logging.info('count jobs: '+str(count_jobs))
        if count_jobs > 1:
            logging.info("more than 1 job, abort")
            self.error(500)
            return
        jobs = []
        for job in decoded['jobs']:
            temp = Job(key_name=str(job['jobId']))
            temp.set(job)
            # Lookup Job in DB and see if already running
            # if not running overwrite and send 200 else 500
            q = Job.all()
            q.filter("jobId =", temp.jobId)
            result = q.get()
            if result.running == True:
                if result.vmIp != self.request.remote_addr:
                    logging.info('job already running from other vm, abort')
                    self.error(500)
                    return
            temp.vmIp = self.request.remote_addr
            jobs.append(temp)
        
        for job in jobs:
            job.put()
            logging.info('put job['+str(job.jobId)+'] into datastore')
            if job.finished:
                memcache.delete(GetAllJobs.cachekey)
                logging.info('memcache deleted!!!!')


class PutVm(webapp2.RequestHandler):
    def put(self):
        
        logging.info('put single vm received')
        
        data_string = self.request.body
        decoded = json.loads(data_string)
        decoded2 = json.dumps(decoded, indent=2)
        
        logging.info(decoded2)
       
        if decoded.has_key('vms'):
            count_vms = len(decoded['vms'])
            logging.info('count vms: '+str(count_vms))
            if count_vms > 1:
                logging.info("more than 1 vm, abort")
                self.error(500)
                return
            vms = []
            for vm in decoded['vms']:
                ip = self.request.remote_addr
                temp = VM(key_name=ip)
                temp.set(vm)
                temp.ip = ip
                vms.append(temp)
            
            for vm in vms:
                vm.put()
                logging.info('put vm['+vm.ip+'] into datastore')
        
        else:
            logging.info('no key vms defined')
            self.error(500)
            return                  

        

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/put/jobs/', PutAllJobs),
                               ('/put/vms/', PutAllVms),
                               ('/put/job/', PutJob),
                               ('/put/vm/', PutVm),
                               ('/get/job/', GetJob),
                               ('/get/vm/', GetVm),
                               ('/get/jobs/', GetAllJobs),
                               ('/get/vms/', GetAllVms)],
                              debug=True)

# APP STARTUP - INIT DB
logging.info('app startup')
