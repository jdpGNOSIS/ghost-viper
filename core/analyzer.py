import re
import json
import os
from datetime import datetime

class CodeAnalyzer:
    def __init__(self, config):
        self.config = config
        self.social_patterns = {
            'instagram': [
                r'instagram\.com', r'insta\.', r'ig\.', r'gramfeed',
                r'insta-follow', r'instagram-follow', r'insta-liker',
                r'auto.*insta', r'insta.*auto', r'insta.*bot',
            ],
            'tiktok': [
                r'tiktok\.com', r'tiktok.*follow', r'tiktok.*view',
                r'tiktok.*like', r'tiktok.*auto', r'auto.*tiktok',
                r'tiktok.*bot', r'douyin',
            ],
            'youtube': [
                r'youtube\.com', r'youtu\.be', r'yt.*subscriber',
                r'youtube.*view', r'youtube.*like', r'youtube.*auto',
                r'subscriber.*bot', r'sub.*bot', r'auto.*sub',
            ],
            'twitter_x': [
                r'twitter\.com', r'x\.com', r'tweet.*bot',
                r'twitter.*follow', r'twitter.*auto', r'twitter.*like',
                r'twitter.*retweet', r'auto.*tweet',
            ],
            'telegram': [
                r't\.me/', r'telegram\.', r'tg.*member',
                r'telegram.*bot', r'telegram.*auto',
                r'tg.*invite', r'telegram.*member',
            ],
            'discord': [
                r'discord\.gg', r'discord\.com', r'discord.*bot',
                r'discord.*member', r'discord.*auto',
                r'discord.*invite',
            ],
            'spotify': [
                r'spotify\.com', r'spotify.*playlist',
                r'spotify.*follow', r'spotify.*auto',
            ],
            'soundcloud': [
                r'soundcloud\.com', r'soundcloud.*follow',
                r'soundcloud.*play', r'soundcloud.*auto',
                r'sc.*follow', r'sc.*bot',
            ],
            'twitch': [
                r'twitch\.tv', r'twitch.*follow',
                r'twitch.*view', r'twitch.*auto',
            ],
            'facebook': [
                r'facebook\.com', r'fb\.com', r'fb.*like',
                r'facebook.*follow', r'facebook.*auto',
            ],
            'linkedin': [
                r'linkedin\.com', r'linkedin.*follow',
                r'linkedin.*auto', r'linkedin.*connect',
            ],
            'telegram_members': [
                r'member.*adder', r'member.*add', r'add.*member',
                r'member.*bot', r'group.*member',
            ],
            'social_generic': [
                r'social.*media.*bot', r'social.*media.*tool',
                r'social.*media.*auto', r'auto.*follower',
                r'follower.*bot', r'follower.*booster',
                r'follower.*generator', r'follower.*tool',
                r'follower.*hack', r'bot.*follower',
                r'like.*bot', r'view.*bot', r'comment.*bot',
                r'mass.*follow', r'mass.*like', r'auto.*like',
                r'auto.*follow', r'auto.*comment', r'auto.*view',
                r'boost.*follower', r'boost.*like', r'boost.*view',
                r'smm.*panel', r'smm.*api', r'social.*panel',
            ],
        }

        self.risk_indicators = {
            'high': [
                r'login.*bypass', r'cookie.*steal', r'session.*hijack',
                r'credential.*stuff', r'password.*crack',
                r'exploit.*inject', r'payload.*deliver',
                r'0day', r'zero.day',
            ],
            'medium': [
                r'fake.*account', r'account.*creator',
                r'account.*generator', r'spoof.*email',
                r'proxy.*rotate', r'user.*agent.*rotate',
                r'captcha.*solve', r'captcha.*bypass',
                r'sms.*verify', r'phone.*verify',
                r'email.*verify', r'llauncher',
            ],
            'low': [
                r'selenium', r'playwright', r'puppeteer',
                r'browser.*auto', r'webdriver',
                r'headless.*browser',
            ],
        }

    def analyze_repo(self, repo_data):
        analysis = {
            'platforms_detected': [],
            'risk_score': 0,
            'risk_level': 'low',
            'features': [],
            'languages_used': [],
            'has_readme': False,
            'readme_matches': [],
            'code_pattern_matches': [],
            'estimated_purpose': 'unknown',
            'has_gui': False,
            'has_api': False,
            'has_cli': False,
            'has_database': False,
        }

        name_desc = f"{repo_data.get('name', '')} {repo_data.get('description', '')}"
        readme = repo_data.get('readme', '')
        match_files = repo_data.get('match_file', '')
        match_text = repo_data.get('match_text', '')

        # Platform detection
        found_platforms = set()
        for platform, patterns in self.social_patterns.items():
            for pat in patterns:
                if re.search(pat, name_desc, re.IGNORECASE):
                    found_platforms.add(platform)
                    analysis['readme_matches'].append(f"{platform}:{pat}")
                if readme and re.search(pat, readme, re.IGNORECASE):
                    found_platforms.add(platform)
                    analysis['readme_matches'].append(f"{platform}(readme):{pat}")
        analysis['platforms_detected'] = list(found_platforms)

        # Risk scoring
        risk_score = 0
        for level, indicators in self.risk_indicators.items():
            weight = {'high': 10, 'medium': 5, 'low': 2}[level]
            for indicator in indicators:
                if re.search(indicator, name_desc, re.IGNORECASE):
                    risk_score += weight
                    analysis['features'].append(f"risk:{level}:{indicator}")
                if readme and re.search(indicator, readme, re.IGNORECASE):
                    risk_score += weight
                    analysis['features'].append(f"risk:{level}(readme):{indicator}")

        # Purpose detection
        if any(pat in name_desc.lower() for pat in ['generator', 'maker', 'creator', 'builder']):
            analysis['estimated_purpose'] = 'generator'
        elif any(pat in name_desc.lower() for pat in ['bot', 'auto', 'script', 'tool']):
            analysis['estimated_purpose'] = 'automation'
        elif any(pat in name_desc.lower() for pat in ['panel', 'dashboard', 'web', 'site']):
            analysis['estimated_purpose'] = 'panel'
        elif any(pat in name_desc.lower() for pat in ['api', 'sdk', 'lib', 'library']):
            analysis['estimated_purpose'] = 'api'
        elif any(pat in name_desc.lower() for pat in ['hack', 'crack', 'exploit', 'inject']):
            analysis['estimated_purpose'] = 'exploit'
            risk_score += 5

        # GUI detection
        gui_keywords = ['gui', 'tkinter', 'pyqt', 'pyside', 'wxpython', 'electron', 'react', 'vue', 'angular', 'flask', 'django', 'streamlit', 'gradio']
        for kw in gui_keywords:
            if kw in name_desc.lower() or (readme and kw in readme.lower()):
                analysis['has_gui'] = True
                break

        # API detection
        api_keywords = ['api', 'rest', 'graphql', 'endpoint', 'flask', 'fastapi', 'express', 'django']
        for kw in api_keywords:
            if kw in name_desc.lower() or (readme and kw in readme.lower()):
                analysis['has_api'] = True
                break

        # CLI detection
        cli_keywords = ['cli', 'command.*line', 'terminal', 'console', 'argparse', 'click', 'typer', 'commander']
        for kw in cli_keywords:
            if kw in name_desc.lower() or (readme and kw in readme.lower()):
                analysis['has_cli'] = True
                break

        # Database detection
        db_keywords = ['sqlite', 'postgres', 'mysql', 'mongodb', 'redis', 'database', 'sqlalchemy', 'prisma']
        for kw in db_keywords:
            if kw in name_desc.lower() or (readme and kw in readme.lower()):
                analysis['has_database'] = True
                break

        # Language detection
        lang = repo_data.get('language', '')
        if lang:
            analysis['languages_used'].append(lang)

        # Stars boost
        stars = repo_data.get('stars', 0) or 0
        analysis['stars'] = stars

        # Final risk
        risk_score = min(risk_score, 100)
        analysis['risk_score'] = risk_score
        if risk_score >= 30:
            analysis['risk_level'] = 'high'
        elif risk_score >= 15:
            analysis['risk_level'] = 'medium'

        return analysis

    def rank_repositories(self, results):
        ranked = []
        for r in results:
            analysis = self.analyze_repo(r)
            score = 0

            # Stars
            score += min(r.get('stars', 0) or 0, 100) * 0.3

            # Platform matches
            score += len(analysis['platforms_detected']) * 15

            # Risk score (higher = more aggressive tools = more what we want)
            score += analysis['risk_score'] * 0.5

            # Features
            score += len(analysis['features']) * 5

            # README quality
            if r.get('readme'):
                score += 10
                score += len(analysis.get('readme_matches', [])) * 3

            # Purpose weight
            purpose_weights = {
                'generator': 25,
                'automation': 20,
                'panel': 15,
                'exploit': 30,
                'api': 10,
            }
            score += purpose_weights.get(analysis['estimated_purpose'], 5)

            ranked.append({
                **r,
                'analysis': analysis,
                '_rank_score': score,
            })

        ranked.sort(key=lambda x: x['_rank_score'], reverse=True)
        return ranked
