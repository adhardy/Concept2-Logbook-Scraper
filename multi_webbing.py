import queue #multithreading
import threading

class Job:
    #holds all the information needed for the worker threads to visit a page and scrape data
    def __init__(self, profile_id, profile_type, url, main_data, cache):
        self.id = profile_id
        self.type = profile_type
        self.url = url
        self.main_data = main_data
        self.cache = cache       

class WebThread(threading.Thread):
    #define how the threads function
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
                job_data = self.job_function(job, self.session)
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
