import os
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "github-puller"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "username": "",
    "token": "",
    "target_dir": str(Path.home() / "Desktop" / "Projects")
}

class Config:
    def __init__(self):
        self.data = self._load_config()
    
    def _load_config(self):
        """Yapılandırmayı yükle"""
        if not CONFIG_FILE.exists():
            return DEFAULT_CONFIG.copy()
        
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Eksik anahtarları varsayılan değerlerle doldur
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"Config yükleme hatası: {e}")
            return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """Yapılandırmayı kaydet"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Config kaydetme hatası: {e}")
    
    def get(self, key, default=None):
        """Yapılandırma değeri al"""
        return self.data.get(key, default)
    
    def set(self, key, value):
        """Yapılandırma değeri ayarla ve kaydet"""
        try:
            self.data[key] = value
            self.save_config()
        except Exception as e:
            print(f"Config ayarlama hatası: {e}")
    
    @property
    def username(self):
        return self.data.get('username', '')
    
    @username.setter
    def username(self, value):
        self.set('username', value)
    
    @property
    def token(self):
        return self.data.get('token', '')
    
    @token.setter
    def token(self, value):
        self.set('token', value)
    
    @property
    def target_dir(self):
        return self.data.get('target_dir', str(Path.home() / "Desktop" / "Projects"))
    
    @target_dir.setter
    def target_dir(self, value):
        self.set('target_dir', value)
