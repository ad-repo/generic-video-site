# Generic Video Site

A modern, responsive video streaming application built with FastAPI, featuring a hierarchical course structure, progress tracking, and star ratings.

## 🚀 Features

- **Hierarchical Course Structure**: Organize videos by courses and sections
- **Progress Tracking**: Track watched videos with persistent storage
- **Star Ratings**: Rate courses and individual videos (1-5 stars)
- **Responsive Design**: Works on desktop and mobile devices
- **Collapsible Navigation**: Sidebar with course navigation
- **Resource Links**: Access supplementary materials (PDFs, HTML files)
- **Video Streaming**: Efficient video streaming with resume functionality
- **Subtitle Support**: Automatic subtitle detection and streaming

## 📁 Project Structure

```
generic-video-site/
├── app/                    # FastAPI application
│   ├── __init__.py
│   └── main.py            # Main application file
├── static/                # Frontend assets
│   ├── index.html         # Main HTML file
│   ├── styles.css         # CSS styles
│   └── script.js          # JavaScript functionality
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_main.py       # Main application tests
│   └── test_docker.py     # Docker and infrastructure tests
├── .github/               # GitHub Actions
│   └── workflows/
│       └── ci.yml         # CI/CD pipeline
├── data/                  # Video files (not in git)
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🛠️ Setup Instructions

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/generic-video-site.git
cd generic-video-site
```

### 2. Set Up the Data Folder

**IMPORTANT**: The `data/` folder is not included in the repository and must be set up manually.

#### Option A: Create Data Structure Manually

```bash
# Create the data directory structure
mkdir -p data

# Your video files should be organized like this:
data/
├── Course Name 1/
│   ├── Section 1/
│   │   ├── video1.mp4
│   │   ├── video1.vtt          # Optional subtitles
│   │   └── resource.pdf         # Optional resources
│   └── Section 2/
│       ├── video2.mp4
│       └── video2.vtt
└── Course Name 2/
    └── Section 1/
        └── video3.mp4
```

#### Option B: Use Docker Volume Mount

```bash
# Mount your existing video directory
docker run -v /path/to/your/videos:/app/data generic-video-site
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```bash
# .env
VIDEOS_ROOT=/app/data
PORT=8000
```

### 4. Docker Setup

#### Using Docker Compose (Recommended)

```bash
# Build and start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

#### Using Docker Directly

```bash
# Build the image
docker build -t generic-video-site .

# Run the container
docker run -d \
  --name video-site \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e VIDEOS_ROOT=/app/data \
  generic-video-site
```

### 5. Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export VIDEOS_ROOT=$(pwd)/data

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🧪 Testing

### Run Tests Locally

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_main.py -v
```

### Test Coverage

The project includes comprehensive test coverage:

- **Unit Tests**: Test individual functions and endpoints
- **Integration Tests**: Test API endpoints and responses
- **Docker Tests**: Test Docker configuration and builds
- **Security Tests**: Test for common vulnerabilities

## 🚀 Deployment

### GitHub Actions CI/CD

The repository includes GitHub Actions for:

- **Automated Testing**: Run tests on every push and PR
- **Docker Build**: Build and push Docker images
- **Security Scanning**: Vulnerability scanning with Trivy
- **Code Coverage**: Upload coverage reports to Codecov

### Manual Deployment

```bash
# Build and deploy
./deploy-with-cache-clear.sh

# Or manually
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📊 Data Organization

### Video File Structure

Organize your videos in the following structure:

```
data/
├── Course Name/
│   ├── Section Name/
│   │   ├── 01. Video Title.mp4
│   │   ├── 01. Video Title.vtt      # Subtitles (optional)
│   │   ├── 02. Another Video.mp4
│   │   ├── resource.pdf             # Resources (optional)
│   │   └── index.html               # Section info (optional)
│   └── Another Section/
│       └── 01. Video.mp4
└── Another Course/
    └── Section/
        └── video.mp4
```

### Supported File Types

- **Videos**: `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`
- **Subtitles**: `.vtt`, `.srt`
- **Resources**: `.pdf`, `.html`, `.htm`

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VIDEOS_ROOT` | `/app/data` | Path to video files directory |
| `PORT` | `8000` | Application port |

### Docker Configuration

The application uses:
- **Base Image**: Python 3.11-slim
- **Port**: 8000
- **Volume**: `/app/data` for video files

## 🛡️ Security

- **Path Traversal Protection**: Prevents directory traversal attacks
- **File Type Validation**: Only serves allowed file types
- **Input Sanitization**: Sanitizes user inputs
- **Security Headers**: Includes security headers in responses

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Write tests for new features
- Follow PEP 8 style guidelines
- Update documentation for new features
- Ensure all tests pass before submitting PR

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

#### 1. Videos Not Loading
- Check that `VIDEOS_ROOT` environment variable is set correctly
- Verify video files are in the correct directory structure
- Check file permissions

#### 2. Docker Build Issues
- Ensure Docker is running
- Check Dockerfile syntax
- Verify all dependencies are in requirements.txt

#### 3. Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

#### 4. Permission Issues
```bash
# Fix file permissions
chmod +x deploy-with-cache-clear.sh
chmod -R 755 data/
```

### Getting Help

- Check the [Issues](https://github.com/yourusername/generic-video-site/issues) page
- Review the [Discussions](https://github.com/yourusername/generic-video-site/discussions) section
- Create a new issue with detailed information

## 🎯 Roadmap

- [ ] User authentication and authorization
- [ ] Playlist functionality
- [ ] Video transcoding
- [ ] Mobile app
- [ ] Advanced analytics
- [ ] Multi-language support

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Docker for containerization
- All contributors and users of this project
