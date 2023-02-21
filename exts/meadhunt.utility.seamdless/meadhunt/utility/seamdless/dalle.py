import os
import json

import omni.kit.pipapi
import omni.kit.app
import carb
import openai

class api():
    ROOT_PATH = ""
    def __init__(self, ext_id):
        self.ROOT_PATH = omni.kit.app.get_app().get_extension_manager().get_extension_path(ext_id)
        self._data = None

    def _get_api_key(self,_ignore:bool=False) -> str:
        _file = ""
        _return_val = ""
        _json = f"{self.ROOT_PATH}/config/api.json"
        if os.path.exists(_json):
            _file = open(_json,"rt")
            _data = json.load(_file)
            if "openai" in _data:
                _return_val = _data["openai"]
            else:
                if not _ignore: carb.log_warn("WARNING: api.json is Missing Data")
        else:
            if not _ignore: carb.log_warn("WARNING: api.json is Missing")
        _data = None
        if _file != "":
            _file.close()
        return _return_val
    
    def _set_json(self,_json:str="",_key:str="",_value:str=""):
        _dict = {_key:_value}
        _jsonString = json.dumps(_dict,indent=4)
        _jsonFile = open(_json,"w")
        _jsonFile.write(_jsonString)
        _jsonFile.close()

    def _get_json(self,_json:str="",_key:str="")->str:
        _return_val = ""
        _file = ""
        print(f"_json: {_json}")
        print(f"_key: {_key}")
        if os.path.exists(_json):
            _file = open(_json,"rt")
            print(f"_file: {_file}")
            _data = json.load(_file)
            if _key in _data:
                _return_val = _data[_key]
            else:
                _return_val = ""
        _data = None
        if _file != "":
            _file.close()
        print(f"_return_val: {_return_val}")
        return _return_val