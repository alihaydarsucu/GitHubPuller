<div align="center">

![GitHub Puller](/icons/github-puller.svg) 

# GitHub Puller

Modern GTK4 + libadwaita application for batch pulling GitHub repositories.

![Made with](https://skillicons.dev/icons?i=python,gtk,linux,git,github)
</div>

## Features

- 🚀 **Modern Interface**: Built with GTK4 and libadwaita
- 🔍 **Easy Search**: Find your repositories easily
- 🌿 **Branch Selection**: Choose different branch for each repository  
- 🔒 **Private Repo Support**: Access your private repositories with GitHub token
- 💾 **Smart Update**: Existing repositories are updated, new ones are cloned
- ⚡ **Multi-Threading**: Process multiple repositories simultaneously
- 🎯 **Target Directory**: Select and save download directory

> **Why not GitHub Desktop?** Unlike GitHub Desktop which focuses on single-repo management, GitHub Puller lets you batch clone/pull dozens of repositories at once with branch selection and smart filtering.

<details>
<summary>📷 Click to see application screenshot</summary>

![GitHub Puller Screenshot](https://raw.githubusercontent.com/alihaydarsucu/GitHubPuller/main/screenshots/main.png)

*Modern GTK4 + libadwaita interface showing repository list with batch selection*

</details>

## Installation

### 🚀 Recommended Installation

**One-line install (easiest):**
```bash
curl -fsSL https://raw.githubusercontent.com/alihaydarsucu/GitHubPuller/main/install.sh | bash
```

### 📦 Alternative Methods

<details>
<summary>Click to expand other installation options</summary>

**Coming soon on Flathub:**
```bash
flatpak install flathub io.github.alihaydarsucu.GitHubPuller
```

**Manual installation:**
```bash
# 1. Install dependencies (Ubuntu/Debian)
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 python3-pip git

# 2. Clone and install
git clone https://github.com/alihaydarsucu/GitHubPuller.git
cd GitHubPuller
./install.sh
```

**For developers:**
```bash
git clone https://github.com/alihaydarsucu/GitHubPuller.git
cd GitHubPuller
make dev
```

</details>

## Usage

1. Launch the application: `github-puller`
2. Enter your GitHub username
3. Add GitHub token from Settings for private repositories
4. Select desired repositories
5. Set target directory (default: ~/Desktop/Projects)
6. Click "Pull Selected" button

## GitHub Token

To access your private repositories:
1. GitHub → Settings → Developer settings → Personal access tokens
2. Create new token with "Generate new token"  
3. Grant `repo` permission
4. Paste it in Application Settings → Token section

## Development

```bash
git clone https://github.com/alihaydarsucu/GitHubPuller.git
cd GitHubPuller
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Contributing

Pull requests are welcome! For major changes, please open an issue first.

## License

MIT - See `LICENSE` file for details.