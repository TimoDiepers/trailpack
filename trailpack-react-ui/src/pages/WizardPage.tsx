import { useState } from 'react';
import {
  Box,
  Paper,
  Stepper,
  Step,
  StepLabel,
  Typography,
} from '@mui/material';
import UploadStep from '../components/UploadStep';
import SheetSelectionStep from '../components/SheetSelectionStep';
import MappingStepEnhanced from '../components/MappingStepEnhanced';
import GeneralDetailsStep from '../components/GeneralDetailsStep';
import ValidationStep from '../components/ValidationStep';
import ExportStep from '../components/ExportStep';
import type { WizardState } from '../types';

const steps = [
  'Upload Excel',
  'Select Sheet', 
  'Map Columns',
  'General Details',
  'Validate',
  'Export'
];

const initialState: WizardState = {
  currentStep: 0,
  excelFile: null,
  excelPreview: null,
  selectedSheet: null,
  fileId: null,
  language: 'en',
  mappings: [],
  generalDetails: {
    name: '',
    title: '',
    description: '',
    version: '1.0.0',
    profile: 'tabular-data-package',
    keywords: [],
    homepage: '',
    repository: '',
    created: new Date().toISOString().split('T')[0],
    modified: new Date().toISOString().split('T')[0],
    licenses: [],
    contributors: [],
    sources: [],
  },
  exportConfig: {
    includeMetadata: true,
    compressionType: 'snappy',
    outputFileName: 'output.parquet',
  },
  validationResult: null,
};

export default function WizardPage() {
  const [wizardState, setWizardState] = useState<WizardState>(initialState);

  const handleNext = () => {
    setWizardState((prev) => ({
      ...prev,
      currentStep: prev.currentStep + 1,
    }));
  };

  const handleBack = () => {
    setWizardState((prev) => ({
      ...prev,
      currentStep: prev.currentStep - 1,
    }));
  };

  const handleReset = () => {
    setWizardState(initialState);
  };

  const updateWizardState = (updates: Partial<WizardState>) => {
    setWizardState((prev) => ({ ...prev, ...updates }));
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <UploadStep
            wizardState={wizardState}
            updateWizardState={updateWizardState}
            onNext={handleNext}
          />
        );
      case 1:
        return (
          <SheetSelectionStep
            wizardState={wizardState}
            updateWizardState={updateWizardState}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 2:
        return (
          <MappingStepEnhanced
            wizardState={wizardState}
            updateWizardState={updateWizardState}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 3:
        return (
          <GeneralDetailsStep
            wizardState={wizardState}
            updateWizardState={updateWizardState}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 4:
        return (
          <ValidationStep
            wizardState={wizardState}
            updateWizardState={updateWizardState}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 5:
        return (
          <ExportStep
            wizardState={wizardState}
            updateWizardState={updateWizardState}
            onBack={handleBack}
            onReset={handleReset}
          />
        );
      default:
        return <Typography>Unknown step</Typography>;
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Excel to PyST Mapper
        </Typography>
        <Stepper activeStep={wizardState.currentStep} sx={{ pt: 3, pb: 5 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        <Box sx={{ mt: 2 }}>
          {renderStepContent(wizardState.currentStep)}
        </Box>
      </Paper>
    </Box>
  );
}
