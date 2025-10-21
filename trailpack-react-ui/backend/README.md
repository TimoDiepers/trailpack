# Trailpack Backend API

FastAPI backend for the Trailpack Excel to PyST Mapper application.

## Features

- Excel file upload and processing
- PyST ontology search integration
- Automatic column mapping suggestions
- Mapping validation
- Parquet export with compression

## Tech Stack

- FastAPI for the web framework
- Pandas for Excel processing
- PyArrow for Parquet export
- httpx for PyST API integration

## Setup

### 1. Install Dependencies

```bash
cd backend
conda run -n hackathon pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and configure:
- `PYST_API_URL`: URL of your PyST ontology API
- `PYST_API_KEY`: API key if required
- `PORT`: Server port (default: 8000)
- `CORS_ORIGINS`: Allowed frontend origins

### 3. Run the Server

```bash
conda run -n hackathon python -m app.main
```

Or with uvicorn directly:

```bash
conda run -n hackathon uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Excel Processing
- `POST /api/excel/upload` - Upload and process Excel file

### PyST Ontology
- `GET /api/pyst/search?q={query}` - Search for concepts
- `GET /api/pyst/concept/{id}` - Get concept by ID

### Mapping
- `POST /api/mapping/auto` - Get auto-mapping suggestions
- `POST /api/mapping/validate` - Validate mappings

### Export
- `POST /api/export/parquet` - Export to Parquet format

## PyST API Integration

The backend integrates with the PyST ontology API to:

1. **Search Concepts**: Find matching ontology concepts based on Excel column names
2. **Auto-Mapping**: Suggest appropriate PyST concepts for each column
3. **Validation**: Verify mappings against ontology constraints

### PyST API Requirements

Your PyST API should implement:

- `GET /api/concepts/search?q={query}&limit={n}` - Search concepts
  - Returns: `{"concepts": [{"id": "...", "name": "...", "description": "...", "category": "..."}]}`

- `GET /api/concepts/{id}` - Get concept details
  - Returns: `{"id": "...", "name": "...", "description": "...", "category": "...", "uri": "..."}`

If your PyST API has a different structure, modify `app/services/pyst_service.py` accordingly.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── routers/
│   │   ├── excel.py         # Excel endpoints
│   │   ├── pyst.py          # PyST endpoints
│   │   ├── mapping.py       # Mapping endpoints
│   │   └── export.py        # Export endpoints
│   └── services/
│       ├── excel_service.py # Excel processing
│       ├── pyst_service.py  # PyST integration
│       └── export_service.py # Parquet export
├── requirements.txt
├── .env
└── README.md
```

## Development

### Adding New Endpoints

1. Create new router in `app/routers/`
2. Add business logic in `app/services/`
3. Define schemas in `app/models/schemas.py`
4. Register router in `app/main.py`

### Testing

```bash
# Test API health
curl http://localhost:8000/health

# Test Excel upload
curl -X POST -F "file=@sample.xlsx" http://localhost:8000/api/excel/upload

# Test PyST search
curl http://localhost:8000/api/pyst/search?q=patient
```

## Troubleshooting

### PyST API Connection Issues

- Verify `PYST_API_URL` in `.env`
- Check if PyST service is running
- Test PyST API directly: `curl http://localhost:5000/api/concepts/search?q=test`

### CORS Errors

- Add frontend URL to `CORS_ORIGINS` in `.env`
- Restart the server after changing `.env`

### Excel Processing Errors

- Check file size (max 10MB)
- Verify file format (.xlsx or .xls)
- Ensure pandas and openpyxl are installed

## License

MIT
