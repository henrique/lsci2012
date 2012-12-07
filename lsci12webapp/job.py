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
    iteration = db.IntegerProperty(required=True, default=0)
    

    def getJSON(self):
        s = {'jobId': self.jobId, 'vmIp': self.vmIp, 'paraSigma': self.paraSigma, 'paraEA': self.paraEA, 'running': self.running, 'finished': self.finished, 'result': self.result, 'counter': self.counter, 'iteration': self.iteration}
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
        self.iteration = job['iteration']

    @staticmethod
    def currentIteration():
        for it in db.GqlQuery("SELECT iteration FROM Job ORDER BY iteration DESC").fetch(1):
            return it
        return -1
