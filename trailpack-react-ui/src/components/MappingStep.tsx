import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Autocomplete,
  TextField,
  Chip,
  Alert,
} from '@mui/material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import type { WizardState, ColumnMapping, PystConcept } from '../types';

interface MappingStepProps {
  wizardState: WizardState;
  updateWizardState: (updates: Partial<WizardState>) => void;
  onNext: () => void;
  onBack: () => void;
}

export default function MappingStep({
  wizardState,
  updateWizardState,
  onNext,
  onBack,
}: MappingStepProps) {
  const [mappings, setMappings] = useState<ColumnMapping[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    if (wizardState.excelPreview) {
      const initialMappings: ColumnMapping[] = wizardState.excelPreview.columns.map(
        (col) => ({
          excelColumn: col.name,
          pystConcept: null,
        })
      );
      setMappings(initialMappings);
    }
  }, [wizardState.excelPreview]);

  const autoMappingMutation = useMutation({
    mutationFn: () => {
      const columnNames = wizardState.excelPreview?.columns.map((c) => c.name) || [];
      return api.getAutoMappings(columnNames);
    },
    onSuccess: (data) => {
      const updatedMappings = mappings.map((mapping) => {
        const autoMapping = data.mappings.find(
          (m) => m.excelColumn === mapping.excelColumn
        );
        return autoMapping || mapping;
      });
      setMappings(updatedMappings);
    },
  });

  const searchQuery_ = useQuery({
    queryKey: ['pyst-search', searchQuery],
    queryFn: () => api.searchPystConcepts(searchQuery),
    enabled: searchQuery.length > 2,
  });

  const handleAutoMap = () => {
    autoMappingMutation.mutate();
  };

  const handleMappingChange = (columnName: string, concept: PystConcept | null) => {
    setMappings((prev) =>
      prev.map((m) =>
        m.excelColumn === columnName ? { ...m, pystConcept: concept } : m
      )
    );
  };

  const handleNext = () => {
    updateWizardState({ mappings });
    onNext();
  };

  const unmappedCount = mappings.filter((m) => !m.pystConcept).length;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">
          Map Excel Columns to PyST Concepts
        </Typography>
        <Button
          variant="outlined"
          onClick={handleAutoMap}
          disabled={autoMappingMutation.isPending}
        >
          Auto-Map Suggestions
        </Button>
      </Box>

      {unmappedCount > 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {unmappedCount} column(s) still need to be mapped
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Excel Column</TableCell>
              <TableCell>Data Type</TableCell>
              <TableCell>Sample Data</TableCell>
              <TableCell width="40%">PyST Concept</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {wizardState.excelPreview?.columns.map((col) => {
              const mapping = mappings.find((m) => m.excelColumn === col.name);
              return (
                <TableRow key={col.name}>
                  <TableCell>
                    <strong>{col.name}</strong>
                  </TableCell>
                  <TableCell>
                    <Chip label={col.type} size="small" />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {col.sampleData.slice(0, 2).join(', ')}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Autocomplete
                      options={searchQuery_.data || []}
                      getOptionLabel={(option) => option.name}
                      value={mapping?.pystConcept || null}
                      onChange={(_, value) =>
                        handleMappingChange(col.name, value)
                      }
                      onInputChange={(_, value) => setSearchQuery(value)}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          placeholder="Search concepts..."
                          size="small"
                        />
                      )}
                      loading={searchQuery_.isLoading}
                    />
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button onClick={onBack}>Back</Button>
        <Button
          variant="contained"
          onClick={handleNext}
          disabled={unmappedCount > 0}
        >
          Continue to Validation
        </Button>
      </Box>
    </Box>
  );
}
