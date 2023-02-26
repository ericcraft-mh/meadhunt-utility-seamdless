import os
import time
import shutil
import numpy as np

import omni.kit.app
import omni.kit.ui
import omni.ui as ui
import omni.usd

from omni.ui import color as cl
from omni.kit.window.filepicker.dialog import FilePickerDialog
from omni.kit.window.filepicker import FilePickerDialog
from omni.kit.widget.filebrowser import FileBrowserItem
from .dalle import api
from PIL import Image, ImageChops
from pathlib import Path

class ExtensionWindow(ui.Window):
    
    # Class Variables
    LABEL_WIDTH = 80
    SPACER_WIDTH = 5
    STATS_WIDTH = 190
    BUTTON_SIZE = 30
    MLD_COUNT = ui.SimpleIntModel(4,min=1,max=10)
    MLD_IMAGE = ui.SimpleIntModel(1,min=1,max=4)
    CURRENT_DIR = ""
    SIZE_LIST = ['1024x1024','512x512','256x256']
    MASK_LIST = ['Center: Small','Center: Large','Cross: Small','Cross: Large']
    MASK_IMG = []
    TILE_LIST = ['Tile: 1x1','Tile: 2x2','Tile: 3x3','Tile: 4x4','Tile: 5x5']
    IMG_LIST = []
    IMG_PLACEHOLDER = []

    def __init__(self, title:str=None, ext_id:str=None, menu_path:str=None, **kwargs):
        super().__init__(title, **kwargs)
        self._path_menu = menu_path
        self._dalle_api = api(ext_id)
        self._filepicker = None
        self._filepicker_selected_folder = ""
        self._path_img_cache = self._dalle_api._get_json(f'{self._dalle_api.ROOT_PATH}/config/seamdless.json','img_cache')
        self._rsc_path = f'{self._dalle_api.ROOT_PATH}/resources'
        if self._path_img_cache == "":
            self._path_img_cache = self._rsc_path
        self._fn_img_placeholder()
        self.CURRENT_DIR = self._path_img_cache
        self.set_visibility_changed_fn(self._on_visibility_changed)
        self._provider = ui.ByteImageProvider()
        self._provider.set_data_array(self.IMG_PLACEHOLDER[0][0],self.IMG_PLACEHOLDER[0][1])
        self._build_ui()
        self._fld_img_cache.model.set_value(self._path_img_cache)
        self._fld_img_cache.tooltip = self._fld_img_cache.model.as_string
        self._cbx_img_size.model.get_item_value_model().set_value(1)
        self._api_key('get',True)
        self.IMG_LIST = []
        self._load_dir = False
        self._fn_img_list()
        self._fn_folder_load()
        self._fn_folder_stats()

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
        _cnt = None
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
        _cnt = len(_api_str)
        if _cnt > 3:
            _str += '*' * (_cnt-3)
        else:
            _str =""
        self._fld_api.model.set_value(_str)

    def _build_ui(self):
        _style_lbl = {'Label':{'margin':5}}
        with self.frame:
            with ui.HStack():
                with ui.VStack(height=0,style={'margin':3},width=512):
                    self._image = ui.ImageWithProvider(self._provider, width=512, height=512, style={'border_radius':5})
                    self._sld_image = ui.IntSlider(self.MLD_IMAGE,min=1,max=10)
                    self._sld_image.model.add_value_changed_fn(lambda a:self._fn_image_preview(a.as_int))
                    self._lbl_image_dir = ui.Label('Image Prompt',word_wrap=True)
                    self._lbl_image_prompt = ui.Label('',word_wrap=True)
                    with ui.HStack():
                        self._btn_seams = ui.Button('Check Seams', height=24, width=ui.Percent(35),clicked_fn=lambda:self._fn_toggle_seams())
                        self._btn_mask = ui.Button('Mask', width=ui.Percent(35),clicked_fn=lambda:self._fn_toggle_mask())
                        self._cbx_mask = ui.ComboBox()
                        for item in self.MASK_LIST:
                            self._cbx_mask.model.append_child_item(None,ui.SimpleStringModel(item))
                        self._cbx_mask.model.get_item_value_model().set_value(2)
                        self._cbx_mask.model.add_item_changed_fn(lambda a, b:self._fn_image_preview())
                    with ui.HStack():
                        self._btn_variation = ui.Button('Generate Variation', height=24, width=ui.Percent(35),clicked_fn=lambda:self._fn_img_variation())
                        self._btn_inpaint = ui.Button('Generate Inpaint', width=ui.Percent(35),clicked_fn=lambda:self._fn_img_edit())
                        self._cbx_tile = ui.ComboBox()
                        for item in self.TILE_LIST:
                            self._cbx_tile.model.append_child_item(None,ui.SimpleStringModel(item))
                        self._cbx_tile.model.get_item_value_model().set_value(0)
                        self._cbx_tile.model.add_item_changed_fn(lambda a, b:self._fn_image_preview())

                with ui.VStack(height=0,width=388,style={'margin':3}):
                    self._cf_api_key = ui.CollapsableFrame('API & Key')
                    with self._cf_api_key:
                        with ui.VStack(height=0):
                            self._lbl_api = ui.Label('API Key Not Intialized',style=_style_lbl)
                            self._fld_api = ui.StringField()
                            self._btn_api_Key = ui.Button('Set API Key', clicked_fn=lambda:self._api_key('set'))
                    self._cf_prompt = ui.CollapsableFrame('AI Prompt and Settings')
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
                            self._lbl_preview = ui.Label('Select the preview size of the images',style=_style_lbl, visible=False, enabled=False)
                            self._cbx_preview_size = ui.ComboBox(visible=False, enabled=False)
                            for item in self.SIZE_LIST:
                                self._cbx_preview_size.model.append_child_item(None,ui.SimpleStringModel(item))
                            self._cbx_preview_size.model.get_item_value_model().set_value(1)
                            self._cbx_preview_size.style = {'background_color':cl('#454545')}
                            self._btn_request = ui.Button('Request AI Image',clicked_fn=lambda:(self._fn_img_request()))
                    self._cf_settings = ui.CollapsableFrame('SeaMDLess Settings',collapsed=False)
                    with self._cf_settings:
                        with ui.VStack(height=0, width=388):
                            with ui.HStack(style={'Button':{'margin':-5.0},'Label':{'margin':5}}):
                                ui.Label('Image Cache')
                                self._fld_img_cache = ui.StringField(height=self.BUTTON_SIZE,width=260)
                                ui.Button(image_url='resources/icons/folder.png', width=self.BUTTON_SIZE, height=self.BUTTON_SIZE, clicked_fn=lambda:self._on_path_change_clicked(False))
                            ui.Button('Load Generated Image Folder', height=self.BUTTON_SIZE, clicked_fn=lambda:self._on_path_change_clicked(True))
                            ui.Button('Load Prompt from Image Prompt', height=self.BUTTON_SIZE, clicked_fn=lambda:self._fld_prompt.model.set_value(self._fn_folder_prompt()[0]))
                            ui.Button('Delete Generated Images', height=self.BUTTON_SIZE, clicked_fn=lambda:self._fn_file_delete(0), visible=False, enabled=False)
                            ui.Button('Delete Temporary Images', height=self.BUTTON_SIZE, clicked_fn=lambda:self._fn_file_delete(1), visible=False, enabled=False)
                            ui.Button('Clear Image Cache', height=self.BUTTON_SIZE, clicked_fn=lambda:self._fn_file_delete(2), visible=False, enabled=False)
                    with ui.CollapsableFrame('Statistics',alignment=ui.Alignment.BOTTOM):
                        with ui.VStack(style={'margin':1}):
                            with ui.HStack(width=self.STATS_WIDTH):
                                self._lbl_process_time:ui.Label = ui.Label('Processing Time:',style=_style_lbl)
                                self._lbl_process_time_val:ui.Label = ui.Label('00:00',style=_style_lbl,alignment=ui.Alignment.RIGHT)
                            with ui.HStack(width=self.STATS_WIDTH):
                                self._lbl_cnt_folder:ui.Label = ui.Label('Folder Count:',style=_style_lbl)
                                self._lbl_cnt_folder_val:ui.Label = ui.Label(f'{0:02d}',style=_style_lbl,alignment=ui.Alignment.RIGHT)
                            with ui.HStack(width=self.STATS_WIDTH):
                                self._lbl_cnt_img:ui.Label = ui.Label('Image Count:',style=_style_lbl)
                                self._lbl_cnt_img_val:ui.Label = ui.Label(f'{0:02d}',style=_style_lbl,alignment=ui.Alignment.RIGHT)
                            with ui.HStack(width=self.STATS_WIDTH):
                                self._lbl_size_cache:ui.Label = ui.Label('Image Cache Size:',style=_style_lbl)
                                self._lbl_size_cache_val:ui.Label = ui.Label(f'00.00 MB',style=_style_lbl,alignment=ui.Alignment.RIGHT)
