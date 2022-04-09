from threading import Thread, Lock
import time

MY_MUTEX = Lock()

class Master:
    def __init__(self):
        self.Test = Test()
        pass

    def start(self):
        for i in range(100):
            t = Thread(target=self.Test.useMutex, args=(i,))
            t.start()
        pass

class Test:
    def __init__(self):
        pass

    def useMutex(self, id):
        print("id:" + str(id) + " waiting for mutex")
        MY_MUTEX.acquire()
        try:
            print("id:" + str(id) + " has mutex")
            time.sleep(1)
        finally:
            print("id:" + str(id) + " released mutex")
            MY_MUTEX.release()

if __name__ == "__main__":
    m = Master()
    m.start()