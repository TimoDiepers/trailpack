import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  TextField,
  Paper,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Stack,
  Divider,
  FormHelperText,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import type {
  WizardState,
  GeneralDetails,
  License,
  Contributor,
  Source,
} from '../types';

interface GeneralDetailsStepProps {
  wizardState: WizardState;
  updateWizardState: (updates: Partial<WizardState>) => void;
  onNext: () => void;
  onBack: () => void;
}

const COMMON_LICENSES: Record<string, License> = {
  'CC-BY-4.0': {
    name: 'CC-BY-4.0',
    title: 'Creative Commons Attribution 4.0',
    path: 'https://spdx.org/licenses/CC-BY-4.0.html',
  },
  'MIT': {
    name: 'MIT',
    title: 'MIT License',
    path: 'https://spdx.org/licenses/MIT.html',
  },
  'Apache-2.0': {
    name: 'Apache-2.0',
    title: 'Apache License 2.0',
    path: 'https://spdx.org/licenses/Apache-2.0.html',
  },
  'CC0-1.0': {
    name: 'CC0-1.0',
    title: 'Creative Commons Zero v1.0 Universal',
    path: 'https://spdx.org/licenses/CC0-1.0.html',
  },
};

export default function GeneralDetailsStep({
  wizardState,
  updateWizardState,
  onNext,
  onBack,
}: GeneralDetailsStepProps) {
  const [details, setDetails] = useState<Partial<GeneralDetails>>({
    profile: 'tabular-data-package',
    licenses: [],
    contributors: [],
    sources: [],
    created: new Date().toISOString().split('T')[0],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // New license form
  const [newLicense, setNewLicense] = useState<string>('');
  const [customLicense, setCustomLicense] = useState({
    name: '',
    title: '',
    path: '',
  });

  // New contributor form
  const [newContributor, setNewContributor] = useState<Contributor>({
    name: '',
    role: 'author',
    email: '',
    organization: '',
  });

  // New source form
  const [newSource, setNewSource] = useState<Source>({
    title: '',
    path: '',
    description: '',
  });

  useEffect(() => {
    if (wizardState.generalDetails) {
      setDetails(wizardState.generalDetails);
    }
  }, [wizardState.generalDetails]);

  const validatePackageName = (name: string): string | null => {
    if (!name) return 'Package name is required';
    if (!/^[a-z0-9\-_\.]+$/.test(name)) {
      return 'Package name can only contain lowercase letters, numbers, hyphens, underscores, and dots';
    }
    if (name.startsWith('.') || name.endsWith('.')) {
      return 'Package name cannot start or end with a dot';
    }
    return null;
  };

  const validateVersion = (version: string): string | null => {
    if (!version) return null; // Optional
    if (!/^\d+\.\d+\.\d+(-[a-zA-Z0-9\-\.]+)?$/.test(version)) {
      return 'Version must follow semantic versioning (e.g., 1.0.0)';
    }
    return null;
  };

  const validateURL = (url: string): string | null => {
    if (!url) return null; // Optional
    if (!/^https?:\/\//.test(url)) {
      return 'URL must start with http:// or https://';
    }
    return null;
  };

  const handleFieldChange = (field: keyof GeneralDetails, value: any) => {
    setDetails((prev) => ({ ...prev, [field]: value }));
    
    // Validate
    let error: string | null = null;
    if (field === 'name') {
      error = validatePackageName(value);
    } else if (field === 'version') {
      error = validateVersion(value);
    } else if (field === 'homepage' || field === 'repository') {
      error = validateURL(value);
    }

    setErrors((prev) => ({
      ...prev,
      [field]: error || '',
    }));
  };

  const addLicense = () => {
    if (newLicense === 'Custom') {
      if (!customLicense.name) return;
      setDetails((prev) => ({
        ...prev,
        licenses: [...(prev.licenses || []), { ...customLicense }],
      }));
      setCustomLicense({ name: '', title: '', path: '' });
    } else if (newLicense) {
      const license = COMMON_LICENSES[newLicense];
      if (license) {
        setDetails((prev) => ({
          ...prev,
          licenses: [...(prev.licenses || []), license],
        }));
      }
    }
    setNewLicense('');
  };

  const removeLicense = (index: number) => {
    setDetails((prev) => ({
      ...prev,
      licenses: prev.licenses?.filter((_, i) => i !== index) || [],
    }));
  };

  const addContributor = () => {
    if (!newContributor.name) return;
    setDetails((prev) => ({
      ...prev,
      contributors: [...(prev.contributors || []), { ...newContributor }],
    }));
    setNewContributor({
      name: '',
      role: 'author',
      email: '',
      organization: '',
    });
  };

  const removeContributor = (index: number) => {
    setDetails((prev) => ({
      ...prev,
      contributors: prev.contributors?.filter((_, i) => i !== index) || [],
    }));
  };

  const addSource = () => {
    if (!newSource.title) return;
    setDetails((prev) => ({
      ...prev,
      sources: [...(prev.sources || []), { ...newSource }],
    }));
    setNewSource({ title: '', path: '', description: '' });
  };

  const removeSource = (index: number) => {
    setDetails((prev) => ({
      ...prev,
      sources: prev.sources?.filter((_, i) => i !== index) || [],
    }));
  };

  const canProceed = (): boolean => {
    const hasName = !!details.name && !errors.name;
    const hasTitle = !!details.title;
    const hasLicense = (details.licenses?.length || 0) > 0;
    const hasContributor = (details.contributors?.length || 0) > 0;
    const hasSource = (details.sources?.length || 0) > 0;
    const noErrors = Object.values(errors).every((e) => !e);

    return hasName && hasTitle && hasLicense && hasContributor && hasSource && noErrors;
  };

  const handleNext = () => {
    if (canProceed()) {
      updateWizardState({ generalDetails: details as GeneralDetails });
      onNext();
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        General Details
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Provide metadata for your data package
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
          Basic Information
        </Typography>
        <Stack spacing={2}>
          <Box sx={{ width: { xs: "100%", md: "48%" } }}>
            <TextField
              fullWidth
              required
              label="Package Name"
              value={details.name || ''}
              onChange={(e) => handleFieldChange('name', e.target.value)}
              error={!!errors.name}
              helperText={
                errors.name ||
                'Use lowercase letters, numbers, hyphens, and dots only'
              }
              placeholder="my-dataset"
            />
          </Box>
          <Box sx={{ width: { xs: "100%", md: "48%" } }}>
            <TextField
              fullWidth
              required
              label="Title"
              value={details.title || ''}
              onChange={(e) => handleFieldChange('title', e.target.value)}
              placeholder="My Dataset Title"
              helperText="Human-readable title for the dataset"
            />
          </Box>
          <Box sx={{ width: "100%" }}>
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Description"
              value={details.description || ''}
              onChange={(e) => handleFieldChange('description', e.target.value)}
              placeholder="This dataset contains..."
              helperText="Longer description explaining what the dataset contains"
            />
          </Box>
          <Box sx={{ width: { xs: "100%", md: "48%" } }}>
            <TextField
              fullWidth
              label="Version"
              value={details.version || ''}
              onChange={(e) => handleFieldChange('version', e.target.value)}
              error={!!errors.version}
              helperText={errors.version || 'Semantic versioning (e.g., 1.0.0)'}
              placeholder="1.0.0"
            />
          </Box>
          <Box sx={{ width: { xs: "100%", md: "48%" } }}>
            <FormControl fullWidth>
              <InputLabel>Profile</InputLabel>
              <Select
                value={details.profile || 'tabular-data-package'}
                onChange={(e) => handleFieldChange('profile', e.target.value)}
                label="Profile"
              >
                <MenuItem value="tabular-data-package">Tabular Data Package</MenuItem>
                <MenuItem value="data-package">Data Package</MenuItem>
                <MenuItem value="fiscal-data-package">Fiscal Data Package</MenuItem>
              </Select>
              <FormHelperText>Type of data package</FormHelperText>
            </FormControl>
          </Box>
          <Box sx={{ width: "100%" }}>
            <TextField
              fullWidth
              label="Keywords"
              value={(details.keywords || []).join(', ')}
              onChange={(e) =>
                handleFieldChange(
                  'keywords',
                  e.target.value.split(',').map((k) => k.trim()).filter(Boolean)
                )
              }
              placeholder="astronomy, catalog, coordinates"
              helperText="Comma-separated tags to help others discover your dataset"
            />
          </Box>
        </Stack>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
          Additional Information
        </Typography>
        <Stack spacing={2}>
          <Box sx={{ width: { xs: "100%", md: "48%" } }}>
            <TextField
              fullWidth
              label="Homepage"
              value={details.homepage || ''}
              onChange={(e) => handleFieldChange('homepage', e.target.value)}
              error={!!errors.homepage}
              helperText={errors.homepage || 'Project or dataset homepage URL'}
              placeholder="https://example.com/my-project"
            />
          </Box>
          <Box sx={{ width: { xs: "100%", md: "48%" } }}>
            <TextField
              fullWidth
              label="Repository"
              value={details.repository || ''}
              onChange={(e) => handleFieldChange('repository', e.target.value)}
              error={!!errors.repository}
              helperText={errors.repository || 'Code repository URL'}
              placeholder="https://github.com/user/repo"
            />
          </Box>
          <Box sx={{ width: { xs: "100%", md: "48%" } }}>
            <TextField
              fullWidth
              type="date"
              label="Created Date"
              value={details.created || ''}
              onChange={(e) => handleFieldChange('created', e.target.value)}
              InputLabelProps={{ shrink: true }}
              helperText="When the dataset was created"
            />
          </Box>
          <Box sx={{ width: { xs: "100%", md: "48%" } }}>
            <TextField
              fullWidth
              type="date"
              label="Modified Date"
              value={details.modified || ''}
              onChange={(e) => handleFieldChange('modified', e.target.value)}
              InputLabelProps={{ shrink: true }}
              helperText="When the dataset was last modified"
            />
          </Box>
        </Stack>
      </Paper>

      {/* Licenses Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
          Licenses *
        </Typography>
        <Typography variant="caption" color="text.secondary" gutterBottom>
          At least one license is required
        </Typography>

        {/* Existing Licenses */}
        {(details.licenses || []).length > 0 && (
          <Box sx={{ my: 2 }}>
            <Typography variant="body2" gutterBottom>
              Current Licenses:
            </Typography>
            <Stack spacing={1}>
              {details.licenses?.map((license, index) => (
                <Chip
                  key={index}
                  label={`${license.name} - ${license.title}`}
                  onDelete={() => removeLicense(index)}
                  deleteIcon={<DeleteIcon />}
                />
              ))}
            </Stack>
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        {/* Add License */}
        <Typography variant="body2" gutterBottom>
          Add License:
        </Typography>
        <Stack direction="row" spacing={1} alignItems="flex-start">
          <FormControl sx={{ minWidth: 200 }}>
            <Select
              value={newLicense}
              onChange={(e) => setNewLicense(e.target.value)}
              displayEmpty
              size="small"
            >
              <MenuItem value="">Select a license</MenuItem>
              {Object.keys(COMMON_LICENSES).map((key) => (
                <MenuItem key={key} value={key}>
                  {COMMON_LICENSES[key].title}
                </MenuItem>
              ))}
              <MenuItem value="Custom">Custom License</MenuItem>
            </Select>
          </FormControl>
          {newLicense && newLicense !== 'Custom' && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={addLicense}
              size="small"
            >
              Add
            </Button>
          )}
        </Stack>

        {newLicense === 'Custom' && (
          <Box sx={{ mt: 2 }}>
            <Stack spacing={2}>
              <Box sx={{ width: { xs: "100%", md: "32%" } }}>
                <TextField
                  fullWidth
                  size="small"
                  label="License Name"
                  value={customLicense.name}
                  onChange={(e) =>
                    setCustomLicense((prev) => ({ ...prev, name: e.target.value }))
                  }
                  placeholder="MIT"
                />
              </Box>
              <Box sx={{ width: { xs: "100%", md: "32%" } }}>
                <TextField
                  fullWidth
                  size="small"
                  label="License Title"
                  value={customLicense.title}
                  onChange={(e) =>
                    setCustomLicense((prev) => ({ ...prev, title: e.target.value }))
                  }
                  placeholder="MIT License"
                />
              </Box>
              <Box sx={{ width: { xs: "100%", md: "32%" } }}>
                <TextField
                  fullWidth
                  size="small"
                  label="License URL"
                  value={customLicense.path}
                  onChange={(e) =>
                    setCustomLicense((prev) => ({ ...prev, path: e.target.value }))
                  }
                  placeholder="https://opensource.org/licenses/MIT"
                />
              </Box>
              <Box sx={{ width: "100%" }}>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={addLicense}
                  disabled={!customLicense.name}
                >
                  Add Custom License
                </Button>
              </Box>
            </Stack>
          </Box>
        )}
      </Paper>

      {/* Contributors Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
          Contributors *
        </Typography>
        <Typography variant="caption" color="text.secondary" gutterBottom>
          At least one contributor is required
        </Typography>

        {/* Existing Contributors */}
        {(details.contributors || []).length > 0 && (
          <Box sx={{ my: 2 }}>
            <Typography variant="body2" gutterBottom>
              Current Contributors:
            </Typography>
            <Stack spacing={1}>
              {details.contributors?.map((contributor, index) => (
                <Chip
                  key={index}
                  label={`${contributor.name} (${contributor.role})${
                    contributor.email ? ` - ${contributor.email}` : ''
                  }`}
                  onDelete={() => removeContributor(index)}
                  deleteIcon={<DeleteIcon />}
                />
              ))}
            </Stack>
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        {/* Add Contributor */}
        <Typography variant="body2" gutterBottom>
          Add Contributor:
        </Typography>
        <Stack spacing={2}>
          <Box sx={{ width: { xs: "100%", md: "24%" } }}>
            <TextField
              fullWidth
              size="small"
              label="Name"
              value={newContributor.name}
              onChange={(e) =>
                setNewContributor((prev) => ({ ...prev, name: e.target.value }))
              }
              placeholder="Jane Doe"
            />
          </Box>
          <Box sx={{ width: { xs: "100%", md: "24%" } }}>
            <FormControl fullWidth size="small">
              <InputLabel>Role</InputLabel>
              <Select
                value={newContributor.role}
                onChange={(e) =>
                  setNewContributor((prev) => ({
                    ...prev,
                    role: e.target.value as Contributor['role'],
                  }))
                }
                label="Role"
              >
                <MenuItem value="author">Author</MenuItem>
                <MenuItem value="contributor">Contributor</MenuItem>
                <MenuItem value="maintainer">Maintainer</MenuItem>
                <MenuItem value="publisher">Publisher</MenuItem>
                <MenuItem value="wrangler">Wrangler</MenuItem>
              </Select>
            </FormControl>
          </Box>
          <Box sx={{ width: { xs: "100%", md: "24%" } }}>
            <TextField
              fullWidth
              size="small"
              label="Email (optional)"
              value={newContributor.email}
              onChange={(e) =>
                setNewContributor((prev) => ({ ...prev, email: e.target.value }))
              }
              placeholder="jane@example.com"
            />
          </Box>
          <Box sx={{ width: { xs: "100%", md: "24%" } }}>
            <TextField
              fullWidth
              size="small"
              label="Organization (optional)"
              value={newContributor.organization}
              onChange={(e) =>
                setNewContributor((prev) => ({ ...prev, organization: e.target.value }))
              }
              placeholder="Example Org"
            />
          </Box>
          <Box sx={{ width: "100%" }}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={addContributor}
              disabled={!newContributor.name}
            >
              Add Contributor
            </Button>
          </Box>
        </Stack>
      </Paper>

      {/* Sources Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
          Sources *
        </Typography>
        <Typography variant="caption" color="text.secondary" gutterBottom>
          At least one source is required
        </Typography>

        {/* Existing Sources */}
        {(details.sources || []).length > 0 && (
          <Box sx={{ my: 2 }}>
            <Typography variant="body2" gutterBottom>
              Current Sources:
            </Typography>
            <Stack spacing={1}>
              {details.sources?.map((source, index) => (
                <Chip
                  key={index}
                  label={`${source.title}${source.path ? ` - ${source.path}` : ''}`}
                  onDelete={() => removeSource(index)}
                  deleteIcon={<DeleteIcon />}
                />
              ))}
            </Stack>
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        {/* Add Source */}
        <Typography variant="body2" gutterBottom>
          Add Source:
        </Typography>
        <Stack spacing={2}>
          <Box sx={{ width: { xs: "100%", md: "32%" } }}>
            <TextField
              fullWidth
              size="small"
              label="Source Title"
              value={newSource.title}
              onChange={(e) =>
                setNewSource((prev) => ({ ...prev, title: e.target.value }))
              }
              placeholder="Original Dataset"
            />
          </Box>
          <Box sx={{ width: { xs: "100%", md: "32%" } }}>
            <TextField
              fullWidth
              size="small"
              label="Source URL (optional)"
              value={newSource.path}
              onChange={(e) =>
                setNewSource((prev) => ({ ...prev, path: e.target.value }))
              }
              placeholder="https://example.com/data"
            />
          </Box>
          <Box sx={{ width: { xs: "100%", md: "32%" } }}>
            <TextField
              fullWidth
              size="small"
              label="Description (optional)"
              value={newSource.description}
              onChange={(e) =>
                setNewSource((prev) => ({ ...prev, description: e.target.value }))
              }
              placeholder="Description of the source"
            />
          </Box>
          <Box sx={{ width: "100%" }}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={addSource}
              disabled={!newSource.title}
            >
              Add Source
            </Button>
          </Box>
        </Stack>
      </Paper>

      {!canProceed() && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Please fill in all required fields:
          {!details.name && ' Package Name,'}
          {!details.title && ' Title,'}
          {!(details.licenses?.length) && ' at least one License,'}
          {!(details.contributors?.length) && ' at least one Contributor,'}
          {!(details.sources?.length) && ' at least one Source'}
        </Alert>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button onClick={onBack}>Back</Button>
        <Button variant="contained" onClick={handleNext} disabled={!canProceed()}>
          Continue to Export
        </Button>
      </Box>
    </Box>
  );
}
