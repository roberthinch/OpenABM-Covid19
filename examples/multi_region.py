import multiprocessing
import time
from numpy import double
import example_utils as utils
import pandas as pd

class WorkerJob(object):
    def __init__(self,e_go,e_global_wait,e_job,idx,data):
        self.e_go   = e_go
        self.e_global_wait = e_global_wait
        self.e_job  = e_job
        self.idx    = idx
        self.data   = data
        
        self.e_go.wait()
        self.initialize_model()
        self.e_job.set()
        self.e_global_wait.wait()
          
    def initialize_model(self):
        params = utils.get_baseline_parameters()
        params.set_param( "n_total", 10000 )
        params.set_param( "rng_seed",self.idx )
        params.set_param( "days_of_interactions",1)
        params.set_param( "quarantine_days",1)
        sim = utils.get_simulation( params )
        self.model = sim.env.model
   
    def set_data(self,value):
        self.data[self.idx]=value
        
    def one_step_work(self):
        self.model.one_time_step()
        res = self.model.one_time_step_results()
        self.set_data(res["total_infected"])
        
    def one_step_wait(self):
        self.e_go.wait()
        self.one_step_work()
        self.e_job.set()
        self.e_global_wait.wait()
              
            
def create_WorkerJob(e_go, e_global_wait,e_job, idx,data,max_steps):
    worker = WorkerJob(e_go, e_global_wait,e_job, idx,data)
    for i in range( max_steps ) :
        worker.one_step_wait()
        
        
class MultiRegionModel(object):
    def __init__(self,n_regions,max_steps = 1000):

        self.n_regions   = n_regions
        self.max_steps   = max_steps
        self.e_global_wait = multiprocessing.Event()
        self.e_jobs_go   = []
        self.e_jobs_wait = []
        self.processes   = []
        self.pause_region = [False] * n_regions
     
        self.shared_array = multiprocessing.Array("i", n_regions)
        
        for j in range( n_regions) :
            e_job = multiprocessing.Event()
            e_go = multiprocessing.Event()
            self.shared_array[j] = 0
           
            self.e_jobs_go.append(e_go)
            self.e_jobs_wait.append(e_job)
            process = multiprocessing.Process(name='block', 
                                 target= create_WorkerJob,
                                 args=(e_go,self.e_global_wait,e_job,j,self.shared_array,max_steps))
            process.start()
            self.processes.append(process)

    def terminate_all_jobs(self):
        for j in range( self.n_regions ) :
            self.processes[j].terminate()
            
    def one_step_wait(self):
        
        # sets the first set of jobs off and blocks the end of the process
        self.e_global_wait.clear()
        for j in range( self.n_regions ) :
            if not self.pause_region[j] :
                self.e_jobs_go[j].set()
        
        # wait for the job to be done and rest counters
        for j in range( self.n_regions ) :
            if not self.pause_region[j] :
                self.e_jobs_wait[j].wait()
       
        for j in range( self.n_regions ) :
            self.e_jobs_wait[j].clear()
            self.e_jobs_go[j].clear()
               
        # get the the jovs ready for the next setp
        self.e_global_wait.set()
        
    def set_pause_in_region(self,region,pause):
        
        if region < 0 or region >= self.n_regions :
            raise( "region index is invalid" )
    
        self.pause_region[region] = pause
      
if __name__ == '__main__':
    
    max_steps = 20
    n_regions = 10
    
    model = MultiRegionModel( n_regions )
    
    for i in range( max_steps ) :
        
        if i == 10 :
            model.set_pause_in_region(0,True)
        if i == 15 :
            model.set_pause_in_region(0,False)

        model.one_step_wait()
        res = "time: " + str( i  ) + ": "
        for j in range( n_regions ) :
             res = res + str( model.shared_array[ j ] ) + "|"
        print( res )
        
    model.terminate_all_jobs()

