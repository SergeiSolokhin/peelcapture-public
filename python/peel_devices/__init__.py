# Copyright (c) 2022 Peel Software Development Inc
# All Rights Reserved.
#
# THIS SOFTWARE AND DOCUMENTATION ARE PROVIDED "AS IS" AND WITH ALL FAULTS AND DEFECTS WITHOUT WARRANTY OF ANY KIND. TO
# THE MAXIMUM EXTENT PERMITTED UNDER APPLICABLE LAW, PEEL SOFTWARE DEVELOPMENT, ON ITS OWN BEHALF AND ON BEHALF OF ITS
# AFFILIATES AND ITS AND THEIR RESPECTIVE LICENSORS AND SERVICE PROVIDERS, EXPRESSLY DISCLAIMS ALL WARRANTIES, WHETHER
# EXPRESS, IMPLIED, STATUTORY, OR OTHERWISE, WITH RESPECT TO THE SOFTWARE AND DOCUMENTATION, INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, AND NON-INFRINGEMENT, AND WARRANTIES THAT MAY
# ARISE OUT OF COURSE OF DEALING, COURSE OF PERFORMANCE, USAGE, OR TRADE PRACTICE. WITHOUT LIMITATION TO THE FOREGOING,
# PEEL SOFTWARE DEVELOPMENT PROVIDES NO WARRANTY OR UNDERTAKING, AND MAKES NO REPRESENTATION OF ANY KIND THAT THE
# LICENSED SOFTWARE WILL MEET REQUIREMENTS, ACHIEVE ANY INTENDED RESULTS, BE COMPATIBLE, OR WORK WITH ANY OTHER
# SOFTWARE, APPLICATIONS, SYSTEMS, OR SERVICES, OPERATE WITHOUT INTERRUPTION, MEET ANY PERFORMANCE OR RELIABILITY
# STANDARDS OR BE ERROR FREE, OR THAT ANY ERRORS OR DEFECTS CAN OR WILL BE CORRECTED.
#
# IN NO EVENT WILL PEEL SOFTWARE DEVELOPMENT OR ITS AFFILIATES, OR ANY OF ITS OR THEIR RESPECTIVE LICENSORS OR SERVICE
# PROVIDERS, BE LIABLE TO ANY THIRD PARTY FOR ANY USE, INTERRUPTION, DELAY, OR INABILITY TO USE THE SOFTWARE; LOST
# REVENUES OR PROFITS; DELAYS, INTERRUPTION, OR LOSS OF SERVICES, BUSINESS, OR GOODWILL; LOSS OR CORRUPTION OF DATA;
# LOSS RESULTING FROM SYSTEM OR SYSTEM SERVICE FAILURE, MALFUNCTION, OR SHUTDOWN; FAILURE TO ACCURATELY TRANSFER, READ,
# OR TRANSMIT INFORMATION; FAILURE TO UPDATE OR PROVIDE CORRECT INFORMATION; SYSTEM INCOMPATIBILITY OR PROVISION OF
# INCORRECT COMPATIBILITY INFORMATION; OR BREACHES IN SYSTEM SECURITY; OR FOR ANY CONSEQUENTIAL, INCIDENTAL, INDIRECT,
# EXEMPLARY, SPECIAL, OR PUNITIVE DAMAGES, WHETHER ARISING OUT OF OR IN CONNECTION WITH THIS AGREEMENT, BREACH OF
# CONTRACT, TORT (INCLUDING NEGLIGENCE), OR OTHERWISE, REGARDLESS OF WHETHER SUCH DAMAGES WERE FORESEEABLE AND WHETHER
# OR NOT THE LICENSOR WAS ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.


from PySide6 import QtWidgets, QtCore
import pkgutil, inspect
import importlib
import os
import logging, sys
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(sys.stdout))

try:
    from PeelApp import cmd
    import PeelApp
except ImportError:
    print("Could not import peel app - this script needs to run with peel Capture")

from peel_devices import device_util
from PySide6.QtNetwork import QTcpSocket, QAbstractSocket


