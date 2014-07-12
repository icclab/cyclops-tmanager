'''
Created on May 13, 2014

@author:  Tea Kolevska
@contact: tea.kolevska@gmail.com
@organization: ICCLab, Zurich University of Applied Sciences
@summary: Module for creating the server side sockets

 Copyright 2014 Zuercher Hochschule fuer Angewandte Wissenschaften
 All Rights Reserved.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.


'''
import socket
import sys,os
import struct
import periodic_web
import json
import threading
import json
from Queue import Queue
from threading import Thread

def main(argv):  
    running_threads={}   
    print ("In main before while, running threads: %s" %running_threads) 
    HOST = '0.0.0.0'   # Symbolic name meaning all available interfaces
    PORT = 9005 # Arbitrary non-privileged port 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Socket created.")
    try:
        s.bind((HOST, PORT))
    except socket.error , msg:
        print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()
    s.listen(20)
    pool = ThreadPool(20)
    while 1:
        conn, addr = s.accept()
        print("Connection accepted.")
        pool.add_task(socket_connection,conn,running_threads)
        #pid=os.fork()
        #print("Forked with pid %s" %pid)
        #if pid==-1:
        #    os._exit(0)
        #elif pid==0:
        #    socket_connection(s,conn,running_threads)
        #    print (pid, running_threads)
        #else:
        #    conn.close()
        #print(pid, running_threads)
        print("In while poool running threads %s" %running_threads)
        pool.wait_completion()
    return

class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception, e:
                print e
            finally:
                self.tasks.task_done()

class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads): Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()

def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = ''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data
 
def socket_connection(conn,running_threads): 
    #s.close()
    data = conn.recv(1024)
    print("Received data.")
    li_var=[]

    if data=="check threads":
        conn.sendall("ok")
        t_name=conn.recv(1024)
        #with open("threads.json") as f:
        #    running_threads=json.load(f)
        print (running_threads)
        print(t_name)
        if t_name in running_threads:

            conn.sendall("True")     
        else:   
            conn.sendall("False")  
        conn.close()
      
    if data=="periodic_stop":
        conn.sendall("ok")
        t_name=conn.recv(1024)
        #with open('threads.json') as f:
        #    data = json.load(f)
        canceled=False
        print(running_threads)
        for key,value in running_threads.iteritems(): 
            if key==t_name:
                value.cancel()
                canceled=True
        if canceled==True:
            conn.sendall("Stopping counter.")
            del running_threads[t_name] 
        else:
            conn.sendall("Error stopping counter.")
        conn.close()
             
    if data=="periodic_start":
        conn.sendall("ok")
        print("Sent ok.")
        while True:
                raw_msglen = recvall(conn, 4)
                
                if not raw_msglen:
                    return None
                msglen = struct.unpack('>I', raw_msglen)[0]
                # Read the message data
                rez=recvall(conn, msglen)
                #result = json.loads(rez)
                li_var.append(rez)
                print("Received message %s" %rez)
                if rez=="None":
                    print("entering if")
                    break
        conn.sendall("Starting periodic counter for the user.")
        conn.close()
        print("Closing server socket.")
        print("len %s" %len(li_var))
        if len(li_var)==12:
            user=li_var[4]
            thread_name="thread"+user
            print(thread_name)
            name=thread_name
            print("Thread created %s." %thread_name)
            #my_dict={thread_name:user}
            #with open("threads.json") as f:
            #    data = json.load(f)
            #data.update(my_dict)
            #with open('threads.json', 'w') as f:
            #    json.dump(data, f)
            
            thread_name=periodic_web.MyThread(li_var[0],li_var[1],li_var[2],li_var[3],li_var[4],li_var[5],li_var[6],li_var[7],li_var[8],li_var[9],li_var[10],thread_name)
            thread_name.start()
            #my_dict={thread_name:user}
            #.update(my_dict)
            running_threads[name]=thread_name
            #running_threads=add_threads(running_threads,name,thread_name)
            print("Thread started %s." %thread_name)
            print ("Running threads %s" %running_threads)
        conn.close()
    return running_threads





if __name__ == '__main__':
    main(sys.argv[1:])
