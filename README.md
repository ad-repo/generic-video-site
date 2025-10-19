# 🔥 Generic Video Site

A modern, responsive video streaming application built with FastAPI, featuring cross-device synchronization, fire ratings, and mobile-optimized design.

## ✨ Features

### 🎯 Core Functionality
- **📚 Hierarchical Course Structure**: Organize videos by courses and sections with intelligent filtering
- **🔥 Fire Rating System**: Rate courses and videos with 1-5 fire icons (🔥🔥🔥🔥🔥)
- **📱 Mobile-First Design**: Responsive design optimized for all screen sizes
- **📊 Progress Tracking**: Persistent video progress with resume functionality
- **🔄 Cross-Device Sync**: Sync ratings, progress, and watched status across all your devices

### 🚀 Advanced Features
- **✨ AI Summaries**: Generate rich, structured summaries for any video (KEY POINTS and DETAILED SUMMARY)
- **⏱️ Jump Points**: AI‑curated key moments rendered below the summary; clickable to seek
- **🧭 Versions**: Summary version history with compact labels (vN • model • mm/dd/yy • Xm)
- **🤖 Model Selection**: Choose Ollama models in the modal; on‑demand pull with persistent caching
- **⚡ Real-time Synchronization**: Permanent sync groups that never expire
- **🎮 Interactive Navigation**: Hamburger menu, course filtering, collapsible sidebar
- **📁 Resource Integration**: Access PDFs, HTML files, and supplementary materials
- **🎬 Smart Video Streaming**: Efficient streaming with range request support
- **📝 Subtitle Support**: Automatic subtitle detection and display
- **💾 Persistent Storage**: SQLite database for reliable data persistence
- **🔧 Reset Functionality**: Complete data reset across all synced devices

### 🔄 Cross-Device Sync System
- **🆔 Sync Codes**: Share 6-character codes to link devices (e.g., `ABC123`)
- **🔗 Permanent Groups**: Sync groups never expire - devices stay connected forever
- **🌐 Network Sync**: Works across different networks and locations
- **📲 Device Detection**: Automatic device type detection (iPhone, Android, Desktop, etc.)
- **⚠️ Reset Options**: Clear all data across synced devices when needed

## 📁 Project Structure

```
generic-video-site/
├── app/                    # FastAPI backend application
│   ├── __init__.py
│   ├── main.py            # Main FastAPI app with all endpoints
│   ├── database.py        # SQLAlchemy models and database setup
│   └── sync_system.py     # Cross-device synchronization logic
├── static/                # Frontend assets
│   ├── index.html         # Main application interface
│   ├── styles.css         # Responsive CSS with mobile-first design
│   ├── script.js          # Core JavaScript functionality
│   └── storage.js         # Storage manager for sync and persistence
├── tests/                 # Comprehensive test suite
│   ├── __init__.py
│   ├── conftest.py        # Test configuration and fixtures
│   ├── test_main.py       # Core application tests
│   ├── test_database.py   # Database model and operation tests
│   ├── test_sync_system.py # Sync functionality tests
│   ├── test_api_endpoints.py # API endpoint tests
│   ├── test_integration.py # End-to-end workflow tests
│   └── test_docker.py     # Docker configuration tests
├── db/                    # SQLite database (auto-created, not in git)
├── data/                  # Video files directory (not in git)
├── htmlcov/              # Test coverage reports (auto-generated)
├── .dockerignore         # Docker build exclusions
├── .gitignore           # Git exclusions
├── Dockerfile           # Docker image configuration
├── docker-compose.yml   # Docker Compose setup
├── deploy-with-cache-clear.sh # Deployment script
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🛠️ Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

### 1. Clone and Setup
```bash
git clone https://github.com/yourusername/generic-video-site.git
cd generic-video-site

# Create data directory for your videos
mkdir -p data
```

### 2. Deploy with Docker (Recommended)
```bash
# Deploy with automatic setup
./deploy-with-cache-clear.sh

# Or manually
docker-compose up -d
```

### 3. Access the Application
- **Desktop**: http://localhost:8000
- **Mobile/Network**: http://YOUR-IP-ADDRESS:8000 (find with `ifconfig`)

### 4. Set Up Cross-Device Sync
1. Open the app on your primary device
2. Click the sync status indicator (☁️) in the top bar
3. Create a sync group and share the 6-character code
4. Join the sync group on other devices using the same code

## 📊 Video Organization

Structure your video files like this in the `data/` directory:

```
data/
├── Python Fundamentals/
│   ├── 01-Introduction/
│   │   ├── welcome.mp4
│   │   ├── welcome.vtt              # Optional subtitles
│   │   └── course-outline.pdf       # Optional resources
│   ├── 02-Variables/
│   │   ├── variables-basics.mp4
│   │   └── variables-advanced.mp4
│   └── 03-Functions/
│       └── functions-intro.mp4
├── JavaScript Essentials/
│   └── Getting Started/
│       ├── setup.mp4
│       └── first-program.mp4
└── Machine Learning/
    ├── Linear Regression/
    │   └── theory.mp4
    └── Neural Networks/
        └── introduction.mp4
