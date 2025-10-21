// Mock data for development/testing
import type { ExcelPreview, PystConcept, MappingResult, ValidationResult } from '../types';

// Simulate API delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const mockApi = {
  uploadExcel: async (_file: File): Promise<ExcelPreview> => {
    await delay(1000);
    
    return {
      columns: [
        {
          name: 'Patient ID',
          type: 'string',
          sampleData: ['P001', 'P002', 'P003'],
        },
        {
          name: 'Age',
          type: 'number',
          sampleData: ['45', '32', '67'],
        },
        {
          name: 'Blood Pressure',
          type: 'string',
          sampleData: ['120/80', '130/85', '140/90'],
        },
        {
          name: 'Diagnosis',
          type: 'string',
          sampleData: ['Hypertension', 'Diabetes', 'Normal'],
        },
      ],
      rowCount: 150,
      previewRows: [
        { 'Patient ID': 'P001', 'Age': 45, 'Blood Pressure': '120/80', 'Diagnosis': 'Hypertension' },
        { 'Patient ID': 'P002', 'Age': 32, 'Blood Pressure': '130/85', 'Diagnosis': 'Diabetes' },
        { 'Patient ID': 'P003', 'Age': 67, 'Blood Pressure': '140/90', 'Diagnosis': 'Normal' },
      ],
      availableSheets: ['Sheet1', 'PatientData', 'Summary'],
      selectedSheet: 'Sheet1',
    };
  },

  searchPystConcepts: async (query: string): Promise<PystConcept[]> => {
    await delay(500);
    
    const concepts: PystConcept[] = [
      {
        id: 'pyst:patient_identifier',
        name: 'Patient Identifier',
        description: 'Unique identifier for a patient',
        category: 'Demographics',
      },
      {
        id: 'pyst:age',
        name: 'Patient Age',
        description: 'Age of the patient in years',
        category: 'Demographics',
      },
      {
        id: 'pyst:blood_pressure',
        name: 'Blood Pressure Measurement',
        description: 'Systolic/Diastolic blood pressure reading',
        category: 'Vital Signs',
      },
      {
        id: 'pyst:diagnosis',
        name: 'Clinical Diagnosis',
        description: 'Medical diagnosis or condition',
        category: 'Clinical',
      },
      {
        id: 'pyst:temperature',
        name: 'Body Temperature',
        description: 'Patient body temperature',
        category: 'Vital Signs',
      },
    ];
    
    return concepts.filter(c => 
      c.name.toLowerCase().includes(query.toLowerCase()) ||
      c.description?.toLowerCase().includes(query.toLowerCase())
    );
  },

  getAutoMappings: async (columns: string[]): Promise<MappingResult> => {
    await delay(800);
    
    const mappingRules: Record<string, PystConcept> = {
      'Patient ID': {
        id: 'pyst:patient_identifier',
        name: 'Patient Identifier',
        description: 'Unique identifier for a patient',
        category: 'Demographics',
      },
      'Age': {
        id: 'pyst:age',
        name: 'Patient Age',
        description: 'Age of the patient in years',
        category: 'Demographics',
      },
      'Blood Pressure': {
        id: 'pyst:blood_pressure',
        name: 'Blood Pressure Measurement',
        description: 'Systolic/Diastolic blood pressure reading',
        category: 'Vital Signs',
      },
      'Diagnosis': {
        id: 'pyst:diagnosis',
        name: 'Clinical Diagnosis',
        description: 'Medical diagnosis or condition',
        category: 'Clinical',
      },
    };
    
    const mappings = columns.map(col => ({
      excelColumn: col,
      pystConcept: mappingRules[col] || null,
      confidence: mappingRules[col] ? 0.85 : 0,
    }));
    
    const unmappedColumns = columns.filter(col => !mappingRules[col]);
    
    return { mappings, unmappedColumns };
  },

  validateMappings: async (mappings: any): Promise<ValidationResult> => {
    await delay(600);
    
    const errors: string[] = [];
    const warnings: string[] = [];
    
    // Simulate some validation
    if (!mappings || mappings.length === 0) {
      errors.push('No mappings provided');
    }
    
    const unmapped = mappings.filter((m: any) => !m.pystConcept);
    if (unmapped.length > 0) {
      errors.push(`${unmapped.length} columns are not mapped`);
    }
    
    // Add a warning
    if (mappings.length < 3) {
      warnings.push('Less than 3 columns mapped. Consider adding more data.');
    }
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings,
    };
  },

  exportToParquet: async (data: any): Promise<Blob> => {
    await delay(1500);
    
    // Create a mock parquet file (actually just a text file)
    const mockContent = `Mock Parquet Export
File: ${data.file?.name || 'unknown'}
Mappings: ${data.mappings?.length || 0}
Generated: ${new Date().toISOString()}
Compression: ${data.config?.compressionType || 'none'}
`;
    
    return new Blob([mockContent], { type: 'application/octet-stream' });
  },
};
