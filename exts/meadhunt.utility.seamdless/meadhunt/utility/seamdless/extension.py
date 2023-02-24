__all__ = ['SeaMDLess']
import carb
import omni.ext
import omni.ui as ui
import omni.kit.ui
import omni.kit.app

from .window import ExtensionWindow

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class SeaMDLess(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.

    WINDOW_TITLE = 'SeaMDLess'
    WINDOW_SIZE = [936,706]
    def on_startup(self, ext_id):
        self._ext_id = ext_id        
        carb.log_info(f'[meadhunt.utility.seamdless] {self._get_extension_info("package","title")} startup')
        self._menu_path = f'Window/Mead & Hunt/{self.WINDOW_TITLE}'
        self._window = None
        self._menu = omni.kit.ui.get_editor_menu().add_item(self._menu_path, self._on_menu_click, True)
        omni.kit.ui.get_editor_menu().set_value(self._menu_path, False)

    def on_shutdown(self):
        carb.log_info(f'[meadhunt.utility.seamdless] {self._get_extension_info("package","title")} shutdown')
        if self._window:
            self._window.hide()
            self._window.destroy()
            self._window = None
        omni.kit.ui.get_editor_menu().remove_item(self._menu)

    def _get_extension_info(self, key:str = 'package', value:str = None):
        '''Handles getting version info from the extension.toml'''
        _data = omni.kit.app.get_app().get_extension_manager().get_extension_dict(self._ext_id)
        if value is None:
            return ''
        else:
            return _data[f'{key}/{value}']

    def _on_menu_click(self, menu, toggled):
        '''Handles showing and hiding the window from the 'Windows' menu.'''
        if toggled:
            if self._window is None:
                _version = self._get_extension_info('package','version')
                self._window = ExtensionWindow(f'{self.WINDOW_TITLE} v{_version}', self.WINDOW_SIZE[0], self.WINDOW_SIZE[1], menu, self._ext_id)
            else:
                self._window.show()
        else:
            if self._window:
                self._window.hide()
                self._window.destroy()
                self._window = None

    def destroy(self):
        if self._window:
            self._window.hide()
            self._window = None