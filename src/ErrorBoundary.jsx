import React from 'react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          fontFamily: 'monospace',
          color: '#555',
          background: '#F0EEE6'
        }}>
          <div style={{ textAlign: 'center' }}>
            <p>Something went wrong.</p>
            <button
              onClick={() => this.setState({ hasError: false })}
              style={{
                marginTop: 12,
                padding: '6px 14px',
                fontFamily: 'monospace',
                fontSize: 12,
                cursor: 'pointer',
                border: '1px solid rgba(0,0,0,0.1)',
                borderRadius: 20,
                background: 'rgba(0,0,0,0.05)',
                color: '#555'
              }}
            >
              Try again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