class BaseDeviceWidget(QtWidgets.QWidget):
    """ Base class used as a widget when adding a new device """
    def __init__(self, settings):
        super(BaseDeviceWidget, self).__init__()
        self.settings = settings
        self.click_flag = False
        self.info_text = ""

    def do_add(self):
        if self.click_flag:
            return False
        self.click_flag = True
        return True

    def set_info(self, msg):
        self.info_text = msg


class SimpleDeviceWidget(BaseDeviceWidget):
    """ A basic dialog for a device that has a name and an optional IP argument """
    def __init__(self, settings, title, has_host, has_port, has_broadcast, has_listen_ip, has_listen_port,
                 has_set_capture_folder=False):
        super(SimpleDeviceWidget, self).__init__(settings)
        self.form_layout = QtWidgets.QFormLayout()
        self.title = title

        self.setWindowTitle(title)
        self.setObjectName(title)

        self.name = QtWidgets.QLineEdit()
        self.name.setText(settings.value(title + "Name", title))
        self.form_layout.addRow("Name", self.name)

        self.host = None
        self.port = None
        self.broadcast = None
        self.listen_ip = None
        self.listen_port = None
        self.set_capture_folder = None

        if has_host:
            self.host = QtWidgets.QLineEdit()
            self.host.setText(settings.value(title + "Host", "192.168.1.100"))
            self.form_layout.addRow("Address", self.host)

        if has_port:
            self.port = QtWidgets.QLineEdit()
            self.port.setText(settings.value(title + "Port", ""))
            self.form_layout.addRow("Port", self.port)

        if has_broadcast:
            self.broadcast = QtWidgets.QCheckBox()
            self.broadcast.setChecked(settings.value(title + "Broadcast") == "True")
            self.form_layout.addRow("Broadcast", self.broadcast)

        if has_listen_ip:
            self.listen_ip = device_util.InterfaceCombo(True)
            self.listen_ip.setCurrentText(settings.value(title + "ListenIp", "--all--"))
            self.form_layout.addRow("Listen Ip", self.listen_ip)

        if has_listen_port:
            self.listen_port = QtWidgets.QLineEdit()
            self.listen_port.setText(settings.value(title + "ListenPort", ""))
            self.form_layout.addRow("Listen Port", self.listen_port)

        if has_set_capture_folder:
            self.set_capture_folder = QtWidgets.QCheckBox("")
            self.set_capture_folder.setChecked(settings.value(title + "SetCaptureFolder") == "True")
            self.form_layout.addRow("Set Capture Folder", self.set_capture_folder)

        self.setLayout(self.form_layout)

    def populate_from_device(self, device):
        """ populate the gui using data from the provided  device object
        """
        self.name.setText(device.name)
        if self.host is not None:
            self.host.setText(device.host)
        if self.port is not None:
            self.port.setText(str(device.port))
        if self.broadcast is not None:
            self.broadcast.setChecked(bool(device.broadcast))
        if self.listen_ip is not None:
            self.listen_ip.setCurrentText(device.listen_ip)
        if self.listen_port is not None:
            self.listen_port.setText(str(device.listen_port))
        if self.set_capture_folder is not None:
            self.set_capture_folder.setChecked(device.set_capture_folder is True)

    def update_device(self, device, data=None):

        """ Set the device properties from values in the ui
            device is the object to modify, by calling reconfigure
            data has any kwargs for reconfigure to be passed on
         """

        name = self.name.text()

        if data is None:
            data = {}

        if self.host is not None:
            data['host'] = self.host.text()

        if self.port is not None:
            try:
                data['port'] = int(self.port.text())
            except ValueError as e:
                QtWidgets.QMessageBox.warning(self, "Error", "Invalid port")
                return False

        if self.broadcast is not None:
            data['broadcast'] = self.broadcast.isChecked()

        if self.listen_ip is not None:
            data['listen_ip'] = self.listen_ip.ip()

        if self.listen_port is not None:
            try:
                data['listen_port'] = int(self.listen_port.text())
            except ValueError as e:
                QtWidgets.QMessageBox.warning(self, "Error", "Invalid Listen Port")
                return False

        if self.set_capture_folder is not None:
            data['set_capture_folder'] = self.set_capture_folder.isChecked()

        device.reconfigure(name, **data)
        return True

    def do_add(self):
        """ The ui is asking for the device to be added - validate and save the settings
            returns true if the data is valid.   If returning false it's a good idea to pop up
            a message to the user to say what was wrong """
        if not super().do_add():
            return False

        self.settings.setValue(self.title + "Name", self.name.text())
        if self.host is not None:
            self.settings.setValue(self.title + "Host", self.host.text())
        if self.port is not None:
            self.settings.setValue(self.title + "Port", self.port.text())
        if self.broadcast is not None:
            self.settings.setValue(self.title + "Broadcast", str(self.broadcast.isChecked()))
        if self.listen_ip is not None:
            self.settings.setValue(self.title + "ListenIp", self.listen_ip.currentText())
        if self.listen_port is not None:
            self.settings.setValue(self.title + "ListenPort", self.listen_port.text())
        if self.set_capture_folder is not None:
            self.settings.setValue(self.title + "SetCaptureFolder", self.set_capture_folder.isChecked())

        return True


