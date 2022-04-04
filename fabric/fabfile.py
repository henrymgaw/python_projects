"""
fabfile (see https://www.fabfile.org/ for more info)

fab --list
fab show-hostname
fab restart-salt
fab restart-and-kill-salt

"""

import getpass
from yaml import load, CLoader as Loader
from fabric import Connection, Config, SerialGroup, task, ThreadingGroup


def get_sudo():
    """
    Gets password for sudo
    """
    sudo_pass = getpass.getpass("What is your sudo password?")
    return Config(overrides={"sudo": {"password": sudo_pass}})


def get_config(config_file="config.yaml"):
    """
    Opens and loads YAML config file -- default: config.yaml
    """
    with open(config_file, "r", encoding="utf8") as file:
        config = load(file, Loader=Loader)
        return config


def get_connection(hosts, bastion, user, config=False, serial=False):
    """
    Instantiates either Serial or Threaded connection to hosts
    """
    if serial:
        if config:
            return SerialGroup(
                *hosts,
                user=user,
                forward_agent=True,
                gateway=Connection(bastion),
                config=config,
            )
        else:
            return SerialGroup(
                *hosts, user=user, forward_agent=True, gateway=Connection(bastion)
            )
    else:
        if config:
            return ThreadingGroup(
                *hosts,
                user=user,
                forward_agent=True,
                gateway=Connection(bastion),
                config=config,
            )
        else:
            return ThreadingGroup(
                *hosts, user=user, forward_agent=True, gateway=Connection(bastion)
            )


def show_results(action, results):
    """
    Displays formatted results
    """
    print(f"Finished: {action}.")
    print("Failures:")
    print(results.failed)


def prepare(config=False):
    """
    Loads configuration and displays basic output
    """
    local_config = get_config()
    serial = bool("serial" in local_config.keys() and local_config["serial"])
    with open(local_config["host_file"], "r", encoding="utf8") as host_file:
        local_config.update({"hosts": [host.replace("\n", "") for host in host_file]})
    group = get_connection(
        local_config["hosts"],
        local_config["bastion"],
        local_config["user"],
        config,
        serial,
    )
    print(f"User: {local_config['user']}")
    print(f"Bastion: {local_config['bastion']}")
    print(f"Serial mode: {serial}")
    print("Hosts:")
    for host in local_config["hosts"]:
        print(f"  - {host}")
    return group


def start_salt(group):
    """
    Helper function: Starts salt-minion service
    """
    action = "Start salt-minion service"
    print(f"Executing: {action}...")
    results = group.sudo("service salt-minion start", hide=True)
    show_results(action, results)


def stop_salt(group):
    """
    Helper function: Stops salt-minion service
    """
    action = "Stop salt-minion service"
    print(f"Executing: {action}...")
    results = group.sudo("service salt-minion stop", hide=True)
    show_results(action, results)


def kill_zombies(group):
    """
    Helper function: Finds zombie salt-minion processes and forcefully kills them
    """
    action = "Kill zombie salt-minion processes"
    print(f"Executing: {action}...")
    results = group.sudo(
        'ps -ef | grep [s]alt-minion | awk "{print $2}" | xargs kill -9 || exit 0',
        hide=True,
    )
    show_results(action, results)


@task
def show_hostname(config):
    """
    Callable task: Shows hostname

    Executes commands directly from this function.
    """
    group = prepare()
    action = "Show hostname"
    print(f"Executing: {action}...")
    results = group.run("hostname -f")
    show_results(action, results)


@task
def restart_salt(config):
    """
    Callable task: Stops and starts salt-minion service

    Uses helper functions "stop_salt" and "start_salt" for execution.
    """
    group = prepare(get_sudo())
    stop_salt(group)
    start_salt(group)


@task
def restart_and_kill_salt(config):
    """
    Callable task: Stops and starts salt-minion service while killing zombie processes

    Uses helper functions "stop_salt", "kill_zombies", and "start_salt" for execution.
    """
    group = prepare(get_sudo())
    stop_salt(group)
    kill_zombies(group)
    start_salt(group)
