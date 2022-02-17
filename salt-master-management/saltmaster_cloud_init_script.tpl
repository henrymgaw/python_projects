#!/bin/bash
#
# set -x

echo "Starting Salt Master Bootstrap Process.."

# set some local vars
saltenv="${grainenv}"
envtype="${grainenvtype}"

if [[ $envtype == "prod" ]]
then
  envtype="prd"
elif [[ $envtype == "stage" ]]
then
  envtype="stg"
fi


### Remove old apt repos
echo "Removing old apt repos.."
sed -i '/artifactory\.eb-tools\.com/d' /etc/apt/sources.list
rm -f /etc/apt/sources.list.d/eb-*
rm -f /etc/apt/sources.list.d/salt.list /etc/apt/sources.list.d/saltstack.list

# get OS info
source "/etc/os-release"
if [[ $VERSION_ID = "" ]]; then
  VERSION_ID="18.04"
fi

### Lets wait for apt to finish using the lock file
### Note, this was recently fixed in cloud-init 17.1 release: https://bugs.launchpad.net/cloud-init/+bug/1693361
echo "Waiting on apt lock to clear"
while lsof | egrep "/var/lib/apt/lists|/var/lib/dpkg/lock" ; do sleep 5s ; done


sudo curl -fsSL -o /etc/apt/trusted.gpg.d/salt-archive-keyring.gpg https://repo.saltproject.io/py3/ubuntu/$VERSION_ID/amd64/${salt_major_version}/salt-archive-keyring.gpg
### Need to change this from 3002.6 to allow latest to make it functional
echo "deb https://repo.saltproject.io/py3/ubuntu/$VERSION_ID/amd64/archive/${salt_major_version}.6 bionic main" | sudo tee /etc/apt/sources.list.d/salt.list

# if the unattended-upgrades havent happened yet, apt wont know about these
# pkg's since the cache is missing. force an update
DEBIAN_FRONTEND=noninteractive apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -q -y -u -o Dpkg::Options::="--force-confdef"

# remove any previously installed salt resources
DEBIAN_FRONTEND=noninteractive apt-get remove -q -y -u -o Dpkg::Options::="--force-confdef" python2.7 salt-common salt-master salt-minion salt-ssh salt-syndic salt-cloud salt-api
DEBIAN_FRONTEND=noninteractive apt-get update

# now lets install dependencies
echo "Installing dependencies…"
DEBIAN_FRONTEND=noninteractive apt-get install -q -y -u -o Dpkg::Options::="--force-confdef" apt-utils python3-requests python3-pip python3-pygit2 nfs-common bind9-host gnupg1 curl git jq vim

# downgrade pip
pip3 install --upgrade --force 'pip<10.0.0'

# lets get python3 requirements installed
#pip3 install --upgrade chardet urllib3 requests cherrypy boto botocore boto3 GitPython awscli
pip3 install GitPython

# remove old version of JDK that may be installed
sudo find /usr/lib -maxdepth 1 -type d -name "jdk*" -exec rm -rf {} \;

## creating ssh private key file for GHE access
## we do this here because these are needed *before* Saltmaster can work
echo "Creating /root/.ssh/id_rsa_github for GHE access.."
echo "${github_key}" > /root/.ssh/id_rsa_github
chmod 600 /root/.ssh/id_rsa_github
ssh-keygen -y -f ~/.ssh/id_rsa_github > ~/.ssh/id_rsa_github.pub
chmod 644 /root/.ssh/id_rsa_github.pub

### identityfile for github
touch /root/.ssh/config
cat > /root/.ssh/config <<'EOFMASTERCONFIG'
Host github.com
    IdentityFile /root/.ssh/id_rsa_github
    UserKnownHostsFile=/dev/null
    StrictHostKeyChecking no
EOFMASTERCONFIG

### identityfile for GHE
cat >> /root/.ssh/config <<'EOFGHECONFIG'
Host eb-github.com
     IdentityFile /root/.ssh/id_rsa_github
     UserKnownHostsFile=/dev/null
     StrictHostKeyChecking no
EOFGHECONFIG

# clone salt repos
git clone https://cep-platform:evbg-gitlab--c-uzUz_7NYQHs_fB4k7@gitlab.eb-tools.com/engineering/platform/sre/cep-sre/cep-saltmaster-tools.git /root/ne-toolbox-saltmaster
python3 /root/ne-toolbox-saltmaster/salt-master-management/update_repos.py /srv/salt /srv/pillar $saltenv

