import json
import os
import sys

class ConfigManager:
    def __init__(self):
        self.config_path = self._get_config_path()
        
    def _get_config_path(self):
        if getattr(sys, 'frozen', False):
            return os.path.join(os.path.dirname(sys.argv[0]), 'config.json')
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')
    
    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: {self.config_path} not found!")
            return None
            
    def save_config(self, config):
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4) 