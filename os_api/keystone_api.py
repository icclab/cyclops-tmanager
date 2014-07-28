'''

-*- coding: ascii -*-
--------------------------------------------------------------
Created on Nov 11, 2013

@author: Piyush Harsh
@contact: piyush.harsh@zhaw.ch
@organization: ICCLab, Zurich University of Applied Sciences
@summary: Module to interact with OS-keystone service
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
import getpass
import os

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

dir_path=os.path.join(os.path.dirname( __file__ ), '..',)
config = {}
execfile(dir_path+"/config.conf", config) 

def strip_non_ascii(string):
    ''' 
    Returns the string without non ASCII characters.
    
    Args:
      string: The string to be converted.
      
    Returns:
      string  
    
    '''
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)

def login():
    ''' 
    Returns the user credidentials.
    
      
    Returns:
      string: The user name.
      string: The password.
      string: The tenant id. 
    
    '''    
    user = raw_input("Username [%s]: " % getpass.getuser())
    tenant = raw_input("Tenant Id: ")
    if not user:
        user = getpass.getuser()
    pprompt = lambda: (getpass.getpass())
    p1 = pprompt()
    return user, p1, tenant

def login_v3():
    ''' 
    Returns the user crededentials.
      
    Returns:
      string: User name.
      string: The password.
      string: The domain name.
      string; The project name.
            
    '''    
    user = raw_input("Username [%s]: " % getpass.getuser())
    domain = raw_input("Domain name: ")
    project = raw_input("Project name: ")
    if not user:
        user = getpass.getuser()
    pprompt = lambda: (getpass.getpass())
    p1 = pprompt()
    return user, p1, domain,project

def get_endpoints(tokenId, uri):
    ''' 
    Returns the endpoints for the services.
    
    Args:
      tokenId: X-Auth-String.
      uri: The identity service uri.
       
    
    '''    
    headers = {
               'Accept': 'application/json',
               'Content-Type': 'application/json;'
    }
    uri=config["AUTH_URI"]
    path = '/v2.0/tokens/' + tokenId + '/endpoints'
    target = urlparse(uri+path)
    method = 'GET'
    body = ''
    h = http.Http()
    response, content = h.request(target.geturl(),method,body,headers)
    print "Endpoints:\n" + content
   
def get_token_v3(uri,web,**kwargs):
    ''' 
    Returns the authentication token for v3 keystone.
    
    Args:
      uri: The endpoint to the identity service.
      
    Returns:
      bool: True if successful, False otherwise.
      dict: List of the authentication data.  
    
    '''    
    auth_data = {}
    headers = {
               'Accept': 'application/json',
               'Content-Type': 'application/json;'
    }
    path = '/v3/auth/tokens'
    target = urlparse(uri+path)
    method = 'POST'
    if web==False:
        username, password, domain,project = login_v3()
    else:
        if kwargs:
            username=kwargs.pop("username")
            password=kwargs.pop("password")
            project=kwargs.pop("project")
            domain=kwargs.pop("domain")
        else:
            return False
    #defining the request body here
    body = '{"auth": {"identity": {"methods": ["password"],"password": {"user": {"domain":{"name":"' + domain + '"},"name": "' + username + '","password": "' + password + '"}}},"scope": {"project": {"domain": {"name": "' + domain + '"},"name": "' + project + '"}}}}'
    
    h = http.Http()
    response, content = h.request(target.geturl(),method,body,headers)
    #converting the header of the response to json object
    header = json.dumps(response)
    json_header = json.loads(header)
    
    server_response = json_header["status"]
    auth_data["server-response"] = server_response
    if server_response not in {'201'}:
        print "Inside get_token_v3(): Something went wrong!"
        return False, auth_data
    else:
        data = json.loads(content)
        auth_data["token-issued-at"] = data["token"]["issued_at"]
        auth_data["token-expires-at"] = data["token"]["expires_at"]
        auth_data["token_id"] = json_header["x-subject-token"]
        auth_data["user-name"] = data["token"]["user"]["name"]
        auth_data["user-id"] = data["token"]["user"]["id"]
        for i in range(len(data["token"]["catalog"])):
            catalog_element =  data["token"]["catalog"][i]
            auth_data[catalog_element["type"]] = catalog_element["endpoints"][0]["url"]
    return True, auth_data 

def get_list_tenants(token,api_endpoint):
    headers = {
               'Accept': 'application/json',
               'Content-Type': 'application/json;',
               'X-Auth-Token': token
    }    
    path = '/v2.0/tenants'
    target = urlparse(api_endpoint+path)
    method = 'GET'
    body=''
    tenant_list=[]
    h = http.Http()
    response, content = h.request(target.geturl(),method,body,headers)
    #converting the header of the response to json object
    header = json.dumps(response)
    json_header = json.loads(header)    
    server_response = json_header["status"]
    if server_response not in {'200'}:
        print "Inside get_tenants_list(): Something went wrong!"
        return False, tenant_list
    else:
        data = json.loads(content)
        tenant_list = [None]*len(data["tenants"])
        for i in range(len(data["tenants"])):
            tenant_list[i] = {}
            tenant_list[i]["tenant_id"] = data["tenants"][i]["id"]
            tenant_list[i]["tenant_name"] = data["tenants"][i]["name"]
            tenant_list[i]["tenant_desc"] = data["tenants"][i]["description"]
    return True, tenant_list

def get_users_per_tenant(token,api_endpoint,tenantId):
    headers = {
               'Accept': 'application/json',
               'Content-Type': 'application/json;',
               'X-Auth-Token': token
    }    
    path = '/v2.0/tenants/'+tenantId+'/users'
    target = urlparse(api_endpoint+path)
    method = 'GET'
    body=''
    users_list=[]
    h = http.Http()
    response, content = h.request(target.geturl(),method,body,headers)
    #converting the header of the response to json object
    header = json.dumps(response)
    json_header = json.loads(header)    
    server_response = json_header["status"]
    if server_response not in {'200'}:
        print "Inside get_users_per_tenants(): Something went wrong!"
        return False, users_list
    else:
        data = json.loads(content)
        users_list = [None]*len(data["users"])
        for i in range(len(data["users"])):
            users_list[i] = {}
            users_list[i]["user_id"] = data["users"][i]["id"]
            users_list[i]["user_name"] = data["users"][i]["name"]
            users_list[i]["user_email"] = data["users"][i]["email"]
            users_list[i]["user_enabled"] = data["users"][i]["enabled"]
    return True, users_list
    
def get_token_v2(uri):
    ''' 
    Returns the authentication token for v2 keystone.
    
    Args:
      uri: The endpoint to the identity service.
      
    Returns:
      bool: True if successful, False otherwise.
      dict: List of the authentication data.  
    
    '''       
    auth_data = {}     #an empty dictionary
    headers = {
               'Accept': 'application/json',
               'Content-Type': 'application/json;'
    }
    
    path = '/v2.0/tokens'
    target = urlparse(uri+path)
    method = 'POST'
    username, password, tenant = login()
    #defining the request body here
    body = '{"auth":{"passwordCredentials":{"username": "' + username + '", "password": "' + password + '"},"tenantId":"' + tenant + '"}}'
    
    h = http.Http()
    response, content = h.request(target.geturl(),method,body,headers)
    #converting the header of the response to json object
    header = json.dumps(response)
    json_header = json.loads(header)
    
    server_response = json_header["status"]
    auth_data["server-response"] = server_response
    if server_response not in {'200'}:
        print "Inside get_token_v2(): Something went wrong!"
        return False, auth_data
    else:
        data = json.loads(content)
        auth_data["token-issued-at"] = data["access"]["token"]["issued_at"]
        auth_data["token-expires-at"] = data["access"]["token"]["expires"]
        auth_data["token-id"] = data["access"]["token"]["id"]
        auth_data["user-name"] = data["access"]["user"]["username"]
        auth_data["user-id"] = data["access"]["user"]["id"]
        for i in range(len(data["access"]["serviceCatalog"])):
            catalog_element =  data["access"]["serviceCatalog"][i]
            auth_data[catalog_element["name"]] = catalog_element["endpoints"][0]["publicURL"]
    return True, auth_data 
