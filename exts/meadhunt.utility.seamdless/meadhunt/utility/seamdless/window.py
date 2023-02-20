import omni.kit.app
import omni.kit.ui
import omni.ui as ui
import omni.usd
from omni.ui import color as cl
from omni.kit.window.filepicker.dialog import FilePickerDialog

from .dalle import api

class ExtensionWindow(ui.Window):
    
    # Class Variables
    LABEL_WIDTH = 80
    SPACER_WIDTH = 5
    BUTTON_SIZE = 24
    SLD_COUNT = ui.IntSlider(min=1,max=10)

    def __init__(self, title, win_width, win_height, menu_path, ext_id):
        super().__init__(title, width=win_width, height=win_height)
        self._menu_path = menu_path
        self._dalle_api = api(ext_id)
        # self._stage = self.STAGE
        self._root_path = omni.kit.app.get_app().get_extension_manager().get_extension_path(ext_id)
        self.set_visibility_changed_fn(self._on_visibility_changed)
        self.SLD_COUNT.model.set_value(4)
        print(self.SLD_COUNT.model.get_value_as_string())
        self._build_ui()
        print(self.SLD_COUNT.model.get_value_as_string())
        self._api_key("get")

    def on_shutdown(self):
        if self:
            self.hide()
            self.destroy()
            self = None

    def on_startup(self):
        self

    def destroy(self):
        if self:
            self = None

    def show(self):
        self.visible = True
        self.focus()

    def hide(self):
        self.visible = False

    def _on_visibility_changed(self, visible:bool):
        if not visible:
            omni.kit.ui.get_editor_menu().set_value(self._menu_path, False)

    def _api_key(self, _type:str="get"):
        _count = ""
        _str = "sk-"
        _api_str = self._dalle_api._get_api_key()
        if _type == "get":
            if _api_str.find("sk-") != -1:
                self._lbl_api.text = "API Key Intialized"
                self._cf_api_key.collapsed = True
        if _type == "set":
            if self._fld_api.model.get_value_as_string().find("*") != -1:
                self._lbl_api.text = "Invalid API Key"
            else:
                self._dalle_api._set_api_key(self._fld_api.model.get_value_as_string())
                self._lbl_api.text = "API Key Intialized"
                self._cf_api_key.collapsed = True
        _count = len(_api_str)

        _str += "*" * (_count-3)
        self._fld_api.model.set_value(_str)

    def _build_ui(self):
        _style_lbl = {"Label":{"margin":5}}
        # _api_key = self._dalle_api._get_api_key()
        # self._cf_api_key = ui.CollapsableFrame("API & Key")
        with self.frame:
            with ui.HStack():
                with ui.VStack(height=0):
                    with ui.ScrollingFrame(height=536,horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF):
                        with ui.HGrid(column_width=536,row_count=1):
                            for i in range(self.SLD_COUNT.model.get_value_as_int()):
                                self._image = ui.Image(f'{self._root_path}/resources/ImagePlaceholder.png',height=512,alignment=ui.Alignment.CENTER,fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT,style={'border_radius':5})
                with ui.VStack(height=0,width=388):
                    self._cf_api_key = ui.CollapsableFrame("API & Key")
                    self._cf_prompt = ui.CollapsableFrame("AI Prompt Settings")                    
                    with self._cf_api_key:
                        with ui.VStack(height=0):
                            self._lbl_api = ui.Label("API Key Not Intialized",style=_style_lbl)
                            with ui.HStack():
                                ui.Spacer(width=3)
                                self._fld_api = ui.StringField()
                                ui.Spacer(width=3)
                            ui.Spacer(height=3)
                            self._btn_api_Key = ui.Button("Set API Key", clicked_fn=lambda: self._api_key("set"))
                    with self._cf_prompt:
                        with ui.VStack(height=0):
                            self._lbl_prompt = ui.Label("Enter AI Prompt",style=_style_lbl)
                            with ui.HStack():
                                ui.Spacer(width=3)
                                self._fld_prompt = ui.StringField()
                                ui.Spacer(width=3)
                            self._lbl_count = ui.Label("Select the number of images to generate",style=_style_lbl)
                            with ui.HStack():
                                ui.Spacer(width=3)
                                self.SLD_COUNT = ui.IntSlider(min=1,max=10)
                                self.SLD_COUNT.model.set_value(4)
                                ui.Spacer(width=3)
                            self._lbl_size = ui.Label("Select the size of the images to generate",style=_style_lbl)
                            with ui.HStack():
                                ui.Spacer(width=3)
                                self._cbx_size = ui.ComboBox()
                                for item in ["1024x1024","512x512","256x256"]:
                                    self._cbx_size.model.append_child_item(None,ui.SimpleStringModel(item))
                                ui.Spacer(width=3)
                            self._lbl_preview = ui.Label("Select the preview size of the images",style=_style_lbl)
                            with ui.HStack():
                                ui.Spacer(width=3)
                                self._cbx_preview = ui.ComboBox(enabled=False)
                                for item in ["1024x1024","512x512","256x256"]:
                                    self._cbx_preview.model.append_child_item(None,ui.SimpleStringModel(item))
                                self._cbx_preview.model.get_item_value_model().set_value(1)
                                self._cbx_preview.style = {"background_color":cl("#454545")}
                                ui.Spacer(width=3)
                            ui.Spacer(height=3)
                            self._btn_request = ui.Button("Request AI Image")
                                