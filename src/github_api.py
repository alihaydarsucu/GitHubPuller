import urllib.request
import json

GITHUB_API = "https://api.github.com"

def api_get(path: str, token: str = "") -> list | dict:
    """GitHub API çağrısı yap"""
    url = GITHUB_API + path
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "GithubPuller/1.0.0")
    if token:
        req.add_header("Authorization", f"token {token}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def fetch_all_repos(username: str, token: str = "") -> list:
    """Kullanıcının tüm repolarını getir"""
    page, all_repos = 1, []
    
    # Token varsa authenticated endpoint kullan (private repolar dahil)
    # Token yoksa public endpoint kullan  
    if token:
        # Authenticated user endpoint - private repolar dahil
        endpoint_base = "/user/repos"
    else:
        # Public user endpoint - sadece public repolar
        endpoint_base = f"/users/{username}/repos"
    
    while True:
        data = api_get(f"{endpoint_base}?per_page=100&page={page}", token)
        if not data:
            break
        all_repos.extend(data)
        page += 1
    return sorted(all_repos, key=lambda r: r["name"].lower())

def fetch_branches(username: str, repo: str, token: str = "") -> list:
    """Repo dallarını getir"""
    data = api_get(f"/repos/{username}/{repo}/branches?per_page=100", token)
    return [b["name"] for b in data]
    """Repo dallarını getir"""
    data = api_get(f"/repos/{username}/{repo}/branches?per_page=100", token)
    return [b["name"] for b in data]