# 
# Image Functions
# 
    def _fn_img_placeholder(self):
        img = Image.new('RGBA',(256,256), (40,40,40))
        self.IMG_PLACEHOLDER[:] = []
        np_data = np.asarray(img)
        self.IMG_PLACEHOLDER.append((np_data,img.size))

    def _fn_img_list(self, _dir:str='', _list:list=[], _type:str='*.png'):
        if _dir == "":
            _dir = self.CURRENT_DIR
        if not _dir.endswith('/'):
            _dir += '/'
        img_dir = Path(_dir)
        files = list(img_dir.glob(_type))
        _list[:] = []
        for f in files:
            with Image.open(f) as img:
                img = img.convert('RGBA')
                np_data = np.asarray(img).data
                _list.append((np_data,img.size))

    def _fn_image_preview(self,_val:int=0):
        if _val == 0:
            _val = self._sld_image.model.as_int
        img = self.IMG_PLACEHOLDER[0]
        if len(self.IMG_LIST) > 0:
            img = self.IMG_LIST.copy()[_val-1]
            if self._btn_seams.checked:
                img = self._fn_seams(img)
            if self._btn_mask.checked:
                img = self._fn_mask(img)
            if self._cbx_tile.model.get_item_value_model().as_int > 0:
                img = self._fn_tiles(img)
        self._provider.set_data_array(img[0],img[1])

    def _fn_img_request(self):
        _cbx_item = self._cbx_img_size.model.get_item_value_model().as_int
        startTime = time.time()
        _img_response = self._dalle_api._img_create(self._fld_prompt.model.as_string,self._sld_count.model.as_int,self.SIZE_LIST[_cbx_item])
        _target_dir = self._dalle_api._img_output(_img_response,self._path_img_cache)
        self._dalle_api._set_json(f'{_target_dir}/{_img_response["created"]}.json','prompt',self._fld_prompt.model.as_string)
        endTime = time.time()
        self._lbl_process_time_val.text = self._fn_process_time(startTime,endTime)
        self.CURRENT_DIR = _target_dir
        self._fn_folder_load()
        self._fn_folder_stats()

    def _fn_img_edit(self):
        None
        # _temp = ''
        # self._btn_mask.checked = True
        # _image = self._image.source_url
        # _cbx_item = self._cbx_img_size.model.get_item_value_model().as_int
        # if len(self._image.source_url.split('_mask')) == 1:
        #     _image = self._fn_visualize_mask()
        # _mask = self._image.source_url
        # _image = f'{self._image.source_url.split("_mask")[0]}.png'
        # self._btn_mask.checked = False
        # if os.path.getsize(_image) > 4000000:         
        #     _temp = f'{_image.split(".png")[0]}_temp.png'
        #     _img = Image.open(_image)
        #     _size = int(_img.size[0]/2)
        #     _img_small = _img.resize([_size,_size])
        #     _out_file = open(_temp, 'wb')
        #     _img_small.save(_temp)
        #     _out_file.flush()
        #     os.fsync(_out_file)
        #     _out_file.close()
        #     _img.close()
        #     _image = _temp
        # startTime = time.time()
        # _img_response = self._dalle_api._img_edit(self._lbl_image_prompt.text,_image,_mask,self._sld_count.model.as_int,self.SIZE_LIST[_cbx_item])
        # _target_dir = self._dalle_api._img_output(_img_response,self._path_img_cache)
        # self._dalle_api._set_json(f'{_target_dir}/{_img_response["created"]}.json','prompt',self._lbl_image_prompt.text)
        # endTime = time.time()
        # self._lbl_process_time_val.text = self._fn_process_time(startTime,endTime)
        # self.CURRENT_DIR = _target_dir
        # if os.path.exists(_image):
        #     shutil.copy2(_image,f'{_target_dir}1_{os.path.basename(_image)}')
        # self._fn_folder_load()
        # self._fn_folder_stats()
        # if os.path.exists(_temp):
        #     os.remove(_temp)

    def _fn_img_variation(self):
        None
        # _cbx_item = self._cbx_img_size.model.get_item_value_model().as_int
        # startTime = time.time()
        # _img_response = self._dalle_api._img_variation(self._image.source_url,self._sld_count.model.as_int,self.SIZE_LIST[_cbx_item])
        # _target_dir = self._dalle_api._img_output(_img_response,self._path_img_cache)
        # self._dalle_api._set_json(f'{_target_dir}/{_img_response["created"]}.json','prompt',self._lbl_image_prompt.text)
        # endTime = time.time()
        # self._lbl_process_time_val.text = self._fn_process_time(startTime,endTime)
        # self.CURRENT_DIR = _target_dir
        # if os.path.exists(self._image.source_url):
        #     shutil.copy2(self._image.source_url,f'{_target_dir}1_{os.path.basename(self._image.source_url)}')
        # self._fn_folder_load()
        # self._fn_folder_stats()

    def _fn_toggle_seams(self):
        self._btn_seams.checked = not self._btn_seams.checked
        self._fn_image_preview()

    def _fn_seams(self,img:tuple) -> tuple:
        if img:
            # img[0] = image data
            # img[1] = image size
            # img[1][0] = image size width/x
            # img[1][1] = image size height/y
            new_img = Image.fromarray(np.asarray(img[0]))
            offset = (int(img[1][0]/2),int(img[1][1]/2))
            img_offset = ImageChops.offset(new_img,offset[0],offset[1])
            np_data = np.asarray(img_offset).data
            return (np_data,img_offset.size)

    def _fn_toggle_mask(self):
        self._btn_mask.checked = not self._btn_mask.checked
        self._fn_image_preview()

    def _fn_mask(self,img:tuple) -> tuple:
        if img:
            # img[0] = image data
            # img[1] = image size
            mask_index = self._cbx_mask.model.get_item_value_model().as_int
            self._fn_img_list(self._rsc_path,self.MASK_IMG,'*Mask*.png')
            mask_img = self.MASK_IMG[mask_index]
            mask = Image.fromarray(np.asarray(mask_img[0]))
            mask = mask.convert('L')
            mask = mask.resize(img[1])
            new_img = Image.fromarray(np.asarray(img[0]))
            new_img.putalpha(mask)
            np_data = np.asarray(new_img).data
            return (np_data,new_img.size)
    
    def _fn_tiles(self,img:tuple) -> tuple:
        if img:
            tiles = self._cbx_tile.model.get_item_value_model().as_int+1
            img_w,img_h = img[1]
            new_img = Image.new('RGBA',(img_w*tiles,img_h*tiles))
            src_img = Image.fromarray(np.asarray(img[0]))
            w,h = new_img.size
            for i in range(0, w, img_w):
                for j in range(0, h, img_h):
                    new_img.paste(src_img, (i,j))
            new_img = new_img.resize(img[1])
            np_data = np.asarray(new_img).data
            return (np_data,new_img.size)

