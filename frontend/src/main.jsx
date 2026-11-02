import React from 'react';
import ReactDOM from 'react-dom/client';
import { AppProvider } from './context/AppContext';
import { ResultsProvider } from './context/useResults';
import { App } from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AppProvider>
      <ResultsProvider>
        <App />
      </ResultsProvider>
    </AppProvider>
  </React.StrictMode>
);
