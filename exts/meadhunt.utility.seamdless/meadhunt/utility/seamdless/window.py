import os
import omni.kit.app
import omni.kit.ui
import omni.ui as ui
import omni.usd
from omni.ui import color as cl
from omni.kit.window.filepicker.dialog import FilePickerDialog
from omni.kit.window.filepicker import FilePickerDialog
from omni.kit.widget.filebrowser import FileBrowserItem
from .dalle import api

class ExtensionWindow(ui.Window):
    
    # Class Variables
    LABEL_WIDTH = 80
    SPACER_WIDTH = 5
    BUTTON_SIZE = 24
    MLD_COUNT = ui.SimpleIntModel(4,min=1,max=10)
    MLD_IMAGE = ui.SimpleIntModel(1,min=1,max=MLD_COUNT.as_int)

    def __init__(self, title, win_width, win_height, menu_path, ext_id):
        super().__init__(title, width=win_width, height=win_height)
        self._path_menu = menu_path
        self._dalle_api = api(ext_id)
        self._filepicker = None
        self._filepicker_selected_folder = ""
        # self._stage = self.STAGE
        self._path_img_cache = self._dalle_api._get_json(f"{self._dalle_api.ROOT_PATH}/config/seamdless.json","img_cache")
        if self._path_img_cache == "":
            self._path_img_cache = f"{self._dalle_api.ROOT_PATH}/resources"
        self.set_visibility_changed_fn(self._on_visibility_changed)
        self._build_ui()
        self._fld_img_cache.model.set_value(self._path_img_cache)
        self._api_key("get",True)
        self._img_list = self._dir_list(self._path_img_cache)
        self._image.source_url = f"{self._path_img_cache}/{self._img_list[0]}"
        self._fn_image_count(len(self._img_list))

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
            omni.kit.ui.get_editor_menu().set_value(self._path_menu, False)

    def _api_key(self, _type:str="get", _ignore:bool=False):
        _count = ""
        _str = "sk-"
        _api_str = ""
        if _type == "get":
            _api_str = self._dalle_api._get_api_key(_ignore)
            if _api_str.find("sk-") != -1:
                self._lbl_api.text = "API Key Intialized"
                self._cf_api_key.collapsed = True
        if _type == "set":
            if self._fld_api.model.get_value_as_string().find("*") != -1:
                self._lbl_api.text = "Invalid API Key"
            else:
                self._dalle_api._set_json(f"{self._dalle_api.ROOT_PATH}/config/api.json","openai",self._fld_api.model.get_value_as_string())
                self._lbl_api.text = "API Key Intialized"
                self._cf_api_key.collapsed = True
        _api_str = self._dalle_api._get_api_key()
        _count = len(_api_str)
        if _count > 3:
            _str += "*" * (_count-3)
        else:
            _str =""
        self._fld_api.model.set_value(_str)

    def _build_ui(self):
        _style_lbl = {"Label":{"margin":5}}
        # _api_key = self._dalle_api._get_api_key()
        # self._cf_api_key = ui.CollapsableFrame("API & Key")
        with self.frame:
            with ui.HStack():
                with ui.VStack(height=0):
                    self._image = ui.Image(f'{self._dalle_api.ROOT_PATH}/resources/ImagePlaceholder.png',height=512,width=512,fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT,style={'border_radius':5})
                    ui.Spacer(height=6)
                    self._sld_image = ui.IntSlider(self.MLD_IMAGE,max=self.MLD_COUNT.as_int,width=512)
                    self._sld_image.model.add_value_changed_fn(lambda a:self._fn_image_preview(a.as_int))
                    # self._sld_count.model.set_value(2)
                    ui.Spacer(height=6)
                    with ui.HStack(width=516):
                        ui.Button("Review Image")
                with ui.VStack(height=0,width=388):
                    self._cf_api_key = ui.CollapsableFrame("API & Key")
                    with self._cf_api_key:
                        with ui.VStack(height=0):
                            self._lbl_api = ui.Label("API Key Not Intialized",style=_style_lbl)
                            with ui.HStack():
                                ui.Spacer(width=3)
                                self._fld_api = ui.StringField()
                                ui.Spacer(width=3)
                            ui.Spacer(height=3)
                            self._btn_api_Key = ui.Button("Set API Key", clicked_fn=lambda:self._api_key("set"))
                    self._cf_prompt = ui.CollapsableFrame("AI Prompt")
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
                                self._sld_count = ui.IntSlider(self.MLD_COUNT,min=1,max=10)
                                self._sld_count.model.add_value_changed_fn(lambda a:self._fn_image_count(a.as_int))
                                ui.Spacer(width=3)
                            self._lbl_size = ui.Label("Select the size of the images to generate",style=_style_lbl)
                            with ui.HStack():
                                ui.Spacer(width=3)
                                self._cbx_img_size = ui.ComboBox()
                                for item in ["1024x1024","512x512","256x256"]:
                                    self._cbx_img_size.model.append_child_item(None,ui.SimpleStringModel(item))
                                ui.Spacer(width=3)
                            self._lbl_preview = ui.Label("Select the preview size of the images",style=_style_lbl)
                            with ui.HStack():
                                ui.Spacer(width=3)
                                self._cbx_preview_size = ui.ComboBox(enabled=False)
                                for item in ["1024x1024","512x512","256x256"]:
                                    self._cbx_preview_size.model.append_child_item(None,ui.SimpleStringModel(item))
                                self._cbx_preview_size.model.get_item_value_model().set_value(1)
                                self._cbx_preview_size.style = {"background_color":cl("#454545")}
                                ui.Spacer(width=3)
                            ui.Spacer(height=3)
                            self._btn_request = ui.Button("Request AI Image")
                    self._cf_settings = ui.CollapsableFrame("AI Settings",collapsed=False)
                    with self._cf_settings:
                        with ui.VStack(height=0):
                            with ui.HStack(style={'Button':{'margin':0.0}}):
                                ui.Spacer(width=5.0)
                                ui.Label("Image Cache")
                                ui.Spacer(width=5.0)
                                self._fld_img_cache = ui.StringField(height=self.BUTTON_SIZE,width=260)
                                ui.Spacer(width=5.0)
                                ui.Button(image_url='resources/icons/folder.png', width=self.BUTTON_SIZE, height=self.BUTTON_SIZE, clicked_fn=lambda:self._on_path_change_clicked())

    def _fn_image_count(self,_val:int=1):
        if _val > self._sld_image.max or _val > len(self._img_list):
            _cnt = len(self._img_list)
            while _cnt < _val:
                self._img_list.append("ImagePlaceholder_040.png")
                _cnt += 1
        if _val < self._sld_image.model.as_int:
            self._sld_image.model.set_value(_val)
        self.MLD_IMAGE.max = self._sld_image.max = _val
        self._sld_image.min = 1
        self._fn_image_preview(self._sld_image.model.as_int)

    def _fn_image_preview(self,_val:int=1):
        _img_path = f"{self._path_img_cache}/{self._img_list[_val-1]}"
        if not os.path.exists(_img_path):
            _img_path = f"{self._dalle_api.ROOT_PATH}/resources/ImagePlaceholder_040.png"
        self._image.source_url = _img_path

    def _on_path_change_clicked(self):
        if self._filepicker is None:
            self._filepicker = FilePickerDialog(
                "Select Folder",
                show_only_collections="my-computer",
                apply_button_label="Select",
                item_filter_fn=lambda item:self._on_filepicker_filter_item(item),
                selection_changed_fn=lambda items:self._on_filepicker_selection_change(items),
                click_apply_handler=lambda filename, dirname:self._on_dir_pick(self._filepicker, filename, dirname),
            )
        self._filepicker.set_filebar_label_name("Folder Name:")
        self._filepicker.refresh_current_directory()
        self._filepicker.show(self._fld_img_cache.model.get_value_as_string())

    def _on_filepicker_filter_item(self, item:FileBrowserItem)->bool:
        if not item or item.is_folder:
            return True
        return False

    def _on_filepicker_selection_change(self, items:list=[FileBrowserItem]):
        last_item:FileBrowserItem = items[-1]
        self._filepicker.set_filename(last_item.name)
        self._filepicker_selected_folder = last_item.path

    def _on_dir_pick(self, dialog:FilePickerDialog, filename:str, dirname:str):
        dialog.hide()
        self._fld_img_cache.model.set_value(self._filepicker_selected_folder)
        self._img_list = self._dir_list(self._filepicker_selected_folder)
        if len(self._img_list) > self._sld_count.model.as_int:
            _cnt = len(self._img_list)
        else:
            _cnt = self._sld_count.model.as_int
        self._fn_image_count(_cnt)
        self._dalle_api._set_json(f"{self._dalle_api.ROOT_PATH}/config/seamdless.json","img_cache",f"{dirname}")

    def _dir_list(self, _dirname:str)->list:
        _imgs = [_img for _img in os.listdir(_dirname) if _img.endswith(".png")]
        if len(_imgs) == 0:
            _imgs.append("ImagePlaceholder_040.png")
        return _imgs
 