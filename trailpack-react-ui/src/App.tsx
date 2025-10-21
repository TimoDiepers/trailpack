import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline, Container, AppBar, Toolbar, Typography, Chip } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import WizardPage from './pages/WizardPage';

const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API === 'true';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <AppBar position="static">
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                Trailpack Excel to PyST Mapper
              </Typography>
              {USE_MOCK_API && (
                <Chip 
                  label="Demo Mode" 
                  color="warning" 
                  size="small"
                  sx={{ ml: 2 }}
                />
              )}
            </Toolbar>
          </AppBar>
          <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            <Routes>
              <Route path="/" element={<Navigate to="/wizard" replace />} />
              <Route path="/wizard" element={<WizardPage />} />
            </Routes>
          </Container>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
