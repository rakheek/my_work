# Revision
# 2016/07/05 - INFR-847, peter.y, Enabling Supercom Site

from optparse import OptionParser
import requests
import sys
import os
from subprocess import call

RESULT_KEY = 'result'
MESSAGE_KEY = 'message'
#DMS_HOST='aplapic'
DMS_HOST = '105.160.64.31' if os.environ['ESCHER_SITE'] == 'SC' else 'aplapic'
SC_ECSERVER_HOST = 'ecserver'

def parse_options():
    usage = 'usage: %prog [options] report'
    parser = OptionParser(usage=usage)
    parser.add_option("-a", "--autocreateapplication", dest="auto_create_application",
                      default=False, action='store_true', help='auto create application names')
    parser.add_option("-p", "--port", dest="port", help='port number of DMS server')
    parser.add_option("-s", "--server", dest="dms_server", help='DMS server (IP/name) to publish to')
    parser.add_option("-l", "--localhost", dest="use_localhost", default=False, action='store_true', help='use localhost for DMS server')
    parser.add_option("", "--noexec", dest="no_exec", default=False, action='store_true', help='Supercom only: no more remote gateway exec')
    (options, args) = parser.parse_args()
    if len(args) == 0:
        parser.print_help()
        sys.exit(1)
    if len(args) > 1:
        print 'only one report may be published at a time'
        parser.print_help()
        sys.exit(1)
    return (options, args)

def main():
    (options, args) = parse_options()

    if (os.environ['ESCHER_SITE'] == 'SC') and (not options.no_exec) and (os.environ['HOSTNAME'] != SC_ECSERVER_HOST):
        sys.argv.insert(1, '--noexec')
        call(['ssh', SC_ECSERVER_HOST, 'python'] + sys.argv)
        sys.exit(0)
    else:
        dms_server = DMS_HOST if options.dms_server is None else options.dms_server
        dms_server = 'localhost' if options.use_localhost else dms_server
        server_port = 8000 if not options.port else int(options.port)
        url = 'http://%s:%d/api/publish' % (dms_server, server_port)
        if options.auto_create_application:
            url += '/auto_create_application/'
        print 'publishing using DMS running at %s' % url
        yaml_file_name = args[0]
        files = {'publishfile': open( yaml_file_name ) }
        response = requests.post(url, files = files)
        print('%s:' % yaml_file_name),
        exit_code = 0
        if response.status_code == 200:
            resp_json = response.json()
            if resp_json[RESULT_KEY] == 'ok':
                print 'publish successful: %s' % resp_json[MESSAGE_KEY]
            else:
                print 'publish error: %s' % resp_json[MESSAGE_KEY]
                exit_code = 1
        else:
            print 'publish error: HTTP status code %d' % response.status_code
            print str(response)
            exit_code = 1
        sys.exit(exit_code)

if __name__ == '__main__':
    main()
