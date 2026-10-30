import '@fontsource-variable/fraunces';
import '@fontsource-variable/nunito';
import '@fontsource-variable/caveat';
import './styles/global.css';

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { loadCocoBytes } from './components/coco/Coco';

// Coco's .riv starts downloading right away (index.html preloads it), so he appears instantly
void loadCocoBytes().catch(() => undefined);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