#           
# Folder Functions
# 
    def _fn_folder_load(self):
        self._fn_set_sld_image()
        self._fn_image_preview(1)
        _prompt,_json_file = self._fn_folder_prompt()
        _prompt_folder = os.path.basename(self.CURRENT_DIR.strip('/'))
        self._lbl_image_dir.text = _prompt_folder
        if os.path.exists(_json_file):
            _prompt_msg = f'{_prompt}'
        else:
            _prompt_msg = f'Prompt not found.'
        self._lbl_image_prompt.text = _prompt_msg

    def _fn_folder_prompt(self)->list:
        _target = os.path.basename(self.CURRENT_DIR.strip('/'))
        _json_file = f'{self.CURRENT_DIR.strip("/")}/{_target}.json'
        _prompt = self._dalle_api._get_json(f'{_json_file}','prompt')
        return [_prompt,_json_file]

    def _fn_dir_list(self, _dirname:str="",_rootonly:bool=False)->list:
        """
        Returns all files and folders.\n
        return [ root , dirs , files ]
        """
        # print(_dirname)
        _rootlist = []
        _dirlist = []
        _filelist = []
        _dirname = _dirname.strip('/')+'/'
        # print(_dirname)
        if _rootonly:
            _rootlist = [_dirname]
            for i in os.listdir(_dirname):
                _path = os.path.join(_dirname,i)
                if os.path.isfile(_path):
                    _filelist.append(_path)
                if os.path.isdir(_path):
                    _dirlist.append(_path)
        else:
            for _root,_dirs,_files in os.walk(_dirname):
                if len(_rootlist) == 0:
                    _rootlist.append(_root)
                # print(f'root:{_root}\ndirs:{_dirs}\nfiles:{_files}')
                for _file in _files:
                    _filelist.append(os.path.join(_root,_file))
                _dirlist.extend(_dirs)
            # print([_rootlist[0],_dirlist,_filelist])
        return [_rootlist[0],_dirlist,_filelist]

    def _fn_folder_stats(self):
        _path = self._fld_img_cache.model.as_string
        _lists = self._fn_dir_list(_path)
        self._lbl_cnt_folder_val.text = f'{len(_lists[1]):02d}'
        self._lbl_cnt_img_val.text = f'{len(_lists[2]):02d}'
        self._lbl_size_cache_val.text = self.get_size_format(self.get_directory_size(_path))
