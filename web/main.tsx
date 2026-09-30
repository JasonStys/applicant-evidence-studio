// Purpose: mount the accessible React application; variables hold the checked root element.
// Index: createRoot@3, App@4, root@6
import { createRoot } from 'react-dom/client';
import App from './App';
import './style.css';
const root = document.getElementById('root');
if (!root) throw new Error('Application root missing');
createRoot(root).render(<App />);
