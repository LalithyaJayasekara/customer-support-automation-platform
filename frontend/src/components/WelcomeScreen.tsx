import React from 'react';
import '../styles/WelcomeScreen.css';

interface WelcomeScreenProps {
  onStart: () => void;
}

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onStart }) => {
  return (
    <div className="welcome-container">
      <div className="welcome-content">
        <div className="welcome-hero">
          <h1>Welcome</h1>
          <h2>Support Helper</h2>
          <p>Streamline your customer support workflow with intelligent message analysis and automated responses.</p>
        </div>

        <div className="welcome-features">
          <div className="feature-card">
            <div className="feature-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 4H4C2.9 4 2.01 4.9 2.01 6L2 18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V6C22 4.9 21.1 4 20 4ZM20 8L12 13L4 8V6L12 11L20 6V8Z" fill="currentColor"/>
              </svg>
            </div>
            <h3>Smart Inbox</h3>
            <p>Automatically organize and prioritize your customer messages for efficient handling.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M13 3C8.03 3 4 7.03 4 12C4 16.97 8.03 21 13 21C17.97 21 22 16.97 22 12C22 7.03 17.97 3 13 3ZM13 19C9.13 19 6 15.87 6 12C6 8.13 9.13 5 13 5C16.87 5 20 8.13 20 12C20 15.87 16.87 19 13 19ZM12 8V12L16 14.5L16.5 13.5L13 11.5V8H12Z" fill="currentColor"/>
              </svg>
            </div>
            <h3>Quick Responses</h3>
            <p>Get contextual response suggestions to resolve issues faster.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L13.09 8.26L20 9L13.09 9.74L12 16L10.91 9.74L4 9L10.91 8.26L12 2Z" fill="currentColor"/>
              </svg>
            </div>
            <h3>Right Team</h3>
            <p>Route messages to the appropriate team members automatically.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <h3>Quality Assurance</h3>
            <p>Ensure all responses meet your quality standards before sending.</p>
          </div>
        </div>

        <div className="welcome-benefits">
          <h3>What you'll get:</h3>
          <ul>
            <li>Save hours on routine support tasks</li>
            <li>Faster response times for happier customers</li>
            <li>Reduced stress and better team organization</li>
            <li>Consistent, high-quality support responses</li>
          </ul>
        </div>

        <button className="welcome-button" onClick={onStart}>
          Get Started
        </button>

        <p className="welcome-footer">
          Free to use. No credit card required.
        </p>
      </div>
    </div>
  );
};

export default WelcomeScreen;