```

### Supported File Types
- **Videos**: `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`, `.m4v`
- **Subtitles**: `.vtt`, `.srt`
- **Resources**: `.pdf`, `.html`, `.htm`

## 🧪 Testing

### Run Complete Test Suite
```bash
# Run all tests with coverage (fast in-memory DB and mocks)
pytest -q --cov=app --cov-report=term-missing

# Or run specific test categories
pytest tests/test_database.py -q        # Database tests
pytest tests/test_sync_system.py -q     # Sync functionality
pytest tests/test_api_endpoints.py -q   # API tests
pytest tests/test_integration.py -q     # End-to-end tests

# HTML coverage report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

### Linting
```bash
# Run Ruff linter
python -m pip install ruff
ruff check .
```

### Test Coverage
Our comprehensive test suite includes:
- **✅ 57 Core Tests** (Database, Sync System, Main App, Docker)
- **✅ API Endpoint Tests** (Preferences, Sync, Reset functionality)
- **✅ Integration Tests** (Full user workflows)
- **✅ Cross-Device Sync Tests** (Multi-device scenarios)
- **✅ Fire Rating System Tests** (Rating workflows and persistence)

Note: CI is optimized for speed. Tests run against a fast in‑memory SQLite database with AI services mocked, typically completing in under ~2 minutes on GitHub Actions.

## 🔄 Cross-Device Synchronization Guide

### Setting Up Sync Between Devices

1. **Primary Device (Desktop/Laptop)**:
   ```
   1. Open http://localhost:8000
   2. Rate some courses/videos with fire icons 🔥
   3. Click sync status (☁️) in top bar
   4. Click "Create Sync Group"
   5. Share the 6-character code (e.g., ABC123)
   ```

2. **Secondary Device (Phone/Tablet)**:
   ```
   1. Open http://YOUR-IP:8000 on mobile browser
   2. Click sync status (☁️) 
   3. Click "Join Sync Group"
   4. Enter the 6-character code
   5. Your ratings and progress sync instantly! 🎉
   ```

### Sync Features
- **🔥 Fire Ratings**: Course and video ratings sync across devices
- **📊 Progress Tracking**: Video progress and watched status syncs
- **🔗 Permanent Groups**: Devices stay synced forever (never expire)
- **🌐 Network Independent**: Works across different WiFi networks
- **⚠️ Data Reset**: Reset all data across all synced devices

## 🚀 Development

### Local Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database directory
mkdir -p db
chmod 755 db

# Set environment variables
export VIDEO_BASE_DIR=$(pwd)/data
export DATABASE_URL=sqlite:///./db/user_preferences.db

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints
The application provides these key endpoints:

- `GET /` — Main application interface
- `GET /api/library` — Video library with course structure
- `GET /api/preferences` — User preferences (ratings, progress, played status)
- `POST /api/preferences` — Save user preferences
- `POST /api/sync/create` — Create sync group
- `POST /api/sync/join` — Join sync group  
- `GET /api/sync/status` — Check sync status
- `POST /api/sync/leave` — Leave sync group
- `POST /api/reset` — Reset all user data
- `GET /video/{path}` — Stream video files (range requests supported)
- `GET /health` — App health check

#### AI Summary API
- `POST /api/summary/start` — Start generating a summary for a video (supports `force` and `model_name`)
- `GET /api/summary/status/{task_id}` — Check background task status
- `GET /api/summary/get?video_path=...` — Retrieve the latest completed summary
- `GET /api/summary/active?video_path=...` — Detect an in‑progress job for the video (resume polling)
- `GET /api/summary/versions?video_path=...` — List summary versions
- `GET /api/summary/version?video_path=...&version=N` — Get a specific version
- `POST /api/ai-model/pull` — On‑demand pull an Ollama model `{ name: "qwen2.5:14b-instruct" }`
- `GET /api/ai-health` — Ollama health and installed models

## 🐳 Docker Configuration

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `VIDEO_BASE_DIR` | `/app/data` | Path to video files |
| `DATABASE_URL` | `sqlite:///./db/user_preferences.db` | Database connection |

