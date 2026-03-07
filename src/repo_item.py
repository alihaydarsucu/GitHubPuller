import gi
gi.require_version("Gtk", "4.0")
from gi.repository import GObject

class RepoItem(GObject.Object):
    """Class holding repository information"""
    __gtype_name__ = "RepoItem"

    def __init__(self, repo_data: dict):
        super().__init__()
        self.data = repo_data
        self.name: str = repo_data["name"]
        self.owner: str = repo_data.get("owner", {}).get("login", "")
        self.private: bool = repo_data.get("private", False)
        self.default_branch: str = repo_data.get("default_branch", "main")
        self.selected: bool = False
        self.branches: list = []
        self.chosen_branch: str = self.default_branch
        self.branches_loaded: bool = False
        self.loading: bool = False
        
        # UI components (will be set by MainWindow)
        self._check_widget = None
        self._branch_combo = None
        self._branch_spinner = None