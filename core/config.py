import json
import os
import base64
import tempfile
import shutil
import logging
from datetime import datetime

logger = logging.getLogger('GhostViper.Config')

DEFAULT_CONFIG = {
    "github_token": "",
    "rate_limit": 1.0,
    "max_pages": 50,
    "results_per_page": 30,
    "search_deep": True,
    "search_readme": True,
    "search_code": True,
    "code_patterns": [
        "followers", "instagram", "social.*media", "bot.*follow",
        "auto.*like", "auto.*comment", "mass.*follow", "follower.*boost",
        "social.*boost", "like.*bot", "view.*bot", "telegram.*member",
        "youtube.*subscriber", "tiktok.*follower", "twitter.*follower",
        "discord.*member", "twitch.*follower", "soundcloud.*follower",
        "spotify.*playlist", "tiktok.*view", "youtube.*view",
        "自动化", "粉丝", "フォロワー", "подписчик",
    ],
    "file_types": [".py", ".js", ".ts", ".java", ".php", ".go", ".rb", ".c", ".cpp", ".sh", ".bat", ".ps1"],
    "min_stars": 0,
    "min_forks": 0,
    "max_results": 500,
    "auto_clone": False,
    "clone_dir": os.path.join(os.environ.get('GHOST_VIPER_ROOT', os.path.expanduser('~')), 'repos'),
    "one_drive_shortcut": True,
    "sound_effects": True,
    "show_banner": True,
    "theme": "hacker_dark",
}

class GhostConfig:
    def __init__(self):
        self.root = os.environ.get('GHOST_VIPER_ROOT', os.path.expanduser('~'))
        self.config_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'GhostViper')
        self.config_file = os.path.join(self.config_dir, 'config.json')
        self._data = dict(DEFAULT_CONFIG)
        self.load()

    @property
    def github_token(self):
        tok = self._data.get('github_token', '')
        if tok and tok.startswith('enc:'):
            try:
                return base64.b64decode(tok[4:]).decode()
            except Exception as e:
                logger.error(f"Failed to decode token: {e}")
                return ''
        return tok

    @github_token.setter
    def github_token(self, value):
        if value:
            self._data['github_token'] = 'enc:' + base64.b64encode(value.encode()).decode()
        else:
            self._data['github_token'] = ''

    def __getitem__(self, key):
        if key == 'github_token':
            return self.github_token
        return self._data.get(key, DEFAULT_CONFIG.get(key))

    def __setitem__(self, key, value):
        if key == 'github_token':
            self.github_token = value
        else:
            self._data[key] = value
        self.save()

    def load(self):
        os.makedirs(self.config_dir, exist_ok=True)
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    if not isinstance(loaded, dict):
                        logger.error(f"Config file is not a dict: {type(loaded)}")
                        return
                    self._data.update(loaded)
                    token_status = 'set' if loaded.get('github_token') else 'not set'
                    logger.info(f"Config loaded from {self.config_file} (token: {token_status})")
            except json.JSONDecodeError as e:
                logger.error(f"Config file corrupted: {e}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")

    def save(self):
        os.makedirs(self.config_dir, exist_ok=True)
        tmp = self.config_file + '.tmp'
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=4)
            shutil.move(tmp, self.config_file)
            token_status = 'set' if self._data.get('github_token') else 'not set'
            logger.info(f"Config saved to {self.config_file} (token: {token_status})")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except:
                    pass
            return False

    def reset(self):
        self._data = dict(DEFAULT_CONFIG)
        return self.save()
