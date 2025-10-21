import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  Alert,
  AlertTitle,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Divider,
  CircularProgress,
  Stack,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import type { WizardState, ValidationResult } from '../types';

interface ValidationStepProps {
  wizardState: WizardState;
  updateWizardState: (updates: Partial<WizardState>) => void;
  onNext: () => void;
  onBack: () => void;
}

export default function ValidationStep({
  wizardState,
  updateWizardState,
  onNext,
  onBack,
}: ValidationStepProps) {
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [hasValidated, setHasValidated] = useState(false);

  const validateMutation = useMutation({
    mutationFn: async () => {
      // Build validation request
      const request = {
        mappings: wizardState.mappings,
        generalDetails: wizardState.generalDetails,
        excelPreview: wizardState.excelPreview,
      };
      return api.validateMappings(request);
    },
    onSuccess: (data) => {
      setValidationResult(data);
      setHasValidated(true);
      updateWizardState({ validationResult: data });
    },
    onError: (error: any) => {
      const errorResult: ValidationResult = {
        isValid: false,
        errors: [error.message || 'Validation failed'],
        warnings: [],
        qualityLevel: 'ERROR',
      };
      setValidationResult(errorResult);
      setHasValidated(true);
    },
  });

  // Auto-validate on mount if not already validated
  useEffect(() => {
    if (!hasValidated && wizardState.mappings.length > 0 && wizardState.generalDetails) {
      validateMutation.mutate();
    }
  }, []);

  const handleValidate = () => {
    setHasValidated(false);
    validateMutation.mutate();
  };

  const handleNext = () => {
    if (validationResult?.isValid) {
      onNext();
    }
  };

  const getQualityLevelColor = (level?: string) => {
    switch (level) {
      case 'VALID':
        return 'success';
      case 'WARNING':
        return 'warning';
      case 'ERROR':
        return 'error';
      default:
        return 'info';
    }
  };

  const getQualityLevelIcon = (level?: string) => {
    switch (level) {
      case 'VALID':
        return <CheckCircleIcon color="success" />;
      case 'WARNING':
        return <WarningIcon color="warning" />;
      case 'ERROR':
        return <ErrorIcon color="error" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Validation & Quality Check
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Review validation results to ensure your data package meets quality standards
      </Typography>

      {/* Validation Controls */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <Button
            variant="contained"
            onClick={handleValidate}
            disabled={validateMutation.isPending}
            startIcon={validateMutation.isPending ? <CircularProgress size={20} /> : undefined}
          >
            {validateMutation.isPending ? 'Validating...' : 'Run Validation'}
          </Button>
          {hasValidated && validationResult && (
            <Chip
              icon={getQualityLevelIcon(validationResult.qualityLevel)}
              label={`Quality Level: ${validationResult.qualityLevel || 'UNKNOWN'}`}
              color={getQualityLevelColor(validationResult.qualityLevel)}
              variant="outlined"
            />
          )}
        </Stack>
      </Paper>

      {/* Validation Results */}
      {hasValidated && validationResult && (
        <>
          {/* Overall Status */}
          <Alert
            severity={validationResult.isValid ? 'success' : 'error'}
            sx={{ mb: 3 }}
          >
            <AlertTitle>
              {validationResult.isValid
                ? 'Validation Passed ✓'
                : 'Validation Failed ✗'}
            </AlertTitle>
            {validationResult.isValid
              ? 'Your data package meets all required standards and is ready for export.'
              : 'Please review and fix the errors below before proceeding.'}
          </Alert>

          {/* Errors Section */}
          {validationResult.errors.length > 0 && (
            <Accordion defaultExpanded={true}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Stack direction="row" spacing={2} alignItems="center">
                  <ErrorIcon color="error" />
                  <Typography variant="subtitle1">
                    Errors ({validationResult.errors.length})
                  </Typography>
                  <Chip
                    label="Must Fix"
                    color="error"
                    size="small"
                  />
                </Stack>
              </AccordionSummary>
              <AccordionDetails>
                <List>
                  {validationResult.errors.map((error, index) => (
                    <ListItem key={index} alignItems="flex-start">
                      <ListItemIcon>
                        <ErrorIcon color="error" />
                      </ListItemIcon>
                      <ListItemText
                        primary={error}
                        primaryTypographyProps={{ color: 'error' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Warnings Section */}
          {validationResult.warnings.length > 0 && (
            <Accordion defaultExpanded={validationResult.errors.length === 0}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Stack direction="row" spacing={2} alignItems="center">
                  <WarningIcon color="warning" />
                  <Typography variant="subtitle1">
                    Warnings ({validationResult.warnings.length})
                  </Typography>
                  <Chip
                    label="Recommended"
                    color="warning"
                    size="small"
                  />
                </Stack>
              </AccordionSummary>
              <AccordionDetails>
                <List>
                  {validationResult.warnings.map((warning, index) => (
                    <ListItem key={index} alignItems="flex-start">
                      <ListItemIcon>
                        <WarningIcon color="warning" />
                      </ListItemIcon>
                      <ListItemText
                        primary={warning}
                        primaryTypographyProps={{ color: 'warning.main' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Validation Summary */}
          <Paper sx={{ p: 3, mt: 3 }}>
            <Typography variant="subtitle1" gutterBottom fontWeight="bold">
              Validation Summary
            </Typography>
            <Divider sx={{ my: 2 }} />
            
            <TableContainer>
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell><strong>Dataset</strong></TableCell>
                    <TableCell>
                      {wizardState.generalDetails?.title || 'Untitled'}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Package Name</strong></TableCell>
                    <TableCell>
                      {wizardState.generalDetails?.name || 'N/A'}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Version</strong></TableCell>
                    <TableCell>
                      {wizardState.generalDetails?.version || '1.0.0'}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Columns</strong></TableCell>
                    <TableCell>{wizardState.mappings.length}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Mapped Columns</strong></TableCell>
                    <TableCell>
                      {wizardState.mappings.filter(m => m.pystConcept || m.description).length}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Numeric Columns</strong></TableCell>
                    <TableCell>
                      {wizardState.excelPreview?.columns.filter(c => c.isNumeric).length || 0}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Units Defined</strong></TableCell>
                    <TableCell>
                      {wizardState.mappings.filter(m => m.unit).length}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Licenses</strong></TableCell>
                    <TableCell>
                      {wizardState.generalDetails?.licenses?.length || 0}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Contributors</strong></TableCell>
                    <TableCell>
                      {wizardState.generalDetails?.contributors?.length || 0}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Sources</strong></TableCell>
                    <TableCell>
                      {wizardState.generalDetails?.sources?.length || 0}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Quality Level</strong></TableCell>
                    <TableCell>
                      <Chip
                        icon={getQualityLevelIcon(validationResult.qualityLevel)}
                        label={validationResult.qualityLevel || 'UNKNOWN'}
                        color={getQualityLevelColor(validationResult.qualityLevel)}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>

          {/* Column Details */}
          <Accordion sx={{ mt: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Stack direction="row" spacing={2} alignItems="center">
                <InfoIcon color="info" />
                <Typography variant="subtitle1">
                  Column Mapping Details
                </Typography>
              </Stack>
            </AccordionSummary>
            <AccordionDetails>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Column</strong></TableCell>
                      <TableCell><strong>Type</strong></TableCell>
                      <TableCell><strong>Ontology</strong></TableCell>
                      <TableCell><strong>Unit</strong></TableCell>
                      <TableCell><strong>Description</strong></TableCell>
                      <TableCell><strong>Status</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {wizardState.mappings.map((mapping, index) => {
                      const column = wizardState.excelPreview?.columns.find(
                        c => c.name === mapping.excelColumn
                      );
                      const hasOntology = !!mapping.pystConcept;
                      const hasUnit = !!mapping.unit;
                      const hasDescription = !!mapping.description;
                      const needsUnit = column?.isNumeric;
                      
                      let status = 'success';
                      let statusText = 'Valid';
                      
                      if (needsUnit && !hasUnit) {
                        status = 'error';
                        statusText = 'Missing Unit';
                      } else if (!hasOntology && !hasDescription) {
                        status = 'error';
                        statusText = 'Missing Info';
                      } else if (!hasOntology) {
                        status = 'warning';
                        statusText = 'No Ontology';
                      }
                      
                      return (
                        <TableRow key={index}>
                          <TableCell>{mapping.excelColumn}</TableCell>
                          <TableCell>
                            <Chip
                              label={column?.type || 'unknown'}
                              size="small"
                              color={column?.isNumeric ? 'primary' : 'default'}
                            />
                          </TableCell>
                          <TableCell>
                            {mapping.pystConcept ? (
                              <Typography variant="body2" noWrap>
                                {mapping.pystConcept.name || mapping.pystConcept.label}
                              </Typography>
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                None
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            {mapping.unit ? (
                              <Typography variant="body2" noWrap>
                                {mapping.unit.name || mapping.unit.label}
                              </Typography>
                            ) : column?.isNumeric ? (
                              <Typography variant="body2" color="error">
                                Required
                              </Typography>
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                N/A
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            {mapping.description ? (
                              <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                                {mapping.description}
                              </Typography>
                            ) : mapping.pystConcept?.description ? (
                              <Typography variant="body2" color="text.secondary" noWrap>
                                (From ontology)
                              </Typography>
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                None
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={statusText}
                              size="small"
                              color={status as any}
                            />
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>
        </>
      )}

      {/* No validation run yet */}
      {!hasValidated && !validateMutation.isPending && (
        <Alert severity="info">
          Click "Run Validation" to check your data package against quality standards.
        </Alert>
      )}

      {/* Navigation */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button onClick={onBack}>Back</Button>
        <Button
          variant="contained"
          onClick={handleNext}
          disabled={!validationResult?.isValid}
        >
          Continue to Export
        </Button>
      </Box>
    </Box>
  );
}
