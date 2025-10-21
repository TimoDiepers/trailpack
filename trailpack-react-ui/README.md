# Trailpack React UI

Excel to PyST Mapper - A React TypeScript web application for mapping Excel data to PyST ontology concepts and exporting to Parquet format.

## Features

- 📤 **Excel Upload**: Upload and preview Excel files (.xlsx, .xls)
- 🔗 **Column Mapping**: Map Excel columns to PyST ontology concepts
- 🔍 **Concept Search**: Search and browse PyST ontology
- ✅ **Validation**: Validate mappings before export
- 📦 **Parquet Export**: Export mapped data to Parquet format with compression options

## Tech Stack

- React 18+ with TypeScript
- Vite for build tooling
- Material-UI for UI components
- React Router for navigation
- TanStack Query for data fetching
- Axios for API calls

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API service running (default: http://localhost:8000)

### Installation

1. Clone the repository:
```bash
cd /Users/ajakobs/Documents/brightcon2025_hackthon/trailpack-react-ui
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Update `.env` with your backend API URL if different from default.

### Development

Run the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Build

Build for production:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

## Project Structure

```
src/
├── components/       # React components
│   ├── UploadStep.tsx
│   ├── MappingStep.tsx
│   ├── ValidationStep.tsx
│   └── ExportStep.tsx
├── pages/           # Page components
│   └── WizardPage.tsx
├── services/        # API services
│   └── api.ts
├── types/           # TypeScript type definitions
│   └── index.ts
├── utils/           # Utility functions
├── App.tsx          # Main application component
└── main.tsx         # Application entry point
```

## Wizard Steps

1. **Upload Excel**: Select and upload an Excel file
2. **Map Columns**: Map Excel columns to PyST concepts with auto-mapping suggestions
3. **Validate**: Validate mappings and view errors/warnings
4. **Export**: Configure and export to Parquet format

## API Integration

The application expects the following API endpoints:

- `POST /api/excel/upload` - Upload Excel file and get preview
- `GET /api/pyst/search?q=query` - Search PyST concepts
- `POST /api/mapping/auto` - Get auto-mapping suggestions
- `POST /api/mapping/validate` - Validate mappings
- `POST /api/export/parquet` - Export to Parquet

## License

MIT
