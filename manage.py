"""
  McDaniel Jul-2019
  lpm0073@gmail.com
  https://lawrencemcdaniel.com

  Usage: high-level code sample / supplement for Jul-2019 blog post on automating
  AWS management operations.
"""

from helpers.aws import tag_get, ec2_instance_list, ip_address_get, \
                        ip_address_associate, ec2_instance_create
from helpers.config import config_register_client, fqdn

def provision(client):
    print('provision AWS infrastructure for client: {}'.format(client.upper()))
    print('================================================================================')
    print('')

    print('provision Open edX app server')
    edxapp_instance_id = _provision_appserver(client)
    edxapp_ip_address = _provision_app_ip(client)
    ip_address_associate(edxapp_ip_address, edxapp_instance_id)
    print('')
    print('')
    print('provision MongoDb server')
    mongo_instance_id = _provision_mongoserver(client)
    mongo_ip_address = _provision_mongo_ip(client)
    ip_address_associate(mongo_ip_address, mongo_instance_id)

    print('')
    print('Register new client')
    config_register_client(client=client,
                           subdomain=client,
                           edxapp_ip_address = edxapp_ip_address,
                           edxapp_instance_id = edxapp_instance_id,
                           mongo_ip_address = mongo_ip_address,
                           mongo_instance_id = mongo_instance_id)

    print('Fully qualified domain: {}'.format(fqdn(client, 'lms')) )
    print('================================================================================')

    return None

def _provision_appserver(client):
    app_tag = tag_get(client=client, service='app')
    print('App server name: {}'.format(app_tag))

    app_server_dict = ec2_instance_list(app_tag)
    if app_server_dict == {}:
        print('No app server found for {}.'.format(client.upper()))
        ec2_instance_create(app_tag, 'app')
        app_server_dict = ec2_instance_list(app_tag)

    print('App server stuff: {}'.format(app_server_dict))

    if app_server_dict != {}:
        return app_server_dict['InstanceId']
    else:
        return ''

def _provision_app_ip(client):
    app_tag = tag_get(client=client, service='app')

    app_ip_dict = ip_address_get(app_tag)
    print('App server IP address: {}'.format(app_ip_dict))

    if app_ip_dict != {}:
        return app_ip_dict['PublicIp']
    return ''


def _provision_mongoserver(client):
    mongo_tag = tag_get(client=client, service='mongo')
    print('Mongo server name: {}'.format(mongo_tag))

    mongo_server_dict = ec2_instance_list(mongo_tag)
    if mongo_server_dict == {}:
        print('No mongo server found for {}.'.format(client.upper()))
        ec2_instance_create(mongo_tag, 'mongo')
        mongo_server_dict = ec2_instance_list(mongo_tag)

    print('Mongo server stuff: {}'.format(mongo_server_dict))

    if mongo_server_dict != {}:
        mongo_instance_id = mongo_server_dict['InstanceId']
        return mongo_instance_id
    else:
        return ''


def _provision_mongo_ip(client):
    mongo_tag = tag_get(client=client, service='mongo')
    mongo_ip_dict = ip_address_get(mongo_tag)
    print('Mongo server IP address: {}'.format(mongo_ip_dict))

    if mongo_ip_dict != {}:
        return mongo_ip_dict['PublicIp']
    return ''

provision('UNT')
