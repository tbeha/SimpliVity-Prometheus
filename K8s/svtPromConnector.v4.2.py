# -*- coding: utf-8 -*-
"""
Created on September 9, 2020
Version 4.2 
Used for a Kubernetes deployment with configmaps instead of runtime arguments.

Copyright (c) 2020 Thomas Beha

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    https://www.gnu.org/licenses/gpl-3.0.en.html 

    This release of the Prometheus Connector requires: SimpliVityClass v4.0

"""

from cryptography.fernet import *
from lxml import etree 
import time
from SimpliVityClass import *
from datetime import datetime
from prometheus_client import Counter, Gauge, start_http_server, Info, Enum
import os


BtoGB=pow(1024,3)
BtoMB=pow(1024,2)

node_state={
    'UNKOWN': 0,
    'ALIVE': 1,
    'SUSPECTED': 2,
    'MANAGED': 3,
    'FAULTY': 4,
    'REMOVED': 5
}

vm_state={
    'ALIVE': 1,
    'DELETED': 2,
    'REMOVED': 3
}

vm_ha_status={
    'UNKNOWN': 0,
    'SAFE': 1,
    'SYNCING': 2,
    'DEGRADED': 3,
    'DEFUNCT': 4,
    'OUT_OF_SCOPE': 5,
    'NOT_APPLICAPLE': 6
}

vm_power_state={
    'UNKNOWN': 0,
    'ON': 1,
    'OFF': 2,
    'SUSPENDED': 3
}

capacitymetric=[
    'allocated_capacity',
    'free_space',
    'capacity_savings',
    'used_capacity',
    'used_logical_capacity',
    'local_backup_capacity',
    'remote_backup_capacity',
    'stored_compressed_data',
    'stored_uncompressed_data',
    'stored_virtual_machine_data'
]

dedupmetric=[
    'compression_ratio',
    'deduplication_ratio',
    'efficiency_ratio'
]

performancemetric=[
    'read_iops',
    'write_iops',
    'read_throughput',
    'write_throughput',
    'read_latency',
    'write_latency'
]

def logwriter(f, text):
        output=str(datetime.today()) +": "+text+" \n"
        print(output)
        f.write(output)
    
def logopen(filename):
        f = open(filename,'a')
        f.write(str(datetime.today())+": Logfile opened \n")
        return f

def logclose(f):
        f.write(str(datetime.today())+": Logfile closed \n")
        f.close()

def getPerformanceAverage(data):
    if(len(data[0]['data_points']) > 0):
        perf={
            'read_iops': 0,
            'write_iops': 0,
            'read_throughput': 0,
            'write_throughput': 0,
            'read_latency': 0,
            'write_latency': 0
        }
        for x in data:
            if x['name'] == 'iops':
                iops=x['data_points']
            elif x['name'] == 'throughput':
                throughput = x['data_points']
            else: 
                latency = x['data_points']
        """ Calculate the averages """
        for i in range(len(iops)):
            perf['read_iops'] += iops[i]['reads']
            perf['write_iops'] += iops[i]['writes']
        for i in range(len(throughput)):
            perf['read_throughput'] += throughput[i]['reads']
            perf['write_throughput'] += throughput[i]['writes']
        for i in range(len(latency)):
            perf['read_latency'] += latency[i]['reads']
            perf['write_latency'] += latency[i]['writes'] 
        perf['read_latency'] /= len(latency)*1000
        perf['write_latency'] /= len(latency)*1000 
        perf['read_iops'] /= len(iops)
        perf['write_iops'] /= len(iops)
        perf['read_throughput'] /= (len(throughput) * BtoMB)
        perf['write_throughput'] /= (len(throughput) * BtoMB)
    else:
        perf={
            'read_iops': -1,
            'write_iops': -1,
            'read_throughput': -1,
            'write_throughput': -1,
            'read_latency': -1,
            'write_latency': -1
        }                           
    return(perf)

