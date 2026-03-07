#!/bin/bash

set -e

echo "🚀 GitHub Puller Installation Script"
echo "======================================"

# Root check
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root!"
   echo "   Please run as a normal user."
   exit 1
fi

# Check system dependencies
echo "📦 Checking system dependencies..."

REQUIRED_PACKAGES=(
    "python3-gi"
    "python3-gi-cairo" 
    "gir1.2-gtk-4.0"
    "gir1.2-adw-1"
    "gir1.2-soup-3.0"
    "python3-pip"
    "python3-setuptools"
    "git"
)

MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! dpkg -l "$package" >/dev/null 2>&1; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo "❌ Missing packages detected:"
    printf '   - %s\n' "${MISSING_PACKAGES[@]}"
    echo ""
    echo "📥 To install missing packages, run:"
    echo "   sudo apt update && sudo apt install ${MISSING_PACKAGES[*]}"
    echo ""
    read -p "Install them automatically now? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔧 Installing packages..."
        sudo apt update
        sudo apt install -y "${MISSING_PACKAGES[@]}"
        echo "✅ System dependencies installed!"
    else
        echo "❌ Installation cancelled. Please install required packages first."
        exit 1
    fi
else
    echo "✅ All system dependencies are available!"
fi

echo ""
echo "🔧 Installing GitHub Puller..."

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download and extract release
echo "📥 Downloading GitHub Puller v1.0.4..."
curl -fsSL https://github.com/alihaydarsucu/GitHubPuller/archive/v1.0.4.tar.gz | tar -xz
cd GitHubPuller-1.0.4

# Local installation - bypass system Python policies
pip install --user . --break-system-packages

# Copy desktop file
mkdir -p ~/.local/share/applications
cp io.github.alihaydarsucu.GitHubPuller.desktop ~/.local/share/applications/
chmod +x ~/.local/share/applications/io.github.alihaydarsucu.GitHubPuller.desktop

# Copy icon
mkdir -p ~/.local/share/icons/hicolor/scalable/apps
mkdir -p ~/.local/share/icons/hicolor/{48x48,64x64,128x128}/apps
cp icons/io.github.alihaydarsucu.GitHubPuller.svg ~/.local/share/icons/hicolor/scalable/apps/

# Create PNG versions for better compatibility
if command -v convert >/dev/null 2>&1; then
    convert ~/.local/share/icons/hicolor/scalable/apps/io.github.alihaydarsucu.GitHubPuller.svg -resize 48x48 ~/.local/share/icons/hicolor/48x48/apps/io.github.alihaydarsucu.GitHubPuller.png
    convert ~/.local/share/icons/hicolor/scalable/apps/io.github.alihaydarsucu.GitHubPuller.svg -resize 64x64 ~/.local/share/icons/hicolor/64x64/apps/io.github.alihaydarsucu.GitHubPuller.png
    convert ~/.local/share/icons/hicolor/scalable/apps/io.github.alihaydarsucu.GitHubPuller.svg -resize 128x128 ~/.local/share/icons/hicolor/128x128/apps/io.github.alihaydarsucu.GitHubPuller.png
    echo "✅ PNG icons created for better compatibility"
elif command -v inkscape >/dev/null 2>&1; then
    inkscape ~/.local/share/icons/hicolor/scalable/apps/io.github.alihaydarsucu.GitHubPuller.svg -o ~/.local/share/icons/hicolor/48x48/apps/io.github.alihaydarsucu.GitHubPuller.png -w 48 -h 48
    inkscape ~/.local/share/icons/hicolor/scalable/apps/io.github.alihaydarsucu.GitHubPuller.svg -o ~/.local/share/icons/hicolor/64x64/apps/io.github.alihaydarsucu.GitHubPuller.png -w 64 -h 64
    inkscape ~/.local/share/icons/hicolor/scalable/apps/io.github.alihaydarsucu.GitHubPuller.svg -o ~/.local/share/icons/hicolor/128x128/apps/io.github.alihaydarsucu.GitHubPuller.png -w 128 -h 128
    echo "✅ PNG icons created with Inkscape"
else
    echo "ℹ️ SVG icon installed (ImageMagick or Inkscape recommended for PNG conversion)"
fi

# Copy metainfo file
mkdir -p ~/.local/share/metainfo
cp io.github.alihaydarsucu.GitHubPuller.metainfo.xml ~/.local/share/metainfo/

# Cleanup temporary directory
cd ..
rm -rf "$TEMP_DIR"

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database ~/.local/share/applications 2>/dev/null || true
fi

# Update icon cache (try multiple methods)
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f ~/.local/share/icons/hicolor 2>/dev/null || true
fi

if command -v gtk4-update-icon-cache >/dev/null 2>&1; then
    gtk4-update-icon-cache -f ~/.local/share/icons/hicolor 2>/dev/null || true
fi

# Update XDG mime database
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database ~/.local/share/mime 2>/dev/null || true
fi

# Refresh GNOME desktop integration
echo "🔄 Refreshing desktop integration..."
if [ "$XDG_CURRENT_DESKTOP" = "GNOME" ]; then
    echo "💡 For immediate icon appearance in GNOME:"
    echo "   - Press Alt+F2, type 'r' and press Enter (refresh shell)"
    echo "   - Or logout and login again"
    echo "   - Or wait a few minutes for automatic refresh"
fi

# Add ~/.local/bin to PATH if not already present
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "✅ Added ~/.local/bin to PATH"
    echo "💡 Run 'source ~/.bashrc' or restart terminal to use 'github-puller' command"
fi

echo ""
echo "🎉 Installation completed!"
echo ""
echo "📍 You can launch the application:"
echo "   • From application menu: 'GitHub Puller'"
echo "   • Terminal: github-puller"
echo "   • Alt+F2: github-puller"
echo ""
echo "🔧 To uninstall: pip uninstall github-puller"
echo "📚 More info: https://github.com/alihaydarsucu/GitHubPuller"