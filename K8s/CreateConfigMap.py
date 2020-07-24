# -*- coding: utf-8 -*-
"""
Created on July 14 2020

@author: Thomas Beha
"""

from cryptography.fernet import Fernet
import getpass
from lxml import etree 

uname = input("Username: ")
password = getpass.getpass()
ovc = input("OVC IP Addr: ")
port = input("Connector Port: ")
namespace = input("K8s namespace: ")
name = input("Name: ")

logfile = name+'.log'

key = Fernet.generate_key()
f = Fernet(key)
token = f.encrypt(password.encode('ASCII'))
user = f.encrypt(uname.encode('ASCII'))

f = open(name+'.yml','w')
f.write('apiVersion: v1 \n')
f.write('kind: ConfigMap \n')
f.write('metadata: \n')
f.write('  name: '+name+'-xml \n')
f.write('  namespace: '+namespace+' \n')
f.write('data: \n')
f.write('  svtconnector.key: |- \n')
f.write('    '+key.decode('ASCII')+'\n')
f.write('  svtconnector.xml: |- \n')
f.write('    <data> \n')
f.write('      <user>'+user.decode('ASCII')+'</user>\n')
f.write('      <password>'+token.decode('ASCII')+'</password>\n')
f.write('      <ovc>'+ovc+'</ovc>\n')
f.write('      <timerange>30</timerange>\n')
f.write('      <resolution>SECOND</resolution>\n')
f.write('      <monitoringintervall>30</monitoringintervall>\n')
f.write('      <logfile>'+logfile+'</logfile>\n')
f.write('      <port>'+port+'</port>\n')
f.write('      <monitor>fcn</monitor>\n')
f.write('      <cluster></cluster>\n')
f.write('      <limit>500</limit>\n')
f.write('      <offset>-1</offset>\n')
f.write('    </data>\n')
f.close()

f = open(name+'.key','w')
f.write(key.decode('ASCII'))
f.close()

f = open(name+'.xml','w')
f.write('    <data> \n')
f.write('      <username>'+uname+'</username>\n')
f.write('      <user>'+user.decode('ASCII')+'</user>\n')
f.write('      <password>'+token.decode('ASCII')+'</password>\n')
f.write('      <ovc>'+ovc+'</ovc>\n')
f.write('      <timerange>30</timerange>\n')
f.write('      <resolution>SECOND</resolution>\n')
f.write('      <monitoringintervall>30</monitoringintervall>\n')
f.write('      <logfile>'+logfile+'</logfile>\n')
f.write('      <port>'+port+'</port>\n')
f.write('      <monitor>fcn</monitor>\n')
f.write('      <cluster></cluster>\n')
f.write('      <limit>-1</limit>\n')
f.write('      <offset>0</offset>\n')
f.write('    </data>\n')
f.close()

""" Test the keys """ 
""" Read keyfile """
f = open(name+'.key', 'r')
k2=f.readline()
f.close()
key2=k2.encode('ASCII')

""" Parse XML File """

tree = etree.parse(name+'.xml')
u2=(tree.find("user")).text
p2=(tree.find("password")).text

f = Fernet(key2)
user = f.decrypt(u2.encode('ASCII')).decode('ASCII')
password = f.decrypt(p2.encode('ASCII')).decode('ASCII')
print(user,password)
