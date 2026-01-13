import React, { useState } from 'react';
import { s3ImportApi, S3FileInfo, BatchImportResponse } from '../api';
import { Icon } from '../components/Icons';

function S3Import() {
  const [prefix, setPrefix] = useState('recordings');
  const [files, setFiles] = useState<S3FileInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [importResult, setImportResult] = useState<BatchImportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastPrefix, setLastPrefix] = useState<string>('');

  const handleListFiles = async () => {
    setLoading(true);
    setError(null);
    setFiles([]);
    setSelectedFiles(new Set());
    setImportResult(null);

    try {
      const searchPrefix = prefix.trim() || '';
      console.log('Scanning S3 with prefix:', searchPrefix || '(root)');
      
      const result = await s3ImportApi.listFiles(searchPrefix);
      console.log('S3 scan result:', result);
      
      setFiles(result.files);
      setLastPrefix(result.prefix);
      
      if (result.files.length === 0) {
        const prefixDisplay = result.prefix || '(root of bucket)';
        setError(`No audio files found in prefix: "${prefixDisplay}". Make sure your files have audio extensions (.mp3, .wav, .m4a, etc.)`);
      }
    } catch (err: any) {
      console.error('Error listing S3 files:', err);
      const errorDetail = err.response?.data?.detail || err.message || 'Unknown error';
      setError(`Failed to list S3 files: ${errorDetail}. Check your S3 configuration in .env file.`);
    } finally {
      setLoading(false);
    }
  };

  const handleImportPrefix = async () => {
    if (!lastPrefix) {
      setError('Please list files first');
      return;
    }

    setImporting(true);
    setError(null);
    setImportResult(null);

    try {
      const result = await s3ImportApi.importPrefix(lastPrefix);
      setImportResult(result);
      
      if (result.queued > 0) {
        // Refresh file list to show updated status
        setTimeout(() => {
          handleListFiles();
        }, 1000);
      }
    } catch (err: any) {
      console.error('Error importing prefix:', err);
      setError(err.response?.data?.detail || 'Failed to import files');
    } finally {
      setImporting(false);
    }
  };

  const handleBatchImport = async () => {
    if (selectedFiles.size === 0) {
      setError('Please select at least one file to import');
      return;
    }

    setImporting(true);
    setError(null);
    setImportResult(null);

    try {
      const s3Keys = Array.from(selectedFiles);
      const result = await s3ImportApi.batchImport(s3Keys);
      setImportResult(result);
      setSelectedFiles(new Set());
      
      if (result.queued > 0) {
        setTimeout(() => {
          handleListFiles();
        }, 1000);
      }
    } catch (err: any) {
      console.error('Error batch importing:', err);
      setError(err.response?.data?.detail || 'Failed to import selected files');
    } finally {
      setImporting(false);
    }
  };

  const toggleFileSelection = (key: string) => {
    const newSelected = new Set(selectedFiles);
    if (newSelected.has(key)) {
      newSelected.delete(key);
    } else {
      newSelected.add(key);
    }
    setSelectedFiles(newSelected);
  };

  const selectAll = () => {
    if (selectedFiles.size === files.length) {
      setSelectedFiles(new Set());
    } else {
      setSelectedFiles(new Set(files.map(f => f.key)));
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  };

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  return (
    <div>
      <h1 className="page-title">Import from S3</h1>

      <div className="card">
        <h2>Scan S3 Bucket</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
          Enter an S3 path/prefix to scan for audio files. Leave empty to scan root. Examples: <code>recordings</code>, <code>recordings/2024</code>, or leave empty for root.
        </p>
        
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              S3 Path/Prefix
            </label>
            <input
              type="text"
              value={prefix}
              onChange={(e) => setPrefix(e.target.value)}
              placeholder="recordings (or leave empty for root)"
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                border: '1px solid var(--card-border)',
                background: 'var(--dark-blue-700)',
                color: 'var(--text-primary)',
                fontSize: '1rem',
              }}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleListFiles();
                }
              }}
            />
          </div>
          <button
            onClick={handleListFiles}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '0.875rem 2rem',
              background: loading 
                ? 'linear-gradient(135deg, rgba(66, 153, 225, 0.3) 0%, rgba(66, 153, 225, 0.2) 100%)' 
                : 'linear-gradient(135deg, var(--blue-400) 0%, var(--blue-500) 100%)',
              border: 'none',
              borderRadius: '12px',
              color: 'white',
              fontWeight: '600',
              fontSize: '1rem',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.3s ease',
              boxShadow: loading 
                ? '0 4px 15px rgba(66, 153, 225, 0.2)' 
                : '0 6px 20px rgba(66, 153, 225, 0.4)',
              opacity: loading ? 0.7 : 1,
              position: 'relative',
              overflow: 'hidden'
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 8px 25px rgba(66, 153, 225, 0.5)';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 6px 20px rgba(66, 153, 225, 0.4)';
              }
            }}
          >
            {loading ? (
              <>
                <svg 
                  width="18" 
                  height="18" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  stroke="currentColor" 
                  strokeWidth="2" 
                  strokeLinecap="round" 
                  strokeLinejoin="round"
                  style={{ animation: 'spin 1s linear infinite' }}
                >
                  <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                </svg>
                <span>Scanning...</span>
              </>
            ) : (
              <>
                <svg 
                  width="18" 
                  height="18" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  stroke="currentColor" 
                  strokeWidth="2" 
                  strokeLinecap="round" 
                  strokeLinejoin="round"
                >
                  <circle cx="11" cy="11" r="8"/>
                  <path d="M21 21l-4.35-4.35"/>
                </svg>
                <span>Scan Files</span>
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="status-message error" style={{ marginTop: '1rem' }}>
            {error}
          </div>
        )}

        {lastPrefix && (
          <div style={{ 
            marginTop: '1rem', 
            padding: '0.75rem 1rem', 
            background: 'rgba(66, 153, 225, 0.1)',
            border: '1px solid rgba(66, 153, 225, 0.3)',
            borderRadius: '8px',
            color: 'var(--text-secondary)',
            fontSize: '0.9rem'
          }}>
            Scanning prefix: <code style={{ color: 'var(--blue-300)' }}>{lastPrefix}</code>
          </div>
        )}
      </div>

      {files.length > 0 && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2 style={{ margin: 0 }}>
              Found {files.length} audio file{files.length !== 1 ? 's' : ''}
            </h2>
            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              <button
                onClick={selectAll}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.625rem 1.25rem',
                  background: 'linear-gradient(135deg, rgba(160, 174, 192, 0.2) 0%, rgba(160, 174, 192, 0.1) 100%)',
                  border: '1px solid rgba(160, 174, 192, 0.3)',
                  borderRadius: '10px',
                  color: 'var(--text-secondary)',
                  fontWeight: '600',
                  fontSize: '0.9rem',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  backdropFilter: 'blur(10px)',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'linear-gradient(135deg, rgba(160, 174, 192, 0.3) 0%, rgba(160, 174, 192, 0.2) 100%)';
                  e.currentTarget.style.borderColor = 'rgba(160, 174, 192, 0.5)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 6px 18px rgba(0, 0, 0, 0.15)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'linear-gradient(135deg, rgba(160, 174, 192, 0.2) 0%, rgba(160, 174, 192, 0.1) 100%)';
                  e.currentTarget.style.borderColor = 'rgba(160, 174, 192, 0.3)';
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9 11 12 14 22 4"/>
                  <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
                </svg>
                <span>{selectedFiles.size === files.length ? 'Deselect All' : 'Select All'}</span>
              </button>
              <button
                onClick={handleImportPrefix}
                disabled={importing}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.625rem 1.25rem',
                  background: importing
                    ? 'linear-gradient(135deg, rgba(72, 187, 120, 0.3) 0%, rgba(72, 187, 120, 0.2) 100%)'
                    : 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)',
                  border: 'none',
                  borderRadius: '10px',
                  color: 'white',
                  fontWeight: '600',
                  fontSize: '0.9rem',
                  cursor: importing ? 'not-allowed' : 'pointer',
                  transition: 'all 0.3s ease',
                  boxShadow: '0 4px 15px rgba(72, 187, 120, 0.3)',
                  opacity: importing ? 0.7 : 1
                }}
                onMouseEnter={(e) => {
                  if (!importing) {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 6px 20px rgba(72, 187, 120, 0.4)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!importing) {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 4px 15px rgba(72, 187, 120, 0.3)';
                  }
                }}
              >
                {importing ? (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ animation: 'spin 1s linear infinite' }}>
                      <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                    </svg>
                    <span>Importing...</span>
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                      <polyline points="7 10 12 15 17 10"/>
                      <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                    <span>Import All ({files.length})</span>
                  </>
                )}
              </button>
              {selectedFiles.size > 0 && (
                <button
                  onClick={handleBatchImport}
                  disabled={importing}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.625rem 1.25rem',
                    background: importing
                      ? 'linear-gradient(135deg, rgba(72, 187, 120, 0.3) 0%, rgba(72, 187, 120, 0.2) 100%)'
                      : 'linear-gradient(135deg, var(--blue-400) 0%, var(--blue-500) 100%)',
                    border: 'none',
                    borderRadius: '10px',
                    color: 'white',
                    fontWeight: '600',
                    fontSize: '0.9rem',
                    cursor: importing ? 'not-allowed' : 'pointer',
                    transition: 'all 0.3s ease',
                    boxShadow: '0 4px 15px rgba(66, 153, 225, 0.3)',
                    opacity: importing ? 0.7 : 1
                  }}
                  onMouseEnter={(e) => {
                    if (!importing) {
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = '0 6px 20px rgba(66, 153, 225, 0.4)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!importing) {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = '0 4px 15px rgba(66, 153, 225, 0.3)';
                    }
                  }}
                >
                  {importing ? (
                    <>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ animation: 'spin 1s linear infinite' }}>
                        <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                      </svg>
                      <span>Importing...</span>
                    </>
                  ) : (
                    <>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="17 8 12 3 7 8"/>
                        <line x1="12" y1="3" x2="12" y2="15"/>
                      </svg>
                      <span>Import Selected ({selectedFiles.size})</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th style={{ width: '40px' }}>
                    <input
                      type="checkbox"
                      checked={selectedFiles.size === files.length && files.length > 0}
                      onChange={selectAll}
                      style={{ cursor: 'pointer' }}
                    />
                  </th>
                  <th>File Path</th>
                  <th>Size</th>
                  <th>Last Modified</th>
                </tr>
              </thead>
              <tbody>
                {files.map((file) => (
                  <tr key={file.key}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedFiles.has(file.key)}
                        onChange={() => toggleFileSelection(file.key)}
                        style={{ cursor: 'pointer' }}
                      />
                    </td>
                    <td>
                      <code style={{ 
                        fontSize: '0.9rem', 
                        color: 'var(--blue-300)',
                        wordBreak: 'break-all'
                      }}>
                        {file.key}
                      </code>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>
                      {formatFileSize(file.size)}
                    </td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                      {formatDate(file.last_modified)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {importResult && (
        <div className="card">
          <h2>Import Results</h2>
          <div style={{ 
            padding: '1.5rem',
            background: 'rgba(26, 47, 74, 0.5)',
            borderRadius: '12px',
            border: '1px solid var(--card-border)'
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1.5rem', marginBottom: '1rem' }}>
              <div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Total Files</div>
                <div style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--blue-300)' }}>
                  {importResult.total_files}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Queued</div>
                <div style={{ fontSize: '1.75rem', fontWeight: '700', color: '#9ae6b4' }}>
                  {importResult.queued}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Skipped</div>
                <div style={{ fontSize: '1.75rem', fontWeight: '700', color: '#f6ad55' }}>
                  {importResult.skipped}
                </div>
              </div>
              {importResult.errors.length > 0 && (
                <div>
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Errors</div>
                  <div style={{ fontSize: '1.75rem', fontWeight: '700', color: '#fc8181' }}>
                    {importResult.errors.length}
                  </div>
                </div>
              )}
            </div>

            {importResult.errors.length > 0 && (
              <div style={{ marginTop: '1.5rem' }}>
                <div style={{ fontSize: '0.9rem', color: '#fc8181', marginBottom: '0.5rem', fontWeight: '600' }}>
                  Import Errors:
                </div>
                <div style={{ 
                  padding: '1rem',
                  background: 'rgba(245, 101, 101, 0.1)',
                  border: '1px solid rgba(245, 101, 101, 0.3)',
                  borderRadius: '8px',
                  maxHeight: '200px',
                  overflowY: 'auto'
                }}>
                  {importResult.errors.map((error, idx) => (
                    <div key={idx} style={{ 
                      fontSize: '0.85rem', 
                      color: '#fc8181',
                      marginBottom: '0.5rem',
                      fontFamily: 'monospace'
                    }}>
                      {error}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {importResult.queued > 0 && (
              <div style={{ 
                marginTop: '1.5rem', 
                padding: '1rem',
                background: 'rgba(72, 187, 120, 0.1)',
                border: '1px solid rgba(72, 187, 120, 0.3)',
                borderRadius: '8px',
                color: '#9ae6b4',
                fontSize: '0.9rem'
              }}>
                ✓ {importResult.queued} file{importResult.queued !== 1 ? 's' : ''} queued for processing. 
                Check the Dashboard to see processing status.
              </div>
            )}
          </div>
        </div>
      )}

      {files.length === 0 && !loading && !error && lastPrefix && (
        <div className="card">
          <div className="empty-state">
            <Icon name="fileText" size={48} color="var(--text-muted)" />
            <p style={{ marginBottom: '1rem' }}>No audio files found with prefix: <code>{lastPrefix || '(root)'}</code></p>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Possible reasons:
            </p>
            <ul style={{ 
              textAlign: 'left', 
              fontSize: '0.9rem', 
              color: 'var(--text-secondary)',
              maxWidth: '500px',
              margin: '0 auto'
            }}>
              <li>Files might be in a different folder/prefix</li>
              <li>Files might not have audio extensions (.mp3, .wav, .m4a, etc.)</li>
              <li>Try scanning with an empty prefix to see all files in root</li>
              <li>Check backend logs for detailed error messages</li>
            </ul>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '1rem' }}>
              💡 Tip: Visit <code>http://localhost:8000/docs</code> and try the <code>GET /s3-import/debug-list-all</code> endpoint to see ALL files (not just audio) in your bucket.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default S3Import;

