import { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  TextField,
  FormControlLabel,
  Checkbox,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
  Chip,
  Divider,
  Stack,
  Card,
  CardContent,
} from '@mui/material';
import {
  Download,
  Refresh,
  CheckCircle,
  Description,
  Settings,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import type { WizardState, ExportConfig } from '../types';

interface ExportStepProps {
  wizardState: WizardState;
  updateWizardState: (updates: Partial<WizardState>) => void;
  onBack: () => void;
  onReset: () => void;
}

export default function ExportStep({
  wizardState,
  updateWizardState,
  onBack,
  onReset,
}: ExportStepProps) {
  const [exportConfig, setExportConfig] = useState<ExportConfig>(
    wizardState.exportConfig
  );
  const [exportComplete, setExportComplete] = useState(false);

  // Get quality level from validation
  const qualityLevel = wizardState.validationResult?.qualityLevel || 'UNKNOWN';
  const qualityColor = 
    qualityLevel === 'VALID' ? 'success' :
    qualityLevel === 'WARNING' ? 'warning' : 'error';

  const exportMutation = useMutation({
    mutationFn: () => {
      if (!wizardState.fileId || !wizardState.selectedSheet || !wizardState.generalDetails) {
        throw new Error('Missing required data for export');
      }
      
      const exportData = {
        fileId: wizardState.fileId,
        sheetName: wizardState.selectedSheet,
        mappings: wizardState.mappings,
        generalDetails: wizardState.generalDetails,
        config: exportConfig,
      };
      return api.exportToParquet(exportData);
    },
    onSuccess: (blob) => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = exportConfig.outputFileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setExportComplete(true);
    },
  });

  const metadataMutation = useMutation({
    mutationFn: () => {
      if (!wizardState.fileId || !wizardState.selectedSheet || !wizardState.generalDetails) {
        throw new Error('Missing required data for export');
      }
      
      const exportData = {
        fileId: wizardState.fileId,
        sheetName: wizardState.selectedSheet,
        mappings: wizardState.mappings,
        generalDetails: wizardState.generalDetails,
        config: exportConfig,
      };
      return api.exportMetadata(exportData);
    },
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'datapackage.json';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
  });

  const configMutation = useMutation({
    mutationFn: () => {
      if (!wizardState.fileId || !wizardState.selectedSheet || !wizardState.generalDetails) {
        throw new Error('Missing required data for export');
      }
      
      const exportData = {
        fileId: wizardState.fileId,
        sheetName: wizardState.selectedSheet,
        mappings: wizardState.mappings,
        generalDetails: wizardState.generalDetails,
        config: exportConfig,
      };
      return api.exportConfig(exportData);
    },
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'mapping-config.json';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
  });

  const handleExport = () => {
    updateWizardState({ exportConfig });
    exportMutation.mutate();
  };

  const handleExportMetadata = () => {
    metadataMutation.mutate();
  };

  const handleExportConfig = () => {
    configMutation.mutate();
  };

  const handleConfigChange = (updates: Partial<ExportConfig>) => {
    setExportConfig((prev) => ({ ...prev, ...updates }));
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Export Data Package
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Export your mapped data as a Parquet file with embedded Frictionless DataPackage metadata.
      </Typography>

      {/* Quality Level Indicator */}
      <Card sx={{ mb: 3, bgcolor: qualityColor === 'success' ? 'success.50' : qualityColor === 'warning' ? 'warning.50' : 'error.50' }}>
        <CardContent>
          <Stack direction="row" spacing={2} alignItems="center">
            <CheckCircle color={qualityColor} />
            <Box flex={1}>
              <Typography variant="subtitle1">
                Data Quality: <Chip label={qualityLevel} color={qualityColor} size="small" />
              </Typography>
              {wizardState.validationResult?.errors && wizardState.validationResult.errors.length > 0 && (
                <Typography variant="body2" color="error">
                  {wizardState.validationResult.errors.length} error(s) found
                </Typography>
              )}
              {wizardState.validationResult?.warnings && wizardState.validationResult.warnings.length > 0 && (
                <Typography variant="body2" color="warning.main">
                  {wizardState.validationResult.warnings.length} warning(s)
                </Typography>
              )}
            </Box>
          </Stack>
        </CardContent>
      </Card>

      {/* Export Configuration */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          <Settings sx={{ verticalAlign: 'middle', mr: 1 }} />
          Export Settings
        </Typography>
        
        <TextField
          fullWidth
          label="Output File Name"
          value={exportConfig.outputFileName}
          onChange={(e) =>
            handleConfigChange({ outputFileName: e.target.value })
          }
          sx={{ mb: 2 }}
          helperText="The Parquet file name for download"
        />

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Compression Type</InputLabel>
          <Select
            value={exportConfig.compressionType}
            label="Compression Type"
            onChange={(e) =>
              handleConfigChange({
                compressionType: e.target.value as 'snappy' | 'gzip' | 'none',
              })
            }
          >
            <MenuItem value="snappy">Snappy (Recommended)</MenuItem>
            <MenuItem value="gzip">GZIP</MenuItem>
            <MenuItem value="none">None</MenuItem>
          </Select>
        </FormControl>

        <FormControlLabel
          control={
            <Checkbox
              checked={exportConfig.includeMetadata}
              onChange={(e) =>
                handleConfigChange({ includeMetadata: e.target.checked })
              }
            />
          }
          label="Embed metadata in Parquet file (recommended)"
        />
      </Paper>

      {/* Export Summary */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: 'grey.50' }}>
        <Typography variant="subtitle1" gutterBottom>
          Export Summary
        </Typography>
        <Divider sx={{ my: 1 }} />
        <Stack spacing={1}>
          <Box display="flex" justifyContent="space-between">
            <Typography variant="body2">Package Name:</Typography>
            <Typography variant="body2" fontWeight="bold">
              {wizardState.generalDetails?.name || 'Not set'}
            </Typography>
          </Box>
          <Box display="flex" justifyContent="space-between">
            <Typography variant="body2">File:</Typography>
            <Typography variant="body2">{wizardState.excelFile?.name}</Typography>
          </Box>
          <Box display="flex" justifyContent="space-between">
            <Typography variant="body2">Sheet:</Typography>
            <Typography variant="body2">{wizardState.selectedSheet}</Typography>
          </Box>
          <Box display="flex" justifyContent="space-between">
            <Typography variant="body2">Columns:</Typography>
            <Typography variant="body2">{wizardState.mappings.length}</Typography>
          </Box>
          <Box display="flex" justifyContent="space-between">
            <Typography variant="body2">Rows:</Typography>
            <Typography variant="body2">{wizardState.excelPreview?.rowCount || 0}</Typography>
          </Box>
          <Box display="flex" justifyContent="space-between">
            <Typography variant="body2">Compression:</Typography>
            <Typography variant="body2">{exportConfig.compressionType.toUpperCase()}</Typography>
          </Box>
          <Box display="flex" justifyContent="space-between">
            <Typography variant="body2">Licenses:</Typography>
            <Typography variant="body2">{wizardState.generalDetails?.licenses.length || 0}</Typography>
          </Box>
          <Box display="flex" justifyContent="space-between">
            <Typography variant="body2">Contributors:</Typography>
            <Typography variant="body2">{wizardState.generalDetails?.contributors.length || 0}</Typography>
          </Box>
        </Stack>
      </Paper>

      {/* Error/Success Messages */}
      {exportMutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to export Parquet file. Please try again.
        </Alert>
      )}

      {metadataMutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to export metadata. Please try again.
        </Alert>
      )}

      {configMutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to export configuration. Please try again.
        </Alert>
      )}

      {exportComplete && (
        <Alert severity="success" sx={{ mb: 2 }} icon={<CheckCircle />}>
          <Typography variant="subtitle2">Export completed successfully!</Typography>
          <Typography variant="body2">
            Your Parquet file with embedded metadata has been downloaded.
          </Typography>
        </Alert>
      )}

      {/* Loading States */}
      {exportMutation.isPending && (
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <CircularProgress size={20} sx={{ mr: 2 }} />
          <Typography>Exporting to Parquet format with embedded metadata...</Typography>
        </Box>
      )}

      {/* Download Buttons */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          Download Options
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Choose what to download. The Parquet file includes embedded metadata.
        </Typography>
        
        <Stack spacing={2}>
          {/* Main Parquet Export */}
          <Button
            variant="contained"
            size="large"
            fullWidth
            startIcon={<Download />}
            onClick={handleExport}
            disabled={exportMutation.isPending || exportComplete}
          >
            Export Parquet with Metadata
          </Button>

          <Divider>
            <Chip label="Additional Downloads" size="small" />
          </Divider>

          {/* Metadata JSON */}
          <Button
            variant="outlined"
            fullWidth
            startIcon={<Description />}
            onClick={handleExportMetadata}
            disabled={metadataMutation.isPending}
          >
            {metadataMutation.isPending ? (
              <>
                <CircularProgress size={16} sx={{ mr: 1 }} />
                Downloading...
              </>
            ) : (
              'Download Metadata (datapackage.json)'
            )}
          </Button>

          {/* Config JSON */}
          <Button
            variant="outlined"
            fullWidth
            startIcon={<Settings />}
            onClick={handleExportConfig}
            disabled={configMutation.isPending}
          >
            {configMutation.isPending ? (
              <>
                <CircularProgress size={16} sx={{ mr: 1 }} />
                Downloading...
              </>
            ) : (
              'Download Mapping Config (mapping-config.json)'
            )}
          </Button>
        </Stack>
      </Paper>

      {/* Navigation Buttons */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button onClick={onBack} disabled={exportMutation.isPending}>
          Back
        </Button>
        <Box>
          {exportComplete && (
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={onReset}
            >
              Start Over
            </Button>
          )}
        </Box>
      </Box>
    </Box>
  );
}
