
# docker build -t tb1378\svtconk8s -f svtconnect.k8s.Dockerfile . 
# docker login
# docker push tb1378\svtconk8s
# User Ubuntu as the base Image
FROM ubuntu
#
LABEL maintainer="Thomas Beha"
LABEL version="4.0"
LABEL copyright="Thomas Beha, 2020"
LABEL license="GNU General Public License v3"
LABEL DESCRIPTION="SimpliVity Connector POD based on Ubuntu"
#
RUN apt-get update
RUN apt-get -y install python3.8 && \
	apt-get -y install python3-pip && \
	apt-get -y install vim && \
	apt-get -y install cron 
RUN /usr/bin/pip3 install requests && \
	/usr/bin/pip3 install fernet && \
	/usr/bin/pip3 install cryptography && \
	/usr/bin/pip3 install lxml && \
	/usr/bin/pip3 install prometheus_client
# copy the necessary python files to the container
RUN mkdir /opt/svt
COPY SimpliVityClass.py /opt/svt
COPY svtPromConnector.v4.2.py /opt/svt/svtpromconnector.py
#COPY SvtConnector.key /opt/svt/data/svtconnector.key  # will be transferred to the container as K8s configmap
#COPY SvtConnector.xml /opt/svt/data/svtconnector.xml  # will be transferred to the container as K8s configmap
# Start the collector
#CMD /usr/bin/python3.8 /opt/svt/svtpromconnector.py # this is the command that needs to be started in the POD