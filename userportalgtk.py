#!/usr/bin/python

import pygtk
import gtk
import gtk.glade
import gobject
import time
import sys
import os
import subprocess
from threading import Thread
import dispatcher
import urllib2
import tempfile

global dispatcher
dispatcher = dispatcher.OvirtApi()
VarSaida = True


class Client:
    def _quit(*args, **kwargs):
        global VarSaida
        VarSaida = False
        gtk.main_quit(*args, **kwargs)
        sys.exit()

    def _connect(self, button=None):
        selected_vm = self._cmb_main_vms.get_active_text().split(" :: ")[1]
        ticket, expiry = dispatcher.ticketVm(selected_vm)

        port = "port="+str(self._port)+"&" if self._port else ""
        sport = "tls-port="+str(self._sport)+"&" if self._sport else ""
        uri = "spice://%s/?%s%spassword=%s" % (self._host,
                                                port,
                                                sport,
                                                ticket)
        cmd = ["spicy", "--uri", uri]

        if self._ca_file is not None:
            cmd.append("--spice-ca-file=%s" % self._ca_file)

        subprocess.Popen(cmd)

    def _auth(self, button=None):
        url = self._ent_auth_server.get_text()
        username = self._ent_auth_user.get_text()
        password = self._ent_auth_pass.get_text()

        try:
            cert = urllib2.urlopen(url+"/ovirt-engine/ca.crt").read()
            cert_file = tempfile.NamedTemporaryFile(delete=False)
            cert_file
            cert_file.write(cert)
            cert_file.close()

            self._ca_file = cert_file.name
        except:
            self._ca_file = None

        login, msg = dispatcher.login(url,
                                      username,
                                      password,
                                      self._ca_file)

        if login:
            self._window1.hide()
            self._window2.show()
            self._list()
            t = Thread(target=self._status)
            t.start()
        else:
            self._sta_auth.push(0, msg)

    def _list(self, button=None):
        self._liststore.clear()
        for vm in dispatcher.getUserVms():
            self._liststore.append([vm.name + " :: " + vm.id])

        self._cmb_main_vms.set_active(0)

    def _status(self, button=None):
        global VarSaida
        while VarSaida:
            selected_vm = self._cmb_main_vms.get_active_text().split(" :: ")[1]
            vm = dispatcher.getVmById(selected_vm)
            state = vm.status.state
            vcpus = vm.cpu.topology
            memory = vm.memory
            os = vm.os.type_
            if vm.usb.enabled:
                usb = "Enabled"
            else:
                usb = "Disabled"

            display = vm.get_display()
            self._port = display.get_port()
            self._sport = display.get_secure_port()
            self._host = display.get_address()

            self._btn_main_refresh.set_sensitive(True)
            self._lab_Smp.set_text(str(vcpus.cores * vcpus.sockets))
            self._lab_Memory.set_text(str(memory / (1024*1024)))
            self._lab_Display.set_text(vm.display.type_)
            self._lab_Usb.set_text(usb)
            self._lab_Status.set_text(state)

            if "rhel" in os:
                self._img_So.set_from_file("images/rhel.png")
            elif "ubuntu" in os:
                self._img_So.set_from_file("images/ubuntu.png")
            elif "other" in os:
                self._img_So.set_from_file("images/linux.png")
            elif "windows" in os:
                self._img_So.set_from_file("images/win.png")
            else:
                self._img_So.set_from_file("images/ovirt.png")

            if state == "up" or state == "powering_up":
                self._checkbutton1.set_sensitive(True)
                self._cmb_main_vms.set_sensitive(True)
                self._btn_main_refresh.set_sensitive(True)
                self._btn_main_start.set_sensitive(False)
                self._btn_main_stop.set_sensitive(True)
                self._btn_main_connect.set_sensitive(True)
            else:
                self._checkbutton1.set_sensitive(True)
                self._cmb_main_vms.set_sensitive(True)
                self._btn_main_refresh.set_sensitive(True)
                self._btn_main_start.set_sensitive(True)
                self._btn_main_stop.set_sensitive(False)
                self._btn_main_connect.set_sensitive(False)

            time.sleep(2)

    def _start(self, button=None):
        selected_vm = self._cmb_main_vms.get_active_text().split(" :: ")[1]
        start, msg, details = dispatcher.startVm(selected_vm)
        if start:
            self._sta_main.push(0, "Success starting VM")
        else:
            self._sta_main.push(0, "%s: %s" % (msg, details))

    def _stop(self, button=None):
        selected_vm = self._cmb_main_vms.get_active_text().split(" :: ")[1]
        stop, msg, details = dispatcher.stopVm(selected_vm)
        if stop:
            self._sta_main.push(0, "Success stopping VM")
        else:
            self._sta_main.push(0, "%s: %s" % (msg, details))

    def __init__(self):
        gtk.gdk.threads_init()
        self.gladefile = os.getenv('HOME')+"/ovirt-userportal-gtk/userportalgtk.glade"
        self.wTree = gtk.glade.XML(self.gladefile)
        self._window1 = self.wTree.get_widget("window1")
        self._window2 = self.wTree.get_widget("window2")
        if (self._window1):
            self._window1.connect("destroy", self._quit)
        if (self._window2):
            self._window2.connect("destroy", self._quit)

        self._btn_auth_ok = self.wTree.get_widget("button1")
        self._btn_auth_cancel = self.wTree.get_widget("button2")
        self._ent_auth_user = self.wTree.get_widget("entry1")
        self._ent_auth_pass = self.wTree.get_widget("entry2")
        self._ent_auth_server = self.wTree.get_widget("entry3")
        self._sta_auth = self.wTree.get_widget("statusbar1")
        self._sta_main = self.wTree.get_widget("statusbar2")

        self._lab_Smp = self.wTree.get_widget("label7")
        self._lab_Memory = self.wTree.get_widget("label9")
        self._lab_Display = self.wTree.get_widget("label11")
        self._lab_Usb = self.wTree.get_widget("label13")
        self._lab_Status = self.wTree.get_widget("label15")

        self._img_So = self.wTree.get_widget("image1")

        self._btn_main_refresh = self.wTree.get_widget("button3")
        self._btn_main_start = self.wTree.get_widget("button4")
        self._btn_main_connect = self.wTree.get_widget("button5")
        self._btn_main_stop = self.wTree.get_widget("button6")
        self._checkbutton1 = self.wTree.get_widget("checkbutton1")

        self._cmb_main_vms = self.wTree.get_widget("combobox1")
        self._liststore = gtk.ListStore(gobject.TYPE_STRING)
        self._cmb_main_vms.set_model(self._liststore)
        cell = gtk.CellRendererText()
        self._cmb_main_vms.pack_start(cell, True)
        self._cmb_main_vms.add_attribute(cell, 'text', 0)

        self._btn_main_refresh.connect("clicked", self._list)
        self._btn_main_start.connect("clicked", self._start)
        self._btn_main_stop.connect("clicked", self._stop)
        self._btn_main_connect.connect("clicked", self._connect)

        self._btn_auth_ok.connect("clicked", self._auth)
        self._btn_auth_cancel.connect("clicked", quit)

        self._window1.show()


if __name__ == "__main__":
        hwg = Client()
        gtk.main()
