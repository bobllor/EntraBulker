import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { FileProvider } from './context/FileContext.tsx'
import { BrowserRouter } from 'react-router'
import { ModalProvider } from './context/ModalContext.tsx'
import './styles.css'
import App from './App.jsx'
import { SettingsProvider } from './context/SettingsContext.tsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <SettingsProvider>
        <ModalProvider>
          <FileProvider>
            <App />
          </FileProvider>
        </ModalProvider>
      </SettingsProvider>
    </BrowserRouter>
  </StrictMode>,
)