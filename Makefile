# GitHub Puller Makefile

.PHONY: help install install-sys install-venv uninstall clean run run-debug dev check-deps

help:
	@echo "GitHub Puller - Makefile Commands"
	@echo "================================"
	@echo ""
	@echo "🚀 Installation:"
	@echo "  make install     - Install application (user space)"
	@echo "  make install-sys - System-wide installation (requires sudo)"
	@echo "  make install-venv - Safe installation with virtual environment"
	@echo ""
	@echo "🧪 Development:"
	@echo "  make dev         - Prepare development environment"
	@echo "  make run         - Run the application"
	@echo "  make run-debug   - Run in debug mode"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean       - Clean temporary files"
	@echo "  make uninstall   - Remove application"

# Installation
install:
	@echo "🔧 Installing GitHub Puller (user space)..."
	pip install --user .
	@mkdir -p ~/.local/share/applications
	@cp github-puller.desktop ~/.local/share/applications/
	@chmod +x ~/.local/share/applications/github-puller.desktop
	@mkdir -p ~/.local/share/icons/hicolor/scalable/apps
	@cp icons/github-puller.svg ~/.local/share/icons/hicolor/scalable/apps/
	@mkdir -p ~/.local/share/metainfo
	@cp github-puller.metainfo.xml ~/.local/share/metainfo/
	@update-desktop-database ~/.local/share/applications 2>/dev/null || true
	@gtk-update-icon-cache -f ~/.local/share/icons/hicolor 2>/dev/null || true
	@echo "✅ Installation completed!"

install-sys:
	@echo "🔧 Installing GitHub Puller (system-wide)..."
	sudo pip install .
	@sudo mkdir -p /usr/share/applications
	@sudo cp github-puller.desktop /usr/share/applications/
	@sudo chmod +x /usr/share/applications/github-puller.desktop
	@sudo mkdir -p /usr/share/icons/hicolor/scalable/apps
	@sudo cp icons/github-puller.svg /usr/share/icons/hicolor/scalable/apps/
	@sudo mkdir -p /usr/share/metainfo
	@sudo cp github-puller.metainfo.xml /usr/share/metainfo/
	@sudo update-desktop-database /usr/share/applications 2>/dev/null || true
	@sudo gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
	@echo "✅ System installation completed!"

# Safe installation with virtual environment
install-venv:
	@echo "🔧 Installing GitHub Puller (with venv)..."
	@echo "📦 Creating virtual environment..."
	python3 -m venv --system-site-packages ~/.local/share/github-puller-venv
	@echo "📦 Installing package..."
	~/.local/share/github-puller-venv/bin/pip install .
	@mkdir -p ~/.local/bin
	@echo '#!/bin/bash' > ~/.local/bin/github-puller
	@echo 'exec ~/.local/share/github-puller-venv/bin/python3 -m src.app' >> ~/.local/bin/github-puller
	@chmod +x ~/.local/bin/github-puller
	@mkdir -p ~/.local/share/applications
	@cp github-puller.desktop ~/.local/share/applications/
	@chmod +x ~/.local/share/applications/github-puller.desktop
	@mkdir -p ~/.local/share/icons/hicolor/scalable/apps
	@cp icons/github-puller.svg ~/.local/share/icons/hicolor/scalable/apps/
	@mkdir -p ~/.local/share/metainfo
	@cp github-puller.metainfo.xml ~/.local/share/metainfo/
	@update-desktop-database ~/.local/share/applications 2>/dev/null || true
	@gtk-update-icon-cache -f ~/.local/share/icons/hicolor 2>/dev/null || true
	@echo "✅ Virtual environment installation completed!"
	@echo "💡 Make sure ~/.local/bin is in your PATH"

# Uninstallation
uninstall:
	@echo "🗑️  Removing GitHub Puller..."
	pip uninstall -y github-puller --break-system-packages || true
	@rm -f ~/.local/share/applications/github-puller.desktop
	@rm -f ~/.local/share/icons/hicolor/scalable/apps/github-puller.svg
	@rm -f ~/.local/share/metainfo/github-puller.metainfo.xml
	@rm -f ~/.local/bin/github-puller
	@rm -rf ~/.local/share/github-puller-venv
	@update-desktop-database ~/.local/share/applications 2>/dev/null || true
	@gtk-update-icon-cache -f ~/.local/share/icons/hicolor 2>/dev/null || true
	@echo "✅ GitHub Puller removed!"

# Development
dev:
	@echo "🧪 Preparing development environment..."
	pip install --user -e . --break-system-packages
	@echo "✅ Development environment ready!"

run:
	@echo "🚀 Starting GitHub Puller..."
	python3 main.py

run-debug:
	@echo "🐛 Starting GitHub Puller in debug mode..."
	G_MESSAGES_DEBUG=all python3 main.py

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@rm -rf __pycache__/
	@rm -rf src/__pycache__/
	@rm -rf .pytest_cache/
	@rm -rf build-dir/
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete
	@echo "✅ Cleanup completed!"

# Check dependencies
check-deps:
	@echo "📋 Checking system dependencies..."
	@command -v python3 >/dev/null 2>&1 || { echo "❌ python3 not found!"; exit 1; }
	@python3 -c "import gi" 2>/dev/null || { echo "❌ python3-gi not found!"; exit 1; }
	@python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk" 2>/dev/null || { echo "❌ GTK4 not found!"; exit 1; }
	@python3 -c "import gi; gi.require_version('Adw', '1'); from gi.repository import Adw" 2>/dev/null || { echo "❌ libadwaita not found!"; exit 1; }
	@command -v git >/dev/null 2>&1 || { echo "❌ git not found!"; exit 1; }
	@echo "✅ All dependencies are available!"