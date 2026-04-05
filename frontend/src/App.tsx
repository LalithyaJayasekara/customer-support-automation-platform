import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './styles.css';
import WelcomeScreen from './components/WelcomeScreen';
import LoginSignup from './components/LoginSignup';
import Dashboard from './components/Dashboard';

// Set up axios defaults
axios.defaults.baseURL = 'http://127.0.0.1:8009';

interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

function App() {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false
  });
  const [showWelcome, setShowWelcome] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    if (token && user) {
      setAuthState({
        token,
        user: JSON.parse(user),
        isAuthenticated: true
      });
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setShowWelcome(false);
    }
    
    setLoading(false);
  }, []);

  const handleStartClick = () => {
    setShowWelcome(false);
  };

  const handleLogin = (token: string, user: User) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    
    setAuthState({
      token,
      user,
      isAuthenticated: true
    });
    setShowWelcome(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
    
    setAuthState({
      user: null,
      token: null,
      isAuthenticated: false
    });
    setShowWelcome(true);
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (showWelcome && !authState.isAuthenticated) {
    return <WelcomeScreen onStart={handleStartClick} />;
  }

  if (!authState.isAuthenticated) {
    return <LoginSignup onSuccess={handleLogin} />;
  }

  return (
    <Dashboard 
      user={authState.user!} 
      onLogout={handleLogout}
    />
  );
}

export default App;