def getNodeCapacity(data):
        ndata={
            'allocated_capacity': 0,
            'free_space': 0,
            'capacity_savings': 0,
            'used_capacity': 0,
            'used_logical_capacity': 0,
            'local_backup_capacity': 0,
            'remote_backup_capacity': 0,
            'stored_compressed_data': 0,
            'stored_uncompressed_data': 0,
            'stored_virtual_machine_data': 0,
            'compression_ratio': 0,
            'deduplication_ratio': 0,
            'efficiency_ratio': 0                              
        }
        for y in data:
            if len(y['data_points']) > 0:
                tmp = y['data_points'][-1]['value']
            else:
                tmp = -1
            if 'ratio' in y['name']:
                ndata[y['name']]=tmp
            else:
                ndata[y['name']] = tmp/BtoGB
        return ndata

### Main ###########################################################################

if __name__ == "__main__":
    
    """ read the key and input file""" 

    path = '/opt/svt/'
    keyfile = path + 'data/svtconnector.key'
    xmlfile = path + 'data/svtconnector.xml'
    
    t0=time.time()
    """ Parse XML File """
    tree = etree.parse(xmlfile)
    u2=(tree.find("user")).text
    p2=(tree.find("password")).text
    ovc=(tree.find("ovc")).text
    mintervall=int((tree.find("monitoringintervall")).text)
    mresolution=(tree.find("resolution")).text
    mrange=(tree.find("timerange")).text
    lfile=(tree.find("logfile")).text
    port=int((tree.find("port")).text)
    monitor=(tree.find("monitor")).text
    cluster=(tree.find("cluster")).text
    limit=(tree.find("limit")).text
    xoffset=(tree.find("offset")).text

    """ Open the logfile """ 
    log=logopen(path+lfile)
    logwriter(log,"Path:    "+path)
    logwriter(log,"Keyfile: "+keyfile)
    logwriter(log,"XMLfile: "+xmlfile)

    """ Read keyfile """
    f = open(keyfile, 'r')
    k2=f.readline()
    f.close()
    key2=k2.encode('ASCII')
    f = Fernet(key2)

    """ Create the SimpliVity Rest API Object"""
    logwriter(log,"Open a connection to the SimpliVity systems")
    svtuser = f.decrypt(u2.encode('ASCII')).decode('ASCII')
    svtpassword = f.decrypt(p2.encode('ASCII')).decode('ASCII')
    url="https://"+ovc+"/api/"         
    svt = SimpliVity(url)
    logwriter(log,"Open Connection to SimpliVity")
    svt.Connect(svtuser,svtpassword)
    logwriter(log,"Connection to SimpliVity is open")
    logclose(log)
        
    start_http_server(port)
    c = Counter('simplivity_sample','SimpliVity sample number')
    scluster = Gauge('simplivity_cluster','SimpliVity Cluster Data',['clustername','clustermetric'])
    snode = Gauge('simplivity_node','SimpliVity Node Data',['nodename','nodemetric'])
    svm = Gauge('simplivity_vm','SimpliVity VM Data',['vmname','vmmetric'])
    sdatastore = Gauge('simplivity_datastore','SimpliVity Datastore Data - Sizes in GB',['dsname','dsmetric'])
    delta = Gauge('ConnectorRuntime','Time required for last data collection in seconds')
    icon = Info('Connector','Connector Paramter Info')
    ivm = Info('vm','Additional VM Info',['vm'])
    inode = Info('node','Additional Node Info',['node'])

    icon.info({'Monitor':monitor,'key':keyfile,'xml':xmlfile,'limit':limit,'oxl':xoffset})
    id_node={}
    replica={}
    """
    Start an endless loop to capture the current status every TIME_RANGE
    Errors will be catched with an error routine
    Please note that the connection must be refreshed after 24h or afte 10 minutes inactivity.
    """
    while True:
        try:
            t0 = time.time()         
            c.inc()

            if int(xoffset) < 0:
                lim = int(limit)
                if ('f' in monitor) or ('c' in monitor): 
                    """ Get Cluster """
                    offset = 0                   
                    x = svt.GetCluster({'show_optional_fields':'true','limit':limit,'offset':str(offset*lim)})['omnistack_clusters']
                    clusters = x
                    while (len(x) == lim):
                        offset += 1
                        x = svt.GetCluster({'show_optional_fields':'true','limit':limit,'offset':str(offset*lim)})['omnistack_clusters']
                        clusters += x
                if ('f' in monitor) or ('n' in monitor):
                    """ Get Nodes """
                    offset = 0                    
                    x = svt.GetHost({'show_optional_fields':'true','limit':limit,'offset':str(offset*lim)})['hosts']
                    hosts = x
                    while (len(x) == lim):
                        offset += 1
                        x = svt.GetHost({'show_optional_fields':'true','limit':limit,'offset':str(offset*lim)})['hosts']
                        hosts += x
                if ('f' in monitor) or ('v' in monitor):
                    """ Get VMs """
                    offset = 0
                    x = svt.GetVM({'show_optional_fields':'true','limit':limit,'offset':str(offset*lim)})['virtual_machines']
                    vms = x
                    while (len(x) == lim):
                        offset += 1
                        x = svt.GetVM({'show_optional_fields':'true','limit':limit,'offset':str(offset*lim)})['virtual_machines']
                        vms += x

                if ('f' in monitor):
                    """ Get Datastores """
                    offset = 0
                    x = svt.GetDataStore({'show_optional_fields':'true','limit':limit,'offset':str(offset*lim)})['datastores']
                    datastores = x
                    while (len(x) == lim):
                        offset += 1
                        x = svt.GetDataStore({'show_optional_fields':'true','limit':limit,'offset':str(offset*lim)})['datastores']
                        datastores += x
            else:
                if ('f' in monitor) or ('c' in monitor): 
                    clusters = svt.GetCluster({'show_optional_fields':'true','limit':limit,'offset':xoffset})['omnistack_clusters']
                if ('f' in monitor) or ('n' in monitor):
                    hosts = svt.GetHost({'show_optional_fields':'true','limit':limit,'offset':xoffset})['hosts']
                if ('f' in monitor) or ('v' in monitor):
                    vms = svt.GetVM({'show_optional_fields':'true','limit':limit,'offset':xoffset})['virtual_machines']
                if ('f' in monitor):
                    datastores = svt.GetDataStore({'show_optional_fields':'true','limit':limit,'offset':xoffset})['datastores']                

            if 'f' in monitor:
                scluster.labels('Federation','Cluster_count').set(len(clusters))
                snode.labels('Federation','Node_count').set(len(hosts))
                svm.labels('Federation','VM_count').set(len(vms))
                sdatastore.labels('Federation','Datastore_count').set(len(datastores))
                for x in hosts:
                    cn = (x['name'].split('.')[0]).replace('-','_')
                    snode.labels(cn,'State').set(node_state[x['state']])
                    id_node[x['id']]=x['name']
                    inode.labels(cn).info({'state':x['state'],'cluster':x['compute_cluster_name']})
                for x in vms:
                    cn = (x['name'].split('.')[0]).replace('-','_')
                    svm.labels(cn,'allocated_capacity').set(x['hypervisor_allocated_capacity']/BtoGB)
                    svm.labels(cn,'free_space').set(x['hypervisor_free_space']/BtoGB)
                    svm.labels(cn,'allocated_cpu').set(x['hypervisor_allocated_cpu'])
                    svm.labels(cn,'cpu_count').set(x['hypervisor_cpu_count'])
                    svm.labels(cn,'consumed_cpu').set(x['hypervisor_consumed_cpu'])
                    svm.labels(cn,'virtual_disk_count').set(x['hypervisor_virtual_disk_count'])
                    svm.labels(cn,'total_memory').set(x['hypervisor_total_memory'])
                    svm.labels(cn,'consumed_memory').set(x['hypervisor_consumed_memory'])
                    svm.labels(cn,'state').set(vm_state[x['state']])
                    svm.labels(cn,'power').set(vm_power_state[x['hypervisor_virtual_machine_power_state']])
                    svm.labels(cn,'ha_state').set(vm_ha_status[x['ha_status']])               
                    for y in x['replica_set']:
                        replica[y['role']]=id_node[y['id']]
                    ivm.labels(cn).info({'vm_state':x['state'],'vm_datastore':x['datastore_name'],'cluster':x['omnistack_cluster_name'],'primary':replica['PRIMARY'],'secondary':replica['SECONDARY']})  
                for x in datastores:
                    cn = (x['name']).replace('-','_')
                    sdatastore.labels(cn,'size').set(x['size']/BtoGB)                
                
            if 'c' in monitor:
                for x in clusters:        
                    perf=getPerformanceAverage(svt.GetClusterMetric(x['name'],timerange=mrange,resolution=mresolution)['metrics'])
                    cn = (x['name'].split('.')[0]).replace('-','_')
                    for metricname in capacitymetric:
                        scluster.labels(cn,metricname).set(x[metricname]/BtoGB)
                    for metricname in dedupmetric:
                        scluster.labels(cn,metricname).set(x[metricname].split()[0])
                    for metricname in performancemetric:
                        scluster.labels(cn,metricname).set(perf[metricname])
                    for x in svt.GetClusterThroughput():
                        cn = x['source_omnistack_cluster_name']
                        metricname=x['destination_omnistack_cluster_name']+' throughput'
                        scluster.labels(cn,metricname).set(x['throughput'])     

            if 'n' in monitor:
                for x in hosts:
                    y = getNodeCapacity(svt.GetHostCapacity(x['name'],timerange=mrange,resolution=mresolution)['metrics'])
                    perf=getPerformanceAverage(svt.GetHostMetrics(x['name'],timerange=mrange,resolution=mresolution)['metrics'])
                    cn = (x['name'].split('.')[0]).replace('-','_')
                    for metricname in capacitymetric:
                        snode.labels(cn,metricname).set(y[metricname])
                    for metricname in dedupmetric:
                        snode.labels(cn,metricname).set(y[metricname])
                    for metricname in performancemetric:
                        snode.labels(cn,metricname).set(perf[metricname])         

            if 'v' in monitor:
                for x in vms:
                    cn = (x['name'].split('.')[0]).replace('-','_')  
                    perf=getPerformanceAverage(svt.GetVMMetric(x['name'],timerange=mrange,resolution=mresolution)['metrics'])
                    for metricname in performancemetric:
                        svm.labels(cn,metricname).set(perf[metricname])

            t1 = time.time()
            delta.set((t1-t0))
            while ((t1-t0) < mintervall):
                time.sleep(1.0)
                t1 = time.time()
        except KeyError as e:
            log=logopen(path+lfile)
            logwriter(log,"KeyError")
            logwriter(log,str(e))
            logclose(log)
            pass                         
        except SvtError as e:
            if e.status == 401:
                try:
                    log=logopen(path+lfile)
                    logwriter(log,str(e.expression))
                    logwriter(log,str(e.status))
                    logwriter(log,str(e.message))                    
                    logwriter(log,"Open Connection to SimpliVity")
                    svt.Connect(svtuser,svtpassword)
                    logwriter(log,"Connection to SimpliVity is open")
                    logclose(log)
                except SvtError as e:
                    log=logopen(path+lfile)
                    logwriter(log,"Failed to open a conection to SimplVity")
                    logwriter(log,str(e.expression))
                    logwriter(log,str(e.status))
                    logwriter(log,str(e.message))
                    logwriter(log,"close SimpliVity connection")
                    logclose(log)
                    exit(-200)
            elif e.status == 555:
                log=logopen(path+lfile)
                logwriter(log,'SvtError:')
                logwriter(log,str(e.expression))
                logwriter(log,str(e.status))
                logwriter(log,str(e.message))
                logclose(log)
                pass                            
            else:
                log=logopen(path+lfile)
                logwriter(log,'Unhandeled SvtError:')
                logwriter(log,str(e.expression))
                logwriter(log,str(e.status))
                logwriter(log,str(e.message))
                logwriter(log,"close SimpliVity connection")
                logclose(log)
                pass
        except Exception as ex:
            print(ex)
            log=logopen(path+lfile)
            logwriter(log,'Exception')
            logwriter(log,str(ex))
            logclose(log)
            pass