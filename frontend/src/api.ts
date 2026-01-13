import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export interface PresignResponse {
  call_id: string;
  object_key: string;
  upload_url: string;
}

export interface CompleteResponse {
  call_id: string;
  status: string;
  message: string;
}

export interface Call {
  id: string;
  status: string;
  created_at: string;
  audio_object_key: string;
  duration_sec: number | null;
}

export interface Transcript {
  text: string;
  model: string | null;
  created_at: string;
}

export interface Analysis {
  sentiment: string;
  topic: string;
  problem_resolved: boolean;
  summary: string;
  confidence: number | null;
  created_at: string;
}

export interface CallDetail {
  id: string;
  status: string;
  created_at: string;
  audio_object_key: string;
  duration_sec: number | null;
  transcript: Transcript | null;
  analysis: Analysis | null;
}

export interface TopicCount {
  topic: string;
  count: number;
}

export interface WeeklySpikeAlert {
  topic: string;
  current_week_count: number;
  last_week_count: number;
  spike_ratio: number;
  negative_rate: number;
  message: string;
}

export const uploadApi = {
  presign: async (contentType: string = 'audio/wav', filename?: string): Promise<PresignResponse> => {
    const params = new URLSearchParams({ content_type: contentType });
    if (filename) {
      params.append('filename', filename);
    }
    const response = await api.post<PresignResponse>(`/upload/presign?${params.toString()}`);
    return response.data;
  },

  complete: async (callId: string): Promise<CompleteResponse> => {
    const response = await api.post<CompleteResponse>(`/upload/complete/${callId}`);
    return response.data;
  },

  uploadFile: async (uploadUrl: string, file: File): Promise<void> => {
    await axios.put(uploadUrl, file, {
      headers: {
        'Content-Type': file.type || 'audio/wav',
      },
    });
  },
};

export const callsApi = {
  list: async (limit: number = 10, offset: number = 0): Promise<Call[]> => {
    const response = await api.get<Call[]>(`/calls?limit=${limit}&offset=${offset}`);
    return response.data;
  },

  get: async (callId: string): Promise<CallDetail> => {
    const response = await api.get<CallDetail>(`/calls/${callId}`);
    return response.data;
  },
};

export interface TopicTrend {
  topic: string;
  weekly_counts: number[];
  weekly_negative_rates: number[];
  trend: 'up' | 'down' | 'flat';
  pct_change: number;
}

export interface ResolutionEffectiveness {
  topic: string;
  resolution_rate: number;
  negative_rate: number;
  avg_confidence: number;
}

export interface EscalationRisk {
  topic: string;
  risk_score: number;
  drivers: string[];
}

export interface ExecutiveSummary {
  summary: string;
}

export interface CallStatistics {
  total_calls: number;
  done_calls: number;
  processing_calls: number;
  pending_calls: number;
  failed_calls: number;
  success_rate: number;
  unique_topics: number;
}

export const metricsApi = {
  callStatistics: async (): Promise<CallStatistics> => {
    const response = await api.get<CallStatistics>('/metrics/call_statistics');
    return response.data;
  },

  topicCounts: async (): Promise<TopicCount[]> => {
    const response = await api.get<TopicCount[]>('/metrics/topic_counts');
    return response.data;
  },

  weeklySpikes: async (): Promise<WeeklySpikeAlert[]> => {
    const response = await api.get<WeeklySpikeAlert[]>('/metrics/weekly_spikes');
    return response.data;
  },
};

export const analyticsApi = {
  topicTrends: async (weeks: number = 8): Promise<TopicTrend[]> => {
    const response = await api.get<TopicTrend[]>(`/analytics/topic_trends?weeks=${weeks}`);
    return response.data;
  },

  resolutionEffectiveness: async (): Promise<ResolutionEffectiveness[]> => {
    const response = await api.get<ResolutionEffectiveness[]>('/analytics/resolution_effectiveness');
    return response.data;
  },

  escalationRisk: async (): Promise<EscalationRisk[]> => {
    const response = await api.get<EscalationRisk[]>('/analytics/escalation_risk');
    return response.data;
  },

  executiveSummary: async (): Promise<ExecutiveSummary> => {
    const response = await api.get<ExecutiveSummary>('/analytics/executive_summary');
    return response.data;
  },
};

// S3 Import Interfaces
export interface S3FileInfo {
  key: string;
  size: number;
  last_modified: string | null;
}

export interface ListS3FilesResponse {
  files: S3FileInfo[];
  count: number;
  prefix: string;
}

export interface BatchImportRequest {
  s3_keys: string[];
}

export interface BatchImportResponse {
  total_files: number;
  queued: number;
  skipped: number;
  errors: string[];
}

export const s3ImportApi = {
  listFiles: async (prefix: string = ''): Promise<ListS3FilesResponse> => {
    const params = new URLSearchParams();
    if (prefix) {
      params.append('prefix', prefix);
    }
    const response = await api.get<ListS3FilesResponse>(`/s3-import/list?${params.toString()}`);
    return response.data;
  },

  importPrefix: async (prefix: string): Promise<BatchImportResponse> => {
    const params = new URLSearchParams({ prefix });
    const response = await api.post<BatchImportResponse>(`/s3-import/import-prefix?${params.toString()}`);
    return response.data;
  },

  batchImport: async (s3Keys: string[]): Promise<BatchImportResponse> => {
    const response = await api.post<BatchImportResponse>('/s3-import/batch-import', {
      s3_keys: s3Keys,
    });
    return response.data;
  },
};

