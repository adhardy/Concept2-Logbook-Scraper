import queue #multithreading
import threading
import requests

class Job:
    #holds all the information needed for the worker threads to visit a page and scrape data
    def __init__(self, profile_id, profile_type, url, main_data, cache):
        self.id = profile_id
        self.type = profile_type
        self.url = url
        self.main_data = main_data
        self.cache = cache  
        self.request = None

    def get_url(self, web_thread, exception_on_error = False):
    #TODO this will currently fail silently when exception on error = False, maybe add a log?
    #TODO error handing in general needs work here
        try:
            r = web_thread.session.get(self.url)
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

class Thread(threading.Thread):
    #define how the threads function
    #TODO add verbosity for more detailed output options
    def __init__(self, name, job_queue, lock, session, job_function):
        threading.Thread.__init__(self)
        self.name = name
        self._stop_event = threading.Event()
        self.job_queue = job_queue
        self.lock = lock
        self.session = session
        self.job_function = job_function

    def run(self):
        #execute on thread.start()
        #job_function should take 
        print(f" ** Starting thread - {self.name}")

        while not self._stop_event.isSet():
            #thread will continuously check the queue for work until the master process joins the threads, and the stop_event signal is sent
            try:
                #get a job
                job = self.job_queue.get(block=False)

            except queue.Empty:
                pass

            else:
                #print("Thread " + self.name + ": Getting profile: " + profile.url)
                #execute main thread function
                job_data = {}
                job.get_url(self)
                job_data = self.job_function(job)
                #update the data structure with the returned data
                self.lock.acquire() #dict.update is thread safe but json.dumps is not, need to hold here when printing output
                job.main_data.update({job.id:job_data})
                job.cache.update({job.id:job_data})
                self.lock.release()

        print(f" ** Completed thread - {self.name}")

    def join(self, timeout=None):
        #send stop event to terminate the work loop before calling join
        self._stop_event.set()
        super().join(timeout)
        print(f" ** Joined thread - {self.name}")

