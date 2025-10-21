import { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  LinearProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { CloudUpload } from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import type { WizardState, ExcelFile, ExcelPreview } from '../types';

interface UploadStepProps {
  wizardState: WizardState;
  updateWizardState: (updates: Partial<WizardState>) => void;
  onNext: () => void;
}

export default function UploadStep({
  updateWizardState,
  onNext,
}: UploadStepProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [initialPreview, setInitialPreview] = useState<ExcelPreview | null>(null);
  const [selectedSheet, setSelectedSheet] = useState<string>('');

  const uploadMutation = useMutation({
    mutationFn: ({ file, sheetName }: { file: File; sheetName?: string }) => 
      api.uploadExcel(file, sheetName),
    onSuccess: (data) => {
      // If this is the initial upload, show sheet selection
      if (!initialPreview && data.availableSheets && data.availableSheets.length > 1) {
        setInitialPreview(data);
        setSelectedSheet(data.selectedSheet || data.availableSheets[0]);
        return;
      }
      
      // Otherwise proceed to next step
      const excelFile: ExcelFile = {
        file: selectedFile!,
        name: selectedFile!.name,
        size: selectedFile!.size,
        uploadedAt: new Date(),
      };
      
      updateWizardState({
        excelFile,
        excelPreview: data,
        fileId: data.fileId || null, // Save file ID for backend retrieval
        selectedSheet: data.selectedSheet || null,
      });
      
      onNext();
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to upload file');
    },
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.name.match(/\.(xlsx|xls)$/)) {
        setError('Please select a valid Excel file (.xlsx or .xls)');
        return;
      }
      setSelectedFile(file);
      setInitialPreview(null);
      setSelectedSheet('');
      setError(null);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate({ file: selectedFile });
    }
  };

  const handleSheetChange = (sheet: string) => {
    setSelectedSheet(sheet);
    if (selectedFile) {
      uploadMutation.mutate({ file: selectedFile, sheetName: sheet });
    }
  };

  const handleProceed = () => {
    if (selectedFile && selectedSheet) {
      uploadMutation.mutate({ file: selectedFile, sheetName: selectedSheet });
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Upload Your Excel File
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Select an Excel file (.xlsx or .xls) to begin the mapping process.
      </Typography>

      <Paper
        variant="outlined"
        sx={{
          p: 4,
          textAlign: 'center',
          borderStyle: 'dashed',
          backgroundColor: 'background.default',
        }}
      >
        <input
          accept=".xlsx,.xls"
          style={{ display: 'none' }}
          id="file-upload"
          type="file"
          onChange={handleFileSelect}
        />
        <label htmlFor="file-upload">
          <Button
            variant="contained"
            component="span"
            startIcon={<CloudUpload />}
            size="large"
          >
            Select Excel File
          </Button>
        </label>

        {selectedFile && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body1">
              Selected: {selectedFile.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Size: {(selectedFile.size / 1024).toFixed(2)} KB
            </Typography>
          </Box>
        )}
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {uploadMutation.isPending && (
        <Box sx={{ mt: 2 }}>
          <LinearProgress />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Uploading and processing file...
          </Typography>
        </Box>
      )}

      {initialPreview && initialPreview.availableSheets && initialPreview.availableSheets.length > 1 && (
        <Paper sx={{ p: 3, mt: 2 }}>
          <Typography variant="h6" gutterBottom>
            Select Sheet
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            This Excel file contains multiple sheets. Please select which sheet to process.
          </Typography>
          
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Sheet Name</InputLabel>
            <Select
              value={selectedSheet}
              label="Sheet Name"
              onChange={(e) => handleSheetChange(e.target.value)}
            >
              {initialPreview.availableSheets.map((sheet) => (
                <MenuItem key={sheet} value={sheet}>
                  {sheet}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {initialPreview.selectedSheet === selectedSheet && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Preview ({initialPreview.rowCount} rows)
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Columns: {initialPreview.columns.map(c => c.name).join(', ')}
              </Typography>
            </Box>
          )}
        </Paper>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
        {initialPreview && initialPreview.availableSheets && initialPreview.availableSheets.length > 1 ? (
          <Button
            variant="contained"
            onClick={handleProceed}
            disabled={!selectedSheet || uploadMutation.isPending}
          >
            Continue with Selected Sheet
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleUpload}
            disabled={!selectedFile || uploadMutation.isPending}
          >
            Upload and Continue
          </Button>
        )}
      </Box>
    </Box>
  );
}
