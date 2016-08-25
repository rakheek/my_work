'''
P4Session Context Manager for P4 sessions

'''

import os
import sys
import tempfile

from P4 import P4, P4Exception

class P4Session(object):
    '''Context Manager for a P4 session'''
    def __init__(self, config, site_name=''):
        '''P4Session constructor
        site_name:
          'sc': use p4 port configured for p4_server_sc instead of p4_server
        '''
        self.config = config
        self.site_name = site_name
        self.p4 = P4()
        self.ticket_file = None

    def __enter__(self):
        '''Context entry point: Connect and log in'''
        script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]

        config = self.config
        self.p4.ticket_file = self.ticket_file = os.path.join(tempfile.gettempdir(), '.p4ticket_%s_%05d'%(script_name, os.getpid()))
        self.p4.user = config.get('p4_server', 'P4USER')
        self.p4.password = config.get('p4_server', 'P4TICKET')

        if self.site_name:
            self.p4.port = config.get('p4_server_'+self.site_name, 'P4PORT')
        else:
            self.p4.port = config.get('p4_server', 'P4PORT')

        self.p4.connect()
        self.p4.run_login()
        return self.p4

    def __exit__(self, exc_type, exc_value, traceback):
        '''Context exit point: Disconnect and delete ticket file'''
        self.p4.disconnect()
        try:
            os.unlink(self.ticket_file)
        except OSError:
            pass


class push_attr(object):
    """Apply attribute(s) for the duration of this context, then restore the previous values.
    The attribute is required to have an initial value prior to this context.

    example:
        x.a = 7

        with push_attr(x, a=3):
            assert(x.a == 3)

        assert(x.a == 7)
    """

    def __init__(self, obj, **kwargs):
        self.obj = obj
        self.kwargs = kwargs;
        self.push = {}

    def __enter__(self):
        for k,v in self.kwargs.items():
            self.push[k] = getattr(self.obj, k)
            setattr(self.obj, k, v)

    def __exit__(self, exc_type, exc_value, traceback):
        for k,v in self.push.items():
            setattr(self.obj, k, v)



if __name__ == '__main__':
    # Sample usage (this module is intended for import)

    try:
        with P4Session() as p4:
            out = p4.run('info')
            print(out)
    except P4Exception as e:
        print(e)

