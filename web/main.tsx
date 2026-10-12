// Purpose: mount the accessible React application; variables hold the checked root element.
// Index: createRoot@3, App@4, PrivatePortal@5, enablePrivateMode@6, root@8, response@12, health@14
import { createRoot } from 'react-dom/client';
import App from './App';
import PrivatePortal from './PrivatePortal';
import { enablePrivateMode } from './api';
import './style.css';
const root = document.getElementById('root');
if (!root) throw new Error('Application root missing');
// Detect service capability, never silently downgrade a failed private account service.
fetch('/health', { cache: 'no-store' })
  .then(async (response) => {
    if (!response.ok) throw new Error('Service unavailable');
    const health = await response.json();
    if (health.mode !== 'local-single-user') enablePrivateMode();
    createRoot(root).render(health.mode === 'local-single-user' ? <App /> : <PrivatePortal />);
  })
  .catch(() => {
    enablePrivateMode();
    createRoot(root).render(<PrivatePortal />);
  });
if ('serviceWorker' in navigator) void navigator.serviceWorker.register('/sw.js').catch(() => undefined);
