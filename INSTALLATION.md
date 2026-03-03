# Installation Guide

Complete setup instructions for installing Docker and running the ISCE2 InSAR workflow.

## 📋 System Requirements

### Minimum Requirements
- **CPU**: 4 cores (8+ cores recommended for faster processing)
- **RAM**: 16GB (32GB+ recommended)
- **Disk Space**: 
  - 10GB for Docker images
  - 30GB+ for processing data per interferogram
  - 100GB+ recommended for multiple processing runs
- **OS**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10/11 with WSL2

### Recommended Setup
- **CPU**: 8+ cores
- **RAM**: 32GB+
- **Disk**: 500GB+ SSD
- **OS**: Ubuntu 22.04 LTS or similar Linux distribution

---

## 🐳 Docker Installation

### Linux (Ubuntu/Debian)

#### Method 1: Official Docker Installation (Recommended)

```bash
# 1. Update package index
sudo apt-get update

# 2. Install prerequisites
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 3. Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 4. Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 6. Verify installation
sudo docker --version
sudo docker compose version
```

#### Method 2: Convenience Script

```bash
# Download and run Docker installation script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose plugin
sudo apt-get install -y docker-compose-plugin
```

#### Post-Installation: Add User to Docker Group

```bash
# Add current user to docker group (avoids needing sudo)
sudo usermod -aG docker $USER

# Apply group changes (logout/login or use newgrp)
newgrp docker

# Verify docker works without sudo
docker run hello-world
```

---

### macOS

#### Option 1: Docker Desktop (Recommended)

1. **Download Docker Desktop**:
   - Visit: https://www.docker.com/products/docker-desktop
   - Download Docker Desktop for Mac (Intel or Apple Silicon)

2. **Install**:
   - Open the downloaded `.dmg` file
   - Drag Docker to Applications folder
   - Launch Docker Desktop from Applications

3. **Configure Resources** (in Docker Desktop settings):
   - **CPUs**: 4+ (adjust based on your Mac)
   - **Memory**: 8GB minimum, 16GB+ recommended
   - **Disk**: 60GB+ (for images and processing)

4. **Verify Installation**:
   ```bash
   docker --version
   docker compose version
   docker run hello-world
   ```

#### Option 2: Homebrew

```bash
# Install Docker and Docker Compose
brew install docker docker-compose

# Note: Still need Docker Desktop or alternative runtime
# Homebrew installs CLI tools, not the Docker daemon
```

---

### Windows 10/11

#### Option 1: Docker Desktop with WSL2 (Recommended)

1. **Enable WSL2**:
   ```powershell
   # Open PowerShell as Administrator
   wsl --install
   
   # Restart computer after installation
   ```

2. **Install Ubuntu from Microsoft Store**:
   - Open Microsoft Store
   - Search "Ubuntu 22.04 LTS"
   - Install and launch
   - Create username and password

3. **Download Docker Desktop**:
   - Visit: https://www.docker.com/products/docker-desktop
   - Download Docker Desktop for Windows

4. **Install Docker Desktop**:
   - Run installer
   - Enable "Use WSL 2 instead of Hyper-V" option
   - Complete installation and restart

5. **Configure Docker Desktop**:
   - Open Docker Desktop
   - Settings → Resources → WSL Integration
   - Enable integration with your Ubuntu distribution

6. **Verify Installation** (in Ubuntu WSL terminal):
   ```bash
   docker --version
   docker compose version
   docker run hello-world
   ```

#### Option 2: Native Windows Containers

Not recommended for this workflow - Linux containers required.

---

## 🔍 Verify Docker Installation

Run these commands to verify Docker is working correctly:

```bash
# 1. Check Docker version
docker --version
# Expected: Docker version 24.0+ 

# 2. Check Docker Compose version
docker compose version
# Expected: Docker Compose version v2.20+

# 3. Test Docker works
docker run hello-world
# Should download and run test container

# 4. Check Docker daemon is running
docker ps
# Should show empty list (no containers running)

# 5. Test Docker Compose
cat > docker-compose-test.yml << 'EOF'
version: '3.8'
services:
  test:
    image: alpine:latest
    command: echo "Docker Compose works!"
EOF

docker compose -f docker-compose-test.yml up
# Should print "Docker Compose works!"

# Clean up test
rm docker-compose-test.yml
```

---

## 📦 Clone This Repository

Once Docker is installed:

```bash
# Clone the repository
git clone https://github.com/MSSJoud/isce2-playbook.git

# Navigate to directory
cd isce2-playbook

# Verify docker-compose.yml exists
ls -l docker-compose.yml
```

---

## 🚀 Start ISCE2 Environment

```bash
# Start all services (downloads images on first run)
docker compose up -d

# This will download:
# - ISCE2 processing container (~5GB)
# - Analysis container (~2GB)
# - STAC search container (~500MB)
# Total download: ~8GB (first time only)

# Check containers are running
docker compose ps

# Expected output:
# NAME                    STATUS
# isce2-playbook-isce2-insar-1    running
# isce2-playbook-analyze-insar-1  running
# isce2-playbook-stac-search-1    running
```

---

## ✅ Verify ISCE2 Installation