# 
# Generic Functions
# 
    def _fn_process_time(self,_start=0,_end=0)->str:
        _calc_time = _end-_start
        _minutes,_seconds = divmod(_calc_time,60)
        return f'{"{:02d}".format(int(_minutes))}:{"{:0.2f}".format(_seconds)}'

    def get_size_format(self, b, factor=1024, suffix="B"):
        """
        Scale bytes to its proper byte format
        e.g:
            1253656 => '1.20MB'
            1253656678 => '1.17GB'
        Source: https://www.thepythoncode.com/article/get-directory-size-in-bytes-using-python
        """
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if b < factor:
                return f"{b:.2f} {unit}{suffix}"
            b /= factor
        return f"{b:.2f} Y{suffix}"

    def get_directory_size(self, directory):
        """
        Returns the `directory` size in bytes.
        Source: https://www.thepythoncode.com/article/get-directory-size-in-bytes-using-python
        """
        total = 0
        try:
            # print("[+] Getting the size of", directory)
            for entry in os.scandir(directory):
                if entry.is_file():
                    # if it's a file, use stat() function
                    total += entry.stat().st_size
                elif entry.is_dir():
                    # if it's a directory, recursively call this function
                    try:
                        total += self.get_directory_size(entry.path)
                    except FileNotFoundError:
                        pass
        except NotADirectoryError:
            # if `directory` isn't a directory, get the file size then
            return os.path.getsize(directory)
        except PermissionError:
            # if for whatever reason we can't open the folder, return 0
            return 0
        return total

    def _fn_set_sld_image(self):
        _img_cnt = len(self.IMG_LIST)
        if _img_cnt == 0:
            _img_cnt = 1
        if _img_cnt > 0:
            self._sld_image.model.set_value(1)
            self._sld_image.max = _img_cnt
            self.MLD_IMAGE.set_max(_img_cnt)
    
    def _fn_file_delete(self,_typeint:1):
        _all = self._fn_dir_list(self._fld_img_cache.model.as_string)
        _root = _all[0]
        _dirs = _all[1]
        _files = _all[2]
        _del = 0
        if len(_dirs) > 0 and len(_files) > 0:
            if _typeint == 0:
                for f in _files:
                    os.remove(f)
                    _del += 1
            elif _typeint == 1:
                for f in _files:
                    if len(f.split('_')) > 1:
                        os.remove(f)
                        _del += 1
            else:
                for d in _dirs:
                    shutil.rmtree(os.path.join(_root,d))
                _del = len(_dirs) + len(_files)
            self._fn_folder_stats()
            print(f'Files Deleted: {_del}')

