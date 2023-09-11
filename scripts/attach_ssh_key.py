"""
Script to attach new ssh key stored in the parameter store to the remote server using authenticated ssh key

usage: attach_ssh_key.py [-h] --parameter-name PARAMETER_NAME --ssh-path
                         SSH_PATH [--region REGION]
                         [--aws-profile AWS_PROFILE] --username USERNAME
                         --ip-address IP_ADDRESS [--name NAME] [--debug]
                         [--generate-pem-file] [--pem-file-path PEM_FILE_PATH]

optional arguments:
  -h, --help            show this help message and exit
  --parameter-name PARAMETER_NAME
                        parameter store name where ssh private key is stored
  --ssh-path SSH_PATH   local ssh path which has access to the remote server
  --region REGION       Region where parameter is stored
  --aws-profile AWS_PROFILE
                        name of the profile to use
  --username USERNAME   host user for the remote server
  --ip-address IP_ADDRESS
                        ip address of the remote server
  --name NAME           name to attach to public key in remote server for
                        identification
  --debug               Include debug logs
  --generate-pem-file   whether to generate the pem file for private key
  --pem-file-path PEM_FILE_PATH
                        where to store the generated pem file

"""
import argparse
import logging
import os

import boto3
import paramiko
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key


def _define_arguments() -> argparse.Namespace:
    """
    Define all the named arguments which are required for script to run
    :return: (object) arguments object
    """
    parser = argparse.ArgumentParser(description='Attach ssh key to the remote server')
    parser.add_argument(
        '--parameter-name',
        type=str,
        help='parameter store name where ssh private key is stored',
        required=True
    )
    parser.add_argument(
        '--ssh-path',
        type=str,
        help='local ssh path which has access to the remote server',
        required=True
    )
    parser.add_argument('--region', type=str, help='Region where parameter is stored', default='us-east-1')
    parser.add_argument('--aws-profile', type=str, help='name of the profile to use', default='default')
    parser.add_argument('--username', type=str, help='host user for the remote server', required=True)
    parser.add_argument('--ip-address', type=str, help='ip address of the remote server', required=True)
    parser.add_argument(
        '--name',
        type=str,
        help='name to attach to public key in remote server for identification',
        default=''
    )
    parser.add_argument('--debug', help='Include debug logs', action='store_true')
    parser.add_argument(
        '--generate-pem-file',
        help='whether to generate the pem file for private key',
        action='store_true'
    )
    parser.add_argument('--pem-file-path', type=str, help='where to store the generated pem file')
    args = parser.parse_args()
    if args.generate_pem_file:
        if not args.pem_file_path:
            raise ValueError(
                '--generate-pem-file argument also need destination file path location please specify'
                ' a file path in --pem-file-path argument'
            )
        elif args.pem_file_path.split('/')[-1].split('.')[1] != 'pem':
            raise ValueError(
                '--pem-file-path should always end with .pem extension'
            )
    return args


def _get_ssh_key_from_parameter_store(parameter_name: str, region: str = 'us-east-1') -> str:
    """
    Fetch the private ssh key from parameter store and return it
    :param parameter_name: parameter store name where the key is stored
    :param region: aws region
    :return: Returns the private key
    """
    client = boto3.client('ssm', region_name=region)
    logger.info('fetching private key from parameter store')
    response = client.get_parameter(
        Name=parameter_name,
        WithDecryption=True
    )
    return response.get('Parameter').get('Value')


def _load_key_to_server(private_key: str, ip_address: str, username: str, ssh_path: str, name: str = '') -> None:
    """
    Add the public key of the private key to the authorized_keys file on the server
    :param private_key: private key to load
    :param ip_address: server ip address
    :param username: username to log in with
    :param ssh_path: ssh path in local which has access to the server
    :param name: any name to assign to this key in server for identification
    """
    logger.info('generating public key for private key')
    key = load_pem_private_key(bytes(private_key, 'utf-8'), None, default_backend())
    err_flag = False
    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH
    )
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip_address, username=username, key_filename=ssh_path)
    logger.info(f'adding public key to the server {ip_address}')
    _, _, err = ssh.exec_command(f"echo {public_key.decode('utf-8')} {name} >> .ssh/authorized_keys")
    err = err.readlines()
    if err:
        logger.error(f'Got error while adding public key to serve err:- {err}')
        err_flag = True
    _, output, err = ssh.exec_command('cat .ssh/authorized_keys')
    err = err.readlines()
    if err:
        logger.error(f'Got error while checking for public key in serve err:- {err}')
        err_flag = True
    if f"{public_key.decode('utf-8')} {name}\n" not in output.readlines():
        logger.error(f'public key not added to the server')
    ssh.close()
    if not err_flag:
        logger.info(f'public key added successfully to the server {ip_address}')


def _generate_pem_file(file_path: str, private_key: str) -> None:
    """
    Generates the ssh pem file on local
    :param file_path: destination file path on where to store the ssh pem file
    :param private_key: private key to store
    """
    logger.info(f'creating pem file {file_path}')
    with open(file_path, 'w') as ssh_file:
        ssh_file.write(private_key)
    os.chmod(file_path, 0o400)
    logger.info(f'pem file {file_path} created successfully')


def main():
    """
    Main script to attach ssh key
    """
    args = _define_arguments()
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger.setLevel(log_level)
    if args.aws_profile:
        os.environ['AWS_PROFILE'] = args.aws_profile
    private_key = _get_ssh_key_from_parameter_store(parameter_name=args.parameter_name, region=args.region)
    _load_key_to_server(
        private_key=private_key,
        ip_address=args.ip_address,
        username=args.username,
        ssh_path=args.ssh_path,
        name=args.name
    )
    if args.generate_pem_file:
        _generate_pem_file(file_path=args.pem_file_path, private_key=private_key)
    if args.aws_profile:
        del os.environ['AWS_PROFILE']


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('airbyte-ssh-key')
    main()
