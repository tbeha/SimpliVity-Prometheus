# Prometheus connector for HPE Simplivity

Any SimpliVity Prometheus connector presented on this Github is not supported by HPE. If you want to have the HPE supported SimpliVity Prometheus connector, then please download the SimpliVity Prometheus connector from the HPE Github:
https://github.com/HewlettPackard/simplivity-prometheus-connector

The HPE SimpliVity Prometheus connector is based on v2.3 of the SimpliVity connector available on this Github. The SimpliVity Prometheus connector v2.3 is kept on this Github, because, there is a HPE Solution Depot paper (see documentation folder) that refers to this version and the Github here. 

Support for any of the available SimpliVity Prometheus versions on this Github is provided on a best effort approach.

The following versions/branches are available:

  <b>v2.3:</b>       
    Implementation as described in the solution depot whitepaper with fixed path and filenames for key- and xml-configurationfile. 
    <b>Attention!</b> The startup command for the connector was changed with the latest Dockerfile to /usr/bin/python3 /opt/svt/svtconnector.py. This was neccessary, since Python 3.8 instead of Python 3.6 is now automatically installed (even if the dockerfile states to install python3.6). 
    
  <b>v3.0:</b>                
    allows the use of system variabls for the path, key- and xml-configuration-file. Hence, the script startcommando for v3.0 changed to:
      python svtPromConnector.v3.0.py -p Path -k Keyfilename -x XMLfilename
  
  <b>master:</b>
    uses SimpliVity class v4.0. Provides additional flexiblity by selecting what performance needs to be monitored: federation, cluster, node, vm.



 The <b>k8s</b>-directory contains the details to deploy the SimpliVity Prometheus connector as a Kubernetes POD, using a configmap to provide the necessary connector input data. Use the CreateConfigMap.py script instead of the createCredentials.py script to create the configmap. Please take a look at the <b>SvtPromDeployment.ipynb</b> Jupyter notebook if you want to have details of the Kubernetes implementation.  


The createCredentials script will ask for the following information:

  - username               vCenter username (a user with readonly access rights is sufficient)
  - password               vCenter password
  - OVC/MVA IP address     IP address that the connector uses to connect to the federation
  - name                   name of the yml-file (<name>.yml) and the configmap: <name>-xml that will be created
  - port                   TCP Port that the connector uses to publish the counters.  
  - timerange              A range in seconds (the duration from the specified point in time)
  - resolution             The resolution (SECOND, MINUTE, HOUR, or DAY)
  - monitoringinterval     connector cyle time (should be >= the time to process the captured data)

additional parameter with v4.0:
  - monitor                performance data capture selector: f(ederation), c(luster), n(ode), v(irtual machine)
  - cluster                enter a clustername if you want to limit the data capture to a single cluster
  - limit                  A positive integer that represents the maximum number of results to return
  - offset                 A positive integer that directs the service to start returning the <offset value> instance, up to the limit. Every result will be collected if the offset is set to a negative value.



