# Panel Deployment Guide

This guide explains how to deploy the Trailpack UI using Panel.

## Prerequisites

1. A server or hosting service that supports Python web applications
2. Python 3.12 or higher
3. PyST API credentials (PYST_HOST and PYST_AUTH_TOKEN)

## Local Development

### Installation

Install the package with UI dependencies:

```bash
pip install -e .
```

### Configuration

Create a `.env` file for local development:

```bash
cp .env.example .env
# Edit .env with your credentials
```

Example `.env` file:

```bash
PYST_HOST=https://your-pyst-api-server.com
PYST_AUTH_TOKEN=your_secret_token_here
```

### Running Locally

Run the app using the CLI:

```bash
trailpack ui
```

Or directly with Panel:

```bash
panel serve trailpack/ui/panel_app.py --port 5006 --show
```

The app will open in your browser at `http://localhost:5006`.

## Deployment Options

### 1. Panel Cloud (Recommended)

Panel provides cloud hosting at [panel.holoviz.org](https://panel.holoviz.org).

1. Sign up for a Panel Cloud account
2. Connect your GitHub repository
3. Configure environment variables in the Panel Cloud dashboard
4. Deploy the `trailpack/ui/panel_app.py` file

### 2. Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYST_HOST=${PYST_HOST}
ENV PYST_AUTH_TOKEN=${PYST_AUTH_TOKEN}

EXPOSE 5006

CMD ["panel", "serve", "trailpack/ui/panel_app.py", "--port", "5006", "--address", "0.0.0.0", "--allow-websocket-origin=*"]
```

Build and run:

```bash
docker build -t trailpack-ui .
docker run -p 5006:5006 -e PYST_HOST=your_host -e PYST_AUTH_TOKEN=your_token trailpack-ui
```

### 3. Traditional Server Deployment

On a Linux server with nginx:

1. Install dependencies:
```bash
pip install -e .
```

2. Create a systemd service (`/etc/systemd/system/trailpack-ui.service`):

```ini
[Unit]
Description=Trailpack Panel UI
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/trailpack
Environment="PYST_HOST=your_host"
Environment="PYST_AUTH_TOKEN=your_token"
ExecStart=/usr/bin/panel serve trailpack/ui/panel_app.py --port 5006 --address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start trailpack-ui
sudo systemctl enable trailpack-ui
```

4. Configure nginx as reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5006;
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

## Configuration Details

### Environment Variables

The application uses the following environment variables:

- `PYST_HOST`: URL of the PyST API server (required)
- `PYST_AUTH_TOKEN`: Authentication token for the PyST API (required)

These can be set via:
1. `.env` file (for local development)
2. System environment variables
3. Deployment platform configuration

### Security Considerations

**Important Notes:**
- Never commit secrets to version control
- Use environment variables or secure secret management
- Ensure HTTPS is used in production
- Configure appropriate CORS settings for your deployment

## Troubleshooting

**Issue: App crashes on startup**
- Verify Python version is 3.12 or higher
- Check that all dependencies are installed: `pip install -e .`
- Verify environment variables are set correctly
- Check application logs for specific error messages

**Issue: API calls fail**
- Verify PYST_HOST is accessible from your deployment environment
- Check that PYST_AUTH_TOKEN is valid
- Ensure the PyST API server accepts connections from your IP/domain

**Issue: Module not found errors**
- Ensure the package is installed: `pip install -e .`
- Check that the Python path includes the repository root
- Verify all external dependencies are listed in `pyproject.toml`

**Issue: WebSocket connection failures**
- Check that your deployment allows WebSocket connections
- Verify the `--allow-websocket-origin` parameter is set correctly
- Ensure your reverse proxy is configured to support WebSocket upgrades

## Requirements

The `requirements.txt` file lists all dependencies:

```
pyst-client @ git+https://github.com/cauldron/pyst-client.git
langcodes
python-dotenv
httpx
openpyxl
panel>=1.3.0
pandas>=2.0.0
pydantic>=2.0.0
pyyaml
```

## Advantages of Panel over Streamlit

Panel offers several benefits for maintainability:

1. **More flexible architecture**: Panel apps can be served as standalone web applications
2. **Better integration with HoloViz ecosystem**: Works seamlessly with Bokeh, HoloViews, and other viz libraries
3. **More deployment options**: Can be embedded in notebooks, deployed as dashboards, or served as web apps
4. **Greater control over layout and styling**: More programmatic control over UI components
5. **Better performance**: More efficient WebSocket handling and rendering

## Support

For issues related to:
- **Trailpack**: Open an issue on GitHub
- **Panel**: Check https://panel.holoviz.org/
- **PyST API**: Contact your PyST API provider
