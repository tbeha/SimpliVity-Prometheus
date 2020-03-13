# Prometheus connector for HPE Simplivity

Please take a look at the documentation to get the details of the Prometheus connector implementation. 

The general steps to take are:

1. run the createCredentials.py script to generate the credentials information for the Prometheus connector. 
2. Adjust the path variable in the svtPromConnector.v2.3.py script to the correct value where your credentials information (.xml files created in step 1) is located.
3. Run the Prometheus connector script. 


# Attention:
The whitepaper that can be found in the documentation folder refers to svtPromConnector.v2.3.py.

The difference between v2.3 and v3.0 is that v3.0 uses system variables for the path, keyfile and the xml-file while v2.3 had the name and the path fixed in the Python script. Hence, the script startcommando for v3.0 changed to:

  python svtPromConnector.v3.0.py -p <path> -k <keyfilename> -x <xmlfilename>

This change was done to be more flexible on deploying the SimpliVityConnector-Prometheus-Grafana monitoring for instance on Kubernetes. The corresponding whitepaper for deploying this environment on Kubernetes cluster is currently work in progress. 



