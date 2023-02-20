import os
import json

import omni.kit.pipapi
import omni.kit.app

import openai

class api():
    def __init__(self, ext_id):
        self._path = omni.kit.app.get_app().get_extension_manager().get_extension_path(ext_id)
        self._data = None
        self._json = f"{self._path}/config/api.json"

    def _get_api_key(self) -> str:
        if os.path.exists(self._json):
            _file = open(self._json,"rt")
            _data = json.load(_file)
            if "openai" in _data:
                _return_val = _data["openai"]
            else:
                _return_val = None
                print("ERROR: api.json is Missing Data")
        else:
            _return_val = None
            print("ERROR: api.json is Missing")
        _data = None
        _file.close()
        return _return_val
    
    def _set_api_key(self,_key:str=""):
        if self._json != None:
            _dict = {"openai":_key}
            with open(self._json, "w") as _outfile:
                json.dump(_dict,_outfile)

