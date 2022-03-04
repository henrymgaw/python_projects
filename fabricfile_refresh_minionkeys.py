#!/usr/local/bin/python3
"""
Usage: 
python3 fabfile.py

Note: 
After key has been removed and salt-minion has been restarted you may need to accept the keys on the saltmaster again
Run on saltmaster: salt-key -A -y

Reference:
https://docs.fabfile.org/en/2.6/api/connection.html

Written by:
Henry Gaw

Date Modified:
2/17/22

"""
from fabric import Connection
from invoke import Responder

def refresh_minion_keys(server):
    sudopass = Responder(pattern = r"\[sudo\] password for henry.gaw: ", response = "$kyler12@@")
    c = Connection(host=server, forward_agent=True, gateway=Connection('bastion-1.cep.us-west-2.prd1.int.evbg.io'), connect_kwargs = {"password": "$kyler12@@"})
    return c.run(f"sudo systemctl stop salt-minion; sudo rm -f /etc/salt/pki/minion/minion_master.pub;sudo systemctl start salt-minion", pty=True, watchers = [sudopass])

#Update your list if servers here
servers = [
'jenkins-slave01', 
'jenkins-master01'
]

for server in servers:
    out=refresh_minion_keys('henry.gaw@'+ str(server))
    print(out)
