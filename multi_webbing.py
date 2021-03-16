import queue #multithreading
import threading
import C2Scrape

class Profile:
    #holds all the information needed for the worker threads to visit this profile and scrape data
    def __init__(self, profile_id, profile_type, url, profile_list, profile_cache, lock,session):
        self.profile_id = profile_id
        self.profile_type = profile_type
        self.url = url
        self.profile_list = profile_list
        self.profile_cache = profile_cache
        self.data = None #json object with the profile data
        self.lock = lock
        self.session = session

class ProfileThread(threading.Thread):
    #define how the threads function
    def __init__(self, name, profile_queue):
        threading.Thread.__init__(self)
        self.name = name
        self._stop_event = threading.Event()
        self.profile_queue = profile_queue

    def run(self):
        #execute on thread.start()
        print(f" ** Starting thread - {self.name}")

        while not self._stop_event.isSet():
            #thread will continuously check the queue for work until the master process joins the threads, and the stop_event signal is sent
            try:
                profile = self.profile_queue.get(block=False)

            except queue.Empty:
                pass

            else:
                #print("Thread " + self.name + ": Getting profile: " + profile.url)
                C2Scrape.thread_get_profile(profile)

        print(f" ** Completed thread - {self.name}")

    
    def join(self, timeout=None):
        #send stop event to terminate the work loop before calling join
        self._stop_event.set()
        super().join(timeout)
        print(f" ** Joined thread - {self.name}")

