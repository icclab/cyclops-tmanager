'''
Created on Apr 9, 2014

@author:  Tea Kolevska
@contact: tea.kolevska@gmail.com
@organization: ICCLab, Zurich University of Applied Sciences
@summary: Module for the periodic pricing thread

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

from threading import Thread
import sys,os
from sympy.core import sympify
import copy
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_ui.settings")
import mysql.connector
from mysql.connector import errorcode
import datetime
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'os_api')))
from os_api import ceilometer_api
from os_api import keystone_api
from time import gmtime, strftime, strptime
from threading import Timer

dir_path=os.path.join(os.path.dirname( __file__ ), '..',)
config = {}
execfile("config.conf", config) 

def is_number(s):
    """

    Check if it is a number.
    
    Args:
      s: The variable that needs to be checked.
      
    Returns:
      bool: True if float, False otherwise.
      
    """    
    try:
        float(s)
        return True
    except ValueError:
        return False


def periodic_counter(self,token_id,token_metering,meters_used,meter_list,func,user,time,from_date,from_time,end_date,end_time,user_id_stack,pricing_list,params,unit):
    """

    Execute the periodic counter.
    
    Args:
    token_data(string): The data received with the authentication.
      token_id(string): X-Auth-token.
      meters_used: List of the meters used in the pricing function.
      meter_list: List of the available meters.
      func: The defined pricing function.
      user: The user for whom we calculate the price.
      time: The time between every loop.
      from_date: The start date.
      from_time: The start time.
      end_date: The end date.
      end_time: The end time.
      user_id_stack: The id of the user.
      
    Returns:
      DateTime: The new start time for the next loop if the duration end is before the end time of the loop.
      
    """        
    udr,new_time=get_udr(self,token_id,token_metering,user,meters_used,meter_list,func,True,from_date,from_time,end_date,end_time,user_id_stack,params)
    price=pricing(self,user,meters_used,pricing_list,udr,unit)
    return new_time
        
def get_udr(self,token_id,token_metering,user,meters_used,meter_list,func,web_bool,from_date,from_time,end_date,end_time,user_id_stack,params):   
    try:
        cnx = mysql.connector.connect(user=config["USER"],
                                      database='db_cyclops',
                                      password=config["PASSWORD"],
                                      host=config["HOST"],
                                      port=config["PORT_DB"])
        cursor=cnx.cursor()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exists")
        else:
            print(err)

    date_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    delta_list=[None]*5
    all_stats=[] 
    total=[None]*len(meters_used)
    new_time="/"
    for i in range(len(meters_used)):
        total[i]=0
        for j in range(len(meter_list)):
            if meters_used[i]==meter_list[j]["meter-name"]:
                resource_id=meter_list[j]["resource-id"]
                q=ceilometer_api.set_query(from_date,end_date,from_time,end_time,resource_id,user_id_stack,True)
                status,stat_list=ceilometer_api.meter_statistics(meters_used[i], token_metering,token_id,meter_list,True,q=q)
                unit=meter_list[j]["meter-unit"]
                if stat_list==[]:
                    total[i]+=0
                else:
                    if meter_list[j]["meter-type"]=="cumulative":
                        total[i]+=stat_list[0]["max"]-stat_list[0]["min"]
                    if meter_list[j]["meter-type"]=="gauge":
                        t1=datetime.datetime.combine(datetime.datetime.strptime(from_date,"%Y-%m-%d").date(),datetime.datetime.strptime(from_time,"%H:%M:%S").time())
                        t2=datetime.datetime.combine(datetime.datetime.strptime(end_date,"%Y-%m-%d").date(),datetime.datetime.strptime(end_time,"%H:%M:%S").time())
                        t=t2-t1
                        time_period=t.total_seconds()
                        total[i]+=stat_list[0]["average"]*time_period
                    if meter_list[j]["meter-type"]=="delta":
                        total[i]+=stat_list[0]["sum"]
                    new_time=stat_list[0]["duration-end"]   
        add_metercounter = ("INSERT INTO main_menu_meterscounter"
                        "(meter_name,user_id_id,counter_volume,unit,timestamp) "
                        "VALUES (%s, %s, %s, %s, %s)")
        data_metercounter = (meters_used[i],user,total[i],unit,date_time)
        cursor.execute(add_metercounter, data_metercounter)

        for m in range(len(params)):
            if params[m]==meters_used[i]:
                delta_list[m]=total[i]
    add_udr = ("INSERT INTO main_menu_udr "
                        "(user_id_id,timestamp,pricing_func_id_id,param1,param2,param3,param4,param5) "
                        "VALUES (%s, %s, %s, %s, %s,%s,%s,%s)")
    data_udr = (user,date_time,str(func),str(delta_list[0]),str(delta_list[1]),str(delta_list[2]),str(delta_list[3]),str(delta_list[4]))
    cursor.execute(add_udr, data_udr)

    cnx.commit()
    cursor.close()
    cnx.close()
    udr={'param1':delta_list[0],'param2':delta_list[1],'param3':delta_list[2],'param4':delta_list[3],'param5':delta_list[4]}
    return udr,new_time



def pricing(self,user,meters_used,pricing_list,udr,unit):
    try:
        cnx = mysql.connector.connect(user=config["USER"],
                                      database='db_cyclops',
                                      password=config["PASSWORD"],
                                      host=config["HOST"],
                                      port=config["PORT_DB"])
        cursor=cnx.cursor()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exists")
        else:
            print(err)
    query = ("SELECT id FROM main_menu_pricingfunc WHERE user_id_id=%s")
    data_query=user
    cursor.execute(query,data_query)
    for row in cursor:
        func_id=row[0]
    price_helper_list=copy.copy(pricing_list) 
    udr_list=[]
    udr_list.append(udr['param1'])
    udr_list.append(udr['param2'])
    udr_list.append(udr['param3'])
    udr_list.append(udr['param4'])
    udr_list.append(udr['param5'])
    for i in udr_list:
        if i==None:
            i=0
            
    k=0
    for i in range(len(pricing_list)):
        if pricing_list[i] in meters_used:
            price_helper_list[i]=udr_list[k]
        if i%2==0:
            k+=1
    print pricing_list        
    price=0.0 
    str_expr=""
    for i in range(len(pricing_list)):
        if i!=None:
            str_expr+=str(price_helper_list[i])
        else:
            break
    print(str_expr)
    expr=sympify(str_expr)   
    price=expr.evalf()
    print price
    price=price*float(unit)   
    date_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    add_pricecdr = ("INSERT INTO main_menu_pricecdr "
               "(price,timestamp,user_id_id,pricing_func_id_id) "
               "VALUES (%s, %s, %s, %s)")
    data_pricecdr = (str(price) ,date_time,user,str(func_id))
    cursor.execute(add_pricecdr, data_pricecdr)
    cnx.commit()
    cursor.close()
    cnx.close()
    print ("Price calculated. Inserted into CDR table.")
    return price



class MyThread(Thread):
    def __init__(self, username,password,domain,project,user,time_f,from_date,from_time,end_date,end_time,user_id_stack,name):
        super(MyThread, self).__init__()
        auth_uri = config["AUTH_URI"]
        try:
            cnx = mysql.connector.connect(user=config["USER"],
                                      database='db_cyclops',
                                      password=config["PASSWORD"],
                                      host=config["HOST"],
                                      port=config["PORT_DB"])
            cursor=cnx.cursor()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exists")
            else:
                print(err)
        self.username=username
        self.password=password
        self.domain=domain
        self.project=project
        status, token_data = keystone_api.get_token_v3(auth_uri,True,username=username, password=password, domain=domain,project=project)
        self.daemon = True
        self.cancelled = False
        self.token_id=token_data["token_id"] 
        self.token_metering=token_data["metering"]
        self.user=user    
        self.from_date=from_date
        self.from_time=from_time
        self.end_date=end_date
        self.end_time=end_time
        self.time_f=float(time_f)*3600
        self.user_id_stack=user_id_stack
        status_meter_list, self.meter_list = ceilometer_api.get_meter_list(self.token_id, self.token_metering)                              
        self.pricing_list=[]
        self.meters_used=[]
        query = ("SELECT param1,sign1,param2,sign2,param3,sign3,param4,sign4,param5,ID,unit FROM main_menu_pricingfunc WHERE user_id_id=%s")
        data_query=user
        self.params=[]
        cursor.execute(query,data_query)
        for row in cursor:
            self.pricing_list.append(row[0])
            self.pricing_list.append(row[1])
            self.pricing_list.append(row[2])
            self.pricing_list.append(row[3])
            self.pricing_list.append(row[4])
            self.pricing_list.append(row[5])
            self.pricing_list.append(row[6])
            self.pricing_list.append(row[7])
            self.pricing_list.append(row[8])
            self.params.append(row[0])
            self.params.append(row[2])
            self.params.append(row[4])
            self.params.append(row[6])
            self.params.append(row[8])
            self.func=row[9]  
            self.unit=row[10]
            print(row)
        print("Inside init thread.")
        cnx.commit()
        cursor.close()
        cnx.close()
        self.name=name            
        for i in range(len(self.pricing_list)):
            j=0
            while j<len(self.meter_list):
                if self.pricing_list[i]==self.meter_list[j]["meter-name"]:
                    if self.pricing_list[i] in self.meters_used:
                        continue
                    else:
                        self.meters_used.append(self.pricing_list[i])                                                                
                    break
                else:
                    j=j+1
    def run(self):
        """Overloaded Thread.run"""
        print("Inside thread run")
        while not self.cancelled:
            print ("while not cancelled")
            new_time=periodic_counter(self,self.token_id,self.token_metering,self.meters_used,self.meter_list,self.func,self.user,self.time_f,self.from_date,self.from_time,self.end_date,self.end_time,self.user_id_stack,self.pricing_list,self.params,self.unit)
            if new_time=="/":
                self.from_time=self.end_time
                self.from_date=self.end_date
            else:
                new_time=new_time.split("T")
                self.from_date=new_time[0]    
                self.from_time=new_time[1]
            today = datetime.date.today()
            today.strftime("%Y-%m-%d")
            now = datetime.datetime.now()
            now=datetime.time(now.hour, now.minute, now.second)
            now.strftime("%H:%M:%S")
            self.end_date=str(today)
            self.end_time=str(now)

            time.sleep(self.time_f)

    def cancel(self):
        """End this timer thread"""
        self.cancelled = True
        

    
    def setName(self,name):
        self.name=name
        
    def getName(self):
        return self.name
        
