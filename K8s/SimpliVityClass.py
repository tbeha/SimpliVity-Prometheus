# -*- coding: utf-8 -*-
"""
Python Class Library for the HPE SimpliVity Rest API v 4.0.0

Copyright (c) Thomas Beha, June 2020

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    https://www.gnu.org/licenses/gpl-3.0.en.html 

Requirements:
    requests
    datetime

RestAPI Response codes:
    200     OK
    201     Created
    202     Accepted
    204     No Content
    400     Bad Request
    401     Unauthorized
    403     Forbidden
    404     Not Found
    405     Method not allowed
    413     Payload too large
    415     Unsupported Media Type
    500     Internal server error
    502     Bad Gateway
    504     Gateway timeout
    551     No backup found 

v4.0.0 of the SimpliVity Class includes the complete parameter list of each
possible RestAPI call. The parameters must be provided as an array of key-value pairs, 
where the key is the parameter name.

This SimpliVity Class is tested against the RestAPI of OmniStack 4.0.0 and 4.0.1

The calls will work with the default limit of 500. If you do have more than 500 entries, then you need to handle
this in your code by either raising the limit (optional parameter) or recursive calls with offset. 

"""

import requests
import datetime

DEBUG = False  

class SimpliVity:
    """
    class SimpliVity
    routines for the SimpliVity RestAPI
    """
    def __init__(self, url):
        self.url = url                      # base URL
        self.access_token= ''               # session access token
        self.headers = {}                   # requests headers
        self.jsonversion="application/vnd.simplivity.v1.9+json"
        requests.urllib3.disable_warnings() # suppress https security warnings

    def doGet(self, url):
        response = requests.get(url, verify=False, headers=self.headers)
        if(response.status_code == 200):
            return response.json()
        else:
            raise SvtError('doGet '+url,response.status_code,response.json())

    def doPost(self, url, body=None):
        if body:
            headers = self.headers
            headers['Content-Type'] = self.jsonversion
            response = requests.post(url,data=body, verify=False, headers=headers)
        else:
            response = requests.post(url, verify=False, headers=self.headers)
        if((response.status_code == 200) or (response.status_code == 201) or (response.status_code == 202)):
            return response.json()
        else:
            raise SvtError('doPost '+url,response.status_code,response.json())        

    def doDelete(self, url):
        response = requests.delete(url, verify=False, headers=self.headers)
        if((response.status_code == 200) or (response.status_code == 201) or (response.status_code == 202)):
            return response.json()
        else:
            raise SvtError('doDelete '+url,response.status_code,response.json())

    def Connect(self, hms_username, hms_password):
        response = requests.post(self.url+'oauth/token', auth=('simplivity', ''), verify=False, data={
                'grant_type':'password',
                'username':hms_username,
                'password':hms_password})
        if(response.status_code == 200):
            self.access_token = response.json()['access_token']
            self.headers = {'Authorization':  'Bearer ' + self.access_token, 
                        'Accept' : self.jsonversion}
            return response
        else:
            raise SvtError('SimpliVity.connect',response.status_code, response.json())

    """ Task Operations """

    def GetTask(self, task_id):
        return self.doGet(self.url+'tasks/'+task_id)
    
    """ Certificate Operations ########################################################################"""

    def GetCertificate(self, certid = None):
        if certid:
            return self.doGet(self.url+'certificates/'+certid)
        else:
            return self.doGet(self.url+'certificates')

    def PostCertificate(self, certificate):
        body = '{"certificate":"'+certificate+'"}'
        return self.doPost(self.url+'certificates', body)   

    def DeleteCertificate(self, certid):
        return self.doDelete(self.url+'certificates/'+certid)
    
    """ Host Operations ########################################################################"""
    
    def GetHost(self, parameters = None ):
        """  Parameters:
            show_optional_fields
            id
            name
            type
            model
            version
            ...
        """
        url = self.url+'hosts'
        if parameters:
            url = url+'?'
            i = 0
            for x in parameters:
                if i > 0: url = url + '&' 
                url = url+x+'='+parameters[x]
                i += 1  
        return self.doGet(url)

    def GetHostId(self, name):
        for x in self.GetHost({'name':name})['hosts']:
            if x['state'] == 'ALIVE':
                return x['id']
        return x['id']

    def GetHostMetrics(self, name, timerange='43200', resolution='Minute', timeOffset='0'):
        url = self.url +'hosts/'+self.GetHostId(name)+'/metrics?range='+timerange+'&resolution='+resolution+'&offset='+timeOffset+'&show_optional_fields=true'
        return self.doGet(url)

    def GetHostCapacity(self, name, timerange='43200', resolution='Minute', timeOffset='0'):
        url = self.url +'hosts/'+self.GetHostId(name)+'/capacity?range='+timerange+'&resolution='+resolution+'&offset='+timeOffset+'&show_optional_fields=true'
        return self.doGet(url)     
       
    def GetHostHardware(self, name):
        url = self.url +'hosts/'+self.GetHostId(name)+'/hardware'    
        return self.doGet(url)
       
    def ShutdownOVC(self, host_id, ha_wait=True):
        return self.doPost(self.url+'hosts/'+host_id+'/shutdown_virtual_controller')

    def CancelShutdownOVC(self, host_id):
        return self.doPost(self.url+'hosts/'+host_id+'/cancel_virtual_controller_shutdown')

    def GetOVCShutdownStatus(self, host_id):
        return self.doGet(self.url+'hosts/'+host_id+'/virtual_controller_shutdown_status')

    def RemoveHostFromFederation(self,host_id, force=False ):
        body='{"force":"'+force+'"}'
        return self.doPost(self.url+'hosts/'+host_id+'/remove_from_federation',body)

    """ VM Operations #######################################################################"""
    
    def GetVM(self,parameters = None):
        """  Parameters:
            show_optional_fields
            id
            name
            type
            model
            version
            limit
            offset
            ...
        """
        url = self.url+'virtual_machines'
        if parameters:
            url = url+'?'
            i = 0
            for x in parameters:
                if i > 0: url = url + '&' 
                url = url+x+'='+parameters[x]
                i += 1
        return self.doGet(url)

    def GetVMId(self, vmname):
        x = self.GetVM({"name":vmname})['virtual_machines']
        for z in x: 
            if z['state'] == 'ALIVE':
                return z['id']                  
        return z['id']
    
    def GetVMMetric(self, vmname, timerange='43200', resolution='Minute', timeOffset='0'):        
        url = self.url +'virtual_machines/'+self.GetVMId(vmname)+'/metrics?range='+timerange+'&resolution='+resolution+'&offset='+timeOffset+'&show_optional_fields=true'
        return self.doGet(url)

    def SetVMPolicy(self, vmname, policyname):
        body = '{"virtual_machine_id":"'+self.GetVMId(vmname)+'",\
                 "policy_id":"'+self.GetPolicyId(policyname)+'"}'
        return self.doPost(self.url+'virtual_machinces/set_policy', body)

    def VMmove(self, name, destination):
        body = '{"virtual_machine_name":"'+name+'",\
                 "destination_datastore_id":"'+self.GetDataStoreId(destination)+'"}'
        return self.doPost(self.url+'virtual_machines/'+self.GetVMId(name)+'/move', body)

    def VMclone(self, name, cloneName, appConsistent=False, consistencyType='None'):
        body = '{"virtual_machine_name":"'+ cloneName +'",\
                 "app_consistent":"'+ appConsistent +'",\
                 "consistency_type":"'+ consistencyType +'"}'
        return self.doPost(self.url+'virtual_machines/'+self.GetVMId(name)+'/clone', body)

    def VMcredentials(self, name, username, password):
        body = '{"guest_username":"'+ username +'",\
                 "guest_password":"'+ password +'"}'
        return self.doPost(self.url+'virtual_machines/'+self.GetVMId(name)+'/validate_backup_credentials', body)

    def VMpowerOff(self, name):
        return self.doPost(self.url+'virtual_machines/'+self.GetVMId(name)+'/power_off')

    def VMpowerOn(self, name):
        return self.doPost(self.url+'virtual_machines/'+self.GetVMId(name)+'/power_on')

    def VMpolicyImpactReport(self, vm_id, policy_id):
        body = '{"virtual_machine_id":"'+ vm_id +'",\
                 "policy_id":"'+ policy_id +'"}'
        return self.doPost(self.url+'virtual_machines/policy_impact_report/apply_policy', body)

    """ DataStore Operations ################################################################"""
    
    def GetDataStore(self, parameters = None):         
        """  Parameters:
            show_optional_fields
            id
            name
            type
            model
            version
            ...
        """
        url = self.url+'datastores'
        if parameters:
            url = url+'?'
            i = 0
            for x in parameters:
                if i > 0: url = url + '&' 
                url = url+x+'='+parameters[x]
                i += 1 
        return self.doGet(url)

    def GetDataStoreId(self, name):
        return self.GetDataStore({"name":name})['datastores'][0]['id']

    def NewDataStore(self, name, cluster, policy, size):
        size = size * 1024 * 1024 * 1024        
        body = '{"name":"'+name+'",\
                "omnistack_cluster_id":"'+self.GetClusterId(cluster)+'",\
                "policy_id":"'+self.GetPolicyId(policy)+'",\
                "size":"'+str(size)+'"}'
        return self.doPost(self.url+'datastores', body)

    def RemoveDataStore(self, name):
          return self.doDelete(self.url+'datastores/'+self.GetDataStoreId(name))
        
    def ResizeDataStore(self, name, size):       
        body = '{"size":"'+str(size*1024*1024*1024)+'"}'
        return self.doPost(self.url+'datastores/'+self.GetDataStoreId(name)+'/resize',body)         
        
    def SetDataStorePolicy(self, name, policy):         
        body = '{"policy_id":"'+ self.GetPolicyId(policy) +'"}'
        return self.doPost(self.url+'datastores/'+self.GetDataStoreId(name)+'/set_policy', body)        
    
    def ShareDataStore(self, name, host):
        body = '{"hostname":"'+ host + '"}'
        return self.doPost(self.url+'datastores/'+self.GetDataStoreId(name)+'/share', body)

    def UnShareDataStore(self, name, host):
        body = '{"hostname":"'+ host + '"}'
        return self.doPost(self.url+'datastores/'+self.GetDataStoreId(name)+'/unshare', body)

    def GetStandardHosts(self, name):
        return self.doPost(self.url+'datastores/'+self.GetDataStoreId(name)+'/standard_hosts')

    """ Cluster Operations ###################################################################"""
    
    def GetCluster(self, parameters=None):
        """  Parameters:
            show_optional_fields
            id
            name
            type
            model
            version
            ...
        """
        url = self.url+'omnistack_clusters'
        if parameters:
            url = url+'?'
            i = 0
            for x in parameters:
                if i > 0: url = url + '&' 
                url = url+x+'='+parameters[x]
                i += 1
        return self.doGet(url)       
       
    def GetClusterId(self, name):
        return self.GetCluster({"name":name})['omnistack_clusters'][0]['id']

    def GetClusterMetric(self, name,timerange='43200', resolution='Minute', timeOffset='0'):       
        url = self.url +'omnistack_clusters/'+self.GetClusterId(name)+'/metrics?range='+timerange+'&resolution='+resolution+'&offset='+timeOffset+'&show_optional_fields=true'
        return self.doGet(url) 
        
    def GetClusterThroughput(self, name=None):
        url =  self.url+'omnistack_clusters/throughput'
        if name:
            url = url + '?cluster_group_id='+self.GetClusterId(name)       
        return self.doGet(url)
    
    def GetClusterTimeZones(self):
        return self.doGet(self.url+'omnistack_clusters/time_zone_list')

    def SetClusterTimeZone(self, name, timezone):      
        body = '{"time_zone":"'+ timezone +'"}'
        return self.doPost(self.url+'omnistack_clusters/set_time_zone', body)

    def GetConnectedClusters(self, name):
        return self.doGet(self.url +'omnistack_clusters/'+self.GetClusterId(name)+'/connected_clusters')

    def GetClusterPairThroughput(self, cluster1, parameters=None):
        """ Parameters:  
               destination_id
               time_offset
               range 
        """
        url = self.url +'omnistack_clusters/'+self.GetClusterId(cluster1)+'/throughput'
        if parameters:
            url = url+'?'
            i = 0
            for x in parameters:
                if i > 0: url = url + '&' 
                url = url+x+'='+parameters[x]
                i += 1
        return self.DoGet(url)

    def GetClusterGroup(self, parameters=None):
        """
        Parameters:
           id, name, fields, limit, offset, case, sort, order
        """
        url = self.url + 'cluster_groups'
        if parameters:
            url = url+'?'
            i = 0
            for x in parameters:
                if i > 0: url = url + '&' 
                url = url+x+'='+parameters[x]
                i += 1
        return self.doGet(url)

    def RenameClusterGroup(self, name, clustergroup_id):      
        body = '{"cluster_group_name":"'+ name +'"}'
        return self.doPost(self.url+'cluster_groups/'+clustergroup_id+'/rename', body)    
    
    """ Backup & Restore #####################################################################"""
        
    def GetBackups(self, parameters=None):
        """
        Parameters:
           id, name, fields, limit, offset, case, sort, order
           createdAfter = (datetime.datetime.now() - datetime.timedelta(hours=past_hours)).isoformat(timespec='seconds')+'Z'
        """
        url = self.url + 'backups'
        if parameters:
            url = url+'?'
            i = 0
            for x in parameters:
                if i > 0: url = url + '&' 
                url = url+x+'='+parameters[x]
                i += 1        
        return self.doGet(url) 
        
    def GetVMLastBackup(self, vmname):
        bck = self.GetBackups({"virtual_machine_name":vmname})['backups']
        if(len(bck)>0):
            return (sorted(bck, key=lambda bck:bck['created_at'],reverse=True))[0]
        else:
            raise SvtError('GetVMLastBackup',551,'No backup found for '+vmname)
        
    def BackupVM(self, name, destination, retention=0, appConsistent=False, consistencyType='None'):      
        bname = name + '_' + str(datetime.datetime.now().isoformat(timespec='seconds'))
        body='{\
                "backup_name":"'+ bname +'",\
                "destination_id":"'+ self.GetClusterId(destination) +'",\
                "app_consistent":"'+ appConsistent +',\
                "consistency_type":"'+ consistencyType +'",\
                "retention":'+ retention +'}'
        return self.doPost(self.url+'virtual_machines/'+self.GetVMId(name)+'/backup', body) 

    def VMbackup_parameter(self, name, username, password, override, app_aware):
        body = '{"guest_username":"'+ username +'",\
                 "guest_password":"'+ password +'",\
                 "override_guest_validation":"'+ override +'",\
                 "app_aware_type":"'+ app_aware +'"}'
        return self.doPost(self.url+'virtual_machines/'+self.GetVMId(name)+'/backup_parameters', body)


    def RestoreVM(self, vmname, destination, bckid, restore=False):       
        if restore:
            url = self.url+'backups/'+bckid+'/restore?restore_original=true'
            return self.doPost(url)
        else:        
            body='{\
                    "virtual_machine_name":"'+ vmname +'",\
                    "dastastore_id":"'+ self.GetDataStoreId(destination)+'"}'
            return self.doPost(self.url+'backups/'+bckid+'/restore?restore_original=false', body)
       
    def GetBackupId(self, vmname, bckname):
        return self.doGet(self.url+'backups?show_optional_fields=true&virtual_machine_name='+vmname+'&name='+bckname)         
        
    def DeleteBackup(self,bckid):       
        body='{\
                "backup_id":["'+ bckid +'"]}'
        return self.doPost(self.url+'backups/delete', body)

    def SetBackupRetention(self, bckid, retention, force=False):
        body='{\
                "backup_id":["'+ bckid +'"],\
                "retention":"'+ retention +',\
                "force":"'+ force + '}'
        return self.doPost(self.url+'backups/set_retention', body)

    def CalculateUniqueSize(self, bckid):
        return self.doPost(self.url+'backups/'+bckid+'/calculate_unique_size')

    def CancelBackup(self, bckid):
        return self.doPost(self.url+'backups/'+bckid+'/cancel')

    def CopyBackup(self, bckid, destination, storeName):
        body='{\
            "destination_id":"'+ destination +'",\
            "external_store_name":"'+ storeName +'"}'
        return self.doPost(self.url+'backups/'+bckid+'/copy', body)
    
    def LockBackup(self, bckid):
        return self.doPost(self.url+'backups/'+bckid+'/lock')

    def RenameBackup(self, bckid, backup_name):
        body='{\
            "backup_name":"'+ backup_name + '"}'
        return self.doPost(self.url+'backups/'+bckid+'/rename', body)

    """ Policy Operations ####################################################################"""
    
    def GetPolicy(self, parameters=None):
        """
        Parameters:
           id, name, cluster_group_id, fields, limit, offset, case, sort, order
           
        """
        url = self.url + 'policies'
        if parameters:
            url = url+'?'
            i = 0
            for x in parameters:
                if i > 0: url = url + '&' 
                url = url+x+'='+parameters[x]
                i += 1        
        return self.doGet(url)         
        
    def GetPolicyId(self, policyname):
        return( self.GetPolicy({'"name":"'+policyname+'"'})['policies'][0]['id'] )
        
        
    def DefinePolicy(self, policyname):       
        body='{\
               "name":"'+ policyname +'"\
              }'
        return self.doPost(self.url+'policies', body)
        
    def DeletePolicy(self, policyname):
        return self.doDelete(self.url+'policies/'+self.GetPolicyId(policyname))
        
    def AddPolicyRule(self, policy_id, destination, frequency=1440, retention=1440, days='All', endTime='00:00', startTime='00:00', replace=False, appConsistent="false", consistencyType='NONE'):
        body='[ \n {\n\
    "destination_id": "'+ destination +'",\n\
    "frequency": '+ str(frequency) + ',\n\
    "retention": '+ str(retention) + ',\n\
    "days": "'+ days + '",\n\
    "start_time": "'+ startTime + '",\n\
    "end_time": "'+ endTime + '",\n\
    "application_consistent": '+ str(appConsistent) +',\n\
    "consistency_type": "'+ consistencyType +'"\n\
 }\n]'        
        return self.doPost(self.url+'policies/'+policy_id+'/rules?replace_all_rules='+str(replace), body)

    def DeletePolicyRule(self, policy_id, rule_id):       
        return self.doDelete(self.url+'policies/'+policy_id+'/rules/'+rule_id)

    """ External Storage - air-gapped Backup Operations ############################################################################"""

    def GetExternalStore(self, parameters=None):
        """
        Parameters:
           name, omnistack_cluster_id, management_ip, cluster_group_id, fields, limit, offset, case, sort, order
           
        """
        url = self.url + 'external_stores'
        if parameters:
            url = url+'?'
            i = 0
            for x in parameters:
                if i > 0: url = url + '&' 
                url = url+x+'='+parameters[x]
                i += 1        
        return self.doGet(url)         

    def RegisterExternalStore(self, parameters):
        """
          Parameters (Dictionary):
          management_ip: IP address of the external store
          management_port: Default 9387 
          name: name of the external Catalyst store
          omnistack_cluster_id: UUID of the cluster associated with the store 
          username: client name of the external store
          passward: client password
          storage_port: Default 9388
        """
        return self.doPost(self.url+'external_stores', parameters)


class SvtError(Exception):
    """ Base class for SimpliVityClass Errors """
    def __init__(self, expression, status, message):
        self.expression = expression
        self.message = message
        self.status = status