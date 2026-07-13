import requests
import time
import logging
import re
import base64
from datetime import datetime
from urllib.parse import quote, urlencode

logger = logging.getLogger('GhostViper.Scanner')

class GitHubScanner:
    def __init__(self, config, callback=None):
        self.config = config
        self.callback = callback
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/vnd.github.v3+json',
        })
        token = config.github_token
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
            self.auth_type = 'token'
        else:
            self.auth_type = 'anonymous'

        self._request_count = 0
        self._rate_remaining = 60
        self._rate_reset = 0

    def _log(self, msg, level='info'):
        if self.callback:
            self.callback(msg, level)
        if level == 'info':
            logger.info(msg)
        elif level == 'warn':
            logger.warning(msg)
        elif level == 'error':
            logger.error(msg)

    def _rate_limit_wait(self):
        delay = float(self.config['rate_limit'])
        if self._rate_remaining < 5 and self._rate_reset > time.time():
            wait = self._rate_reset - time.time() + 1
            self._log(f"[!] Rate limit low. Waiting {wait:.0f}s...", 'warn')
            time.sleep(wait)
        else:
            time.sleep(delay)

    def _request(self, url, params=None):
        self._rate_limit_wait()
        try:
            resp = self.session.get(url, params=params, timeout=30)
            self._request_count += 1

            if 'X-RateLimit-Remaining' in resp.headers:
                self._rate_remaining = int(resp.headers['X-RateLimit-Remaining'])
            if 'X-RateLimit-Reset' in resp.headers:
                self._rate_reset = int(resp.headers['X-RateLimit-Reset'])

            if resp.status_code == 401:
                try:
                    detail = resp.json().get('message', '')
                except:
                    detail = resp.text[:200]
                self._log(f"[!] GitHub 401: {detail}", 'error')
                if 'requires' in detail.lower() and 'authentication' in detail.lower():
                    if self.config.github_token:
                        self._log("[!] Token sent but lacks required scope for this endpoint.", 'error')
                        self._log("[!] Create a classic token with 'repo' scope at github.com/settings/tokens", 'error')
                    else:
                        self._log("[!] No token configured. Set one in Settings (⚙).", 'error')
                elif 'bad' in detail.lower() or 'invalid' in detail.lower():
                    self._log("[!] Token is invalid or expired. Update it in Settings (⚙).", 'error')
                else:
                    self._log("[!] Authentication failed. Check your token in Settings (⚙).", 'error')
                return None

            if resp.status_code == 403:
                try:
                    detail = resp.json().get('message', '')
                except:
                    detail = resp.text[:200]
                if 'rate' in detail.lower() or 'limit' in detail.lower():
                    self._log(f"[!] Rate limited: {detail}", 'warn')
                    time.sleep(60)
                    resp = self.session.get(url, params=params, timeout=30)
                else:
                    self._log(f"[!] Forbidden: {detail}", 'error')
                    return None

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.Timeout:
            self._log("[!] Request timed out. Retrying...", 'warn')
            time.sleep(5)
            return self._request(url, params)
        except Exception as e:
            self._log(f"[!] Request failed: {e}", 'error')
            return None

    def validate_token(self):
        """Test if the current token is valid and has code search scope."""
        results = {'user': False, 'code_search': False, 'scopes': [], 'user_login': ''}
        try:
            resp = self.session.get('https://api.github.com/user', timeout=15)
            if resp.status_code == 200:
                user = resp.json()
                scopes = (resp.headers.get('X-OAuth-Scopes', '') or '').split(', ')
                results['user'] = True
                results['scopes'] = [s.strip() for s in scopes if s.strip()]
                results['user_login'] = user.get('login', '?')
            elif resp.status_code == 401:
                detail = ''
                try: detail = resp.json().get('message', '')
                except: detail = resp.text[:100]
                self._log(f"[!] User endpoint 401: {detail}", 'error')
                return False
        except Exception as e:
            self._log(f"[!] User endpoint error: {e}", 'error')
            return False

        if not results['user']:
            return False

        # Test code search endpoint specifically
        try:
            resp2 = self.session.get(
                'https://api.github.com/search/code?q=hello+world&per_page=1',
                timeout=15
            )
            if resp2.status_code == 200:
                results['code_search'] = True
            elif resp2.status_code == 401:
                detail = ''
                try: detail = resp2.json().get('message', '')
                except: detail = resp2.text[:100]
                self._log(f"[!] Code search requires additional permissions: {detail}", 'error')
                self._log("[!] Your token works for basic auth but lacks code search scope.", 'error')
        except Exception as e:
            self._log(f"[!] Code search test error: {e}", 'warn')

        # Report
        scopes_str = ', '.join(results['scopes']) if results['scopes'] else 'none'
        self._log(f"[+] Authenticated as: {results['user_login']} (scopes: {scopes_str})", 'success')
        if results['code_search']:
            self._log("[+] Code search: OK", 'success')
        else:
            self._log("[!] Code search: UNAVAILABLE - add 'repo' scope or use a classic token", 'warn')

        return results['user'] and results['code_search']

    def search_repositories(self, query, page=1):
        q = f"{query} sort:stars-desc"
        params = {
            'q': q,
            'per_page': min(int(self.config['results_per_page']), 100),
            'page': page,
        }
        url = 'https://api.github.com/search/repositories'
        return self._request(url, params)

    def search_code(self, query, page=1):
        params = {
            'q': query,
            'per_page': min(int(self.config['results_per_page']), 100),
            'page': page,
        }
        url = 'https://api.github.com/search/code'
        return self._request(url, params)

    def get_repo_details(self, full_name):
        url = f'https://api.github.com/repos/{full_name}'
        return self._request(url)

    def get_repo_readme(self, full_name):
        url = f'https://api.github.com/repos/{full_name}/readme'
        data = self._request(url)
        if data and 'content' in data:
            try:
                content = base64.b64decode(data['content']).decode('utf-8', errors='replace')
                return content
            except:
                return None
        return None

    def get_repo_contents(self, full_name, path=''):
        url = f'https://api.github.com/repos/{full_name}/contents/{path}'
        return self._request(url)

    def get_file_content(self, full_name, path):
        url = f'https://api.github.com/repos/{full_name}/contents/{path}'
        data = self._request(url)
        if data and 'content' in data:
            try:
                content = base64.b64decode(data['content']).decode('utf-8', errors='replace')
                return content
            except:
                return data.get('content', '')
        return ''

    def get_repo_topics(self, full_name):
        repo = self.get_repo_details(full_name)
        if repo:
            topics = repo.get('topics', [])
            topics_url = f"https://api.github.com/repos/{full_name}/topics"
            resp = self.session.get(topics_url, headers={
                'Accept': 'application/vnd.github.mercy-preview+json',
                'User-Agent': self.session.headers['User-Agent'],
            })
            if resp.status_code == 200:
                topics = resp.json().get('names', topics)
            return topics
        return []

    def advanced_search(self, query, patterns=None, file_types=None):
        self._log(f"[*] Launching advanced search: '{query}'")
        all_results = []
        seen_repos = set()

        # Phase 1: Repository search
        self._log("[*] Phase 1: Searching repositories...")
        page = 1
        max_pages = int(self.config['max_pages'])
        max_results = int(self.config['max_results'])

        while len(all_results) < max_results and page <= max_pages:
            data = self.search_repositories(query, page)
            if not data or 'items' not in data:
                break
            for item in data['items']:
                full_name = item['full_name']
                if full_name not in seen_repos:
                    seen_repos.add(full_name)
                    all_results.append({
                        'type': 'repository',
                        'source': 'repo_search',
                        'full_name': full_name,
                        'name': item['name'],
                        'description': item.get('description', '') or '',
                        'url': item['html_url'],
                        'stars': item.get('stargazers_count', 0),
                        'forks': item.get('forks_count', 0),
                        'language': item.get('language', '') or '',
                        'topics': item.get('topics', []),
                        'owner': item.get('owner', {}).get('login', ''),
                        'created_at': item.get('created_at', ''),
                        'updated_at': item.get('updated_at', ''),
                        'score': item.get('score', 0),
                    })
            if len(data['items']) < int(self.config['results_per_page']):
                break
            page += 1

        # Phase 2: Code content search
        if self.config['search_code'] and patterns:
            self._log("[*] Phase 2: Searching repository code...")
            for pattern in patterns[:10]:
                for ft in (file_types or self.config['file_types']):
                    page = 1
                    while page <= 5:
                        q = f"{pattern} extension:{ft.lstrip('.')}"
                        data = self.search_code(q, page)
                        if not data or 'items' not in data:
                            break
                        for item in data['items']:
                            full_name = item['repository']['full_name']
                            if full_name not in seen_repos:
                                seen_repos.add(full_name)
                                repo_data = self.get_repo_details(full_name) or {}
                                all_results.append({
                                    'type': 'repository',
                                    'source': 'code_search',
                                    'full_name': full_name,
                                    'name': repo_data.get('name', full_name.split('/')[-1]),
                                    'description': repo_data.get('description', '') or '',
                                    'url': repo_data.get('html_url', item['html_url']),
                                    'stars': repo_data.get('stargazers_count', 0),
                                    'forks': repo_data.get('forks_count', 0),
                                    'language': repo_data.get('language', '') or '',
                                    'topics': repo_data.get('topics', []),
                                    'owner': repo_data.get('owner', {}).get('login', ''),
                                    'created_at': repo_data.get('created_at', ''),
                                    'updated_at': repo_data.get('updated_at', ''),
                                    'match_file': item.get('path', ''),
                                    'match_text': pattern,
                                    'score': 0,
                                })
                        if len(data['items']) < int(self.config['results_per_page']):
                            break
                        page += 1

        # Phase 3: README search
        if self.config['search_readme']:
            self._log("[*] Phase 3: Scanning README files...")
            enriched = []
            for r in all_results:
                readme = self.get_repo_readme(r['full_name'])
                if readme:
                    r['readme'] = readme
                    r['readme_pattern_matches'] = []
                    for pat in (patterns or []):
                        if re.search(pat, readme, re.IGNORECASE):
                            r['readme_pattern_matches'].append(pat)
                enriched.append(r)
            all_results = enriched

        # Sort by stars desc
        all_results.sort(key=lambda x: (x.get('stars', 0) or 0), reverse=True)

        self._log(f"[+] Found {len(all_results)} results")
        return all_results[:max_results]

    def search_repo_code_content(self, full_name, patterns):
        matches = []
        contents = self.get_repo_contents(full_name)
        if not isinstance(contents, list):
            contents = [contents] if contents else []

        for item in contents:
            if item.get('type') == 'dir':
                sub = self.search_repo_code_content(f"{full_name}/{item['name']}", patterns)
                matches.extend(sub)
            elif item.get('type') == 'file':
                ext = os.path.splitext(item['name'])[1].lower()
                if ext in (self.config['file_types'] or ['.py', '.js', '.ts']):
                    content = self.get_file_content(full_name, item['path'])
                    for pat in patterns:
                        if re.search(pat, content, re.IGNORECASE):
                            matches.append({
                                'repo': full_name,
                                'file': item['path'],
                                'pattern': pat,
                            })
        return matches

    def get_starred_by(self, repo_full_name, max_pages=5):
        users = []
        for page in range(1, max_pages + 1):
            url = f'https://api.github.com/repos/{repo_full_name}/stargazers'
            data = self._request(url, {'page': page, 'per_page': 100})
            if not data:
                break
            for user in data:
                users.append({
                    'login': user['login'],
                    'id': user['id'],
                    'url': user['html_url'],
                })
            if len(data) < 100:
                break
        return users

    def cleanup(self):
        self.session.close()
