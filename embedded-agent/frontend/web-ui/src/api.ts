import axios from 'axios';

// API base URL
const API_BASE_URL = 'http://localhost:8000';

console.log("API base URL:", API_BASE_URL);

// Types
export interface DesignRequest {
  request: string;
}

export interface DesignResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface DesignStatus {
  task_id: string;
  status: string;
  response?: string;
  artifacts?: Record<string, string>;
  error?: string;
}

// Create a new design request
export const createDesign = async (request: string): Promise<DesignResponse> => {
  try {
    console.log(`Making POST request to ${API_BASE_URL}/design with request:`, request);
    const response = await axios.post<DesignResponse>(
      `${API_BASE_URL}/design`,
      { request }
    );
    console.log("Design creation response:", response.data);
    return response.data;
  } catch (error: any) {
    console.error("Error creating design:", error);
    console.error("Error details:", error.response?.data || error.message);
    throw error;
  }
};

// Get the status of a design task
export const getDesignStatus = async (taskId: string): Promise<DesignStatus> => {
  try {
    const response = await axios.get<DesignStatus>(
      `${API_BASE_URL}/design/${taskId}`
    );
    return response.data;
  } catch (error) {
    console.error('Error getting design status:', error);
    throw error;
  }
};

// Get URL for downloading an artifact
export const getArtifactUrl = (taskId: string, artifactType: string): string => {
  return `${API_BASE_URL}/artifacts/${taskId}/${artifactType}`;
}; 