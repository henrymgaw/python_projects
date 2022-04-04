# CEP Fabric files

From [Fabric's website](https://www.fabfile.org/):
> Fabric is a high level Python (2.7, 3.4+) library designed to execute shell commands remotely over SSH, yielding useful Python objects in return.

This repository includes Fabfiles used by CEP-SRE to execute commands against servers over SSH. This is typically useful in a scenario where Salt is either nonfunctional or not installed.

## Dependencies

The following packages must be prior to installing Fabric:
- Python 3.4+
- pip

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install requirements.

```bash
pip3 install -r requirements.txt
```

Create configuration files.

```bash
cp config.template.yaml config.yaml # see config.example.yaml for example configuration
vi hosts.yaml # see hosts.example.txt for example hosts file
```

**Note: Setting `serial: False` in `config.yaml` does not work very well at the time of this writing. Keep this set to `True` until we get this working a little better.**

## Usage

```bash
# shows available tasks
fab -l

# shows hostnames for servers in hosts.txt
fab show-hostname

# restarts salt-minion for servers in hosts.txt
fab restart-salt

# restarts salt-minion and kills salt-minion zombie processes for servers in hosts.txt
fab restart-and-kill-salt
```

**Note:**
If you see a `q must be exactly 160, 224, or 256 bits long` error while attempting to run Fabric, ensure your SSH config file is not attempting to use an SSH key not associated with the host(s) you're trying to access. For more information, see: [https://github.com/iterative/dvc/issues/3652](https://github.com/iterative/dvc/issues/3652).


## Contributing
Merge requests are welcome.

To add additional functionality, create new task in `fabfile.py`. The task itself may directly execute commands or call helper functions as desired.


## License
[MIT](https://choosealicense.com/licenses/mit/)
