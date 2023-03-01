import os
import json

import omni.kit.pipapi
import omni.kit.app
import carb

import openai
import requests

from urllib.parse import urlparse
from urllib.request import urlretrieve

class api():
    ROOT_PATH = ""
    def __init__(self, ext_id):
        self.ROOT_PATH = omni.kit.app.get_app().get_extension_manager().get_extension_path(ext_id)
        self._data = None

    def _get_api_key(self,_ignore:bool=False) -> str:
        _file = ""
        _return_val = ""
        _json = f'{self.ROOT_PATH}/config/api.json'
        if os.path.exists(_json):
            _file = open(_json,'rt')
            _data = json.load(_file)
            if 'openai' in _data:
                _return_val = _data['openai']
            else:
                if not _ignore: carb.log_warn('WARNING: api.json is Missing Data')
        else:
            if not _ignore: carb.log_warn('WARNING: api.json is Missing')
        _data = None
        if _file != "":
            _file.close()
        return _return_val
    
    def _set_json(self,_file:str="",_key:str="",_value:str=""):
        _dict = {_key:_value}
        _jsonString = json.dumps(_dict,indent=4)
        _jsonFile = open(_file,'w')
        _jsonFile.write(_jsonString)
        _jsonFile.close()

    def _get_json(self,_json:str="",_key:str="")->str:
        _return_val = ""
        _file = ""
        if os.path.exists(_json):
            _file = open(_json,'rt')
            _data = json.load(_file)
            if _key in _data:
                _return_val = _data[_key]
            else:
                _return_val = ""
        _data = None
        if _file != "":
            _file.close()
        return _return_val
    
    def _register_openai(self):
        openai.api_key = self._get_api_key()
    
    def _img_create(self,_prompt:str="",_n:int=1,_size:str='256x256')->dict:
        _response = openai.Image.create(
            api_key=self._register_openai(),
            prompt=_prompt,
            n=_n,
            size=_size
        )
        return _response
    
    def _img_edit(self,_prompt:str="",_image:str="",_mask:str="",_n:int=1,_size:str='256x256')->dict:
        _response = openai.Image.create_edit(
            api_key=self._register_openai(),
            image=open(_image,'rb'),
            mask=open(_mask,'rb'),
            prompt=_prompt,
            n=_n,
            size=_size
        )
        return _response
    
    def _img_variation(self,_image:str="",_n:int=1,_size:str='256x256')->dict:
        _response = openai.Image.create_variation(
            api_key=self._register_openai(),
            image=open(_image,'rb'),
            n=_n,
            size=_size
        )
        return _response
    
    def _img_name(self,_response:dict={},_int:int=0):
        _url_path = urlparse(_response['data'][_int]['url']).path
        return os.path.basename(_url_path)

    def _img_output(self,_url_dict:dict={},_img_cache:str="")->str:
        if _url_dict != {}:
            if _img_cache == "":
                _img_cache = f'{self.ROOT_PATH}/resources'
            _target_folder = _url_dict['created']
            _target_dir = f'{_img_cache}/{_target_folder}'
            if not os.path.exists(_target_dir):
                os.mkdir(_target_dir)
            for i in range(0,len(_url_dict['data'])):
                _url = _url_dict['data'][i]['url']
                _response = requests.get(_url, stream = True)

                if _response.status_code == 200:
                    _target_file = f'{_target_dir}/{self._img_name(_url_dict,i)}'
                    urlretrieve(_url,_target_file)
                    print(f'Image sucessfully Downloaded: {_target_file}\n{_url}')
                else:
                    carb.log_warn('Image Couldn\'t be retrieved')
            return _target_dir