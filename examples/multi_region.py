import multiprocessing
import time
from numpy import double
import example_utils as utils
import pandas as pd
import sys

sys.path.append("../src/COVID19")
import covid19
from model import PYTHON_SAFE_UPDATE_PARAMS

STEP_TYPE_TIME = 0
STEP_TYPE_PARAM_UPDATE = 1

RESULT_FIELDS = [
    "time",
    "total_infected",
    "total_death",
    "n_critical"  
]

class WorkerJob(object):
    def __init__(
            self,
            e_go,
            e_global_wait,
            e_job,
            step_type,
            idx,
            data,
            n_regions,
            init_params,
            update_param,
            update_value
        ):
        self.e_go   = e_go
        self.e_global_wait = e_global_wait
        self.e_job  = e_job
        self.step_type = step_type
        self.idx    = idx
        self.data   = data
        self.n_regions = n_regions
        self.init_params = init_params
        self.update_param = update_param
        self.update_value = update_value

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
        
        for fdx in range( len( RESULT_FIELDS ) ) :
            self.data[self.idx + (fdx * self.n_regions) ]= res[ RESULT_FIELDS[fdx]]        
      
    def update_running_params(self):
        
        param = PYTHON_SAFE_UPDATE_PARAMS[self.update_param.value ]
        self.model.update_running_params(param,self.update_value.value)
                
    def run(self):
        self.e_go.wait()
        if self.step_type.value == STEP_TYPE_TIME :
            self.one_step_work()
        elif self.step_type.value == STEP_TYPE_PARAM_UPDATE :
            self.update_running_params()      
        self.e_job.set()
        self.e_global_wait.wait()
        
            
def create_WorkerJob(
        e_go, 
        e_global_wait,
        e_job, 
        step_type,
        idx,
        shared_data,
        n_regions,
        init_params,
        update_param,
        update_value
    ):
    worker = WorkerJob(e_go, e_global_wait,e_job,step_type,idx,shared_data,n_regions,init_params,update_param,update_value)
    
    while True :
        worker.run()
        
        
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
        self.time_offsets = [0] * n_regions
     
        self.results      = multiprocessing.Array("i", n_regions * len( RESULT_FIELDS ) )   
        self.index_values = params[ index_col ]
        self.index_col    = index_col
        self.step_type    = multiprocessing.Value('i',0)
        self.update_param = multiprocessing.Value('i',0)
        self.update_value = multiprocessing.Value('d', 0)
        self.result_ts_init()
        
        params.drop(columns=[ index_col ],inplace=True)
        params = params.to_dict('records')
        
        for j in range( n_regions) :
            e_job = multiprocessing.Event()
            e_go = multiprocessing.Event()
            self.results[j] = 0

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
                args   = (e_go,self.e_global_wait,e_job,self.step_type,j,self.results,n_regions,init_params,self.update_param,self.update_value)
            )
            process.start()
            self.processes.append(process)
            
        self.time = 0;
        self.one_step_wait()

    def terminate_all_jobs(self):
        for j in range( self.n_regions ) :
            self.processes[j].terminate()
            
    def one_step_wait(self):
        self.step_type.value = STEP_TYPE_TIME
        
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
        self.time = self.time + 1
        
        self.results_ts_dt = pd.concat( [ self.results_ts_dt, self.result_dt() ] )
        
    def update_running_params(self,param,value,index=None):

        if index == None :
            for j in range( n_regions) :
                self.update_running_paramss(param, value, j)
        
        # set the param to update and value in shared memory        
        param_idx = PYTHON_SAFE_UPDATE_PARAMS.index(param)
        self.step_type.value    = STEP_TYPE_PARAM_UPDATE  
        self.update_param.value = param_idx
        self.update_value.value = value
        
        # fire off the update in the relevant job
        self.e_global_wait.clear()
        self.e_jobs_go[index].set()
        self.e_jobs_wait[index].wait()
        self.e_jobs_go[index].clear()
        self.e_jobs_wait[index].clear()
        self.e_global_wait.set()
        
    def set_pause_in_region(self,region,pause):
        
        if region < 0 or region >= self.n_regions :
            raise( "region index is invalid" )
    
        self.pause_region[region] = pause
      
    def set_pause(self,pause):
        
        for region in range( self.n_regions ) : 
           self.pause_region[region] = pause
           
    def result_array(self,field):
        
        if not field in RESULT_FIELDS :
            raise( "field not known" )
        
        fdx = RESULT_FIELDS.index(field)
        fdx = fdx * self.n_regions
        
        res = [];
        for idx in range( self.n_regions ) :
            res.append(self.results[fdx+idx])
            
        return res
    
    def result_dt(self):
        
        dt = pd.DataFrame( data = { self.index_col : self.index_values })
        
        for field in RESULT_FIELDS :
            dt[ field ] = self.result_array( field )
        
        dt["time_global"] = self.time
            
        return dt      
    
    def result_ts(self):   
        return self.results_ts_dt
    
    def result_ts_init(self):   
        self.results_ts_dt = pd.DataFrame(columns = [ "time_global" ] + RESULT_FIELDS )
         
    def step_to_synch_point(self,synch_param,synch_value,verbose = True, maxSteps = 100):
        
        # reset the results_ts 
        self.result_ts_init()
        initial_offsets = self.time_offsets
        initial_time    = self.result_array( "time" )
        self.set_pause( False )
        
        if not isinstance(synch_value, list ) :
            synch_value = [ synch_value ] * self.n_regions
        
        for step in range( maxSteps ) :
        
            # pause procesess that have reached the synch point
            res = self.result_array( synch_param )    
            n_waiting = 0     
            for j in range( n_regions ) :
                if res[ j ] >= synch_value[ j ] :
                    self.set_pause_in_region( j, True )
                    n_waiting = n_waiting + 1;
              
            # if all at synch point, wait  
            if n_waiting == self.n_regions :
                model.set_pause( False )
                break;
            
            if verbose :
                print( "step " + str( step ) + "; " + str( n_waiting ) + "/" + str( self.n_regions ) + " reached synch point" )
            
            model.one_step_wait()
        
        # failure to synch
        if n_waiting == self.n_regions :
            if verbose :
                print( "Not all regions reached the target after maxSteps" )
            return False
        
        return True

        
      
      
if __name__ == '__main__':
        
    max_steps = 20
    
    file_param =  "~/Downloads/ox_bdi_data/baseline_parameters_calibrated_by_stp.csv"
    params     = pd.read_csv( file_param, sep = ",", comment = "#", skipinitialspace = True )    
    
    params["n_total"] = params["n_total"] / 100
    params.round({"n_total" : 0 })
    n_regions = len( params.index )

    model = MultiRegionModel( params, index_col = "stp" )
    model.one_step_wait()
    
    model.step_to_synch_point("total_infected", 50 )
    model.update_running_params( "lockdown_on", 1, 0)
    
    for i in range( max_steps ) :
        
        model.one_step_wait()
        resStr = "time: " + str( i  ) + ": "
        res    = model.result_array("total_infected")
        for j in range( n_regions ) :
            resStr = resStr + str( res[j] ) + "|"
        print( resStr )
    
                    
    model.terminate_all_jobs()
    
    print( model.result_ts())

