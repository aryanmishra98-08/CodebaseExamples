import React from 'react'
import ReactDOM from 'react-dom/client'
import CameraAsciiProjection from './CameraAsciiProjection'
import { ErrorBoundary } from './ErrorBoundary'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <CameraAsciiProjection />
    </ErrorBoundary>
  </React.StrictMode>,
)
