#!/usr/local/bin/python3
"""
Usage: 
python3 fabfile.py

Reference:
https://docs.fabfile.org/en/2.6/api/connection.html

Written by:
Henry Gaw

Date Modified:
2/17/22

"""
from fabric import Connection
from invoke import Responder

def restart_service(server):
    sudopass = Responder(pattern = r"\[sudo\] password for henry.gaw: ", response = "$kyler12@@")
    c = Connection(host=server, forward_agent=True, gateway=Connection('bastion-1.cep.us-west-2.prd1.int.evbg.io'), connect_kwargs = {"password": "$kyler12@@"})
    return c.run(f"sudo systemctl status salt-minion", pty=True, watchers = [sudopass])

servers = [
'cep-salt1', 
'jenkins-master01'
]

for server in servers:
    out=restart_service('henry.gaw@'+ str(server))
    print(out)
