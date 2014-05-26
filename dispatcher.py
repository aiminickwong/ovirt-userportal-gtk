from ovirtsdk.api import API
from ovirtsdk.infrastructure.errors import RequestError, ConnectionError

api = None

class OvirtApi(object):
    def login(self, url, username, password, ca_file):
        global api
        try:
            api = API(url=url,
                      username=username,
                      password=password,
                      ca_file=ca_file)
        except RequestError as reqErr:
            return False, "Login error"
        except ConnectionError as conErr:
            return False, "Bad URL"
        return True, ''

    def getUserVms(self):
        global api
        return api.vms.list()

    def getVmById(self, id):
        global api
        return api.vms.get(id=id)

    def getVmStatus(self, id):
        global api
        return api.vms.get(id=id).status.state

    def startVm(self, vmid):
        global api
        try:
            api.vms.get(id=vmid).start()
        except RequestError as reqErr:
            return False, reqErr.reason, reqErr.detail
        except ConnectionError as conErr:
            return False, 'Connection Error'
        return True, None, None

    def stopVm(self, vmid):
        global api
        try:
            api.vms.get(id=vmid).stop()
        except RequestError as reqErr:
            return False, reqErr.reason, reqErr.detail
        except ConnectionError as conErr:
            return False, 'Connection Error'
        return True, None, None

    def ticketVm(self, vmid):
        global api
        try:
            ticket = api.vms.get(id=vmid).ticket()
            return ticket.get_ticket().get_value(), ticket.get_ticket().get_expiry()
        except RequestError as reqErr:
            raise Exception(reqErr.reason, reqErr.detail)
        except ConnectionError as conErr:
            raise Exception('Connection Error', '')
