'''

-*- coding: ascii -*-
--------------------------------------------------------------
Created on Nov 21, 2013

@author: Piyush Harsh
@contact: piyush.harsh@zhaw.ch
@organization: ICCLab, Zurich University of Applied Sciences
@summary: Module to interact with OS-ceilometer service
@contributor: Tea Kolevska
@contact: tea.kolevska@gmail.com
@var username, tenant-id, password
@requires: python 2.7

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

import httplib2 as http
import sys, re
import json
import logging
from collections import namedtuple
import os

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
 
path=(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'logs'))) 
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
handler = logging.FileHandler(path+'/ceilometer.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False      
    
def get_meter_list(token, api_endpoint):
    """

    Get the list of available meters.
    
    Args:
      token(string): X-Auth-token.
      api_endpoint(string): The api endpoint for the ceilometer service.
      
    Returns:
      bool: True if successful, False otherwise.
      list: The list with the available meters.
      
    """    
    meter_list = [None]
    headers = {
               'Accept': 'application/json',
               'Content-Type': 'application/json;',
               'X-Auth-Token': token
    }
    path = "/v2/meters"
    target = urlparse(api_endpoint+path)
    logger.info('Path is %s',target)
    method = 'GET'
    body = ''
    h = http.Http()
    response, content = h.request(target.geturl(),method,body,headers)
    #converting the header of the response to json object
    header = json.dumps(response)
    json_header = json.loads(header)
    
    server_response = json_header["status"]
    if server_response not in {'200'}:
        print "Inside get_server_list(): Something went wrong!"
        logger.warn('Not a valid response')
        return False, meter_list
    else:
        data = json.loads(content)
        logger.info('Return meter list \n')
        meter_list = [None]*len(data)
        for i in range(len(data)):
            meter_list[i] = {}
            meter_list[i]["user-id"] = data[i]["user_id"]
            meter_list[i]["meter-name"] = data[i]["name"]
            meter_list[i]["resource-id"] = data[i]["resource_id"]
            meter_list[i]["meter-source"] = data[i]["source"]
            meter_list[i]["meter-id"] = data[i]["meter_id"]
            meter_list[i]["tenant-id"] = data[i]["project_id"]
            meter_list[i]["meter-type"] = data[i]["type"]
            meter_list[i]["meter-unit"] = data[i]["unit"]
    return True, meter_list


def is_in_mlist(meter_name,meter_list):
    """

    Check if the meter is in the list of available meters.
    
    Args:
      meter_name(string): The name of the meter that is being checked.
      meter_list(string): The list of available meters.
      
    Returns:
      bool: True if successful, False otherwise.
      
    """ 
    status=False
    for i in range(len(meter_list)):
        if meter_name==meter_list[i]["meter-name"]:
            status=True 
    return status


def query():
    """

    Get the query details.
    
    Args:
      None.
      
    Returns:
      string: Defined starting date.
      string: Defined starting time.
      string: Defined ending date.
      string: Defined ending time.
      string: Defined resource id.
      string: Defined project id.
      bool: True if successful, False otherwise.
      
    """       
    status=False
    
    period=raw_input("Do you want to define the starting and ending time? If yes, enter 'Y',else enter 'N'. ")
    if(period=="Y"):
        from_date = raw_input("Date from yyyy-mm-dd: ")
        from_time= raw_input("Time from hh:mm:ss ")
        to_date = raw_input("Date to yyyy-mm-dd: ")
        to_time= raw_input("Time to hh:mm:ss ")
        status=True
    else:
        from_date="/" 
        to_date="/" 
        from_time="/" 
        to_time="/" 
    rid=raw_input("Do you want to define the resource id? If yes, enter 'Y', else enter 'N'. ")
    if(rid=="Y"):
        resource_id=raw_input("Enter the resource id: ")
        status=True
    else:
        resource_id="/"
    pid=raw_input("Do you want to define the user id? If yes, enter 'Y', else enter 'N'. ")
    if(pid=="Y"):
        user_id=raw_input("Enter the user id: ")
        status=True
    else:
        user_id="/"
    return from_date,to_date,from_time,to_time,resource_id,user_id,status


def set_query(from_date,to_date,from_time,to_time,resource_id,user_id,status_q):
    """

    Define the query.
    
    Args:
      string: Defined starting date.
      string: Defined starting time.
      string: Defined ending date.
      string: Defined ending time.
      string: Defined resource id.
      string: Defined user id.
      bool: True if successful, False otherwise.
      
    Returns:
      string: Properly defined query field for the api call.
      
    """       
    if(status_q==True):
        q='"q":['
        if (from_date not in "/"):
            q= q+'{"field": "timestamp","op": "ge","value": "'+from_date+'T'+from_time+'"},{"field": "timestamp","op": "lt","value": "'+to_date+'T'+to_time+'"}'
            if (resource_id != "/"):
                q=q+',{"field": "resource_id","op": "eq","value": "'+resource_id+'"}'
                if (user_id != "/"):
                    q=q+',{"field": "user_id","op": "eq","value": "'+user_id+'"}'
            else:
                if (user_id != "/"):
                    q=q+',{"field": "user_id","op": "eq","value": "'+user_id+'"}'
        else:
            if (resource_id != "/"):
                q=q+'{"field": "resource_id","op": "eq","value": "'+resource_id+'"}'
                if (user_id != "/"):
                    q=q+',{"field": "user_id","op": "eq","value": "'+user_id+'"}'
            else:
                if (user_id != "/"):
                    q=q+'{"field": "user_id","op": "eq","value": "'+user_id+'"}'
        q=q+']'
    return q



def meter_statistics(meter_id,api_endpoint,token,meter_list,web,**kwargs):
    """

    Get the statistics for the specified meter.
    
    Args:
      meter_id(string): The meter name.
      api_endpoint(string): The api endpoint for the ceilometer service.
      token(string): X-Auth-token.
      meter_list(list): The list of available meters.
      
    Returns:
      bool: True if successful, False otherwise.
      list: The list with the meter statistics.
      
    """      
    meter_stat = [None]
    headers = {
               #'Accept': 'application/json',
               'Content-Type': 'application/json;',
               'X-Auth-Token': token
               
    }



        
    path = "/v2/meters/"+meter_id+"/statistics"
    target = urlparse(api_endpoint+path)
    method = 'GET'
    logger.info('Inside meter-statistics: Path is %s',target)
    if(web==False):    
        from_date,to_date,from_time,to_time,resource_id,user_id,status_q=query()   
        if(status_q==True):
            q=set_query(from_date,to_date,from_time,to_time,resource_id,user_id,status_q)
            body="{"+q
            period=raw_input("Do you want to define a time period? Enter 'Y' if yes, 'N' if no.")
            if(period=="Y"):
                period_def=raw_input("Enter the desired time period in seconds: ")
                body=body+',"period":'+period_def
            groupby=raw_input("Do you want to define a group by value? Enter 'Y' if yes, 'N' if no.")  
            if (groupby=="Y") :
                rid=raw_input("Do you want to group by the resource id? If yes, enter 'Y', else enter 'N'. ")
                if(rid=="Y"):
                        groupby_def=',"groupby":['
                        groupby_def=groupby_def+'"resource_id"'
                        pid=raw_input("Do you want to group by the project id? If yes, enter 'Y', else enter 'N'. ")
                        if(pid=="Y"):
                            groupby_def=groupby_def+',"project_id"'  
                            groupby_def=groupby_def+']'
                            body=body+groupby_def            
                else:
                    pid=raw_input("Do you want to group by the project id? If yes, enter 'Y', else enter 'N'. ")
                    if(pid=="Y"):
                        groupby_def=',"groupby":['
                        groupby_def=groupby_def+'"project_id"'  
                        groupby_def=groupby_def+']'
                        body=body+groupby_def
            body=body+"}"
        else:
            body="{"
            period=raw_input("Do you want to define a time period? Enter 'Y' if yes, 'N' if no.")
            if(period=="Y"):
                period_def=raw_input("Enter the desired time period in seconds: ")
                body=body+'"period":'+period_def
                rid=raw_input("Do you want to group by the resource id? If yes, enter 'Y', else enter 'N'. ")
                if(rid=="Y"):
                    groupby_def=',"groupby":['
                    groupby_def=groupby_def+'"resource_id"'
                    pid=raw_input("Do you want to group by the project id? If yes, enter 'Y', else enter 'N'. ")
                    if(pid=="Y"):
                        groupby_def=groupby_def+',"project_id"'  
                        groupby_def=groupby_def+']'
                        body=body+groupby_def            
                    else:
                        pid=raw_input("Do you want to group by the project id? If yes, enter 'Y', else enter 'N'. ")
                        if(pid=="Y"):
                            groupby_def=',"groupby":['
                            groupby_def=groupby_def+'"project_id"'  
                            groupby_def=groupby_def+']'
                            body=body+groupby_def
                body=body+"}"
            else: 
                rid=raw_input("Do you want to group by the resource id? If yes, enter 'Y', else enter 'N'. ")
                if(rid=="Y"):
                        groupby_def='"groupby":['
                        groupby_def=groupby_def+'"resource_id"'
                        pid=raw_input("Do you want to group by the project id? If yes, enter 'Y', else enter 'N'. ")
                        if(pid=="Y"):
                            groupby_def=groupby_def+',"project_id"'  
                        groupby_def=groupby_def+']'
                        body=body+groupby_def            
                else:
                    pid=raw_input("Do you want to group by the project id? If yes, enter 'Y', else enter 'N'. ")
                    if(pid=="Y"):
                        groupby_def='"groupby":['
                        groupby_def=groupby_def+'"project_id"'  
                        groupby_def=groupby_def+']'
                        body=body+groupby_def
                body=body+"}"
    else:       
        q=kwargs.pop('q')
        if 'period' in kwargs:
            period=kwargs.pop('period')
            body="{"+q
            body=body+',"period":'+period+"}"
        else:   
            body="{"+q+"}"
        
    if is_in_mlist(meter_id,meter_list):        
        logger.info('Inside meter_statistics: body is  %s',body)        
        h = http.Http()
        response, content = h.request(target.geturl(),method,body,headers)
        header = json.dumps(response)
        json_header = json.loads(header)
    
        server_response = json_header["status"]
        if server_response not in {'200'}:
            print "Inside meter_statistics(): Something went wrong!"
            logger.warn('Inside meter_statistics: not a valid response ')
            return False, meter_stat
        else:
            logger.info('Getting the meter statistics \n')
            data = json.loads(content)
            meter_stat = [None]*len(data)
            for i in range(len(data)):
                meter_stat[i]={}
                meter_stat[i]["average"] = data[i]["avg"]
                meter_stat[i]["count"] = data[i]["count"]
                meter_stat[i]["duration"] = data[i]["duration"]
                meter_stat[i]["duration-end"] = data[i]["duration_end"]
                meter_stat[i]["duration-start"] = data[i]["duration_start"]
                meter_stat[i]["max"] = data[i]["max"]
                meter_stat[i]["min"] = data[i]["min"]
                meter_stat[i]["period"] = data[i]["period"]
                meter_stat[i]["period-end"] = data[i]["period_end"]
                meter_stat[i]["period-start"] = data[i]["period_start"]
                meter_stat[i]["sum"] = data[i]["sum"]
                meter_stat[i]["unit"] = data[i]["unit"]
                meter_stat[i]["group-by"] = data[i]["groupby"]
            return True, meter_stat
    else:
        logger.warn("Inside meter statistics: not an existing meter name")  
        print "Choose a meter from the meter list!"
        return False,meter_stat
      

def get_meter_samples(meter_name,api_endpoint,token,bool_query,meter_list,web,q):
    """

    Get the samples for the specified meter.
    
    Args:
      meter_name(string): The meter name.
      api_endpoint(string): The api endpoint for the ceilometer service.
      token(string): X-Auth-token.
      bool_query(bool): True if query needs to be specified, False otherwise.
      meter_list(list): The list of available meters.
      
    Returns:
      bool: True if successful, False otherwise.
      list: The list with the meter samples.
      
    """          
    meter_samples=[None]
    if is_in_mlist(meter_name,meter_list): 

        headers = {
               'Content-Type': 'application/json;',
               'X-Auth-Token': token
               
        }   
        path = "/v2/meters/"+meter_name
        target = urlparse(api_endpoint+path)
        logger.info('Inside get_meter_sample: Path is %s',target)
        method = 'GET'
        if web==False:      
            if bool_query==True:
                from_date,to_date,from_time,to_time,resource_id,user_id,status_q=query()
                if(status_q==True):
                    q=set_query(from_date,to_date,from_time,to_time,resource_id,user_id,status_q)
                    body="{"+q
                    limit=raw_input("Do you want to set a limit to the number of samples that gets returned? Enter 'Y' if yes, 'N' if no.")
                    if(limit=="Y"):
                        limit_def=raw_input("Enter the desired limit for the number of samples: ")
                        body=body+',"limit":'+limit_def
                    body=body+"}"
                else:
                    body="{"
                    limit=raw_input("Do you want to set a limit to the number of samples that gets returned? Enter 'Y' if yes, 'N' if no.")
                    if(limit=="Y"):
                        limit_def=raw_input("Enter the desired limit for the number of samples: ")
                        body=body+'"limit":'+limit_def
                    body=body+"}"
            else:
                body='{"limit": 1 }'
        else:
            if q=='':
                body='{"limit": 1 }'
            else:
                body="{"+q+"}"
            
    
        logger.info('Inside get_meter_samples: Body is %s', body)
        h = http.Http()
        response, content = h.request(target.geturl(),method,body,headers)
        header = json.dumps(response)
        json_header = json.loads(header)
    
        server_response = json_header["status"]
        if server_response not in {'200'}:
            print "Inside meter_samples(): Something went wrong!"
            logger.warn('Inside meter_samples: not a valid response ')
            return False, meter_samples
        else:
            logger.info('Fetching meter samples \n')
            data = json.loads(content)
            meter_samples = [None]*len(data)

            for i in range(len(data)):
                meter_samples[i]={}
                meter_samples[i]["counter-name"] = data[i]["counter_name"]
                meter_samples[i]["counter-type"] = data[i]["counter_type"]
                meter_samples[i]["counter-unit"] = data[i]["counter_unit"]
                meter_samples[i]["counter-volume"] = data[i]["counter_volume"]
                meter_samples[i]["message-id"] = data[i]["message_id"]
                meter_samples[i]["project-id"] = data[i]["project_id"]
                meter_samples[i]["resource-id"] = data[i]["resource_id"]
                catalog=data[i]["resource_metadata"]
                cat_pom = json.dumps(catalog)
                cat_pom=cat_pom.translate(None,'"{}')
                meter_samples[i]["resource-metadata"]=cat_pom
                meter_samples[i]["source"] = data[i]["source"]
                meter_samples[i]["timestamp"] = data[i]["timestamp"]
                meter_samples[i]["user-id"] = data[i]["user_id"]
            return True, meter_samples
    else:
        logger.warn("Inside meter samples: not an existing meter name")  
        print "Choose a meter from the meter list!"
        return False,meter_samples
        
   
def get_resources(api_endpoint,token,bool_query):
    """

    Get the list of available resources.
    
    Args:
      api_endpoint(string): The api endpoint for the ceilometer service.
      token(string): X-Auth-token.
      bool_query(bool): True if query needs to be specified, False otherwise.
      
    Returns:
      bool: True if successful, False otherwise.
      list: The list with the available resources.
      
    """       
    resources_list=[None]
    headers = {
               'Content-Type': 'application/json;',
               'X-Auth-Token': token
               
    }
 
    path = "/v2/resources"
    target = urlparse(api_endpoint+path)
    logger.info('Inside get_resources: Path is %s',target)
    method = 'GET'
    
    if bool_query:
        from_date,to_date,from_time,to_time,resource_id,user_id,status_q=query()  
        body="{"
        if(status_q==True):
            q=set_query(from_date,to_date,from_time,to_time,resource_id,user_id,status_q)
            body=body+q
        body=body+"}"
    else:
         body='{}'
    logger.info('Inside get_resources: Body is %s', body)   
    h = http.Http()
    response, content = h.request(target.geturl(),method,body,headers)
    header = json.dumps(response)
    json_header = json.loads(header)
    
    server_response = json_header["status"]
    if server_response not in {'200'}:
        print "Inside resources_list(): Something went wrong!"
        logger.warn('Inside resources_list: not a valid response ')
        return False, resources_list
    else:
        logger.info('Fetching resources \n')
        data = json.loads(content)
        resources_list = [None]*len(data)  
        links_list=[None]      
        
        for i in range(len(data)):
            resources_list[i]={}
            links_list = [None]*len(data[i]["links"]) 
            for j in range(len(data[i]["links"])):
                links_list[j]={}
                links_list[j]["href"]=data[i]["links"][j]["href"]
                links_list[j]["rel"]=data[i]["links"][j]["rel"]
            resources_list[i]["links"] = links_list
            catalog=data[i]["metadata"]
            cat_pom = json.dumps(catalog)
            cat_pom=cat_pom.translate(None,'"{}')
            resources_list[i]["metadata"]=cat_pom
            resources_list[i]["project-id"] = data[i]["project_id"]
            resources_list[i]["resource-id"] = data[i]["resource_id"]
            #resources_list[i]["source"] = data[i]["source"]
            resources_list[i]["user-id"]=data[i]["user_id"]
        return True, resources_list       

               
def get_resources_by_id(api_endpoint,token,rid):
    """

    Get the details for a certain resource.
    
    Args:
      api_endpoint(string): The api endpoint for the ceilometer service.
      token(string): X-Auth-token.
      rid(string): The id of the soecified resource.
      
    Returns:
      bool: True if successful, False otherwise.
      list: The list with the resources.
      
    """      
    
    resources_list=[None]
    resources_list={}
    if rid=="":
        print "Resource id required!"
        return False,{}

    else:    
        headers = {
               'Content-Type': 'application/json;',
               'X-Auth-Token': token
               
        }
 
        path = "/v2/resources/"+rid
        target = urlparse(api_endpoint+path)
        logger.info('Inside get_resources_by_id: Path is %s',target)
        method = 'GET'
        body="{"

        body=body+"}"
        
        h = http.Http()
        response, content = h.request(target.geturl(),method,body,headers)
        header = json.dumps(response)
        json_header = json.loads(header)
    
        server_response = json_header["status"]
        if server_response not in {'200'}:
            print "Inside resources_list(): Something went wrong!"
            logger.warn('Inside resources_by_id: not a valid response ')
            return False, resources_list
        else:
            logger.info('Fetching resources for id \n')
            data = json.loads(content)
            resources_list = [None]*len(data)  
            links_list=[None]      
        
            for i in range(len(data)):
                resources_list[i]={}
                links_list = [None]*len(data["links"]) 
                for j in range(len(data["links"])):
                    links_list[j]={}
                    links_list[j]["href"]=data["links"][j]["href"]
                    links_list[j]["rel"]=data["links"][j]["rel"]
                resources_list[i]["links"] = links_list
                catalog=data["metadata"]
                cat_pom = json.dumps(catalog)
                cat_pom=cat_pom.translate(None,'"{}')
                resources_list[i]["metadata"]=cat_pom
                resources_list[i]["project-id"] = data["project_id"]
                resources_list[i]["resource-id"] = data["resource_id"]
                #resources_list[i]["source"] = data["source"]
                #resources_list[i]["first-sample-timestamp"]=data["first_sample_timestamp"]
                #resources_list[i]["last-sample-timestamp"]=data["last_sample_timestamp"]

                resources_list[i]["user-id"]=data["user_id"]
                return True, resources_list       
        
    
    
    
    
    
    
    
    