### Docker Compose Configuration
```yaml
services:
  generic-video-site:
    image: nas3/generic-video-site:local
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data:ro      # Video files (read-only)
      - ./db:/app/db:rw          # Database (read-write)
    environment:
      - VIDEO_BASE_DIR=/app/data
      - DATABASE_URL=sqlite:///./db/user_preferences.db
      - OLLAMA_URL=http://ollama:11434
    user: "0:0"  # Run as root for SQLite permissions
```

## 🛠️ Deployment

### Production Deployment
```bash
# Clean deployment with cache clearing
./deploy-with-cache-clear.sh

# Manual deployment
docker-compose down --remove-orphans
docker rmi nas3/generic-video-site:local 2>/dev/null || true
docker-compose build --no-cache
docker-compose up -d
```

### Ollama Models (Persistence and Pulls)
- Models are stored in a persistent volume (`ollama_models`) and survive redeploys.
- The model dropdown shows locally installed models (via `/api/ai-health`).
- Selecting a “Pull …” option triggers `/api/ai-model/pull`; once downloaded it becomes selectable.

### Health Monitoring
```bash
# Check application health
curl http://localhost:8000/health

# View logs
docker-compose logs -f

# Check database
docker exec generic-video-site ls -la /app/db/
```

## 🔧 Troubleshooting

### Sync Issues
**Problem**: 500 errors on sync endpoints
```bash
# Check database permissions
docker exec generic-video-site ls -la /app/db/
# Should show: drwxrwxrwx ... /app/db

# Check logs for specific errors
docker logs generic-video-site --tail=20
```

**Problem**: Cross-device sync not working
```bash
# Ensure server is accessible on network IP, not just localhost
# Find your IP: ifconfig | grep "inet " | grep -v 127.0.0.1
# Use: http://192.168.X.XXX:8000 (not localhost)
```

### Database Issues
**Problem**: "Unable to open database file"
```bash
# Fix database directory permissions
mkdir -p ./db
chmod 777 ./db

# Redeploy
docker-compose down
docker-compose up -d
```

**Problem**: "Text file busy" error on deploy script
```bash
# Kill any stuck processes
pkill -f "deploy-with-cache-clear" || true
pkill -f "docker-compose" || true
sleep 2
chmod +x deploy-with-cache-clear.sh
./deploy-with-cache-clear.sh
```

### Mobile Issues
**Problem**: Interface not responsive on mobile
- Hard refresh (Ctrl+F5 or Cmd+Shift+R)
- Clear browser cache
- Check viewport meta tag is present

**Problem**: Fire ratings not working
- Ensure JavaScript is enabled
- Check browser console for errors
- Verify sync status in top bar

## 🏗️ Architecture

### Frontend (Mobile-First)
- **HTML5**: Semantic structure with proper viewport configuration
- **CSS3**: Flexbox/Grid layouts with responsive design patterns
- **Vanilla JavaScript**: No framework dependencies, optimized for performance
- **Progressive Enhancement**: Works without JavaScript, enhanced with JS

### Backend (FastAPI + SQLite)
- **FastAPI**: Modern Python web framework with automatic OpenAPI documentation
- **SQLAlchemy**: ORM for database operations with proper relationships
- **SQLite**: Lightweight database for development and small-scale deployments
- **Pydantic**: Data validation and serialization

### Cross-Device Sync Architecture
```
Device A ←→ [FastAPI Server + SQLite] ←→ Device B
         ↑                              ↑
    Sync Code: ABC123         Sync Code: ABC123
    User Preferences          User Preferences
    - Fire Ratings           - Fire Ratings  
    - Progress Data          - Progress Data
    - Watched Status         - Watched Status
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest -q`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

### Development Guidelines
- **🧪 Test Coverage**: Write tests for new features
- **📱 Mobile-First**: Design for mobile, enhance for desktop
- **🔄 Sync-Aware**: Consider cross-device implications
- **🔥 Fire Icons**: Use fire emoji (🔥) for ratings, not stars
- **📚 Documentation**: Update README for new features

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

- [ ] **🎨 Themes**: Dark/light mode toggle
- [ ] **👥 User Accounts**: Full authentication system  
- [ ] **📱 PWA**: Progressive Web App capabilities
- [ ] **🎵 Playlists**: Custom video playlists
- [ ] **📊 Analytics**: Detailed learning analytics
- [ ] **🌍 i18n**: Multi-language support
- [ ] **🔄 Real-time Sync**: WebSocket-based real-time updates
- [ ] **📤 Export**: Export learning progress and ratings

## 🙏 Acknowledgments

- **FastAPI** for the excellent Python web framework
- **SQLAlchemy** for robust database ORM
- **Docker** for containerization
- **pytest** for comprehensive testing framework
- All contributors and users making this project better! 🔥