import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  TextField,
  Button,
  Paper,
  CircularProgress,
  Card,
  CardContent,
  CardActions,
  Chip,
  Grid,
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
} from '@mui/material';
import { 
  Memory as MemoryIcon, 
  Build as BuildIcon, 
  Download as DownloadIcon,
  Lightbulb as LightbulbIcon
} from '@mui/icons-material';
import { createDesign, getDesignStatus, getArtifactUrl, DesignResponse, DesignStatus } from './api';

// Define theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#f50057',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
});

// Example request interface
interface ExampleRequest {
  title: string;
  description: string;
  request: string;
}

const App: React.FC = () => {
  // State
  const [request, setRequest] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<DesignStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<ReturnType<typeof setInterval> | null>(null);

  // Example request templates
  const exampleRequests: ExampleRequest[] = [
    {
      title: "Temperature Sensor with LED and Fan",
      description: "Use LM35 to monitor temperature, control LED and fan when temperature exceeds threshold",
      request: "Design a system that uses an 8051 microcontroller and an LM35 temperature sensor. The system should read the temperature once per second. If the temperature exceeds 30°C, turn on an LED and activate a cooling fan. Otherwise, keep the LED off and the fan off. Display the current temperature on the UART."
    },
    {
      title: "LED Sequencer with Button Control",
      description: "Create sequential LED pattern with button to change patterns",
      request: "Design an 8051 system with 8 LEDs connected to Port 1 and a push button connected to P3.2. The LEDs should display different patterns that change every second. When the button is pressed, the system should switch to the next pattern. Implement at least 3 different patterns."
    }
  ];

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Form submitted with request:", request);
    setLoading(true);
    setError(null);
    setStatus(null);
    
    try {
      console.log("Calling createDesign API...");
      const response = await createDesign(request);
      console.log("API response:", response);
      setTaskId(response.task_id);
      
      // Set up polling for status updates
      const interval = setInterval(async () => {
        try {
          console.log("Polling for status updates...");
          const statusResponse = await getDesignStatus(response.task_id);
          console.log("Status response:", statusResponse);
          setStatus(statusResponse);
          
          // Stop polling when the task is completed or failed
          if (statusResponse.status === 'completed' || statusResponse.status === 'failed') {
            if (pollingInterval) clearInterval(pollingInterval);
            setPollingInterval(null);
          }
        } catch (err) {
          console.error("Error polling status:", err);
          if (pollingInterval) clearInterval(pollingInterval);
          setPollingInterval(null);
          setError('Error polling status');
        }
      }, 5000); // Poll every 5 seconds
      
      setPollingInterval(interval);
    } catch (err) {
      console.error("Error creating design request:", err);
      setError('Error creating design request');
    } finally {
      setLoading(false);
    }
  };

  // Clean up polling interval when component is unmounted
  useEffect(() => {
    return () => {
      if (pollingInterval) clearInterval(pollingInterval);
    };
  }, [pollingInterval]);

  // Function to download an artifact
  const handleDownloadArtifact = (artifactType: string) => {
    if (!taskId || !status?.artifacts?.[artifactType]) return;
    
    const artifactUrl = getArtifactUrl(taskId, artifactType);
    window.open(artifactUrl, '_blank');
  };

  // Function to set an example request
  const handleUseExampleRequest = (exampleRequest: string) => {
    setRequest(exampleRequest);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static">
          <Toolbar>
            <MemoryIcon sx={{ mr: 2 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              8051 Embedded System Design Agent
            </Typography>
          </Toolbar>
        </AppBar>
      </Box>
      
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Grid container spacing={3}>
          {/* Request Form */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                Describe Your Embedded System
              </Typography>
              <Typography color="text.secondary" paragraph>
                Describe the 8051-based embedded system you want to design, including functionality, 
                inputs, outputs, and any specific requirements.
              </Typography>
              
              <form onSubmit={handleSubmit}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="Design Request"
                  variant="outlined"
                  value={request}
                  onChange={(e) => setRequest(e.target.value)}
                  placeholder="Describe the embedded system you want to design..."
                  required
                  margin="normal"
                />
                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
                  <Button
                    variant="contained"
                    color="primary"
                    type="submit"
                    disabled={loading || !request}
                    startIcon={loading ? <CircularProgress size={20} /> : <BuildIcon />}
                  >
                    {loading ? 'Processing...' : 'Design System'}
                  </Button>
                </Box>
              </form>
            </Paper>
          </Grid>
          
          {/* Example Requests */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Example Requests
            </Typography>
            <Grid container spacing={2}>
              {exampleRequests.map((example, index) => (
                <Grid item xs={12} md={6} key={index}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        <LightbulbIcon sx={{ mr: 1, verticalAlign: 'middle', color: 'primary.main' }} />
                        {example.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {example.description}
                      </Typography>
                    </CardContent>
                    <CardActions>
                      <Button size="small" onClick={() => handleUseExampleRequest(example.request)}>
                        Use This Example
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Grid>
          
          {/* Results Section */}
          {status && (
            <Grid item xs={12}>
              <Paper sx={{ p: 3, mt: 3 }}>
                <Typography variant="h5" gutterBottom>
                  Design Results
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Chip 
                    label={`Status: ${status.status}`} 
                    color={
                      status.status === 'completed' ? 'success' : 
                      status.status === 'failed' ? 'error' : 
                      'primary'
                    } 
                    sx={{ mr: 1 }} 
                  />
                  <Chip label={`Task ID: ${status.task_id}`} variant="outlined" />
                </Box>
                
                {status.error && (
                  <Box sx={{ mb: 2, p: 2, bgcolor: 'error.dark', borderRadius: 1 }}>
                    <Typography color="error.contrastText">
                      Error: {status.error}
                    </Typography>
                  </Box>
                )}
                
                {status.response && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Agent Response
                    </Typography>
                    <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.paper' }}>
                      <Typography component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                        {status.response || ''}
                      </Typography>
                    </Paper>
                  </Box>
                )}
                
                {status.artifacts && Object.keys(status.artifacts).length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Generated Artifacts
                    </Typography>
                    <Grid container spacing={2}>
                      {Object.entries(status.artifacts).map(([key, path]) => (
                        <Grid item xs={12} sm={6} md={4} key={key}>
                          <Card variant="outlined">
                            <CardContent>
                              <Typography variant="subtitle1" gutterBottom>
                                {key.replace(/_/g, ' ').toUpperCase()}
                              </Typography>
                              <Typography variant="body2" color="text.secondary" noWrap>
                                {path}
                              </Typography>
                            </CardContent>
                            <CardActions>
                              <Button 
                                size="small" 
                                startIcon={<DownloadIcon />}
                                onClick={() => handleDownloadArtifact(key)}
                              >
                                Download
                              </Button>
                            </CardActions>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                )}
              </Paper>
            </Grid>
          )}
        </Grid>
        
        <Box sx={{ mt: 5, mb: 3, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            8051 Embedded System Design Agent © {new Date().getFullYear()}
          </Typography>
        </Box>
      </Container>
    </ThemeProvider>
  );
};

export default App; 