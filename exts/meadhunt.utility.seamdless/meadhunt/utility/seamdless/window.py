import os
import omni.kit.app
import omni.kit.ui
import omni.ui as ui
import omni.usd
import time
from omni.ui import color as cl
from omni.kit.window.filepicker.dialog import FilePickerDialog
from omni.kit.window.filepicker import FilePickerDialog
from omni.kit.widget.filebrowser import FileBrowserItem
from .dalle import api
from PIL import Image, ImageChops

class ExtensionWindow(ui.Window):
    
    # Class Variables
    LABEL_WIDTH = 80
    SPACER_WIDTH = 5
    BUTTON_SIZE = 30
    MLD_COUNT = ui.SimpleIntModel(4,min=1,max=10)
    MLD_IMAGE = ui.SimpleIntModel(1,min=1,max=4)
    CURRENT_DIR = ""
    SIZE_LIST = ['1024x1024','512x512','256x256']

    def __init__(self, title, win_width, win_height, menu_path, ext_id):
        super().__init__(title, width=win_width, height=win_height)
        self._path_menu = menu_path
        self._dalle_api = api(ext_id)
        self._filepicker = None
        self._filepicker_selected_folder = ""
        # self._stage = self.STAGE
        self._path_img_cache = self._dalle_api._get_json(f'{self._dalle_api.ROOT_PATH}/config/seamdless.json','img_cache')
        if self._path_img_cache == "":
            self._path_img_cache = f'{self._dalle_api.ROOT_PATH}/resources'
        self.set_visibility_changed_fn(self._on_visibility_changed)
        self._build_ui()
        self._fld_img_cache.model.set_value(self._path_img_cache)
        self._fld_img_cache.tooltip = self._fld_img_cache.model.as_string
        self._api_key('get',True)
        self._img_list = self._fn_dir_list(self._path_img_cache)
        self.CURRENT_DIR = self._path_img_cache
        self._image.source_url = f'{self._path_img_cache}{self._img_list[0]}'
        self._fn_folder_load()

        # startTime = time.time()
        # temp = self._dalle_api._img_create('top down photo of red bricks, zoom out, create seamless tileable background for a webpage, texture pack, in the style of M.C. Escher Tessellation',10)
        # self._dalle_api._img_output(temp,self._path_img_cache)
        # endTime = time.time()
        # self._lbl_process_time.text = self._fn_process_time(startTime,endTime)

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
        self.CURRENT_DIR = self._path_img_cache
        self._fn_folder_load()
        self.visible = True
        self.focus()

    def hide(self):
        self.visible = False

    def _on_visibility_changed(self, visible:bool):
        if not visible:
            omni.kit.ui.get_editor_menu().set_value(self._path_menu, False)

    def _api_key(self, _type:str='get', _ignore:bool=False):
        _count = ""
        _str = 'sk-'
        _api_str = ""
        if _type == 'get':
            _api_str = self._dalle_api._get_api_key(_ignore)
            if _api_str.find('sk-') != -1:
                self._lbl_api.text = 'API Key Intialized'
                self._cf_api_key.collapsed = True
        if _type == 'set':
            if self._fld_api.model.get_value_as_string().find('*') != -1:
                self._lbl_api.text = 'Invalid API Key'
            else:
                self._dalle_api._set_json(f'{self._dalle_api.ROOT_PATH}/config/api.json','openai',self._fld_api.model.get_value_as_string())
                self._lbl_api.text = 'API Key Intialized'
                self._cf_api_key.collapsed = True
        _api_str = self._dalle_api._get_api_key()
        _count = len(_api_str)
        if _count > 3:
            _str += '*' * (_count-3)
        else:
            _str =""
        self._fld_api.model.set_value(_str)

    def _build_ui(self):
        _style_lbl = {'Label':{'margin':5}}
        # _api_key = self._dalle_api._get_api_key()
        # self._cf_api_key = ui.CollapsableFrame('API & Key')
        with self.frame:
            with ui.HStack():
                with ui.VStack(height=0,style={'margin':3},width=512):
                    self._image = ui.Image(f'{self._dalle_api.ROOT_PATH}/resources/ImagePlaceholder.png', height=512, fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT, style={'border_radius':5})
                    # ui.Spacer(height=6)
                    self._sld_image = ui.IntSlider(self.MLD_IMAGE,min=1,max=10)
                    self._sld_image.model.add_value_changed_fn(lambda a:self._fn_image_preview(a.as_int))
                    # self._sld_count.model.set_value(2)
                    # ui.Spacer(height=6)
                    self._lbl_image_prompt = ui.Label("Image Prompt:\n",word_wrap=True)
                    self._btn_seams = ui.Button('Check Seams', height=24, width=ui.Percent(50),clicked_fn=lambda:self._fn_visualize_seams())
                    
                with ui.VStack(height=0,width=388,style={'margin':3}):
                    self._cf_api_key = ui.CollapsableFrame('API & Key')
                    with self._cf_api_key:
                        with ui.VStack(height=0):
                            self._lbl_api = ui.Label('API Key Not Intialized',style=_style_lbl)
                            self._fld_api = ui.StringField()
                            self._btn_api_Key = ui.Button('Set API Key', clicked_fn=lambda:self._api_key('set'))
                    self._cf_prompt = ui.CollapsableFrame('AI Prompt')
                    with self._cf_prompt:
                        with ui.VStack(height=0):
                            self._lbl_prompt = ui.Label('Enter AI Prompt',style=_style_lbl)
                            self._fld_prompt = ui.StringField()
                            self._lbl_count = ui.Label('Select the number of images to generate',style=_style_lbl)
                            self._sld_count = ui.IntSlider(self.MLD_COUNT,min=1,max=10)
                            self._lbl_size = ui.Label('Select the size of the images to generate',style=_style_lbl)
                            self._cbx_img_size = ui.ComboBox()
                            for item in self.SIZE_LIST:
                                self._cbx_img_size.model.append_child_item(None,ui.SimpleStringModel(item))
                            self._lbl_preview = ui.Label('Select the preview size of the images',style=_style_lbl)
                            self._cbx_preview_size = ui.ComboBox(enabled=False)
                            for item in self.SIZE_LIST:
                                self._cbx_preview_size.model.append_child_item(None,ui.SimpleStringModel(item))
                            self._cbx_preview_size.model.get_item_value_model().set_value(1)
                            self._cbx_preview_size.style = {'background_color':cl('#454545')}
                            self._btn_request = ui.Button('Request AI Image',clicked_fn=lambda:(self._fn_img_request()))
                    self._cf_settings = ui.CollapsableFrame('AI Settings',collapsed=False)
                    with self._cf_settings:
                        with ui.VStack(height=0, width=388):
                            with ui.HStack(style={'Button':{'margin':-5.0},'Label':{'margin':5}}):
                                ui.Label('Image Cache')
                                self._fld_img_cache = ui.StringField(height=self.BUTTON_SIZE,width=260)
                                ui.Button(image_url='resources/icons/folder.png', width=self.BUTTON_SIZE, height=self.BUTTON_SIZE, clicked_fn=lambda:self._on_path_change_clicked(False))
                            ui.Button('Load Generated Image Folder', height=self.BUTTON_SIZE, clicked_fn=lambda:self._on_path_change_clicked(True))
                            ui.Button('Load Prompt from Image Prompt', height=self.BUTTON_SIZE, clicked_fn=lambda:self._fld_prompt.model.set_value(self._fn_folder_prompt()[0]))
                            ui.Button('Delete Generated Images', height=self.BUTTON_SIZE, clicked_fn=lambda:self._on_path_change_clicked(True), enabled=False)
                            ui.Button('Delete Generated Image Folders', height=self.BUTTON_SIZE, clicked_fn=lambda:self._on_path_change_clicked(True), enabled=False)
                    with ui.CollapsableFrame('Statistics',alignment=ui.Alignment.BOTTOM):
                        self._lbl_process_time:ui.Label = ui.Label('Processing Time',style=_style_lbl)

    def _fn_folder_load(self):
        self._img_list=self._fn_dir_list(self.CURRENT_DIR)
        _img_cnt = len(self._img_list)
        if _img_cnt == 0:
            _img_cnt = 1
        self._fn_set_sld_image(_img_cnt)
        self._fn_image_preview(1)
        _prompt,_json_file = self._fn_folder_prompt()
        _prompt_prefix = os.path.basename(os.path.dirname(self.CURRENT_DIR))
        if os.path.exists(_json_file):
            _prompt_msg = f'{_prompt_prefix}\n{_prompt}'
        else:
            _prompt_msg = f'{_prompt_prefix}\nPrompt not found.'
        self._lbl_image_prompt.text = _prompt_msg

    def _fn_folder_prompt(self):
        _split = os.path.dirname(self.CURRENT_DIR).split('/')
        _target = _split[len(_split)-1]
        _json_file = f'{self.CURRENT_DIR}{_target}.json'
        _prompt = self._dalle_api._get_json(f'{_json_file}','prompt')
        return [_prompt,_json_file]

    def _fn_image_preview(self,_val:int=1):
        _img_path = f'{self.CURRENT_DIR}/{self._img_list[_val-1]}'
        if not os.path.exists(_img_path):
            _img_path = f'{self._dalle_api.ROOT_PATH}/resources/ImagePlaceholder_040.png'
        self._image.source_url = _img_path
   
    def _fn_dir_list(self, _dirname:str="")->list:
        if os.path.exists(_dirname):
            _imgs = [_img for _img in os.listdir(_dirname) if _img.endswith('.png') and not _img.endswith('_seams.png')]
        if _imgs == None or len(_imgs) == 0:
            _imgs.append('ImagePlaceholder_040.png')
        return _imgs
 
    def _fn_process_time(self,_start=0,_end=0)->str:
        _calc_time = _end-_start
        return f'Processing Time: {"%.2f" % _calc_time} seconds'

    def _fn_set_sld_image(self,_val:int=1):
        if _val > 0:
            self._sld_image.model.set_value(1)
            self._sld_image.max = _val
            self.MLD_IMAGE.set_max(_val)
    
    def _fn_img_request(self):
        _cbx_item = self._cbx_img_size.model.get_item_value_model().as_int
        startTime = time.time()
        _img_response = self._dalle_api._img_create(self._fld_prompt.model.as_string,self._sld_count.model.as_int,self.SIZE_LIST[_cbx_item])
        _target_dir = self._dalle_api._img_output(_img_response,self._path_img_cache)
        self._dalle_api._set_json(f'{_target_dir}{_img_response["created"]}.json','prompt',self._fld_prompt.model.as_string)
        endTime = time.time()
        self._lbl_process_time.text = self._fn_process_time(startTime,endTime)
        self.CURRENT_DIR = _target_dir
        self._fn_folder_load()
    
    def _fn_visualize_seams(self):
        if self._image.source_url.endswith('_seams.png'):
            _img_out = f'{(os.path.dirname(self._image.source_url))}/{(os.path.basename(self._image.source_url)).split("_")[0]}.png'
        else:
            _img_out = f'{(os.path.dirname(self._image.source_url))}/{(os.path.basename(self._image.source_url)).split(".")[0]}_seams.png'
        if not os.path.exists(_img_out):
            _img = Image.open(self._image.source_url)
            if _img:
                _img_half = int(_img.size[0]/2)
                _img_offset = ImageChops.offset(_img,_img_half)
                _out_file = open(_img_out, 'wb')
                _img_offset.save(_img_out)
                _out_file.flush()
                os.fsync(_out_file)
                _out_file.close()
        if os.path.exists(_img_out):
            try:
                self._image.source_url = _img_out
            except:
                None
        
    def _on_path_change_clicked(self,_load:bool=False):
        if self._filepicker is None:
            self._filepicker = FilePickerDialog(
                'Select Folder',
                show_only_collections='my-computer',
                apply_button_label='Select',
                item_filter_fn=lambda item:self._on_filepicker_filter_item(item),
                selection_changed_fn=lambda items:self._on_filepicker_selection_change(items),
                click_apply_handler=lambda filename, dirname:self._on_dir_pick(self._filepicker, filename, dirname, _load),
            )
        self._filepicker.set_filebar_label_name('Folder Name:')
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

    def _on_dir_pick(self, dialog:FilePickerDialog, filename:str, dirname:str, _load_dir:bool=False):
        dialog.hide()
        self._img_list = self._fn_dir_list(self._filepicker_selected_folder)
        if _load_dir:
            self.CURRENT_DIR = dirname
            self._fn_folder_load()
        else:
            self._fld_img_cache.model.set_value(self._filepicker_selected_folder)
            self._fld_img_cache.tooltip = self._fld_img_cache.model.as_string
            self._dalle_api._set_json(f'{self._dalle_api.ROOT_PATH}/config/seamdless.json','img_cache',f'{dirname}')
