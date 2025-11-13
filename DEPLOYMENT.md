# 🌐 Deployment Guide

This guide shows how to deploy the NetSuite Financial Reporting MVP for your users.

---

## Deployment Options

### Option 1: Streamlit Cloud (Recommended for Testing)

**Best for:** Quick demos, proof of concepts, small user groups

**Pros:**
- ✅ Free tier available
- ✅ Automatic SSL/HTTPS
- ✅ Easy GitHub integration
- ✅ Automatic updates on git push

**Cons:**
- ⚠️ Limited resources on free tier
- ⚠️ Public unless on paid plan

#### Steps:

1. **Create a GitHub repository**
```bash
git init
git add .
git commit -m "Initial NetSuite MVP"
git remote add origin https://github.com/yourusername/netsuite-mvp.git
git push -u origin main
```

2. **Deploy on Streamlit Cloud**
- Go to [share.streamlit.io](https://share.streamlit.io)
- Click "New app"
- Select your repository
- Set main file: `app.py`
- Click "Deploy"

3. **Share URL with users**
- Users receive URL like: `https://yourusername-netsuite-mvp.streamlit.app`
- No installation needed for users

---

### Option 2: Docker Container (Recommended for Production)

**Best for:** Enterprise deployments, private networks, full control

#### Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Build and Run

```bash
# Build image
docker build -t netsuite-mvp .

# Run container
docker run -p 8501:8501 netsuite-mvp

# Access at http://localhost:8501
```

#### Docker Compose (with nginx reverse proxy)

```yaml
# docker-compose.yml
version: '3.8'

services:
  streamlit:
    build: .
    container_name: netsuite-app
    restart: unless-stopped
    ports:
      - "8501:8501"
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_HEADLESS=true
    
  nginx:
    image: nginx:alpine
    container_name: netsuite-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - streamlit
```

---

### Option 3: Azure App Service

**Best for:** Microsoft-centric organizations, integration with Azure services

#### Deploy Script

```bash
# Login to Azure
az login

# Create resource group
az group create --name netsuite-mvp-rg --location eastus

# Create App Service plan
az appservice plan create \
  --name netsuite-mvp-plan \
  --resource-group netsuite-mvp-rg \
  --sku B1 \
  --is-linux

# Create web app
az webapp create \
  --resource-group netsuite-mvp-rg \
  --plan netsuite-mvp-plan \
  --name netsuite-financial-mvp \
  --runtime "PYTHON:3.9"

# Configure deployment
az webapp config set \
  --resource-group netsuite-mvp-rg \
  --name netsuite-financial-mvp \
  --startup-file "streamlit run app.py --server.port 8000 --server.address 0.0.0.0"

# Deploy from local Git
az webapp deployment source config-local-git \
  --resource-group netsuite-mvp-rg \
  --name netsuite-financial-mvp

# Push code
git remote add azure <deployment-url>
git push azure main
```

#### Estimated Cost
- **B1 Basic**: ~$13/month
- **S1 Standard**: ~$70/month (recommended for production)

---

### Option 4: AWS EC2

**Best for:** AWS customers, maximum flexibility

#### Launch Instance

1. **Create EC2 instance**
   - AMI: Ubuntu 22.04 LTS
   - Instance type: t3.medium (4 GB RAM)
   - Security group: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS)

2. **Connect and setup**

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3-pip python3-venv nginx -y

# Clone repository
git clone https://github.com/yourusername/netsuite-mvp.git
cd netsuite-mvp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/netsuite-app.service
```

3. **Systemd service file**

```ini
[Unit]
Description=NetSuite Financial Reporting MVP
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/netsuite-mvp
Environment="PATH=/home/ubuntu/netsuite-mvp/venv/bin"
ExecStart=/home/ubuntu/netsuite-mvp/venv/bin/streamlit run app.py --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target
```

4. **Start service**

```bash
sudo systemctl daemon-reload
sudo systemctl enable netsuite-app
sudo systemctl start netsuite-app
```

5. **Configure nginx reverse proxy**

```nginx
# /etc/nginx/sites-available/netsuite-app
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/netsuite-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### Option 5: Kubernetes (Enterprise Scale)

**Best for:** Large organizations, high availability requirements