class PeelDeviceBase(QtCore.QObject):

    """ Base class for all devices """

    def __init__(self, name, parent=None):
        super(PeelDeviceBase, self).__init__(parent)
        self.name = name
        self.device_id = None
        self.plugin_id = -1
        self.enabled = True

    def __str__(self):
        return self.name

    def set_enabled(self, value):
        self.enabled = value

    @staticmethod
    def device():
        """ returns the string name for this device type """
        raise NotImplementedError

    def as_dict(self):
        """ Returns the constructor fields and values for this instance.  Used to
            recreate the instance between application sessions """
        raise NotImplementedError

    def reconfigure(self, name, **kwargs):
        """ Called by the SimpleDevice dialog to set the device settings.  Does not
            need to be overridden if a different dialog is being used.
            The kwargs need to match the parameters specified in SimpleDeviceWidget
            constructor, ie if has_host is True, kwargs will have a "host" parameter.

             """
        raise NotImplementedError

    def teardown(self):
        """ Called when the app is shutting down - tell all threads to stop and return """
        raise NotImplementedError

    def thread_join(self):
        """ Called when the app is shutting down - block till threads are stopped """
        raise NotImplementedError

    def command(self, command, argument):
        """ Command, Argument may be:
           record, {takename}
           play, {takename} or "" for last recorded
           stop, ""
           transport, stop | next | prev
           notes, {note}
           description, {description}
           timecode, {timecode}    - called when recording starts
           takeNumber, {nnn} - updates the current take number before recording starts
        """
        raise NotImplementedError

    def get_state(self):
        """ devices should return "OFFLINE", "ONLINE", "RECORDING", "PLAYING" or "ERROR" """
        raise NotImplementedError

    def get_info(self):
        """ Return the text to put in the main ui next to the device name """
        return ""

    def device_ref(self, state=None, info=None):
        """ Create a PeelApp.Device() object that contains the information needed
            to update the main ui.  The Device() object is implemented in c++ to
            make it easier to pass around inside the main app.

            This function does not need to be overridden for subclasses, the default
            should be okay for most uses.

            See the note in update_state() about populating state and info values when
            calling this from get_state() or get_info()
        """

        if state is None:
            state = self.get_state()
        if info is None:
            info = self.get_info()

        device = PeelApp.cmd.newDevice()  # CPP class from parent app
        device.deviceId = self.device_id
        device.pluginId = self.plugin_id
        device.name = self.name
        device.status = state
        device.info = info
        device.enabled = self.enabled

        # Get the list of files the device says it has recorded.  This data is used in the
        # take table of the main ui to show how many files are recorded for each take.
        try:
            device.takes = self.list_takes()
        except NotImplementedError:
            device.takes = []

        # print(device.name, device.status)
        return device

    def update_state(self, state=None, info=None):
        """ Call this to push a status update to the main app.

            Note that device_ref() may call get_state() and get_info() for the device,
            so it's important that any calls to this function inside of get_state() or
            get_info() populate state and info fields to avoid a loop/lockup.

            This function is usually called in response to a device thread or socket
            changing state or having new info to update in the ui to avoid the need for
            polling devices.
        """
        if self.device_id is None:
            # print("No device id")
            return
        cmd.writeLog(f"State: {self.name} {state} {info}\n")
        cmd.updateDevice(self.device_ref(state, info))

    @staticmethod
    def dialog(settings):
        """ Static method to create the UI for this device.  It should return
            an blank instance of this device type.
        """
        raise NotImplementedError

    @staticmethod
    def dialog_callback(widget):
        """ Static method to populate the device from the creation widget """
        raise NotImplementedError

    def edit(self, settings):
        """ Create the UI to edit this device.  It should return an populated
            instance of this device object.
        """
        raise NotImplementedError

    def has_harvest(self):
        """ Return True if the device supports the ability to download files from
            the device to local storage
        """
        return False

    def harvest(self, directory):
        """ Download the takes to the local storage directory
        """
        raise NotImplementedError

    def list_takes(self):
        """ list the take files currently on the device
        """
        raise NotImplementedError

    def data_directory(self):
        return cmd.getDataDirectory() + "/" + self.name


