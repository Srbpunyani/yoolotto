import json

from fabric.api import *
from fabric.context_managers import *

env.hosts = ["app.yoolotto.com"]
env.user = "deploy"

@task
def deploy_backend(password, commit, build=None):
    env.password = password
    
    with cd("/opt/apps/yl"):
        data = {"commit": commit, "build": build}
        path = "/opt/apps/yl/deploy/version.json"
        
        sudo("git fetch")
        sudo("git reset -q %s --hard" % commit)
        sudo("echo '%s' > %s" % (json.dumps(data), path))
        sudo("chmod 0770 /opt/apps/yl/manage.py")
        sudo("chown -R www-data: /opt/apps/yl")
        sudo("touch /opt/yoolotto-uwsgi.pid")
        sudo("service celeryd restart")
        