import React, { useState } from 'react';
import { uploadApi } from '../api';
import { Icon } from '../components/Icons';

function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);
  const [callId, setCallId] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatus(null);
      setCallId(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setStatus({ type: 'error', message: 'Please select a file first' });
      return;
    }

    setUploading(true);
    setStatus({ type: 'info', message: 'Requesting upload URL...' });

    try {
      // Step 1: Request presigned URL (pass filename to preserve extension)
      const presignData = await uploadApi.presign(file.type || 'audio/wav', file.name);
      setCallId(presignData.call_id);
      
      setStatus({ type: 'info', message: 'Uploading file to storage...' });

      // Step 2: Upload file to MinIO using presigned URL
      await uploadApi.uploadFile(presignData.upload_url, file);

      setStatus({ type: 'info', message: 'Finalizing upload...' });

      // Step 3: Mark upload as complete and enqueue processing
      await uploadApi.complete(presignData.call_id);

      setStatus({
        type: 'success',
        message: `Upload successful! Call ID: ${presignData.call_id}. Processing has been queued.`,
      });
      
      // Reset file input
      setFile(null);
      const fileInput = document.getElementById('file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

    } catch (error: any) {
      console.error('Upload error:', error);
      setStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Upload failed. Please try again.',
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <h1 className="page-title">Upload Audio Call</h1>

      <div className="card">
        <h2>Select Audio File</h2>
        <div className="upload-zone">
          <label htmlFor="file-input" className="file-input-label">
            <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Icon name="microphone" size={48} color="var(--blue-400)" />
            </div>
            <div>
              {file ? (
                <p style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              ) : (
                <>
                  <p style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                    Click to select audio file
                  </p>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    WAV, MP3, M4A, or other audio formats
                  </p>
                </>
              )}
            </div>
            <input
              id="file-input"
              type="file"
              accept="audio/*"
              onChange={handleFileChange}
              disabled={uploading}
            />
          </label>
        </div>

        <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
          <button
            className="btn"
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? 'Uploading...' : 'Upload & Process'}
          </button>
        </div>

        {status && (
          <div className={`status-message ${status.type}`}>
            {status.message}
          </div>
        )}

        {callId && (
          <div style={{ marginTop: '1rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <p>
              <strong>Call ID:</strong> <code style={{ 
                background: 'var(--dark-blue-700)', 
                padding: '0.25rem 0.5rem', 
                borderRadius: '4px',
                color: 'var(--blue-300)'
              }}>{callId}</code>
            </p>
            <p style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>
              Check the Dashboard to see processing status
            </p>
          </div>
        )}
      </div>

      <div className="card">
        <h2>Instructions</h2>
        <ol style={{ paddingLeft: '1.5rem', lineHeight: 1.8, color: 'var(--text-secondary)' }}>
          <li>Select an audio file containing a customer support call</li>
          <li>Click "Upload & Process" to upload the file</li>
          <li>The system will transcribe and analyze the call automatically</li>
          <li>View results in the Dashboard once processing is complete</li>
        </ol>
      </div>
    </div>
  );
}

export default Upload;