# install salt
DEBIAN_FRONTEND=noninteractive apt-get install -q -y -u -o Dpkg::Options::="--force-confdef" salt-common salt-master salt-minion salt-ssh salt-syndic salt-cloud salt-api

# rename salt repo file if applicable
if [ -f /etc/apt/sources.list.d/salt.list ]
then
  sudo mv /etc/apt/sources.list.d/salt.list /etc/apt/sources.list.d/saltstack.list
fi

# stop services for now
service salt-master stop
service salt-minion stop
service salt-syndic stop
service salt-api stop

# cleanup
apt-get autoremove -y

### Lets kill the minion if its running
echo "Checking for a running salt-minion.."
if [ $(ps aux |grep minion |grep -v grep | wc -l) -gt 0 ]
  then
    echo "Found a running salt-minion. Let's stop it."
    service salt-minion stop
    if [ $(ps aux |grep minion |grep -v grep | wc -l) -eq 0 ]
      then
        echo "Minion's Dead.. Moving On."
      else
        min_pid=$(cat /var/run/salt-minion.pid)
        kill -9 $min_pid
    fi
  else
    echo "Doesn't look like the minion was pre-installed. Moiving on."
fi

### remove any NFS mounts before we blow away the salt dir
### (in a multi-master set up the state is shared via NFS mount)
umount -a -t nfs4

### Lets blow away any pre-existing salt configs
dirs="/etc/salt /var/cache/salt /usr/lib/python2.7/dist-packages/salt"
for dir in $dirs
  do
    if [ -d "$dir" ]
      then
        echo "Removing $dir"
        rm -rf $dir
    fi
done

### Lets setup EFS mounts if create_fs is true
if [ "${create_fs}" = "true" ]
  then
    # Create our necessary directories for mounting first
    echo "Adding EFS mounts to /etc/fstab.."
    mkdir -p /etc/salt/pki/master/minions
    # chown -R salt:salt /etc/salt
    mkdir -p /var/cache/salt/master/minions
    # chown -R salt:salt /var/cache/salt
# Create our fstab entries
cat >> /etc/fstab <<'EOFEFSCONFIG'
# EFS mounts for persistent Salt data
${key_efs_name}:/ /etc/salt/pki/master nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 0 0
${cache_efs_name}:/ /var/cache/salt/master/minions nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 0 0
EOFEFSCONFIG
fi

### Lets wait until the salt cname is working .. this is needed before we can proceed for a saltmaster
echo "Waiting for the salt CNAME to resolve before continuing.."
while ! /usr/bin/host ${salt_hostname} > /dev/null ; do sleep 5s ; done

### Lets try to mount our nfs/efs mounts - then check the exit code for success
### nfs-common is needed to mount these .. lets ensure this exits cleanly
if [ "${create_fs}" = "true" ]
  then
    echo "Trying to mount EFS mounts.."
    mount -a -t nfs4
    if [ "$?" = 0 ]
      then
        echo "EFS mounts successfully mounted!"
      else
        echo "There was a problem mounting the EFS mounts!"
        exit 2
    fi
fi

### Creating our Salt config files
### bootstrap contains gitfs config
mkdir -p /etc/salt/master.d
cat > /etc/salt/master <<EOFMASTERCONFIG
file_roots:
  base:
    - /srv/salt
  $saltenv:
    - /srv/salt
pillar_roots:
  base:
    - /srv/pillar
  $saltenv:
    - /srv/pillar
EOFMASTERCONFIG

### Create our salt grains
echo "Writing grains to /etc/salt/grains"
cat > /etc/salt/grains <<EOFGRAINS
availability_zone: ${grainavailability_zone}
backend_key: ${backend_key}
backend_bucket: ${backend_bucket}
backend_region: ${backend_region}
environment: $saltenv
envtype: $saltenv
cache_efs_name: ${cache_efs_name}
create_fs: ${create_fs}
function: saltmaster
key_efs_name: ${key_efs_name}
master_count: ${master_count}
master_number: ${master_number}
region: ${grainregion}
roles:
  - ${grainrole}
salt_repos: ${salt_repos}
salt_hostname: ${salt_hostname}
salt_api_hostname: ${salt_hostname}-api
saltenv: $saltenv
system_name: ${system_name}
EOFGRAINS