class DeviceCollection(QtCore.QObject):
    def __init__(self, parent=None):
        super(DeviceCollection, self).__init__(parent)
        self.devices = []
        self.current_id = 0

    @staticmethod
    def all_classes():
        for device_module in pkgutil.iter_modules([os.path.split(__file__)[0]]):
            dm = importlib.import_module("peel_devices." + device_module.name)
            for name, klass in inspect.getmembers(dm, inspect.isclass):
                if issubclass(klass, PeelDeviceBase):
                    try:
                        klass.device()
                    except NotImplementedError:
                        continue
                    yield klass

        # Search for valid classes in peel_user_devices module, if it exists
        try:
            dm = importlib.import_module("peel_user_devices")
            for i in pkgutil.iter_modules(dm.__path__):
                klass = importlib.import_module("peel_user_devices." + i.name)
                for name, klass in inspect.getmembers(klass, inspect.isclass):
                    if issubclass(klass, PeelDeviceBase):
                        try:
                            klass.device()
                        except NotImplementedError:
                            continue
                        yield klass

        except ModuleNotFoundError:
            pass

    def add_device(self, device):

        print("Adding Device")

        if not isinstance(device, PeelDeviceBase):
            raise ValueError("Not a device while adding: " + str(device))

        device.device_id = self.current_id
        self.current_id += 1
        self.devices.append(device)

        print("Added device: %s (%s)" % (device.name, device.device()))

    def remove_all(self):
        for d in self.devices:
            d.teardown()
        self.devices = []

    def remove(self, device_id):
        for d in self.devices:
            if d.device_id == device_id:
                d.teardown()
                self.devices.remove(d)
                break

    def update_all(self):
        cmd.setDevices([i.device_ref() for i in self.devices])

    def teardown(self):
        for d in self.devices:
            try:
                d.teardown()
            except NotImplementedError as e:
                print("Incomplete device  (teardown): " + d.name)

    def get_data(self):
        data = []
        for d in self.devices:
            try:
                data.append((d.device(), d.as_dict()))
            except NotImplementedError as e:
                print("Incomplete device (as_dict): " + d.name)

        return data

    def unique_name(self, device_name):
        name = device_name
        i = 1
        while name in [i.name for i in self.devices]:
            name = device_name + str(i)
            i += 1
        return name

    def from_id(self, id):
        for d in self.devices:
            if d.device_id == id:
                return d

    def __len__(self):
        return len(self.devices)

    def __getitem__(self, item):
        return self.devices[item]

    def has_device(self, device_name, name):
        for i in self.devices:
            if i.device() == device_name and i.name == name:
                return True

        return False

    def load_json(self, data, mode):
        if mode == "replace":
            self.remove_all()

        klass = dict([(i.device(), i) for i in self.all_classes()])
        if "devices" in data:
            for name, device_data in data["devices"]:

                if not isinstance(device_data, dict):
                    print("Not a dict while reading device data:" + str(device_data))
                    continue

                if name not in klass:
                    print("Could not find device class for: " + name)
                    continue

                if mode == "merge" and self.has_device(name, device_data["name"]):
                    continue

                try:
                    d = klass[name](**device_data)
                    self.add_device(d)
                except TypeError as e:
                    print("Error recreating class: " + str(name))
                    print(str(e))
                    print(str(device_data))


