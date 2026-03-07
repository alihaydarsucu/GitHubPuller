import os
import threading
import subprocess
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio
from .repo_item import RepoItem
from .github_api import fetch_all_repos, fetch_branches
from .config import Config

APP_VERSION = "1.0.0"

class MainWindow(Adw.ApplicationWindow):
    """Ana pencere sınıfı"""
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("GitHub Puller")
        self.set_default_size(780, 680)
        self.set_size_request(540, 400)

        # Yapılandırma
        try:
            self.config = Config()
        except Exception as e:
            print(f"Config hatası: {e}")
            # Fallback değerler
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
        
        # Değişkenler - ilk açıldığında kullanıcı adı boş
        self.username = self.config.username
        self.token_val = self.config.token
        self.target_dir = self.config.target_dir
        self.repo_items: list[RepoItem] = []
        self.pull_running = False
        
        print(f"MainWindow initialized with username: '{self.username}'")
        print(f"Target dir: {self.target_dir}")

        self._build()
        # Sadece kullanıcı adı varsa repoları yükle
        if self.username:
            print(f"Loading repos for user: {self.username}")
            GLib.idle_add(self._load_repos)
        else:
            print("No username set, showing welcome message")

    def _build(self):
        """Arayüz oluştur"""
        print("Building GUI components...")
        
        # Toast overlay (bildirimler için)
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)
        print("✓ Toast overlay created")

        # Ana dikey kutu
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toast_overlay.set_child(root_box)
        print("✓ Root box created")

        # ── Header Bar ──
        header = Adw.HeaderBar()
        header.add_css_class("flat")

        title_widget = Adw.WindowTitle(
            title="GitHub Puller",
            subtitle=f"@{self.username}" if self.username else "Kullanıcı adı belirtilmedi"
        )
        header.set_title_widget(title_widget)
        self.title_widget = title_widget

        # Ayarlar butonu (token için)
        settings_btn = Gtk.Button(icon_name="emblem-system-symbolic")
        settings_btn.set_tooltip_text("Ayarlar")
        settings_btn.connect("clicked", self._show_settings)
        header.pack_end(settings_btn)

        # Yenile butonu
        self.refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        self.refresh_btn.set_tooltip_text("Repoları Yenile")
        self.refresh_btn.connect("clicked", lambda _: self._load_repos())
        header.pack_start(self.refresh_btn)

        root_box.append(header)

        # ── Kullanıcı adı + filtre çubuğu ──
        toolbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar_box.set_margin_start(12)
        toolbar_box.set_margin_end(12)
        toolbar_box.set_margin_top(6)
        toolbar_box.set_margin_bottom(6)

        self.username_entry = Gtk.Entry()
        self.username_entry.set_text(self.username)  # Config'den gelen değer
        self.username_entry.set_placeholder_text("GitHub kullanıcı adı")
        self.username_entry.set_hexpand(True)
        self.username_entry.connect("activate", self._on_username_activate)

        go_btn = Gtk.Button(label="Git")
        go_btn.add_css_class("suggested-action")
        go_btn.connect("clicked", self._on_username_activate)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Repo ara…")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self._on_search)

        toolbar_box.append(self.username_entry)
        toolbar_box.append(go_btn)
        toolbar_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        toolbar_box.append(self.search_entry)
        root_box.append(toolbar_box)
        root_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # ── Seçim toolbar ──
        sel_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sel_bar.set_margin_start(12)
        sel_bar.set_margin_end(12)
        sel_bar.set_margin_top(4)
        sel_bar.set_margin_bottom(4)

        self.sel_label = Gtk.Label(label="0 repo seçili")
        self.sel_label.add_css_class("dim-label")
        self.sel_label.set_hexpand(True)
        self.sel_label.set_xalign(0)

        sel_all_btn = Gtk.Button(label="Tümünü Seç")
        sel_all_btn.add_css_class("flat")
        sel_all_btn.connect("clicked", lambda _: self._select_all(True))

        clear_btn = Gtk.Button(label="Temizle")
        clear_btn.add_css_class("flat")
        clear_btn.connect("clicked", lambda _: self._select_all(False))

        sel_bar.append(self.sel_label)
        sel_bar.append(clear_btn)
        sel_bar.append(sel_all_btn)
        root_box.append(sel_bar)
        root_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # ── Repo listesi ──
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

        # İlk durum için bilgi satırı
        if not self.username:
            info_row = Adw.ActionRow(
                title="Hoş geldiniz!",
                subtitle="Başlamak için yukarıdan GitHub kullanıcı adınızı girin"
            )
            info_row.add_prefix(Gtk.Image(icon_name="system-users-symbolic"))
            self.list_box.append(info_row)

        root_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # ── Alt panel: Hedef dizin + Pull butonu ──
        bottom = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        bottom.set_margin_start(12)
        bottom.set_margin_end(12)
        bottom.set_margin_top(8)
        bottom.set_margin_bottom(12)

        # Hedef dizin satırı - config'den geliyor
        dir_group = Adw.PreferencesGroup(title="Hedef Dizin")
        dir_row = Adw.ActionRow(title=self.target_dir)
        dir_row.set_activatable(True)
        dir_row.set_tooltip_text("Klasör seç")

        dir_icon = Gtk.Image(icon_name="folder-symbolic")
        dir_row.add_prefix(dir_icon)

        browse_btn = Gtk.Button(icon_name="document-open-symbolic")
        browse_btn.set_valign(Gtk.Align.CENTER)
        browse_btn.add_css_class("flat")
        browse_btn.set_tooltip_text("Gözat")
        browse_btn.connect("clicked", self._browse_dir)
        dir_row.add_suffix(browse_btn)
        dir_row.connect("activated", self._browse_dir)

        self.dir_row = dir_row
        dir_group.add(dir_row)
        bottom.append(dir_group)

        # Pull butonu
        self.pull_btn = Gtk.Button(label="Seçilenleri Çek")
        self.pull_btn.add_css_class("suggested-action")
        self.pull_btn.add_css_class("pill")
        self.pull_btn.set_halign(Gtk.Align.CENTER)
        self.pull_btn.set_margin_top(6)
        self.pull_btn.connect("clicked", self._start_pull)

        bottom.append(self.pull_btn)

        # İlerleme çubuğu (gizli başlar)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_visible(False)
        bottom.append(self.progress_bar)

        root_box.append(bottom)
        
        print("✅ GUI build completed successfully!")

    # ── Repo yükleme ──────────────────────────────────────────────────────────

    def _load_repos(self):
        """Repoları yükle"""
        if not self.username:
            self._toast("Lütfen kullanıcı adı girin", error=True)
            return
            
        self._clear_list()
        self.list_box.append(self._make_spinner_row())
        self.refresh_btn.set_sensitive(False)
        self.pull_btn.set_sensitive(False)
        self.repo_items.clear()
        threading.Thread(target=self._fetch_repos_thread, daemon=True).start()

    def _fetch_repos_thread(self):
        """Repoları arka planda getir"""
        try:
            repos = fetch_all_repos(self.username, self.token_val)
            GLib.idle_add(self._on_repos_loaded, repos, None)
        except Exception as e:
            GLib.idle_add(self._on_repos_loaded, None, str(e))

    def _on_repos_loaded(self, repos, error):
        """Repolar yüklendiğinde çalışır"""
        self._clear_list()
        self.refresh_btn.set_sensitive(True)
        self.pull_btn.set_sensitive(True)

        if error:
            err_row = Adw.ActionRow(title="Hata", subtitle=error)
            err_row.add_css_class("error")
            err_icon = Gtk.Image(icon_name="dialog-error-symbolic")
            err_row.add_prefix(err_icon)
            self.list_box.append(err_row)
            self._toast(f"Hata: {error}", error=True)
            return

        if not repos:
            empty_row = Adw.ActionRow(title="Repo bulunamadı")
            empty_row.add_prefix(Gtk.Image(icon_name="folder-symbolic"))
            self.list_box.append(empty_row)
            return

        for r in repos:
            item = RepoItem(r)
            self.repo_items.append(item)
            row = self._make_repo_row(item)
            self.list_box.append(row)

        self._update_sel_label()
        self._toast(f"{len(repos)} repo yüklendi")

    def _make_spinner_row(self):
        """Yükleme spinner'ı oluştur"""
        row = Adw.ActionRow(title="Repolar yükleniyor…")
        sp = Gtk.Spinner()
        sp.start()
        row.add_prefix(sp)
        return row

    def _make_repo_row(self, item: RepoItem) -> Adw.ActionRow:
        """Repo satırı oluştur"""
        row = Adw.ActionRow()
        
        # Repo adı ve sahibi
        if item.owner != self.username:
            # Farklı sahipse owner'i göster
            title = f"{item.owner}/{item.name}"
        else:
            # Kendi reposu ise sadece repo adı
            title = item.name
            
        row.set_title(title)
        
        # Alt yazı: privacy + açıklama
        subtitle_parts = []
        if item.private:
            subtitle_parts.append("🔒 Private")
        else:
            subtitle_parts.append("🌐 Public")
            
        # Eğer farklı sahibi varsa bunu da belirt
        if item.owner != self.username:
            subtitle_parts.append(f"(Sahibi: @{item.owner})")
            
        row.set_subtitle(" ".join(subtitle_parts))

        # Checkbox
        check = Gtk.CheckButton()
        check.set_valign(Gtk.Align.CENTER)
        check.connect("toggled", self._on_check_toggled, item, row)
        row.add_prefix(check)
        item._check_widget = check

        # Branch dropdown (başta gizli)
        branch_combo = Gtk.DropDown()
        branch_combo.set_valign(Gtk.Align.CENTER)
        branch_combo.set_visible(False)
        branch_combo.connect("notify::selected", self._on_branch_changed, item)
        row.add_suffix(branch_combo)
        item._branch_combo = branch_combo

        # Yükleniyor spinner (branch için, gizli)
        branch_spinner = Gtk.Spinner()
        branch_spinner.set_visible(False)
        branch_spinner.set_valign(Gtk.Align.CENTER)
        row.add_suffix(branch_spinner)
        item._branch_spinner = branch_spinner

        row.item = item
        return row

    # ── Etkileşim ─────────────────────────────────────────────────────────────

    def _on_check_toggled(self, check, item: RepoItem, row):
        """Checkbox değiştiğinde çalışır"""
        item.selected = check.get_active()
        if item.selected and not item.branches_loaded and not item.loading:
            self._load_branches(item)
        item._branch_combo.set_visible(item.selected and item.branches_loaded)
        self._update_sel_label()

    def _load_branches(self, item: RepoItem):
        """Branch'leri yükle"""
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
        """Branch'ler yüklendiğinde çalışır"""
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
        """Branch değiştiğinde çalışır"""
        idx = combo.get_selected()
        if item.branches and idx < len(item.branches):
            item.chosen_branch = item.branches[idx]

    def _on_search(self, entry):
        """Arama kutusunda değişiklik olduğunda çalışır"""
        query = entry.get_text().lower()
        row = self.list_box.get_first_child()
        while row:
            if hasattr(row, "item"):
                visible = query in row.item.name.lower()
                row.set_visible(visible)
            row = row.get_next_sibling()

    def _on_username_activate(self, *_):
        """Kullanıcı adı değiştiğinde çalışır"""
        new_username = self.username_entry.get_text().strip()
        if new_username and new_username != self.username:
            self.username = new_username
            self.config.username = new_username  # Config'e kaydet
            self.title_widget.set_subtitle(f"@{self.username}")
            self.repo_items.clear()
            self._load_repos()
        elif not new_username:
            self._toast("Lütfen geçerli bir kullanıcı adı girin", error=True)

    def _select_all(self, val: bool):
        """Tümünü seç/temizle"""
        for item in self.repo_items:
            if item._check_widget.get_visible():
                item._check_widget.set_active(val)
        self._update_sel_label()

    def _update_sel_label(self):
        """Seçili repo sayısını güncelle"""
        n = sum(1 for i in self.repo_items if i.selected)
        self.sel_label.set_label(f"{n} repo seçili")

    def _clear_list(self):
        """Liste içeriğini temizle"""
        while True:
            child = self.list_box.get_first_child()
            if child is None:
                break
            self.list_box.remove(child)

    # ── Dizin seçme ───────────────────────────────────────────────────────────

    def _browse_dir(self, *_):
        """Dizin seçme diyaloğu"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Hedef Dizin Seç")
        dialog.set_initial_folder(Gio.File.new_for_path(self.target_dir))
        dialog.select_folder(self, None, self._on_dir_selected)

    def _on_dir_selected(self, dialog, result):
        """Dizin seçildiğinde çalışır"""
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                self.target_dir = folder.get_path()
                self.config.target_dir = self.target_dir  # Config'e kaydet
                self.dir_row.set_title(self.target_dir)
                self._toast(f"Hedef dizin değiştirildi: {self.target_dir}")
        except Exception:
            pass

    # ── Pull / Clone ──────────────────────────────────────────────────────────

    def _start_pull(self, *_):
        """Pull işlemini başlat"""
        selected = [i for i in self.repo_items if i.selected]
        if not selected:
            self._toast("Lütfen en az bir repo seçin.", error=True)
            return

        self.pull_btn.set_sensitive(False)
        self.pull_btn.set_label("İşleniyor…")
        self.progress_bar.set_visible(True)
        self.progress_bar.set_fraction(0)

        threading.Thread(
            target=self._pull_thread,
            args=(selected,), daemon=True
        ).start()

    def _pull_thread(self, items: list[RepoItem]):
        """Pull işlemini arka planda yap"""
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
                if os.path.isdir(os.path.join(repo_dir, ".git")):
                    self._run(["git", "-C", repo_dir, "fetch", "--all"])
                    self._run(["git", "-C", repo_dir, "checkout", item.chosen_branch])
                    self._run(["git", "-C", repo_dir, "pull", "origin", item.chosen_branch])
                else:
                    self._run(["git", "clone", "-b", item.chosen_branch, url, repo_dir])
                ok += 1
            except Exception as e:
                fail += 1
                GLib.idle_add(self._toast, f"✘ {item.name}: {e}", True)

        GLib.idle_add(self._on_pull_done, ok, fail)

    def _run(self, cmd):
        """Git komutunu çalıştır"""
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip() or f"Kod {r.returncode}")

    def _on_pull_done(self, ok, fail):
        """Pull işlemi bittiğinde çalışır"""
        self.pull_btn.set_sensitive(True)
        self.pull_btn.set_label("Seçilenleri Çek")
        self.progress_bar.set_fraction(1.0)
        GLib.timeout_add(1500, lambda: self.progress_bar.set_visible(False))

        if fail == 0:
            self._toast(f"✓ {ok} repo başarıyla çekildi")
        else:
            self._toast(f"{ok} başarılı, {fail} hatalı", error=True)

    # ── Ayarlar diyaloğu ─────────────────────────────────────────────────────

    def _show_settings(self, *_):
        """Ayarlar diyaloğunu göster"""
        dialog = Adw.PreferencesDialog()
        dialog.set_title("Ayarlar")
        dialog.set_search_enabled(False)

        page = Adw.PreferencesPage(title="Genel", icon_name="preferences-system-symbolic")
        dialog.add(page)

        group = Adw.PreferencesGroup(
            title="GitHub Token",
            description="Private repolara erişmek için kişisel erişim tokeni. "
                        "Settings → Developer settings → Personal access tokens"
        )
        page.add(group)

        token_row = Adw.PasswordEntryRow(title="Token")
        token_row.set_text(self.token_val)
        group.add(token_row)

        about_group = Adw.PreferencesGroup(title="Hakkında")
        page.add(about_group)

        about_row = Adw.ActionRow(
            title="GitHub Puller",
            subtitle=f"Sürüm {APP_VERSION} · alihaydarsucu"
        )
        about_row.add_prefix(Gtk.Image(icon_name="system-software-install-symbolic"))
        about_group.add(about_row)

        dialog.present(self)

        # Token kaydet bağlantısı için kapat sinyali
        def _on_close(*_):
            new_token = token_row.get_text().strip()
            if new_token != self.token_val:
                self.token_val = new_token
                self.config.token = new_token  # Config'e kaydet
                self._toast("Token kaydedildi" if new_token else "Token temizlendi")
        
        dialog.connect("closed", _on_close)

    # ── Toast bildirimi ───────────────────────────────────────────────────────

    def _toast(self, msg: str, error: bool = False):
        """Toast bildirimi göster"""
        toast = Adw.Toast(title=msg)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)