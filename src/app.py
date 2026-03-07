import sys
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio
from .main_window import MainWindow

APP_ID = "io.github.alihaydarsucu.GitHubPuller"

class App(Adw.Application):
    """Ana uygulama sınıfı"""
    def __init__(self):
        super().__init__(application_id=APP_ID,
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.connect("activate", self._on_activate)
        print(f"App initialized with ID: {APP_ID}")

    def _on_activate(self, app):
        print("App activation signal received")
        # Zaten açık pencere var mı kontrol et
        windows = self.get_windows()
        if windows:
            print("Window already exists, bringing to front")
            windows[0].present()
            return
            
        print("Creating new window")
        win = MainWindow(app)
        win.present()
        print("Window presented")

def main():
    """Ana uygulama fonksiyonu"""
    print("Starting GitHub Puller application...")
    app = App()
    exit_status = app.run(sys.argv)
    print(f"Application finished with exit status: {exit_status}")
    return exit_status