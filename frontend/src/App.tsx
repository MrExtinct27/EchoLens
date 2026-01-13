import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import Upload from './pages/Upload';
import Dashboard from './pages/Dashboard';
import CallDetail from './pages/CallDetail';
import Landing from './pages/Landing';
import S3Import from './pages/S3Import';
import { Icon } from './components/Icons';
import './App.css';

function Navbar() {
  const location = useLocation();
  const isLanding = location.pathname === '/landing' || location.pathname === '/';

  if (isLanding) return null;

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        <span className="navbar-icon" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Icon name="target" size={24} color="var(--blue-300)" />
        </span>
        <span>EchoLens</span>
      </Link>
      <div className="nav-links">
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/upload">Upload</Link>
        <Link to="/s3-import">Import from S3</Link>
      </div>
    </nav>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Navbar />
        
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/landing" element={<Landing />} />
          <Route path="/dashboard" element={
            <main className="main-content">
              <Dashboard />
            </main>
          } />
          <Route path="/upload" element={
            <main className="main-content">
              <Upload />
            </main>
          } />
          <Route path="/s3-import" element={
            <main className="main-content">
              <S3Import />
            </main>
          } />
          <Route path="/calls/:id" element={
            <main className="main-content">
              <CallDetail />
            </main>
          } />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;

