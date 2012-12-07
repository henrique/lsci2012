from google.appengine.ext import db

class Job(db.Model):
    
    jobId = db.IntegerProperty()
    vmIp = db.StringProperty()
    paraSigma = db.FloatProperty()
    paraEA = db.FloatProperty()
    result = db.FloatProperty()
    running = db.BooleanProperty()
    finished = db.BooleanProperty()
    counter = db.IntegerProperty(required=True, default=0)
    iter = db.IntegerProperty(required=True, default=0)
    

    def getJSON(self):
        s = {'jobId': self.jobId, 'vmIp': self.vmIp, 'paraSigma': self.paraSigma, 'paraEA': self.paraEA, 'running': self.running, 'finished': self.finished, 'result': self.result, 'counter': self.counter, 'iter': self.iter}
        return s
    
    def __repr__(self):
        return str(self.__dict__)
    
    def set(self, job):
        self.jobId = job['jobId']
        self.vmIp = job['vmIp']
        self.paraSigma = job['paraSigma']
        self.paraEA = job['paraEA']
        self.running = job['running']
        self.finished = job['finished']
        self.result = job['result']
        self.counter = job['counter']
        self.iter = job['iter']

    @staticmethod
    def currentIteration(self):
        q = db.GqlQuery(Job)
        job = q.order("-iter").fetch(1)
        print "currentIteration", job
        return job.iter
