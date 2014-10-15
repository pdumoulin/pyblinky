__author__ = "Paul Dumoulin"
__email__ = "paul.l.dumoulin@gmail.com"

import re
import urllib2
import time

try:
    import android
    droid = android.Android()
except ImportError:
    import sys
    droid = None


class wemo:
    OFF_STATE = '0'
    ON_STATE = '1'
    ip = None
    ports = [49153, 49152, 49154]

    def __init__(self, switch_ip):
        self.ip = switch_ip      
   
    def toggle(self):
        status = self.status()
        if status == self.ON_STATE:
            result = self.off()
        elif status == self.OFF_STATE:
            result = self.on()
        else:
            raise Exception("UnexpectedStatusResponse")
        return result    
    
    def burst(self, seconds):
        status = self.status()
        if status == self.OFF_STATE:
            self.on()
            time.sleep(seconds)
            result = self.off()
            return result
        else:
            raise Exception("UnexpectedStatusResponse")

    def on(self):
        return self._send('SetBinaryState', 'BinaryState', 1)

    def off(self):
        return self._send('SetBinaryState', 'BinaryState', 0)

    def status(self):
        return self._send('GetBinaryState', 'BinaryState')

    def name(self):
        return self._send('GetFriendlyName', 'FriendlyName')

    def signal(self):
        return self._send('GetSignalStrength', 'SignalStrength')
  
    def _get_header_xml(self, method):
        return '"urn:Belkin:service:basicevent:1#%s"' % method
   
    def _get_body_xml(self, method, obj, value=0):
        return '<u:%s xmlns:u="urn:Belkin:service:basicevent:1"><%s>%s</%s></u:%s>' % (method, obj, value, obj, method)
    
    def _send(self, method, obj, value=None):
        body_xml = self._get_body_xml(method, obj, value)
        header_xml = self._get_header_xml(method)
        for port in self.ports:
            result = self._try_send(self.ip, port, body_xml, header_xml, obj) 
            if result is not None:
                self.ports = [port]
            return result
        raise Exception("TimeoutOnAllPorts")

    def _try_send(self, ip, port, body, header, data):
        try:
            request = urllib2.Request('http://%s:%s/upnp/control/basicevent1' % (ip, port))
            request.add_header('Content-type', 'text/xml; charset="utf-8"')
            request.add_header('SOAPACTION', header)
            request_body = '<?xml version="1.0" encoding="utf-8"?>'
            request_body += '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
            request_body += '<s:Body>%s</s:Body></s:Envelope>' % body
            request.add_data(request_body)
            result = urllib2.urlopen(request, timeout=1)
            return self._extract(result.read(), data)
        except Exception as e:
            print str(e)
            return None

    def _extract(self, response, name):
        exp = '<%s>(.*?)<\/%s>' % (name, name)
        g = re.search(exp, response)
        if g:
            return g.group(1)
        return response

def get_args():
    result = {}
    params = droid.getIntent().result[u'extras'] if droid is not None else {}
    result['ip'] = sys.argv[1] if droid is None else params['%argv1']
    result['command'] = sys.argv[2] if droid is None else params['%argv2']
    if result['command'] == 'burst':
        result['time'] = sys.argv[3] if droid is None else params['%argv3']
        result['time'] = float(result['time'])
    return result

def output(message):
    if droid is None:
        print message
    else:
        droid.makeToast(message)

def main():
    args = get_args()
    switch = wemo(args['ip'])
    if args['command'] == 'on':
        output(switch.on())
    elif args['command'] == 'off':
        output(switch.off())
    elif args['command'] == 'toggle':
        output(switch.toggle())
    elif args['command'] == 'status':
        output(switch.status())
    elif args['command'] == 'name':
        output(switch.name())
    elif args['command'] == 'signal':
        output(switch.signal())
    elif args['command'] == 'burst':
        output(switch.burst(args['time']))
    
if __name__ == "__main__":
    main()
