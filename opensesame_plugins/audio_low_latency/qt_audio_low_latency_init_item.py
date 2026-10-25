"""
This file is part of OpenSesame.

OpenSesame is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenSesame is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenSesame.  If not, see <http://www.gnu.org/licenses/>.
"""

__author__ = "Bob Rosbag"
__license__ = "GPLv3"

from libqtopensesame.items.qtautoplugin import QtAutoPlugin

from .audio_low_latency_item import ALL_HOST_APIS, PYALSAAUDIO, SOUNDDEVICE, WASAPI


class QtAudioLowLatencyInitItem(QtAutoPlugin):
    """GUI of the init items: the host API list follows the chosen module
    (SoundDevice and PyAudio), the device list follows the module and the
    host API, the module, host API and device are disabled in dummy mode,
    the number of periods is only enabled for PyAlsaAudio and WASAPI
    exclusive mode only for SoundDevice with host API WASAPI.
    """

    def init_edit_widget(self):
        super().init_edit_widget()
        module_list = self._get('module_list')
        if not module_list:
            return

        if self.var.module in module_list:
            self.current_module = self.var.module
        else:
            self.current_module = module_list[0]
            self.var.module = self.current_module
        if self.var.host_api not in self._host_api_list(self.current_module):
            self.var.host_api = ALL_HOST_APIS

        self.combobox_module.clear()
        self.combobox_module.addItems(module_list)
        self.combobox_module.setCurrentIndex(module_list.index(self.current_module))
        self._fill_host_apis()
        self._fill_devices()

    def _host_api_list(self, module):
        return [ALL_HOST_APIS] + self._get('host_api_dict').get(module, [])

    def _device_list(self, module, host_api):
        device_list = self._get('device_dict')[module]
        if host_api == ALL_HOST_APIS:
            return device_list
        host_apis = self._get('device_host_api_dict')[module]
        return [name for name, device_host_api in zip(device_list, host_apis) if device_host_api == host_api]

    def _fill_host_apis(self):
        """Shows the host APIs of the current module, with var.host_api
        selected.
        """
        host_api_list = self._host_api_list(self.current_module)
        self.combobox_host_api.clear()
        self.combobox_host_api.addItems(host_api_list)
        self.combobox_host_api.setCurrentIndex(host_api_list.index(self.var.host_api))
        self.current_host_api = self.var.host_api

    def _fill_devices(self):
        """Shows the devices of the current module and host API, with
        var.device_name selected, or else the first one.
        """
        device_list = self._device_list(self.current_module, self.current_host_api)
        if self.var.device_name not in device_list:
            self.var.device_name = device_list[0]
        self.combobox_device_name.clear()
        self.combobox_device_name.addItems(device_list)
        self.combobox_device_name.setCurrentIndex(device_list.index(self.var.device_name))
        self.current_device_name = self.var.device_name

    def apply_edit_changes(self):
        if not QtAutoPlugin.apply_edit_changes(self) or self.lock:
            return False
        self.custom_interactions()
        return True

    def edit_widget(self):
        if self.lock:
            return
        self.lock = True
        w = QtAutoPlugin.edit_widget(self)
        self.custom_interactions()
        self.lock = False
        return w

    def custom_interactions(self):
        if not hasattr(self, 'current_module'):
            # No modules with devices
            return
        if self.current_module != self.var.module:
            device_selected_dict = self._get('device_selected_dict')
            device_selected_dict[self.current_module] = self.var.device_name
            self.current_module = self.var.module
            if self.var.host_api not in self._host_api_list(self.current_module):
                self.var.host_api = ALL_HOST_APIS
            self._fill_host_apis()
            self.var.device_name = device_selected_dict[self.current_module]
            self._fill_devices()
        elif self.current_host_api != self.var.host_api:
            self.current_host_api = self.var.host_api
            self._fill_devices()

        if self.var.dummy_mode == 'yes':
            self.combobox_module.setDisabled(True)
            self.combobox_host_api.setDisabled(True)
            self.combobox_device_name.setDisabled(True)
        elif self.var.dummy_mode == 'no':
            self.combobox_module.setEnabled(True)
            self.combobox_host_api.setEnabled(self.current_module != PYALSAAUDIO)
            self.combobox_device_name.setEnabled(True)

        self.line_edit_periods.setEnabled(self.current_module == PYALSAAUDIO)
        self.checkbox_wasapi_exclusive.setEnabled(self.current_module == SOUNDDEVICE and self.current_host_api == WASAPI)
