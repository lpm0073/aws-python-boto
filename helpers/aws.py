"""
  McDaniel Jul-2019
  lpm0073@gmail.com
  https://lawrencemcdaniel.com

  Usage: AWS CLI helper methods to manage EC2, S3, Route53, Security Groups, Elastic IP

"""
import boto3
from botocore.exceptions import ClientError


ec2 = boto3.client('ec2')
route53 = boto3.client('route53')
Services = {
    'app': '_edxapp',
    'mongo': '_mongo',
    's3': '',
    'route53': '',
    'elastic_ip': ''
}
servers = {
    'app': 'edxapp-launch-configuration',
    'mongo': 'edxapp-launch-configuration'
}

"""
returns attribute data for the EC2 instance with the given tag name
"""
def ec2_instance_list(name_tag):
    filters = []
    filters.append({
                'Name': 'instance-state-name',
                'Values': ['running']
    })
    if name_tag:
        filters.append({
                    'Name': 'tag:Name',
                    'Values': [name_tag]
                    })

    response = ec2.describe_instances(Filters=filters)

    retval = {}
    for r in response['Reservations']:
        for i in r['Instances']:
            if 'Tags' in i: instance_name = i['Tags'][0]['Value']
            else: instance_name = ''

            if 'PublicIpAddress' in i: PublicIpAddress = i['PublicIpAddress']
            else: PublicIpAddress = ''

            retval = {'InstanceId': i['InstanceId'], 'PublicIpAddress': PublicIpAddress, 'Tag': instance_name, 'InstanceType': i['InstanceType']}

    # for now we'll just return the last occurrance
    return retval

"""
    Docs: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.run_instances

    Launch configuration:
        ami-0f93b5fd8f220e428
"""
def ec2_instance_create(tagName, serverType=None):

    print('Creating EC2 instance {}'.format(tagName))
    try:
        instance = ec2.run_instances(
            DryRun=False,
            Monitoring={
                'Enabled': False
            },
            InstanceInitiatedShutdownBehavior='stop',
            MaxCount=1,
            MinCount=1,
            LaunchTemplate={
                'LaunchTemplateName': servers.get(serverType, "edxapp-launch-configuration")
            },
            TagSpecifications=[
                {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': tagName
                    }
                ]
                },
            ],
        )
        print('Successfully created EC2 instance.')
        _ec2_instance_wait(tagName)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            print("Could not create EC2 instance")
            raise

"""
    setup a waiter to suspend execution until the tagged instance is up
"""
def _ec2_instance_wait(tagName):
    InstanceIds=_get_instanceids_by_filter(
            filter=[
                {
                'Name': 'tag:Name',
                'Values': [tagName]
                },
                {
                'Name': 'instance-state-name',
                'Values': ['pending']
                }
            ]
    )

    if len(InstanceIds) > 0:
        print('Waiting for new instance {} to launch.'.format(tagName))
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(
            InstanceIds=InstanceIds,
            DryRun=False,
            WaiterConfig={
                'Delay': 15,
                'MaxAttempts': 10
            }
        )
        print('New instance is launched.')

"""
    returns a list of EC2 instance id's meeting the filter criteria.
"""
def _get_instanceids_by_filter(filter):
    response = ec2.describe_instances(Filters=filter)
    InstanceIds=[]
    for r in response['Reservations']:
        for i in r['Instances']:
            if 'InstanceId' in i:
                InstanceIds.append(i['InstanceId'])

    return InstanceIds

"""
    reboot an EC2 instance
"""
def ec2_instance_reboot(instance_id):
    try:
        ec2.reboot_instances(InstanceIds=[instance_id], DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            print("You don't have permission to reboot instances.")
            raise

    try:
        response = ec2.reboot_instances(InstanceIds=[instance_id], DryRun=False)
        print('Success', response)
    except ClientError as e:
        print('Error', e)

"""
return the AWS resource identifier and pubic IP address
for the given Name tag
"""
def ip_address_get(name_tag):
    filters = [
        {'Name': 'domain', 'Values': ['vpc']},
        {'Name': 'tag:Name', 'Values': [name_tag]}
    ]
    response = ec2.describe_addresses(Filters=filters)
    retval = {}
    if len(response['Addresses']) == 0:
        print("No IP address found. Creating new IP address for {}".format(name_tag))
        result_dict = ip_address_create(name_tag)
    else:
        result_dict = response['Addresses'][0]

    retval = {'PublicIp': result_dict['PublicIp'], 'AllocationId': result_dict['AllocationId']}
    return retval

"""
    create a new Elastic IP and tag it with name_tag
"""
def ip_address_create(name_tag):
    retval = {}
    try:
        allocation = ec2.allocate_address(Domain='vpc')
        # returns {'Domain': 'vpc', 'PublicIpv4Pool': 'amazon', 'AllocationId': 'eipalloc-0c52ca59d9efd6036', 'ResponseMetadata': {'HTTPStatusCode': 200, 'RetryAttempts': 0, 'RequestId': '5cc0465f-c124-4668-bdd5-04300db69530', 'HTTPHeaders': {'server': 'AmazonEC2', 'content-type': 'text/xml;charset=UTF-8', 'date': 'Wed, 10 Jul 2019 14:34:49 GMT', 'content-length': '372'}}, 'PublicIp': '3.13.206.175'}
        print('New IP address created: {}'.format(allocation['PublicIp']))
    except ClientError as e:
        print(e)
        return retval

    # tag the new IP address
    response = tag_set(allocation['AllocationId'], name_tag)
    retval = {'PublicIp': allocation['PublicIp'], 'AllocationId': allocation['AllocationId']}
    return retval

"""
  Associate an Elastic IP address with an EC2 instance
"""
def ip_address_associate(PublicIp, InstanceId):

    print('Associating IP address {PublicIp} with InstanceId {InstanceId}'.format(
                                                    PublicIp=PublicIp,
                                                    InstanceId=InstanceId
                                                    ))
    try:
        response = ec2.associate_address(PublicIp=PublicIp,
                                         InstanceId=InstanceId)
        print(response)
    except ClientError as e:
        print(e)



"""
Add a name tag to a AWS resource
"""
def tag_set(AllocationId, name_tag):
    try:
        response = ec2.create_tags(
            DryRun=False,
            Resources=[
                AllocationId,
            ],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': name_tag
                },
            ]
        )
        print('tagged resource: {}'.format(response))
    except ClientError as e:
        print(e)

    return response

"""
Generate a pre-formatted AWS resource tag name
"""
def tag_get(client, service=None):

    return client.lower() + Services.get(service, "")
