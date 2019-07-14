"""
  McDaniel Jul-2019
  lpm0073@gmail.com
  https://lawrencemcdaniel.com

  Helpers to connect to EC2 instance via SSH using paramiko, and execute
  and log remote commands

  docs: https://docs.paramiko.org/en/2.6/

"""
import traceback
import paramiko


paramiko.util.log_to_file("aws.ssh.log")
# Paramiko client configuration
UseGSSAPI = (
    paramiko.GSS_AUTH_AVAILABLE
)  # enable "gssapi-with-mic" authentication, if supported by your python installation
DoGSSAPIKeyExchange = (
    paramiko.GSS_AUTH_AVAILABLE
)  # enable "gssapi-kex" key exchange, if supported by your python installation



def ssh_connect(hostname, username, pkey_path, port):
    pkey = paramiko.RSAKey.from_private_key_file(pkey_path)

    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())

        print("Connecting to {} ...".format(hostname))
        client.connect(hostname=hostname, port=port, username=username, pkey=pkey)
        return client

    except Exception as e:
        print("*** Caught exception: %s: %s" % (e.__class__, e))
        traceback.print_exc()
        try:
            client.close()
        except:
            pass

        return None

def ssh_disconnect(client):
    print("Disconnecting ...")
    client.close()

def ssh_exec(client, command_string):
    print('Executing remote command ...')
    print('================================================================================')
    print('~$ ' + command_string)
    stdin, stdout, stderr = client.exec_command(command_string)
    for ln in stdout:
        print(ln.strip('\n'))
    print('================================================================================')
    print('Completed remote command.')
