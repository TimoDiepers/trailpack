import { useState, useEffect, useCallback, useMemo, memo, useRef } from 'react';
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
  IconButton,
  Collapse,
  Stack,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import type { WizardState, ColumnMapping, PystConcept, ExcelColumn } from '../types';

interface MappingStepProps {
  wizardState: WizardState;
  updateWizardState: (updates: Partial<WizardState>) => void;
  onNext: () => void;
  onBack: () => void;
}

interface ColumnSearchState {
  [columnName: string]: {
    ontologySearch: string;
    unitSearch: string;
    showUnitSearch: boolean;
  };
}

export default function MappingStep({
  wizardState,
  updateWizardState,
  onNext,
  onBack,
}: MappingStepProps) {
  const [mappings, setMappings] = useState<ColumnMapping[]>([]);
  const [searchStates, setSearchStates] = useState<ColumnSearchState>({});
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const language = wizardState.language || 'en';

  // Initialize mappings and search states
  useEffect(() => {
    if (wizardState.excelPreview) {
      // Initialize mappings
      const initialMappings: ColumnMapping[] = wizardState.excelPreview.columns.map(
        (col) => ({
          excelColumn: col.name,
          pystConcept: null,
          unit: null,
          description: '',
        })
      );
      setMappings(initialMappings);

      // Initialize search states with first word of column name
      const initialSearchStates: ColumnSearchState = {};
      wizardState.excelPreview.columns.forEach((col) => {
        const firstWord = extractFirstWord(sanitizeSearchQuery(col.name));
        initialSearchStates[col.name] = {
          ontologySearch: firstWord,
          unitSearch: col.isNumeric ? 'unit' : '',
          showUnitSearch: false,
        };
      });
      setSearchStates(initialSearchStates);
    }
  }, [wizardState.excelPreview]);

  // Helper function to sanitize search queries
  const sanitizeSearchQuery = (query: string): string => {
    return query.replace(/[^\w\s\-.]/g, ' ').replace(/\s+/g, ' ').trim();
  };

  // Helper function to extract first word
  const extractFirstWord = (query: string): string => {
    if (!query) return '';
    const parts = query.split(' ');
    return parts[0] || '';
  };

  // Auto-mapping mutation
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

  const handleAutoMap = () => {
    autoMappingMutation.mutate();
  };

  const handleOntologyChange = useCallback((columnName: string, concept: PystConcept | null) => {
    setMappings((prev) =>
      prev.map((m) =>
        m.excelColumn === columnName ? { ...m, pystConcept: concept } : m
      )
    );
  }, []);

  const handleUnitChange = useCallback((columnName: string, unit: PystConcept | null) => {
    setMappings((prev) =>
      prev.map((m) =>
        m.excelColumn === columnName ? { ...m, unit } : m
      )
    );
  }, []);

  const handleDescriptionChange = useCallback((columnName: string, description: string) => {
    setMappings((prev) =>
      prev.map((m) =>
        m.excelColumn === columnName ? { ...m, description } : m
      )
    );
  }, []);

  const handleSearchChange = useCallback((
    columnName: string,
    field: 'ontologySearch' | 'unitSearch',
    value: string
  ) => {
    setSearchStates((prev) => ({
      ...prev,
      [columnName]: {
        ...prev[columnName],
        [field]: value,
      },
    }));
  }, []);

  const handleClearOntology = useCallback((columnName: string) => {
    setMappings((prev) =>
      prev.map((m) =>
        m.excelColumn === columnName ? { ...m, pystConcept: null } : m
      )
    );
    setSearchStates((prev) => ({
      ...prev,
      [columnName]: {
        ...prev[columnName],
        ontologySearch: '',
      },
    }));
  }, []);

  const handleClearUnit = useCallback((columnName: string) => {
    setMappings((prev) =>
      prev.map((m) =>
        m.excelColumn === columnName ? { ...m, unit: null } : m
      )
    );
    setSearchStates((prev) => ({
      ...prev,
      [columnName]: {
        ...prev[columnName],
        unitSearch: '',
      },
    }));
  }, []);

  const toggleRowExpansion = useCallback((columnName: string) => {
    setExpandedRows((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(columnName)) {
        newSet.delete(columnName);
      } else {
        newSet.add(columnName);
      }
      return newSet;
    });
  }, []);

  const handleNext = () => {
    updateWizardState({ mappings });
    onNext();
  };

  // Validation logic
  const getValidationStatus = (col: ExcelColumn, mapping: ColumnMapping) => {
    const hasOntology = !!mapping.pystConcept;
    const hasDescription = !!mapping.description && mapping.description.trim().length > 0;
    const hasUnit = !!mapping.unit;
    const needsUnit = col.isNumeric;

    // For numeric columns: must have ontology AND unit
    if (needsUnit) {
      const missingUnit = !hasUnit;
      const missingOntology = !hasOntology && !hasDescription;
      
      if (missingUnit && missingOntology) {
        return { valid: false, message: 'Numeric column requires unit AND (ontology OR description)' };
      }
      if (missingUnit) {
        return { valid: false, message: 'Numeric column requires a unit' };
      }
      if (missingOntology) {
        return { valid: false, message: 'Requires ontology mapping OR description' };
      }
    } else {
      // For non-numeric columns: must have ontology OR description
      if (!hasOntology && !hasDescription) {
        return { valid: false, message: 'Requires ontology mapping OR description' };
      }
    }

    return { valid: true, message: '' };
  };

  const canProceed = wizardState.excelPreview?.columns.every((col) => {
    const mapping = mappings.find((m) => m.excelColumn === col.name);
    if (!mapping) return false;
    return getValidationStatus(col, mapping).valid;
  }) || false;

  const ColumnMappingRow = memo(({ col }: { col: ExcelColumn }) => {
    const mapping = mappings.find((m) => m.excelColumn === col.name);
    if (!mapping) return null;

    const searchState = searchStates[col.name] || {
      ontologySearch: '',
      unitSearch: '',
      showUnitSearch: false,
    };
    const isExpanded = expandedRows.has(col.name);
    const validation = useMemo(() => getValidationStatus(col, mapping), [col, mapping]);

    // Local state for input values to prevent parent re-renders
    const [localOntologySearch, setLocalOntologySearch] = useState(searchState.ontologySearch);
    const [localUnitSearch, setLocalUnitSearch] = useState(searchState.unitSearch);
    const [localDescription, setLocalDescription] = useState(mapping.description || '');

    // Track if we've initialized from parent state
    const initializedRef = useRef(false);

    // Only sync from parent on initial mount, NOT on every parent update
    useEffect(() => {
      if (!initializedRef.current) {
        setLocalOntologySearch(searchState.ontologySearch);
        setLocalUnitSearch(searchState.unitSearch);
        setLocalDescription(mapping.description || '');
        initializedRef.current = true;
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Empty deps - only run once on mount

    // Debounced update to parent state for ontology search
    useEffect(() => {
      const timeoutId = setTimeout(() => {
        if (localOntologySearch !== searchState.ontologySearch) {
          handleSearchChange(col.name, 'ontologySearch', localOntologySearch);
        }
      }, 500);
      return () => clearTimeout(timeoutId);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [localOntologySearch]);

    // Debounced update to parent state for unit search
    useEffect(() => {
      const timeoutId = setTimeout(() => {
        if (localUnitSearch !== searchState.unitSearch) {
          handleSearchChange(col.name, 'unitSearch', localUnitSearch);
        }
      }, 500);
      return () => clearTimeout(timeoutId);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [localUnitSearch]);

    // Debounced update to parent state for description (debounce to prevent re-renders)
    useEffect(() => {
      const timeoutId = setTimeout(() => {
        if (localDescription !== (mapping.description || '')) {
          handleDescriptionChange(col.name, localDescription);
        }
      }, 300); // Short debounce to prevent re-renders while typing
      return () => clearTimeout(timeoutId);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [localDescription]);

    // ALWAYS call hooks - enabled flag controls when they actually fetch
    const ontologyQuery = useQuery({
      queryKey: ['pyst-ontology', col.name, searchState.ontologySearch, language],
      queryFn: () => api.searchPystConcepts(searchState.ontologySearch, language),
      enabled: searchState.ontologySearch.length >= 2, // Always search when user types
      staleTime: 30000, // Cache for 30 seconds
    });

    const unitQuery = useQuery({
      queryKey: ['pyst-unit', col.name, searchState.unitSearch, language],
      queryFn: () => api.searchPystConcepts(searchState.unitSearch, language),
      enabled: col.isNumeric === true && searchState.unitSearch.length >= 2, // Always search when user types
      staleTime: 30000, // Cache for 30 seconds
    });

    return (
      <>
        <TableRow>
          <TableCell>
            <Stack direction="row" alignItems="center" spacing={1}>
              <IconButton
                size="small"
                onClick={() => toggleRowExpansion(col.name)}
              >
                {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
              <Box>
                <Typography variant="body2" fontWeight="bold">
                  {col.name}
                </Typography>
                {col.isNumeric && (
                  <Chip label="Numeric" size="small" color="primary" sx={{ mt: 0.5 }} />
                )}
              </Box>
            </Stack>
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
            {!validation.valid && (
              <Alert severity="warning" sx={{ mb: 1 }}>
                {validation.message}
              </Alert>
            )}
            {mapping.pystConcept ? (
              <Chip
                label={mapping.pystConcept.name || mapping.pystConcept.label}
                onDelete={() => handleClearOntology(col.name)}
                color="success"
              />
            ) : (
              <Typography variant="body2" color="text.secondary">
                No ontology mapped
              </Typography>
            )}
            {col.isNumeric && mapping.unit && (
              <Chip
                label={`Unit: ${mapping.unit.name || mapping.unit.label}`}
                onDelete={() => handleClearUnit(col.name)}
                color="info"
                sx={{ ml: 1 }}
              />
            )}
          </TableCell>
        </TableRow>
        <TableRow>
          <TableCell colSpan={4} sx={{ py: 0, border: 0 }}>
            <Collapse in={isExpanded} timeout="auto" unmountOnExit>
              <Box sx={{ p: 2, bgcolor: 'grey.50' }}>
                {/* Ontology Search */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Search for Ontology
                  </Typography>
                  <Autocomplete
                    freeSolo
                    options={ontologyQuery.data || []}
                    getOptionLabel={(option) => {
                      if (typeof option === 'string') return option;
                      return option.name || option.label || '';
                    }}
                    value={mapping.pystConcept}
                    inputValue={localOntologySearch}
                    onChange={(_, value) => {
                      if (typeof value === 'string') return; // Ignore free text
                      handleOntologyChange(col.name, value);
                    }}
                    onInputChange={(_, value, reason) => {
                      if (reason === 'input' || reason === 'clear') {
                        setLocalOntologySearch(value);
                      }
                    }}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        placeholder="Type to search ontology concepts..."
                        size="small"
                        fullWidth
                      />
                    )}
                    renderOption={(props, option) => {
                      if (typeof option === 'string') return null;
                      return (
                        <li {...props} key={option.id || option.uri}>
                          <Box>
                            <Typography variant="body2">
                              {option.name || option.label}
                            </Typography>
                            {option.description && (
                              <Typography variant="caption" color="text.secondary">
                                {option.description.substring(0, 100)}
                                {option.description.length > 100 ? '...' : ''}
                              </Typography>
                            )}
                          </Box>
                        </li>
                      );
                    }}
                    loading={ontologyQuery.isLoading}
                    loadingText="Searching..."
                    noOptionsText={
                      searchState.ontologySearch.length < 2
                        ? 'Type at least 2 characters to search'
                        : 'No concepts found'
                    }
                  />
                  {mapping.pystConcept?.description && (
                    <Alert severity="info" icon={<InfoIcon />} sx={{ mt: 1 }}>
                      <Typography variant="body2">
                        <strong>Description:</strong> {mapping.pystConcept.description}
                      </Typography>
                      {(mapping.pystConcept.uri || mapping.pystConcept.id) && (
                        <Typography variant="caption" component="div" sx={{ mt: 0.5 }}>
                          <a
                            href={mapping.pystConcept.uri || mapping.pystConcept.id}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            View on vocab.sentier.dev →
                          </a>
                        </Typography>
                      )}
                    </Alert>
                  )}
                </Box>

                {/* Unit Search (for numeric columns) */}
                {col.isNumeric && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom color="error">
                      Search for Unit (Required for Numeric Columns)
                    </Typography>
                    <Autocomplete
                      freeSolo
                      options={unitQuery.data || []}
                      getOptionLabel={(option) => {
                        if (typeof option === 'string') return option;
                        return option.name || option.label || '';
                      }}
                      value={mapping.unit}
                      inputValue={localUnitSearch}
                      onChange={(_, value) => {
                        if (typeof value === 'string') return; // Ignore free text
                        handleUnitChange(col.name, value);
                      }}
                      onInputChange={(_, value, reason) => {
                        if (reason === 'input' || reason === 'clear') {
                          setLocalUnitSearch(value);
                        }
                      }}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          placeholder="Type to search units (e.g., kg, m, celsius)..."
                          size="small"
                          fullWidth
                          error={!mapping.unit}
                        />
                      )}
                      renderOption={(props, option) => {
                        if (typeof option === 'string') return null;
                        return (
                          <li {...props} key={option.id || option.uri}>
                            <Box>
                              <Typography variant="body2">
                                {option.name || option.label}
                              </Typography>
                              {option.description && (
                                <Typography variant="caption" color="text.secondary">
                                  {option.description.substring(0, 100)}
                                  {option.description.length > 100 ? '...' : ''}
                                </Typography>
                              )}
                            </Box>
                          </li>
                        );
                      }}
                      loading={unitQuery.isLoading}
                      loadingText="Searching..."
                      noOptionsText={
                        searchState.unitSearch.length < 2
                          ? 'Type at least 2 characters to search'
                          : 'No units found'
                      }
                    />
                    {mapping.unit?.description && (
                      <Alert severity="info" icon={<InfoIcon />} sx={{ mt: 1 }}>
                        <Typography variant="body2">
                          <strong>Unit Description:</strong> {mapping.unit.description}
                        </Typography>
                        {(mapping.unit.uri || mapping.unit.id) && (
                          <Typography variant="caption" component="div" sx={{ mt: 0.5 }}>
                            <a
                              href={mapping.unit.uri || mapping.unit.id}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              View on vocab.sentier.dev →
                            </a>
                          </Typography>
                        )}
                      </Alert>
                    )}
                  </Box>
                )}

                {/* Description Field */}
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    {mapping.pystConcept?.description
                      ? 'Additional Comment (Optional)'
                      : 'Column Description (Required if no ontology mapping)'}
                  </Typography>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    size="small"
                    placeholder={
                      mapping.pystConcept?.description
                        ? 'Add optional comments or notes...'
                        : 'Describe what this column represents...'
                    }
                    value={localDescription}
                    onChange={(e) => setLocalDescription(e.target.value)}
                    error={!mapping.pystConcept && !localDescription}
                    helperText={
                      !mapping.pystConcept && !localDescription
                        ? 'Please provide either an ontology mapping or a description'
                        : ''
                    }
                  />
                </Box>
              </Box>
            </Collapse>
          </TableCell>
        </TableRow>
      </>
    );
  }, (prevProps, nextProps) => {
    // Custom comparison: only re-render if column name changes
    return prevProps.col.name === nextProps.col.name;
  });

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
          {autoMappingMutation.isPending ? 'Auto-Mapping...' : 'Auto-Map Suggestions'}
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 2 }}>
        <Typography variant="body2">
          Click the expand icon (▼) on each row to search for ontology concepts and units.
        </Typography>
        <Typography variant="body2" sx={{ mt: 1 }}>
          <strong>Requirements:</strong>
        </Typography>
        <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
          <li>Numeric columns require both a <strong>unit</strong> and an <strong>ontology mapping OR description</strong></li>
          <li>Non-numeric columns require an <strong>ontology mapping OR description</strong></li>
        </ul>
      </Alert>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell width="25%">Excel Column</TableCell>
              <TableCell width="15%">Data Type</TableCell>
              <TableCell width="20%">Sample Data</TableCell>
              <TableCell width="40%">Mapping Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {wizardState.excelPreview?.columns.map((col) => (
              <ColumnMappingRow key={col.name} col={col} />
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button onClick={onBack}>Back</Button>
        <Button
          variant="contained"
          onClick={handleNext}
          disabled={!canProceed}
        >
          Continue to General Details
        </Button>
      </Box>
    </Box>
  );
}
