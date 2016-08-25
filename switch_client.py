
import os
import sys
import argparse
from ConfigParser import SafeConfigParser
from P4Session import P4Session, P4Exception

def get_config():
    config = SafeConfigParser()
    if (sys.platform == "win32"):
        configPath = os.path.join('e:', '/', 'EC', 'cad_scripts')
    elif (sys.platform == "linux2"):
        configPath = os.path.join('/', 'mntdir', 'common', 'ec_scripts')
    testIni = os.path.join(configPath, 'tests.ini')
    configIni = os.path.join(configPath, 'config.ini')
    listConfigs = [configIni, testIni]
    config.read(listConfigs)

    print testIni
    print configIni

    return config


def switchWS(p4, sgpuRootWs, clientRoot, branch):
# Add ectool subroutine
    stream = "//%s/%s" % ("sgpu", branch)
    print stream

    client = p4.fetch_client("-t", sgpuRootWs)
    client._root = "%s_%s" % (clientRoot, branch)
    p4.save_client(client)
    p4.run("client", "-f", "-s", "-S", stream)
    switchedClient = p4.run("client", "-o")

    for client in switchedClient:
        print "The client is now switched to %s stream" % (client['Stream'])

#        p4.run("sync", "-n", "-m", "1")
# use the plugin to sync
#        wsStatus = p4.run("status")
#        print wsStatus


def main():
    parser = argparse.ArgumentParser(description='script to switch clients')
    parser.add_argument('--client_root', type=str, help='clent root', required=True)
    parser.add_argument('--branch', type=str, help='branch to sync', required=True)
    args = parser.parse_args()

    clientRoot = args.client_root
    branch = args.branch

    config = get_config()
    sgpuRootWs = config.get('p4_server', 'sgpu_submit_client')

    # Add checkout step from ectool

    try:
        with P4Session(config) as p4:
            switchWS(p4, sgpuRootWs, clientRoot, branch)

    except P4Exception, e:
        print "Error : ", e
        sys.exit(e)


if  __name__ == '__main__':
    main()

