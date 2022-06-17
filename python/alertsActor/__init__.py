
import os
import yaml

from sdsstools import get_logger

log = get_logger('alerts')


# Loads config

if os.path.isfile(os.path.expanduser('~/.alertsConfig.yml')):
    configFile = os.path.expanduser('~/.alertsConfig.yml')
else:
    print("Local config not found! Using default")
    configFile = os.path.join(os.path.dirname(__file__), 'etc/alerts.cfg')

if os.path.isfile(os.path.expanduser("~/.alertActions.yml")):
    actionsFile = os.path.expanduser("~/.alertActions.yml")
else:
    print("Local alert actions not found! Using default")
    actionsFile = os.path.join(os.path.dirname(__file__), 'etc/alertActions.yml')

try:
    config = yaml.load(open(configFile), Loader=yaml.FullLoader)

    alertActions = yaml.load(open(actionsFile), Loader=yaml.UnsafeLoader)
except AttributeError:
    # using pyyaml < 5, enforce old behavior
    config = yaml.load(open(configFile))

    alertActions = yaml.load(open(actionsFile))

__version__ = '2.2.1'