class TcpDevice(PeelDeviceBase):

    def __init__(self, name=None, host=None, port=None):
        super(TcpDevice, self).__init__(name)
        self.host = host
        self.port = port
        self.tcp = QTcpSocket()
        self.tcp.connected.connect(self.do_connected)
        self.tcp.disconnected.connect(self.do_disconnected)
        self.tcp.readyRead.connect(self.do_read)
        self.tcp.errorOccurred.connect(self.do_error)
        self.current_take = None
        self.error = None
        self.connected_state = None  # ONLINE, OFFLINE, ERROR
        self.device_state = None  # ONLINE, PLAYING, RECORDING
        self.info = None

        self.reconfigure(name=name, host=host, port=port)

    def send(self, msg):
        #if self.connected_state != "CONNECTED":
        #    self.tcp.connectToHost(self.host, self.port)
        self.tcp.write(msg.encode("utf8"))

    def do_read(self):
        raise NotImplementedError

    def do_connected(self):
        self.connected_state = "ONLINE"
        self.update_state(self.connected_state, "")

    def do_disconnected(self):
        self.connected_state = "OFFLINE"
        self.update_state(self.connected_state, "")

    def do_error(self, err):
        self.connected_state = "ERROR"
        if err == QAbstractSocket.ConnectionRefusedError:
            self.update_state(self.connected_state, "Connection Refused")
        elif err == QAbstractSocket.SocketError.RemoteHostClosedError:
            self.update_state(self.connected_state, "Host Closed")
        elif err == QAbstractSocket.SocketError.HostNotFoundError:
            self.update_state(self.connected_state, "Host Not Found")
        elif err == QAbstractSocket.SocketError.SocketAccessError:
            self.update_state(self.connected_state, "Access Error")
        elif err == QAbstractSocket.SocketError.SocketResourceError:
            self.update_state(self.connected_state, "Resource Error")
        elif err == QAbstractSocket.SocketError.SocketTimeoutError:
            self.update_state(self.connected_state, "Timeout")
        elif err == QAbstractSocket.SocketError.DatagramTooLargeError:
            self.update_state(self.connected_state, "Overflow")
        elif err == QAbstractSocket.SocketError.NetworkError:
            self.update_state(self.connected_state, "No Connection")
        elif err == QAbstractSocket.SocketError.AddressInUseError:
            self.update_state(self.connected_state, "Address in use")
        elif err == QAbstractSocket.SocketError.SocketAddressNotAvailableError:
            self.update_state(self.connected_state, "Unavailable")
        elif err == QAbstractSocket.SocketError.UnsupportedSocketOperationError:
            self.update_state(self.connected_state, "Unsupported")
        elif err == QAbstractSocket.SocketError.ProxyAuthenticationRequiredError:
            self.update_state(self.connected_state, "Proxy Required")
        elif err == QAbstractSocket.SocketError.SslHandshakeFailedError:
            self.update_state(self.connected_state, "SSL HS Error")
        elif err == QAbstractSocket.SocketError.UnfinishedSocketOperationError:
            self.update_state(self.connected_state, "Unfinished Error")
        elif err == QAbstractSocket.SocketError.ProxyConnectionRefusedError:
            self.update_state(self.connected_state, "Proxy Refused")
        elif err == QAbstractSocket.SocketError.ProxyConnectionClosedError:
            self.update_state(self.connected_state, "Proxy Closed")
        elif err == QAbstractSocket.SocketError.ProxyConnectionTimeoutError:
            self.update_state(self.connected_state, "Proxy Timeout")
        elif err == QAbstractSocket.SocketError.ProxyNotFoundError:
            self.update_state(self.connected_state, "Proxy Not Found")
        elif err == QAbstractSocket.SocketError.ProxyProtocolError:
            self.update_state(self.connected_state, "Proxy tx Error")
        elif err == QAbstractSocket.SocketError.OperationError:
            self.update_state(self.connected_state, "Op Error")
        elif err == QAbstractSocket.SocketError.SslInternalError:
            self.update_state(self.connected_state, "SSL Error")
        elif err == QAbstractSocket.SocketError.SslInvalidUserDataError:
            self.update_state(self.connected_state, "SSL User Error")
        elif err == QAbstractSocket.SocketError.TemporaryError:
            self.update_state(self.connected_state, "Temp Error")
        elif err == QAbstractSocket.SocketError.UnknownSocketError:
            self.update_state(self.connected_state, "Unknown")
        else:
            self.update_state(self.connected_state, str(err))

    def as_dict(self):
        return {'name': self.name,
                'host': self.host,
                'port': self.port}

    def reconfigure(self, name, host=None, port=None):

        print(f"Reconfigure {host} {port}  {self.host} {self.port}")

        if self.tcp is not None:
            if self.connected_state == "CONNECTED":
                self.tcp.disconnectFromHost()
            self.tcp.close()

        if host is not None:
            self.host = host

        if port is not None:
            self.port = port

        self.current_take = None
        self.error = None
        self.connected_state = None
        self.name = name

        if self.host is not None and self.port is not None:
            print(f"Connecting to {self.host} {self.port}")
            self.tcp.connectToHost(self.host, self.port)

        self.update_state()

    def get_state(self):

        if not self.enabled:
            return "OFFLINE"

        if self.error is not None:
            return "ERROR"

        if self.connected_state in ["OFFLINE", "ERROR"]:
            return self.connected_state

        if self.device_state is None:
            return "OFFLINE"

        return self.device_state

    def get_info(self):
        if self.error is not None:
            return self.error
        return ""

    def teardown(self):
        if self.tcp is not None:
            self.tcp.close()
            self.tcp = None



