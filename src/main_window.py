import os
import threading
import subprocess
import shutil
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio
from .repo_item import RepoItem
from .github_api import fetch_all_repos, fetch_branches
from .config import Config

APP_VERSION = "1.0.0"

class MainWindow(Adw.ApplicationWindow):
    """Main window class"""
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("GitHub Puller")
        self.set_default_size(780, 680)
        self.set_size_request(540, 400)

        # Configuration
        try:
            self.config = Config()
        except Exception as e:
            print(f"Config error: {e}")
            # Fallback values
            class FallbackConfig:
                def __init__(self):
                    self.data = {"username": "", "token": "", "target_dir": os.path.expanduser("~/Desktop/Projects")}
                def get(self, key, default=""): return self.data.get(key, default)
                def set(self, key, value): pass
                @property
                def username(self): return self.data.get("username", "")
                @username.setter 
                def username(self, value): pass
                @property
                def token(self): return self.data.get("token", "")
                @token.setter
                def token(self, value): pass
                @property
                def target_dir(self): return self.data.get("target_dir", os.path.expanduser("~/Desktop/Projects"))
                @target_dir.setter
                def target_dir(self, value): pass
            self.config = FallbackConfig()
        
        # Variables - username empty on first open
        self.username = self.config.username
        self.token_val = self.config.token
        self.target_dir = self.config.target_dir
        self.repo_items: list[RepoItem] = []
        self.pull_running = False
        self.show_public = True
        self.show_private = True
        
        print(f"MainWindow initialized with username: '{self.username}'")
        print(f"Target dir: {self.target_dir}")

        self._build()
        # Only load repos if username exists
        if self.username:
            print(f"Loading repos for user: {self.username}")
            GLib.idle_add(self._load_repos)
        else:
            print("No username set, showing welcome message")

    def _build(self):
        """Create interface"""
        print("Building GUI components...")
        
        # Toast overlay (for notifications)
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)
        print("✓ Toast overlay created")

        # Main vertical box
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toast_overlay.set_child(root_box)
        print("✓ Root box created")

        # ── Header Bar ──
        header = Adw.HeaderBar()
        header.add_css_class("flat")

        title_widget = Adw.WindowTitle(
            title="GitHub Puller",
            subtitle=f"@{self.username}" if self.username else "No username specified"
        )
        header.set_title_widget(title_widget)
        self.title_widget = title_widget

        # Settings button (for token)
        settings_btn = Gtk.Button(icon_name="emblem-system-symbolic")
        settings_btn.set_tooltip_text("Ayarlar")
        settings_btn.connect("clicked", self._show_settings)
        header.pack_end(settings_btn)

        # Refresh button
        self.refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        self.refresh_btn.set_tooltip_text("Refresh Repositories")
        self.refresh_btn.connect("clicked", lambda _: self._load_repos())
        header.pack_start(self.refresh_btn)

        root_box.append(header)

        # ── Username + filter bar ──
        toolbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar_box.set_margin_start(12)
        toolbar_box.set_margin_end(12)
        toolbar_box.set_margin_top(6)
        toolbar_box.set_margin_bottom(6)

        self.username_entry = Gtk.Entry()
        self.username_entry.set_text(self.username)  # Value from config
        self.username_entry.set_placeholder_text("GitHub username")
        self.username_entry.set_hexpand(True)
        self.username_entry.connect("activate", self._on_username_activate)

        go_btn = Gtk.Button(label="Load")
        go_btn.add_css_class("suggested-action")
        go_btn.connect("clicked", self._on_username_activate)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search repositories…")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self._on_search)

        toolbar_box.append(self.username_entry)
        toolbar_box.append(go_btn)
        toolbar_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        toolbar_box.append(self.search_entry)
        root_box.append(toolbar_box)
        root_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # ── Selection toolbar ──
        sel_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sel_bar.set_margin_start(12)
        sel_bar.set_margin_end(12)
        sel_bar.set_margin_top(4)
        sel_bar.set_margin_bottom(4)

        self.sel_label = Gtk.Label(label="0 repos selected")
        self.sel_label.add_css_class("dim-label")
        self.sel_label.set_hexpand(True)
        self.sel_label.set_xalign(0)

        # Public/Private filter toggles
        public_btn = Gtk.ToggleButton(label="Public")
        public_btn.set_active(True)
        public_btn.add_css_class("flat")
        public_btn.connect("toggled", self._on_public_filter_changed)
        
        private_btn = Gtk.ToggleButton(label="Private")
        private_btn.set_active(True)
        private_btn.add_css_class("flat")
        private_btn.connect("toggled", self._on_private_filter_changed)

        sel_all_btn = Gtk.Button(label="Select All")
        sel_all_btn.add_css_class("flat")
        sel_all_btn.connect("clicked", lambda _: self._select_all(True))

        clear_btn = Gtk.Button(label="Clear")
        clear_btn.add_css_class("flat")
        clear_btn.connect("clicked", lambda _: self._select_all(False))

        sel_bar.append(self.sel_label)
        sel_bar.append(public_btn)
        sel_bar.append(private_btn)
        sel_bar.append(clear_btn)
        sel_bar.append(sel_all_btn)
        root_box.append(sel_bar)
        root_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # ── Repository list ──
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.add_css_class("boxed-list")
        self.list_box.set_margin_start(12)
        self.list_box.set_margin_end(12)
        self.list_box.set_margin_top(8)
        self.list_box.set_margin_bottom(8)

        scrolled.set_child(self.list_box)
        root_box.append(scrolled)

        # First state info row
        if not self.username:
            info_row = Adw.ActionRow(
                title="Welcome!",
                subtitle="Enter your GitHub username above to get started"
            )
            info_row.add_prefix(Gtk.Image(icon_name="system-users-symbolic"))
            self.list_box.append(info_row)

        root_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # ── Bottom panel: Target directory + Pull button ──
        bottom = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        bottom.set_margin_start(12)
        bottom.set_margin_end(12)
        bottom.set_margin_top(8)
        bottom.set_margin_bottom(12)

        # Target directory row - from config
        dir_group = Adw.PreferencesGroup(title="Target Directory")
        dir_row = Adw.ActionRow(title=self.target_dir)
        dir_row.set_activatable(True)
        dir_row.set_tooltip_text("Select folder")

        dir_icon = Gtk.Image(icon_name="folder-symbolic")
        dir_row.add_prefix(dir_icon)

        browse_btn = Gtk.Button(icon_name="document-open-symbolic")
        browse_btn.set_valign(Gtk.Align.CENTER)
        browse_btn.add_css_class("flat")
        browse_btn.set_tooltip_text("Browse")
        browse_btn.connect("clicked", self._browse_dir)
        dir_row.add_suffix(browse_btn)
        dir_row.connect("activated", self._browse_dir)

        self.dir_row = dir_row
        dir_group.add(dir_row)
        bottom.append(dir_group)

        # Pull button
        self.pull_btn = Gtk.Button(label="Pull Selected")
        self.pull_btn.add_css_class("suggested-action")
        self.pull_btn.add_css_class("pill")
        self.pull_btn.set_halign(Gtk.Align.CENTER)
        self.pull_btn.set_margin_top(6)
        self.pull_btn.connect("clicked", self._start_pull)

        bottom.append(self.pull_btn)

        # Progress bar (hidden initially)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_visible(False)
        bottom.append(self.progress_bar)

        root_box.append(bottom)
        
        print("✅ GUI build completed successfully!")

    # ── Repository loading ────────────────────────────────────────────────────────

    def _load_repos(self):
        """Load repositories"""
        if not self.username:
            self._toast("Please enter a username", error=True)
            return
            
        self._clear_list()
        self.list_box.append(self._make_spinner_row())
        self.refresh_btn.set_sensitive(False)
        self.pull_btn.set_sensitive(False)
        self.repo_items.clear()
        threading.Thread(target=self._fetch_repos_thread, daemon=True).start()

    def _fetch_repos_thread(self):
        """Fetch repositories in background"""
        try:
            repos = fetch_all_repos(self.username, self.token_val)
            GLib.idle_add(self._on_repos_loaded, repos, None)
        except Exception as e:
            GLib.idle_add(self._on_repos_loaded, None, str(e))

    def _on_repos_loaded(self, repos, error):
        """Called when repositories are loaded"""
        self._clear_list()
        self.refresh_btn.set_sensitive(True)
        self.pull_btn.set_sensitive(True)

        if error:
            err_row = Adw.ActionRow(title="Error", subtitle=error)
            err_row.add_css_class("error")
            err_icon = Gtk.Image(icon_name="dialog-error-symbolic")
            err_row.add_prefix(err_icon)
            self.list_box.append(err_row)
            self._toast(f"Error: {error}", error=True)
            return

        if not repos:
            empty_row = Adw.ActionRow(title="No repositories found")
            empty_row.add_prefix(Gtk.Image(icon_name="folder-symbolic"))
            self.list_box.append(empty_row)
            return

        for r in repos:
            item = RepoItem(r)
            self.repo_items.append(item)
            row = self._make_repo_row(item)
            self.list_box.append(row)

        self._update_sel_label()
        self._toast(f"{len(repos)} repositories loaded")
        
        # Apply current filters to newly loaded repositories
        self._apply_filters()

    def _make_spinner_row(self):
        """Create loading spinner"""
        row = Adw.ActionRow(title="Loading repositories…")
        sp = Gtk.Spinner()
        sp.start()
        row.add_prefix(sp)
        return row

    def _make_repo_row(self, item: RepoItem) -> Adw.ActionRow:
        """Create repository row"""
        row = Adw.ActionRow()
        
        # Repo name and owner
        if item.owner != self.username:
            # Show owner if different
            title = f"{item.owner}/{item.name}"
        else:
            # Just repo name if own repo
            title = item.name
            
        row.set_title(title)
        
        # Subtitle: privacy + description
        subtitle_parts = []
        if item.private:
            subtitle_parts.append("🔒 Private")
        else:
            subtitle_parts.append("🌐 Public")
            
        # If different owner, also specify this
        if item.owner != self.username:
            subtitle_parts.append(f"(Sahibi: @{item.owner})")
            
        row.set_subtitle(" ".join(subtitle_parts))

        # Checkbox
        check = Gtk.CheckButton()
        check.set_valign(Gtk.Align.CENTER)
        check.connect("toggled", self._on_check_toggled, item, row)
        row.add_prefix(check)
        item._check_widget = check

        # Branch dropdown (hidden initially)
        branch_combo = Gtk.DropDown()
        branch_combo.set_valign(Gtk.Align.CENTER)
        branch_combo.set_visible(False)
        branch_combo.connect("notify::selected", self._on_branch_changed, item)
        row.add_suffix(branch_combo)
        item._branch_combo = branch_combo

        # Loading spinner (for branch, hidden)
        branch_spinner = Gtk.Spinner()
        branch_spinner.set_visible(False)
        branch_spinner.set_valign(Gtk.Align.CENTER)
        row.add_suffix(branch_spinner)
        item._branch_spinner = branch_spinner

        row.item = item
        return row

    # ── Interaction ───────────────────────────────────────────────────────────────

    def _on_check_toggled(self, check, item: RepoItem, row):
        """Called when checkbox changes"""
        item.selected = check.get_active()
        if item.selected and not item.branches_loaded and not item.loading:
            self._load_branches(item)
        item._branch_combo.set_visible(item.selected and item.branches_loaded)
        self._update_sel_label()

    def _load_branches(self, item: RepoItem):
        """Load branches"""
        item.loading = True
        item._branch_spinner.start()
        item._branch_spinner.set_visible(True)
        threading.Thread(
            target=self._fetch_branches_thread,
            args=(item,), daemon=True
        ).start()

    def _fetch_branches_thread(self, item: RepoItem):
        """Branch'leri arka planda getir"""
        try:
            branches = fetch_branches(item.owner, item.name, self.token_val)
            GLib.idle_add(self._on_branches_loaded, item, branches, None)
        except Exception as e:
            GLib.idle_add(self._on_branches_loaded, item, None, str(e))

    def _on_branches_loaded(self, item: RepoItem, branches, error):
        """Called when branches are loaded"""
        item.loading = False
        item._branch_spinner.stop()
        item._branch_spinner.set_visible(False)

        if error or not branches:
            item.branches = [item.default_branch]
        else:
            item.branches = branches

        item.branches_loaded = True
        item.chosen_branch = (item.default_branch if item.default_branch in item.branches
                              else item.branches[0])

        string_list = Gtk.StringList()
        for b in item.branches:
            string_list.append(b)
        item._branch_combo.set_model(string_list)

        idx = item.branches.index(item.chosen_branch) if item.chosen_branch in item.branches else 0
        item._branch_combo.set_selected(idx)
        item._branch_combo.set_visible(item.selected)

    def _on_branch_changed(self, combo, _param, item: RepoItem):
        """Called when branch changes"""
        idx = combo.get_selected()
        if item.branches and idx < len(item.branches):
            item.chosen_branch = item.branches[idx]

    def _on_search(self, entry):
        """Called when search box changes"""
        self._apply_filters()

    def _on_public_filter_changed(self, button):
        """Called when public filter changes"""
        self.show_public = button.get_active()
        self._apply_filters()

    def _on_private_filter_changed(self, button):
        """Called when private filter changes"""  
        self.show_private = button.get_active()
        self._apply_filters()

    def _apply_filters(self):
        """Apply search and public/private filters"""
        query = self.search_entry.get_text().lower()
        row = self.list_box.get_first_child()
        while row:
            if hasattr(row, "item"):
                # Check search filter
                search_match = query in row.item.name.lower()
                
                # Check public/private filter  
                type_match = True
                if row.item.private and not self.show_private:
                    type_match = False
                elif not row.item.private and not self.show_public:
                    type_match = False
                
                visible = search_match and type_match
                row.set_visible(visible)
            row = row.get_next_sibling()

    def _on_username_activate(self, *_):
        """Called when username changes"""
        new_username = self.username_entry.get_text().strip()
        if new_username and new_username != self.username:
            self.username = new_username
            self.config.username = new_username  # Save to config
            self.title_widget.set_subtitle(f"@{self.username}")
            self.repo_items.clear()
            self._load_repos()
        elif not new_username:
            self._toast("Please enter a valid username", error=True)

    def _select_all(self, val: bool):
        """Select all/clear all"""
        for item in self.repo_items:
            if item._check_widget.get_visible():
                item._check_widget.set_active(val)
        self._update_sel_label()

    def _update_sel_label(self):
        """Update selected repository count"""
        n = sum(1 for i in self.repo_items if i.selected)
        self.sel_label.set_label(f"{n} repos selected")

    def _clear_list(self):
        """Clear list content"""
        while True:
            child = self.list_box.get_first_child()
            if child is None:
                break
            self.list_box.remove(child)

    # ── Directory selection ────────────────────────────────────────────────────────────

    def _browse_dir(self, *_):
        """Directory selection dialog"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Select Target Directory")
        dialog.set_initial_folder(Gio.File.new_for_path(self.target_dir))
        dialog.select_folder(self, None, self._on_dir_selected)

    def _on_dir_selected(self, dialog, result):
        """Called when directory is selected"""
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                self.target_dir = folder.get_path()
                self.config.target_dir = self.target_dir  # Save to config
                self.dir_row.set_title(self.target_dir)
                self._toast(f"Target directory changed: {self.target_dir}")
        except Exception:
            pass

    # ── Pull / Clone ──────────────────────────────────────────────────────────

    def _start_pull(self, *_):
        """Start pull operation"""
        selected = [i for i in self.repo_items if i.selected]
        if not selected:
            self._toast("Please select at least one repository.", error=True)
            return

        self.pull_btn.set_sensitive(False)
        self.pull_btn.set_label("Processing…")
        self.progress_bar.set_visible(True)
        self.progress_bar.set_fraction(0)

        threading.Thread(
            target=self._pull_thread,
            args=(selected,), daemon=True
        ).start()

    def _pull_thread(self, items: list[RepoItem]):
        """Perform pull operation in background"""
        total = len(items)
        ok = fail = 0

        for i, item in enumerate(items):
            GLib.idle_add(
                self.progress_bar.set_text,
                f"{item.name}:{item.chosen_branch} ({i+1}/{total})"
            )
            GLib.idle_add(self.progress_bar.set_fraction, i / total)

            token = self.token_val
            if token:
                url = f"https://{token}@github.com/{item.owner}/{item.name}.git"
            else:
                url = f"https://github.com/{item.owner}/{item.name}.git"

            repo_dir = os.path.join(self.target_dir, item.name)
            os.makedirs(self.target_dir, exist_ok=True)

            try:
                git_cmd = self._get_git_executable()
                if os.path.isdir(os.path.join(repo_dir, ".git")):
                    self._run([git_cmd, "-C", repo_dir, "fetch", "--all"])
                    self._run([git_cmd, "-C", repo_dir, "checkout", item.chosen_branch])
                    self._run([git_cmd, "-C", repo_dir, "pull", "origin", item.chosen_branch])
                else:
                    self._run([git_cmd, "clone", "-b", item.chosen_branch, url, repo_dir])
                ok += 1
            except Exception as e:
                fail += 1
                GLib.idle_add(self._toast, f"✘ {item.name}: {e}", True)

        GLib.idle_add(self._on_pull_done, ok, fail)

    def _get_git_executable(self):
        """Find git executable path"""
        git_path = shutil.which("git")
        if not git_path:
            raise RuntimeError("Git not found in PATH. Please install git.")
        return git_path

    def _run(self, cmd):
        """Execute git command"""
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip() or f"Kod {r.returncode}")

    def _on_pull_done(self, ok, fail):
        """Called when pull operation completes"""
        self.pull_btn.set_sensitive(True)
        self.pull_btn.set_label("Pull Selected")
        self.progress_bar.set_fraction(1.0)
        GLib.timeout_add(1500, lambda: self.progress_bar.set_visible(False))

        if fail == 0:
            self._toast(f"✓ {ok} repositories pulled successfully")
        else:
            self._toast(f"{ok} successful, {fail} failed", error=True)

    # ── Settings dialog ─────────────────────────────────────────────────────

    def _show_settings(self, *_):
        """Show settings dialog"""
        dialog = Adw.PreferencesDialog()
        dialog.set_title("Settings")
        dialog.set_search_enabled(False)

        page = Adw.PreferencesPage(title="General", icon_name="preferences-system-symbolic")
        dialog.add(page)

        group = Adw.PreferencesGroup(
            title="GitHub Token",
            description="Personal access token to access private repositories. "
                        "Settings → Developer settings → Personal access tokens"
        )
        page.add(group)

        token_row = Adw.PasswordEntryRow(title="Token")
        token_row.set_text(self.token_val)
        group.add(token_row)

        about_group = Adw.PreferencesGroup(title="About")
        page.add(about_group)

        about_row = Adw.ActionRow(
            title="GitHub Puller",
            subtitle=f"Version {APP_VERSION} · alihaydarsucu"
        )
        about_row.add_prefix(Gtk.Image(icon_name="system-software-install-symbolic"))
        about_group.add(about_row)

        dialog.present(self)

        # Connection to save token on close signal
        def _on_close(*_):
            new_token = token_row.get_text().strip()
            if new_token != self.token_val:
                self.token_val = new_token
                self.config.token = new_token  # Save to config
                self._toast("Token saved" if new_token else "Token cleared")
        
        dialog.connect("closed", _on_close)

    # ── Toast bildirimi ───────────────────────────────────────────────────────

    def _toast(self, msg: str, error: bool = False):
        """Toast bildirimi göster"""
        toast = Adw.Toast(title=msg)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)