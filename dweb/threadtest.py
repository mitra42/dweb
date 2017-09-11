# encoding: utf-8
#  Simple thread queue test

import threading
import time
bar = "Global variable"

class ThreadingExample(object):
    def __init__(self, interval):
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        self.queue = []
        self.interval = interval
        self.name="My thread"
        thread.start()
        time.sleep(1)
        print "This is the __init__ woken from sleep, and name here is",self.name

    def run(self):
        print self.__class__.__name__   # Gets the "ThreadingExample"
        print "name in thread",self.name                 # Gets the variable from ThreadingExample
        print self.interval
        self.name = "Foo"                                # Change name, main should see this.
        print "name in thread",self.name                 # shows it changed
        while True:
            while len(self.queue):
                t = self.queue.pop(0)    # First item on queue
                print t**2
            time.sleep(self.interval)    # Sleeps in outer loop, only when queue is empty
        # Never exits

    def add(self,i):
        print ">",i
        self.queue.append(i)

print "bar=",bar
example = ThreadingExample(5)
time.sleep(2)
example.add(5)
print "bar=",bar
time.sleep(2)
print "name in main",example.name      # Note it gets the new name,
example.add(6)
time.sleep(2)
example.add(7)
time.sleep(1)
example.add(8)
time.sleep(1)
example.add(9)
time.sleep(1)
example.add(10)
time.sleep(1)
example.add(11)
time.sleep(1)
example.add(12)
time.sleep(1)
example.add(13)
time.sleep(1)

