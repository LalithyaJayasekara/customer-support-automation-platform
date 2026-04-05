import React, { useState } from 'react';
import axios from 'axios';
import '../styles/LoginSignup.css';

interface LoginSignupProps {
  onSuccess: (token: string, user: any) => void;
}

const LoginSignup: React.FC<LoginSignupProps> = ({ onSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccessMessage('');

    try {
      if (isLogin) {
        // Login
        const response = await axios.post('/auth/login', {
          username: formData.username,
          password: formData.password
        });

        const { access_token, user } = response.data;
        onSuccess(access_token, user);
      } else {
        // Register
        const response = await axios.post('/auth/register', formData);
        setSuccessMessage('Account created! Logging you in...');
        setTimeout(() => {
          setIsLogin(true);
          setFormData({ ...formData, password: '' });
        }, 1500);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Support Helper</h1>
        </div>

        <h2>{isLogin ? 'Welcome Back' : 'Create Account'}</h2>
        <p className="auth-subtitle">
          {isLogin 
            ? 'Sign in to get started' 
            : 'Join us and streamline your support team'}
        </p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Team Name or Username</label>
            <input
              type="text"
              name="username"
              placeholder="Enter your name"
              value={formData.username}
              onChange={handleInputChange}
              required
            />
          </div>

          {!isLogin && (
            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                name="email"
                placeholder="your@email.com"
                value={formData.email}
                onChange={handleInputChange}
                required
              />
            </div>
          )}

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              name="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={handleInputChange}
              required
            />
          </div>

          {error && <div className="error-message">⚠️ {error}</div>}
          {successMessage && <div className="success-message">✓ {successMessage}</div>}

          <button type="submit" disabled={loading} className="submit-button">
            {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button
              type="button"
              className="toggle-button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
                setSuccessMessage('');
              }}
            >
              {isLogin ? 'Sign Up' : 'Sign In'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginSignup;