```bash
# Test ISCE2 is working
docker compose run --rm isce2-insar topsApp.py --help

# Should show topsApp.py help message

# Test Python environment
docker compose run --rm isce2-insar python -c "import isce; print(isce.__version__)"

# Should print: 2.6.3
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Permission Denied" Errors (Linux)

**Problem**: `permission denied while trying to connect to Docker daemon`

**Solution**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again, or use:
newgrp docker

# Verify
docker run hello-world
```

#### 2. "Cannot Connect to Docker Daemon" (macOS/Windows)

**Problem**: Docker daemon not running

**Solution**:
- **macOS**: Launch Docker Desktop from Applications
- **Windows**: Launch Docker Desktop from Start Menu
- Wait for Docker icon in system tray to show "Docker Desktop is running"

#### 3. "Docker Compose Not Found"

**Problem**: `docker-compose: command not found`

**Modern Solution** (Docker Compose V2 - built into Docker):
```bash
# Use 'docker compose' (no hyphen) instead of 'docker-compose'
docker compose version
```

**Legacy Solution** (if you need docker-compose V1):
```bash
# Linux
sudo apt-get install docker-compose

# macOS
brew install docker-compose

# Verify
docker-compose --version
```

#### 4. "No Space Left on Device"

**Problem**: Not enough disk space for Docker images/containers

**Solution**:
```bash
# Check Docker disk usage
docker system df

# Clean up unused images/containers
docker system prune -a

# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune -a
```

#### 5. WSL2 Installation Issues (Windows)

**Problem**: WSL2 not installing properly

**Solution**:
```powershell
# Update WSL
wsl --update

# Set default version to WSL2
wsl --set-default-version 2

# Check active distributions
wsl --list --verbose

# Should show Ubuntu with VERSION 2
```

#### 6. Slow Performance (Windows WSL2)

**Problem**: Docker/file access is slow in WSL2

**Solution**:
- Store project files INSIDE WSL filesystem, not Windows drives
- Don't use `/mnt/c/` paths - use `/home/username/` instead

```bash
# Check current location
pwd

# If on Windows drive (/mnt/c/...), move to WSL home
cd ~
git clone https://github.com/MSSJoud/isce2-playbook.git
cd isce2-playbook
```

#### 7. "Port Already in Use"

**Problem**: `port is already allocated`

**Solution**:
```bash
# Find what's using the port (example: 8501)
sudo lsof -i :8501

# Or on Linux
sudo netstat -tulpn | grep 8501

# Stop the conflicting service or change port in docker-compose.yml
```

---

## 🔧 Docker Resource Configuration

### Adjust Resources (if needed)

**Docker Desktop (macOS/Windows)**:
1. Open Docker Desktop
2. Settings → Resources
3. Adjust:
   - **CPUs**: 4-8 cores for ISCE2 processing
   - **Memory**: 16GB minimum, 32GB recommended
   - **Disk**: 100GB+ for processing multiple interferograms
4. Click "Apply & Restart"

**Linux**:
Docker on Linux uses all available system resources by default. No configuration needed.

---

## 🎓 Next Steps

Once Docker is installed and verified:

1. **Read the Main README**:
   ```bash
   cat README.md
   ```

2. **Follow Complete Workflow Guide**:
   ```bash
   cat README_COMPLETE_WORKFLOW.md
   ```

3. **Try Test Processing**:
   - The repository includes a working test case (Venezuela 2021)
   - Follow Quick Start in README.md

4. **Process Your Own Data**:
   - Download Sentinel-1 SLCs
   - Update input configuration files
   - Run processing workflow

---

## 📚 Additional Resources

### Official Documentation
- **Docker**: https://docs.docker.com/get-docker/
- **Docker Compose**: https://docs.docker.com/compose/
- **ISCE2**: https://github.com/isce-framework/isce2

### Useful Commands

```bash
# View running containers
docker compose ps

# View container logs
docker compose logs isce2-insar

# Stop all services
docker compose down

# Rebuild containers (after changes)
docker compose build

# Enter container shell
docker compose exec isce2-insar bash

# Run one-off command
docker compose run --rm isce2-insar <command>

# Update images
docker compose pull
```

---

## ⚠️ Important Notes

1. **First Run**: Docker will download ~8GB of images. This takes 10-30 minutes depending on internet speed.

2. **Disk Space**: Processing interferograms requires significant disk space. Monitor with:
   ```bash
   df -h
   docker system df
   ```

3. **Memory**: ISCE2 processing is memory-intensive. Close other applications during processing if RAM is limited.

4. **Windows Users**: Always work inside WSL2 Ubuntu terminal for best performance.

5. **Network**: Some organizations block Docker Hub. If downloads fail, check network/firewall settings.

---

## 🆘 Getting Help

If you encounter issues not covered here:

1. **Check Docker Status**:
   ```bash
   docker info
   docker compose version
   ```

2. **Check Container Logs**:
   ```bash
   docker compose logs
   ```

3. **Search Issues**: Check common Docker/ISCE2 issues online

4. **System Info**: Provide this when asking for help:
   ```bash
   uname -a
   docker --version
   docker compose version
   docker info
   ```

---

**Installation complete!** 🎉

Continue to [README.md](README.md) for workflow instructions.
