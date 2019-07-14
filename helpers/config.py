"""
  McDaniel Jul-2019
  lpm0073@gmail.com
  https://lawrencemcdaniel.com

  Usage: Read/write configuration data
  docs:  https://docs.python.org/3/library/configparser.html

  Example setters:
        set('client', 'subdomain', 'church-of-lawrence')

  Example getters:
        get('client', 'subdomain')
        get('edx_platform', 'instance_id')

"""
import configparser
from os import path

APP_CONFIGURATION_FILE = '/home/ubuntu/config'
APP_DOMAIN_NAME = 'roverbyopenstax.org'
cfgParser = configparser.ConfigParser()


"""
    Generate a fully-qualified domain name based on stored app config data.
"""
def fqdn(client=None, appName=None):
    app = {
        'lms': 'courses',
        'am': 'am'
    }
    domain = get('settings', 'domain')
    subdomain = get(client, 'subdomain').lower()
    return  '{app}.{subdomain}.{domain}'.format(
                                            app = app.get(appName, "").lower(),
                                            domain = domain,
                                            subdomain = subdomain
                                            )


"""
    called at app startup iff no config file exists
"""
def config_write_default():
    cfgParser['SETTINGS'] = {
            'domain': APP_DOMAIN_NAME
    }

    cfgParser['DEV'] = {
            'subdomain': 'dev',
            'edxapp_ip_address': '1.2.3.4',
            'edxapp_instance_id': '123456789',
            'mongo_ip_address': '',
            'mongo_instance_id': ''
    }

    with open(APP_CONFIGURATION_FILE, 'w') as configfile:
        cfgParser.write(configfile)

def config_register_client(client, subdomain, edxapp_ip_address,
            edxapp_instance_id, mongo_ip_address, mongo_instance_id):

    cfgParser[client.upper()] = {
            'subdomain': subdomain,
            'edxapp_ip_address': edxapp_ip_address,
            'edxapp_instance_id': edxapp_instance_id,
            'mongo_ip_address': mongo_ip_address,
            'mongo_instance_id': mongo_instance_id
    }

    with open(APP_CONFIGURATION_FILE, 'w') as configfile:
        cfgParser.write(configfile)


def get(section, element):
    try:
        retval = cfgParser[section.upper()][element.lower()]
    except Exception as e:
        retval = None
        pass

    return retval

def set(client, element, value):
    cfgParser[client.upper()][element.lower()] = value
    with open(APP_CONFIGURATION_FILE, 'w') as configfile: cfgParser.write(configfile)
    return

def init():
    cfgParser.read(APP_CONFIGURATION_FILE)

#==============================================================================
if not path.exists(APP_CONFIGURATION_FILE):
    print('Creating default config file.')
    config_write_default()