class FileItem(object):
    def __init__(self, remote_file, local_file):
        self.remote_file = remote_file
        self.local_file = local_file
        self.file_size = None
        self.data_size = None
        self.error = None
        self.complete = False


class DownloadThread(QtCore.QThread):

    tick = QtCore.Signal(float)  # 0.0 - 1.0 progress done
    file_done = QtCore.Signal(str, int, str)  # Name, CopyState, error string
    all_done = QtCore.Signal()
    message = QtCore.Signal(str)

    COPY_FAIL = 0
    COPY_OK = 1
    COPY_SKIP = 2

    STATUS_NONE = 0
    STATUS_RUNNING = 1
    STATUS_STOP = 2
    STATUS_FINISHED = 3

    def __init__(self):
        super(DownloadThread, self).__init__()
        self.status = self.STATUS_NONE
        self.current_file = None

    def __del__(self):
        self.terminate()

    def log(self, message):
        self.message.emit(message)

    def teardown(self):
        cmd.writeLog(f"Teardown {str(self)}\n")
        self.status = self.STATUS_STOP
        self.wait(1000)

    def set_finished(self):
        self.status = self.STATUS_FINISHED
        self.tick.emit(0.0)
        self.all_done.emit()

    def set_started(self):
        self.status = self.STATUS_RUNNING
        self.tick.emit(0.0)

    def set_current(self, value):
        self.current_file = value

    def file_ok(self, name):
        self.file_done.emit(name, self.COPY_OK, None)

    def file_fail(self, name, err):
        self.file_done.emit(name, self.COPY_FAIL, err)
        
    def file_skip(self, name):
        self.file_done.emit(name, self.COPY_SKIP, None)

    def is_running(self):
        return self.status is self.STATUS_RUNNING



