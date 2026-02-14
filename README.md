# ⚡ Boltdown

<div align="center">

![Django](https://img.shields.io/badge/Django-5.1-green.svg)
![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![aria2](https://img.shields.io/badge/aria2-1.37-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Lightning-fast web-based torrent downloader powered by Django and aria2c**

*Download torrents and magnet links at blazing speeds through a beautiful, modern web interface. Built with Python Django and aria2c - the world's fastest download utility. No complicated setup, no external dependencies, just pure downloading power.*

[Features](#-features) • [Quick Start](#-quick-start) • [Installation](#installation) • [Usage](#-usage) • [Screenshots](#-demo)

</div>

---

## 📖 About Boltdown

**Boltdown** is a high-performance, open-source torrent downloader that brings the power of aria2c to your browser. Built with Django and Python, it offers a sleek web interface for managing torrent downloads with real-time progress tracking, multi-threaded connections, and full magnet link support.

### Why Boltdown?

- **Zero Configuration** - Works out of the box with minimal setup
- **Cross-Platform** - Run on Windows, Linux, or macOS
- **Production Ready** - Secure, tested, and ready for deployment
- **Open Source** - MIT licensed, free forever

---

## ✨ Features

- ⚡ **High-Speed Downloads** - Powered by aria2c with 16 parallel connections
- 📊 **Real-Time Progress** - Live speed tracking, progress bars, and ETA  
- 🧲 **Magnet Link Support** - Full DHT support for trackerless torrents
- 📁 **Multi-File Torrents** - Handle complex torrent structures
- ⏸️ **Pause/Resume** - Full control over your downloads
- 🔒 **Secure** - Environment-based configuration, no hardcoded secrets
- 🐳 **Docker Ready** - Easy deployment (coming soon)


## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- aria2c (download engine)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/mohammadameenbarech/boltdown.git
   cd boltdown
   ```

2. **Download aria2c**
   - Windows: [aria2 releases](https://github.com/aria2/aria2/releases)
   - Extract `aria2c.exe` to project root
   - OR add to PATH

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your SECRET_KEY

5. **Database Setup**
   ```bash
   python manage.py migrate
   ```

6. **Run the Server**
   ```bash
   python manage.py runserver
   ```

7. **Open in Browser**
   ```
   http://127.0.0.1:8000
   ```

## 📖 Usage

### Adding Torrents

**Method 1: Torrent File**
1. Click **"+ Add Torrent"**
2. Drag & drop or select `.torrent` file
3. Click **"Start Download"**

**Method 2: Magnet Link**
1. Click **"+ Add Torrent"**
2. Paste magnet link
3. Click **"Start Download"**

### Managing Downloads

- **Pause**: Click ⏸️ icon
- **Resume**: Click ▶️ icon
- **Delete**: Click 🗑️ icon

Downloaded files are saved to `downloads/` directory.

## ⚙️ Configuration

### Environment Variables

Edit `.env` file:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# aria2c Settings
ARIA2_SECRET=your-aria2-rpc-secret
```

### aria2c Options

Customize download behavior in `downloader/services.py`:

```python
aria2_cmd = [
    "aria2c",
    "--enable-rpc",
    "--max-connection-per-server=16",  # Connections per file
    "--split=16",                       # Parallel chunks
    "--bt-max-peers=50",               # Max peer connections
]
```

For all options: [aria2c documentation](https://aria2.github.io/manual/en/html/aria2c.html#options)

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│   Django Web Interface          │
│   (Premium Glassmorphism UI)    │
└──────────────┬──────────────────┘
               │ JSON-RPC
┌──────────────▼──────────────────┐
│      aria2c RPC Server           │
│   (BitTorrent Engine)           │
│                                 │
│  • Connects to peers/trackers   │
│  • Downloads & verifies pieces  │
│  • Writes files to disk         │
│  • Handles DHT, PEX, encryption │
└─────────────────────────────────┘
```

## 📁 Project Structure

```
boltdown/
├── downloader/              # Main Django app
│   ├── models.py           # TorrentTask model
│   ├── services.py         # aria2c RPC integration
│   ├── views.py            # API endpoints
│   └── templates/          # HTML templates
├── static/                 # CSS, JavaScript, assets
│   ├── css/styles.css     # Glassmorphism styles
│   └── js/main.js         # AJAX updates
├── torrent_web/           # Django project settings
├── downloads/             # Downloaded files (created automatically)
├── requirements.txt       # Python dependencies
└── manage.py
```

## 🔒 Security

- ✅ Environment-based configuration
- ✅ No hardcoded secrets
- ✅ CSRF protection enabled
- ✅ Secure headers configured
- ✅ Debug mode disabled in production
- ✅ `.gitignore` excludes sensitive files

**Important**: Always change the default SECRET_KEY and ARIA2_SECRET in production!

## 🐛 Troubleshooting

### "aria2c not found"
- Ensure `aria2c.exe` is in project root or system PATH
- Test: `aria2c --version`

### Downloads not starting
- Check console for "aria2c RPC server started"
- Verify aria2c process is running
- Try different torrent with more seeders

### Slow downloads
- Normal for unpopular torrents (few seeders)
- Increase `--bt-max-peers` in services.py
- Check firewall settings

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [aria2](https://aria2.github.io/) - The powerhouse behind Boltdown's speed
- [Django](https://www.djangoproject.com/) - The web framework for perfectionists
- [Font Awesome](https://fontawesome.com/) - Beautiful icons

## 🌟 Support Boltdown

If you find **Boltdown** useful, please give it a ⭐ star on GitHub! It helps others discover this project.


---

<div align="center">

**Made with ⚡ by the Boltdown Team**

[Report Bug](https://github.com/yourusername/boltdown/issues) • [Request Feature](https://github.com/yourusername/boltdown/issues) • [Documentation](https://github.com/yourusername/boltdown/wiki)

</div>