#### Kubernetes Manifests

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: netsuite-mvp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: netsuite-mvp
  template:
    metadata:
      labels:
        app: netsuite-mvp
    spec:
      containers:
      - name: streamlit
        image: your-registry/netsuite-mvp:latest
        ports:
        - containerPort: 8501
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: netsuite-mvp-service
spec:
  selector:
    app: netsuite-mvp
  ports:
  - port: 80
    targetPort: 8501
  type: LoadBalancer
```

#### Deploy

```bash
kubectl apply -f deployment.yaml
kubectl get services
```

---

## Security Considerations

### For Production Deployments

1. **HTTPS/SSL**
   - Use Let's Encrypt for free SSL certificates
   - Configure automatic renewal

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com
```

2. **Authentication** (if needed)

Add to `app.py`:

```python
import streamlit as st

def check_password():
    """Returns True if user enters correct password."""
    
    def password_entered():
        if st.session_state["password"] == "your-secure-password":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if check_password():
    # Main app code here
    st.title("NetSuite Financial Reporting MVP")
```

3. **Rate Limiting**

```nginx
# In nginx.conf
limit_req_zone $binary_remote_addr zone=mylimit:10m rate=10r/s;

server {
    location / {
        limit_req zone=mylimit burst=20;
        proxy_pass http://localhost:8501;
    }
}
```

4. **Data Privacy**
   - All processing is client-side
   - No data persistence by default
   - Add data retention policy if needed

---

## Monitoring

### Basic Health Check

Add to `app.py`:

```python
import os
from datetime import datetime

# Add to sidebar
st.sidebar.markdown("---")
st.sidebar.info(f"🟢 App Status: Running\n\nLast updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
```

### Application Insights (Azure)

```python
from applicationinsights import TelemetryClient

tc = TelemetryClient(os.environ.get('APPINSIGHTS_KEY'))

# Track page views
tc.track_event('page_view', {'page': 'home'})

# Track report generation
tc.track_metric('reports_generated', 1)

tc.flush()
```

---

## User Distribution

### For Non-Technical Users

**Option A: Hosted Service**
1. Deploy to cloud (Streamlit Cloud, Azure, AWS)
2. Share URL with users
3. Users access via web browser
4. No installation required

**Option B: Desktop Executable (Advanced)**

Using PyInstaller:

```bash
pip install pyinstaller

pyinstaller --onefile --add-data "sql:sql" --add-data "config:config" app.py
```

Distribute the generated `.exe` file.

---

## Cost Estimates

| Deployment Option | Monthly Cost | Best For |
|-------------------|--------------|----------|
| Streamlit Cloud (Free) | $0 | Testing, demos |
| Streamlit Cloud (Pro) | $250 | Small teams |
| Azure App Service (B1) | $13 | Development |
| Azure App Service (S1) | $70 | Production |
| AWS EC2 (t3.medium) | $30 | Small production |
| AWS EC2 (t3.large) | $60 | Medium production |
| Docker on VPS | $5-20 | Small deployments |

---

## Scaling Recommendations

### User Count Guidelines

| Users | Recommended Setup | Specs |
|-------|-------------------|-------|
| 1-10 | Streamlit Cloud Free | Shared resources |
| 10-50 | App Service B1 / EC2 t3.small | 1 vCPU, 2 GB RAM |
| 50-200 | App Service S1 / EC2 t3.medium | 2 vCPU, 4 GB RAM |
| 200-1000 | App Service P1V2 / EC2 t3.large | 2 vCPU, 8 GB RAM |
| 1000+ | Kubernetes cluster | Auto-scaling |

---

## Maintenance

### Regular Updates

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Test locally
streamlit run app.py

# Push to production
git add .
git commit -m "Update dependencies"
git push
```

### Backup Strategy

```bash
# Backup configuration
tar -czf backup-$(date +%Y%m%d).tar.gz sql/ config/ sample_data/

# Store in S3 or Azure Blob Storage
```

---

## Support Resources

- **Documentation**: See README.md
- **Quick Start**: See QUICKSTART.md
- **Issues**: GitHub Issues page
- **Updates**: Check GitHub for latest version

---

**Ready to deploy?** Choose the option that best fits your needs and follow the steps above! 🚀

