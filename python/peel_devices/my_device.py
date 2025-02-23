from PeelApp import cmd
from peel_devices import SimpleDeviceWidget, PeelDeviceBase

class MyDeviceWidget(SimpleDeviceWidget):
    def __init__(self, settings):
        super(MyDeviceWidget, self).__init__(settings, "AxisStudio", has_host=False, has_port=False,
                                             has_broadcast=False, has_listen_ip=False, has_listen_port=False)

class MyDevice(PeelDeviceBase):

    def __init__(self, name="MyDevice"):
        super(MyDevice, self).__init__(name)
        self.device_state = "ONLINE"
        self.info = ""
        self.name = name
        self.plugin_id = cmd.createDevice("MyDevice")
        if self.plugin_id == -1:
            raise RuntimeError("Could not create plugin device")

        self.reconfigure(name)

    def set_enabled(self, value):
        super().set_enabled(value)
        cmd.setDeviceEnabled(self.plugin_id, value)

    @staticmethod
    def device():
        return "mydevice"

    def as_dict(self):
        return {'name': self.name}

    def reconfigure(self, name, **kwargs):
        self.name = name
        cmd.configureDevice(self.plugin_id, "DATA")
        cmd.setDeviceEnabled(self.plugin_id, self.enabled)

    def teardown(self):
        cmd.deleteDevice(self.plugin_id)

    def thread_join(self):
        pass

    def command(self, command, arg):
        # plugin commands are passed directly
        pass

    def get_state(self):
        # plugin device states are managed directly
        return ""

    def get_info(self):
        # plugin device info messages are handled directly
        return ""

    @staticmethod
    def dialog(settings):
        return MyDeviceWidget(settings)

    @staticmethod
    def dialog_callback(widget):
        if not widget.do_add():
            return

        ret = MyDevice()
        if widget.update_device(ret):
            return ret

    def edit(self, settings):
        dlg = MyDeviceWidget(settings)
        dlg.populate_from_device(self)
        return dlg

    def edit_callback(self, widget):
        if not widget.do_add():
            return
        widget.update_device(self)

    def has_harvest(self):
        return False

    def list_takes(self):
        return []
