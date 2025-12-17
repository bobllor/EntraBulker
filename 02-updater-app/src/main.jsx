import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// strict mode disabled due to double API calls in testing
createRoot(document.getElementById('root')).render(
    <App />
)
