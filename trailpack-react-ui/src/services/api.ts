import axios from 'axios';
import type { ExcelPreview, PystConcept, MappingResult, ValidationResult } from '../types';
import { mockApi } from './mockApi';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API === 'true';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Upload Excel file and get preview
  uploadExcel: async (file: File, sheetName?: string): Promise<ExcelPreview> => {
    if (USE_MOCK_API) {
      return mockApi.uploadExcel(file);
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const url = sheetName 
      ? `/excel/upload?sheet_name=${encodeURIComponent(sheetName)}`
      : '/excel/upload';
    
    const response = await apiClient.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  // Search PyST ontology concepts
  searchPystConcepts: async (query: string, language: string = 'en'): Promise<PystConcept[]> => {
    if (USE_MOCK_API) {
      return mockApi.searchPystConcepts(query);
    }
    
    const response = await apiClient.get('/pyst/search', {
      params: { q: query, language },
    });
    
    return response.data;
  },

  // Get auto-mapping suggestions
  getAutoMappings: async (columns: string[]): Promise<MappingResult> => {
    if (USE_MOCK_API) {
      return mockApi.getAutoMappings(columns);
    }
    
    const response = await apiClient.post('/mapping/auto', { columns });
    
    return response.data;
  },

  // Validate mappings
  validateMappings: async (data: any): Promise<ValidationResult> => {
    if (USE_MOCK_API) {
      return mockApi.validateMappings(data);
    }
    
    const response = await apiClient.post('/validation/validate', data);
    
    return response.data;
  },

  // Export to Parquet
  exportToParquet: async (data: any): Promise<Blob> => {
    if (USE_MOCK_API) {
      return mockApi.exportToParquet(data);
    }
    
    const response = await apiClient.post('/export/parquet', data, {
      responseType: 'blob',
    });
    
    return response.data;
  },

  // Export metadata only
  exportMetadata: async (data: any): Promise<Blob> => {
    const response = await apiClient.post('/export/metadata', data, {
      responseType: 'blob',
    });
    
    return response.data;
  },

  // Export mapping config
  exportConfig: async (data: any): Promise<Blob> => {
    const response = await apiClient.post('/export/config', data, {
      responseType: 'blob',
    });
    
    return response.data;
  },
};

export default api;
