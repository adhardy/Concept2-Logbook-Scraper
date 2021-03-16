import queue #multithreading
import threading
import requests

class MultiWebbing():
    """call this class first to initiate MultiWebbing and the individual threads"""
    def __init__(self, num_threads):
        """Creates a job queue, lock object, session and creates the number of requested threads"""
        self.job_queue = queue.Queue()
        self.lock = threading.Lock() #session and lock can be overwritten on a per job basis
        self.session = requests.session()
        self.threads = []
        for i in range(num_threads):
            self.threads.append(self.Thread(i, self.job_queue, self.lock, self.session))

    def start(self):
        """Call after initiating a Threading object to start the threads."""
        for thread in self.threads:
            thread.start()

    def finish(self):
        """When you are ready to finish your threads (e.g. when your work queue is empty and you have visited all pages, call this method to stop and join the threads."""
        for thread in self.threads:
            thread.join()

    class Thread(threading.Thread):
        #define how the threads function
        #TODO add verbosity for more detailed output options
        def __init__(self, number, job_queue, lock, session):
            threading.Thread.__init__(self)
            self.number = number
            self._stop_event = threading.Event()
            self.job_queue = job_queue
            self.lock = lock
            self.session = session

        def run(self):
            #execute on thread.start()
            #job_function should have a Job object as its sole argument. Can update job argument with additional attributes if needed for the function
            print(f" ** Starting thread - {self.number}")

            while not self._stop_event.isSet():
                #thread will continuously check the queue for work until the master process joins the threads, and the stop_event signal is sent
                try:
                    #get a job
                    job = self.job_queue.get(block=False)
                    job.set_thread(self) #give job access to thread attributes

                except queue.Empty:
                    pass

                else:
                    #print("Thread " + self.name + ": Getting profile: " + profile.url)
                    #execute main thread function
                    job.function(job)
                    #update the data structure with the returned data

            print(f" ** Completed thread - {self.number}")

        def join(self, timeout=None):
            #send stop event to terminate the work loop before calling join
            self._stop_event.set()
            super().join(timeout)
            print(f" ** Joined thread - {self.number}")

class Job:
    #holds all the information needed for the worker threads to make a request and execute the job_function
    def __init__(self, job_id, function, url, custom_data, session = None, lock = None):
        self.id = job_id #will be made the key in main_data, should be unique
        self.url = url
        self.custom_data = custom_data #your data structure, accessible inside your job function (list, dictionaey, list of list, list of dictionaries...)
        self.request = None
        self.function = function
        self.session = None #can set session and lock per job, or can leave unset and attributes will be taken from thread
        self.lock = None

    def set_thread(self, thread):
        """allows access to thread attributes(e.g. session, lock) that may be needed for the job function"""
        self.thread = thread
        # if not set in init, use thread session and lock 
        if self.session == None:
            self.session = self.thread.session
        if self.lock == None:
            self.lock = self.thread.lock

    def get_url(self, exception_on_error = False):
    #TODO this will currently fail silently when exception on error = False, maybe add a log?
    #TODO error handing in general needs work here
        try:
            r = self.thread.session.get(self.url)
            if r.status_code == 200:
                self.request = r
            else:
                if exception_on_error == False:
                    self.request = None
                else:
                    raise ValueError(f"A server error occured, status code: {str(r.status_code)}, URL: {url}")
        except requests.exceptions.ConnectionError:
            if exception_on_error == False:
                self.request = None
            else:
                raise ValueError(f"Could not access url: {url}")

def job_function_template(job):
    """not used, template code for a job_function"""
    job_data = {}
    job.get_url() #get the URL
    if job.request != None: #check that a URL was recieved OK, will be None if there as a problem
        job.lock.acquire() #update/append are thread safe but other operations elsewhere (e.g. JSON.dumps) might not be
        if job.type == "jobtype1": #do something
            job.custom_data.update({"key1":"val3", "key2":"val4"})
        if job.type == "jobtype2": #do something different
            job.custom_data.update({"key1":"val3", "key2":"val4"})
        job.lock.release()