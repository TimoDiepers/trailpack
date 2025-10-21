import { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Paper,
  Alert,
} from '@mui/material';
import type { WizardState } from '../types';

interface SheetSelectionStepProps {
  wizardState: WizardState;
  updateWizardState: (updates: Partial<WizardState>) => void;
  onNext: () => void;
  onBack: () => void;
}

export default function SheetSelectionStep({
  wizardState,
  updateWizardState,
  onNext,
  onBack,
}: SheetSelectionStepProps) {
  const [selectedSheet, setSelectedSheet] = useState<string>(
    wizardState.selectedSheet || 
    wizardState.excelPreview?.selectedSheet || 
    wizardState.excelPreview?.availableSheets?.[0] || 
    ''
  );

  const availableSheets = wizardState.excelPreview?.availableSheets || [];

  const handleSheetChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedSheet(event.target.value);
  };

  const handleNext = () => {
    updateWizardState({ selectedSheet });
    onNext();
  };

  if (!wizardState.excelPreview || availableSheets.length === 0) {
    return (
      <Box>
        <Alert severity="error">
          No Excel file loaded. Please go back and upload a file.
        </Alert>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
          <Button onClick={onBack}>Back</Button>
        </Box>
      </Box>
    );
  }

  // If only one sheet, auto-select and continue
  if (availableSheets.length === 1) {
    const onlySheet = availableSheets[0];
    if (wizardState.selectedSheet !== onlySheet) {
      updateWizardState({ selectedSheet: onlySheet });
    }
    return (
      <Box>
        <Alert severity="info" sx={{ mb: 3 }}>
          Only one sheet found: <strong>{onlySheet}</strong>
        </Alert>
        <Typography variant="body1" gutterBottom>
          Click "Next" to continue with this sheet.
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
          <Button onClick={onBack}>Back</Button>
          <Button variant="contained" onClick={() => onNext()}>
            Next
          </Button>
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Select Excel Sheet
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Your Excel file contains multiple sheets. Please select which sheet to process.
      </Typography>

      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <FormControl component="fieldset">
          <FormLabel component="legend">Available Sheets</FormLabel>
          <RadioGroup
            value={selectedSheet}
            onChange={handleSheetChange}
            sx={{ mt: 2 }}
          >
            {availableSheets.map((sheet) => (
              <FormControlLabel
                key={sheet}
                value={sheet}
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="body1">{sheet}</Typography>
                    {sheet === wizardState.excelPreview?.selectedSheet && (
                      <Typography variant="caption" color="text.secondary">
                        (Currently previewed)
                      </Typography>
                    )}
                  </Box>
                }
              />
            ))}
          </RadioGroup>
        </FormControl>
      </Paper>

      <Alert severity="info" sx={{ mb: 3 }}>
        Selected sheet: <strong>{selectedSheet || 'None'}</strong>
      </Alert>

      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Button onClick={onBack}>Back</Button>
        <Button
          variant="contained"
          onClick={handleNext}
          disabled={!selectedSheet}
        >
          Next
        </Button>
      </Box>
    </Box>
  );
}