### Set our minion env
echo "Setting salt environment in /etc/salt/minion.d/env.conf"
mkdir -p /etc/salt/minion.d/
touch /etc/salt/minion.d/env.conf
cat > /etc/salt/minion.d/env.conf <<EOFILE
saltenv: $saltenv
EOFILE

### Set our minion env
echo "Setting salt environment in /etc/salt/minion.d/env.conf"
touch /etc/salt/minion.d/master.conf
cat > /etc/salt/minion.d/master.conf <<'EOFILE'
master:
  - ${salt_hostname}
EOFILE

touch /etc/salt/minion_id
# chown salt:salt /etc/salt/minion_id
cat > /etc/salt/minion_id  <<'EOFILE'
${master}
EOFILE

### Set our global minion mine functions we want avail AT minion provisoning
echo "Setting minion mine_functions in /etc/salt/minion.d/mine.conf"
touch /etc/salt/minion.d/mine.conf
cat > /etc/salt/minion.d/mine.conf <<'EOFILE'
## Lets have all minions send these 3 basic pieces on info back into the saltmine
## for future use if needed.
mine_functions:
  network.ip_addrs: []
  network.get_hostname: []
  minion_id:
    - mine_function: grains.get
    - id
EOFILE

### Lets preseed a key for the minion on our master
echo "Generating minions keys for the master.."
mkdir -p /etc/salt/pki/minion
mkdir -p /etc/salt/pki/master/minions
salt-key --gen-keys=minion --gen-keys-dir=/etc/salt/pki/minion/ > /dev/null
cp /etc/salt/pki/minion/minion.pub /etc/salt/pki/master/minions/${master}

echo "Starting Salt Master.."
service salt-master restart

### lets give it a buffer to start
sleep 15s

echo "Downloading SSH public key from remote host github.com, and saving the record in the known_hosts file.."
salt-call ssh.set_known_host user=root hostname=github.com > /dev/null

echo "Downloading SSH public key from remote host eb-github.com, and saving the record in the known_hosts file.."
salt-call ssh.set_known_host user=root hostname=eb-github.com > /dev/null

echo "Generating self signed certs for the salt-api.."
salt-call tls.create_self_signed_cert > /dev/null

### start up the minion now that we have keys preseeded
echo "Starting Salt Minion.."
service salt-minion restart

### clean-up if our key got stuck as unaccepted
if [ -f "/etc/salt/pki/master/minions_pre/${master}" ]
  then
    echo "Removing unaccepted minion key"
    rm -f /etc/salt/pki/master/minions_pre/${master}
fi

### Force a saltmine update in-case multimaster is in use - we want to ensure all Saltmasters are available in the mine asap
echo "Forcing salt-mine update.."
salt-call mine.update > /dev/null

### If this Saltmaster is NOT a primary master, lets wait until the first master comes up
if [ ${master_number} -gt 1 ]
  then
    ## Lets wait for the salt-api to come up on the main master.. this will tell us the main master is done
    echo "This appears to be a redundant Saltmaster. Waiting for primary Saltmaster to come online first.."
    while ! curl -skf -m 5 https://${salt_hostname}-api:8000/login > /dev/null ; do sleep 10s ; done
fi

### Master setup
echo "

#########################
Configuring master...
#########################

"

echo -e "\nSyncing files to cache..."
salt-run saltutil.sync_all
salt-call saltutil.sync_all
echo -e "\nPatching master..."
salt-call state.apply salt-configs.master.patches || exit 1
echo -e "\nSetting grains..."
salt-call state.apply salt-configs.master.set_grains saltenv=$saltenv || exit 1
echo -e "\nInstalling extra packages..."
salt-call state.apply salt-configs.master.extra_pkgs.gpg saltenv=$saltenv || exit 1
echo -e "\nConfiguring GPG..."
salt-call state.apply salt-configs.master.gpg_config saltenv=$saltenv || exit 1
echo -e "\nConfiguring Salt Master mine functions..."
salt-call state.apply salt-configs.master.mine_master saltenv=$saltenv || exit 1
salt-call mine.update
echo -e "\nConfiguring Salt Master..."
salt-call state.apply saltenv=$saltenv || exit 1

echo -e "\nHighstate Successful!"
salt-call grains.set bootstrap True
echo -e "\nStarting salt-api for minions.."
service salt-api restart
echo -e "\nBootstrap Done."
exit 0
