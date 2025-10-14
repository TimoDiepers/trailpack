# Streamlit Cloud Deployment Guide

This guide explains how to deploy the Trailpack UI to Streamlit Cloud.

## Prerequisites

1. A GitHub account with access to this repository
2. A Streamlit Cloud account (free tier available at https://share.streamlit.io)
3. PyST API credentials (PYST_HOST and PYST_AUTH_TOKEN)

## Deployment Steps

### 1. Prepare Your Repository

Ensure your repository is pushed to GitHub:

```bash
git push origin main
```

### 2. Create a New App on Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "New app"
3. Select your repository: `TimoDiepers/trailpack`
4. Set the branch (e.g., `main` or your deployment branch)
5. Set the main file path: `trailpack/ui/streamlit_app.py`
6. Click "Advanced settings"

### 3. Configure Secrets

In the "Secrets" section, add your PyST API credentials in TOML format:

```toml
PYST_HOST = "https://your-pyst-api-server.com"
PYST_AUTH_TOKEN = "your_secret_token_here"
```

**Important Notes:**
- Do NOT include these secrets in your code or repository
- The config system automatically detects Streamlit Cloud and uses `st.secrets`
- For local development, use a `.env` file instead (see `.env.example`)

### 4. Deploy

Click "Deploy" and wait for the app to build and start.

## Configuration Details

### How Configuration Loading Works

The application uses a smart configuration system that:

1. **On Streamlit Cloud**: Automatically loads from `st.secrets`
2. **Locally**: Falls back to environment variables or `.env` file
3. **Lazy Loading**: Secrets are loaded when first accessed, not at import time

This ensures compatibility with both local development and cloud deployment.

### Troubleshooting

**Issue: App crashes on startup**
- Check that your secrets are correctly formatted in TOML
- Verify PYST_HOST includes the protocol (http:// or https://)
- Check Streamlit Cloud logs for specific error messages

**Issue: API calls fail**
- Verify your PYST_HOST is accessible from Streamlit Cloud
- Check that PYST_AUTH_TOKEN is valid
- Ensure the PyST API server accepts connections from Streamlit Cloud's IP range

**Issue: Module not found errors**
- The app includes automatic path configuration to find trailpack modules
- Verify all external dependencies are listed in `requirements.txt`
- Check that there are no circular dependencies
- Review Streamlit Cloud build logs

## Local Development vs. Cloud Deployment

### Local Development

Create a `.env` file:

```bash
cp .env.example .env
# Edit .env with your credentials
```

Run the app:

```bash
streamlit run trailpack/ui/streamlit_app.py
```

### Cloud Deployment

- No `.env` file needed
- Configure secrets through Streamlit Cloud dashboard
- App automatically uses cloud configuration

## Requirements

The `requirements.txt` file at the repository root lists all dependencies:

```
pyst-client @ git+https://github.com/cauldron/pyst-client.git
langcodes
python-dotenv
httpx
openpyxl
streamlit>=1.28.0
pandas>=2.0.0
```

**Note**: The package code is deployed directly, so `requirements.txt` does NOT include the trailpack package itself. The streamlit app automatically adds the repository root to Python's import path to ensure all trailpack modules can be imported.

## Support

For issues related to:
- **Trailpack**: Open an issue on GitHub
- **Streamlit Cloud**: Check https://docs.streamlit.io/streamlit-community-cloud
- **PyST API**: Contact your PyST API provider