# 
# File Picker Functions
# 
    def _on_path_change_clicked(self,_load:bool=False):
        self._load_dir = _load
        if self._filepicker is None:
            self._filepicker = FilePickerDialog(
                'Select Folder',
                show_only_collections='my-computer',
                apply_button_label='Select',
                item_filter_fn=lambda item:self._on_filepicker_filter_item(item),
                selection_changed_fn=lambda items:self._on_filepicker_selection_change(items),
                click_apply_handler=lambda filename, dirname:self._on_dir_pick(self._filepicker, filename, dirname),
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

    def _on_dir_pick(self, dialog:FilePickerDialog, filename:str, dirname:str):
        dialog.hide()
        self._fn_img_list(dirname,self.IMG_LIST)
        if self._load_dir:
            self._btn_seams.checked = False
            self._btn_mask.checked = False
            self._cbx_tile.model.get_item_value_model().set_value(0)
            self.CURRENT_DIR = dirname.strip('/')
            self._fn_folder_load()
            self._load_dir = False
        else:
            self._fld_img_cache.model.set_value(self._filepicker_selected_folder)
            self._fld_img_cache.tooltip = self._fld_img_cache.model.as_string
            self._dalle_api._set_json(f'{self._dalle_api.ROOT_PATH}/config/seamdless.json','img_cache',f'{dirname.strip("/")}')
        self._fn_folder_stats()