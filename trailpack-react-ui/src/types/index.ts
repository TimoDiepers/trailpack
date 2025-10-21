// Type definitions for the application

export interface ExcelFile {
  file: File;
  name: string;
  size: number;
  uploadedAt: Date;
}

export interface ExcelColumn {
  name: string;
  type: string;
  sampleData: string[];
  isNumeric?: boolean;
}

export interface ExcelPreview {
  columns: ExcelColumn[];
  rowCount: number;
  previewRows: Record<string, any>[];
  availableSheets?: string[];
  selectedSheet?: string;
  fileId?: string; // Session file ID for later retrieval
}

export interface PystConcept {
  id: string;
  name: string;
  description?: string;
  category?: string;
  uri?: string;
  iri?: string;
  label?: string;
}

export interface ColumnMapping {
  excelColumn: string;
  pystConcept: PystConcept | null;
  confidence?: number;
  unit?: PystConcept | null; // Unit for numeric columns
  description?: string; // Custom description or comment
}

export interface MappingResult {
  mappings: ColumnMapping[];
  unmappedColumns: string[];
}

export interface License {
  name: string;
  title: string;
  path?: string;
}

export interface Contributor {
  name: string;
  role: 'author' | 'contributor' | 'maintainer' | 'publisher' | 'wrangler';
  email?: string;
  organization?: string;
}

export interface Source {
  title: string;
  path?: string;
  description?: string;
}

export interface GeneralDetails {
  name: string; // Package name (required)
  title: string; // Package title (required)
  description?: string;
  version?: string;
  profile?: string;
  keywords?: string[];
  homepage?: string;
  repository?: string;
  created?: string; // ISO date
  modified?: string; // ISO date
  licenses: License[]; // Required, at least one
  contributors: Contributor[]; // Required, at least one
  sources: Source[]; // Required, at least one
  resourceName?: string; // Resource name for the data file
}

export interface ExportConfig {
  includeMetadata: boolean;
  compressionType: 'snappy' | 'gzip' | 'none';
  outputFileName: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  qualityLevel?: 'VALID' | 'WARNING' | 'ERROR';
}

export interface WizardState {
  currentStep: number;
  excelFile: ExcelFile | null;
  excelPreview: ExcelPreview | null;
  selectedSheet: string | null; // Selected sheet name
  fileId: string | null; // Session file ID for backend retrieval
  mappings: ColumnMapping[];
  generalDetails: GeneralDetails | null;
  exportConfig: ExportConfig;
  validationResult: ValidationResult | null;
  language?: string; // PyST language selection
}
