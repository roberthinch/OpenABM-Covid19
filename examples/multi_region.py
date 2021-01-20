import multiprocessing
import time
from numpy import double
import example_utils as utils
import pandas as pd

class WorkerJob(object):
    def __init__(
            self,
            e_go,
            e_global_wait,
            e_job,
            idx,
            data,
            fields,
            n_regions,
            init_params
        ):
        self.e_go   = e_go
        self.e_global_wait = e_global_wait
        self.e_job  = e_job
        self.idx    = idx
        self.data   = data
        self.fields  = fields
        self.n_regions = n_regions
        self.init_params = init_params
        
        self.e_go.wait()
        self.initialize_model()
        self.e_job.set()
        self.e_global_wait.wait()
          
    def initialize_model(self):
        
        params = utils.get_baseline_parameters()
        
        for param, val in self.init_params.items():
            params.set_param( param, val )

        sim = utils.get_simulation( params )
        self.model = sim.env.model
           
    def one_step_work(self):
        self.model.one_time_step()
        res = self.model.one_time_step_results()
        
        for fdx in range( len( self.fields ) ) :
            self.data[self.idx + (fdx * self.n_regions) ]= res[ self.fields[fdx]]        
        
    def one_step_wait(self):
        self.e_go.wait()
        self.one_step_work()
        self.e_job.set()
        self.e_global_wait.wait()
            
def create_WorkerJob(
        e_go, 
        e_global_wait,
        e_job, 
        idx,
        shared_data,
        shared_fields,
        n_regions,
        max_steps,
        init_params
    ):
    worker = WorkerJob(e_go, e_global_wait,e_job, idx,shared_data,shared_fields,n_regions,init_params)
    for i in range( max_steps ) :
        worker.one_step_wait()
        
        
class MultiRegionModel(object):
    def __init__(self,params,index_col="idx", max_steps = 1000,turn_off_contract_tracing = True ):

        n_regions = len( params.index ) 
        
        self.n_regions   = n_regions
        self.max_steps   = max_steps
        self.e_global_wait = multiprocessing.Event()
        self.e_jobs_go   = []
        self.e_jobs_wait = []
        self.processes   = []
        self.pause_region = [False] * n_regions
     
        self.fields = [
            "total_infected",
            "total_death",
            "n_critical"
        ]
        self.shared_array = multiprocessing.Array("i", n_regions * len( self.fields) )   
        
        
        params.drop(columns=[ index_col ],inplace=True)
        params = params.to_dict('records')
        
        for j in range( n_regions) :
            e_job = multiprocessing.Event()
            e_go = multiprocessing.Event()
            self.shared_array[j] = 0

            init_params = params[j] 
            init_params["rng_seed"] = j
            if turn_off_contract_tracing :
                init_params[ "days_of_interactions" ] = 1
                init_params[ "quarantine_days" ]      = 1  
           
            self.e_jobs_go.append(e_go)
            self.e_jobs_wait.append(e_job)
            process = multiprocessing.Process(
                name   = 'block', 
                target = create_WorkerJob,
                args   = (e_go,self.e_global_wait,e_job,j,self.shared_array,self.fields,n_regions,max_steps,init_params)
            )
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
      
    def set_pause(self,pause):
        
        for region in range( self.n_regions ) : 
           self.pause_region[region] = pause
           
    def result_array(self,field):
        
        if not field in self.fields :
            raise( "field not known" )
        
        fdx = self.fields.index(field)
        fdx = fdx * self.n_regions
        
        res = [];
        for idx in range( self.n_regions ) :
            res.append(self.shared_array[fdx+idx])
            
        return res
              
      
if __name__ == '__main__':
    
    max_steps = 20
    n_regions = 10
    sync_inf  = 50
    
    file_param =  "~/Downloads/ox_bdi_data/baseline_parameters_calibrated_by_stp.csv"
    params     = pd.read_csv( file_param, sep = ",", comment = "#", skipinitialspace = True )    
    
    params["n_total"] = params["n_total"] / 50
    params.round({"n_total" : 0 })
        
    model = MultiRegionModel( params, index_col = "stp" )
    
    for i in range( max_steps ) :
        
        model.one_step_wait()
        resStr = "time: " + str( i  ) + ": "
        res    = model.result_array("total_infected")
        for j in range( n_regions ) :
            resStr = resStr + str( res[j] ) + "|"
        print( resStr )
        
        n_waiting = 0     
        for j in range( n_regions ) :
            if model.shared_array[ j ] >= sync_inf :
                model.set_pause_in_region(j,True)
                n_waiting = n_waiting + 1;
                
        if n_waiting == n_regions :
            model.set_pause(False)
                    
    model.terminate_all_jobs()

