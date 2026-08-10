const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Proxy all requests starting with /api to the Flask backend on port 5000
app.use(createProxyMiddleware({
  pathFilter: '/api',
  target: 'http://127.0.0.1:5000',
  changeOrigin: true,
}));

// Serve static assets from public/ directory
app.use(express.static(path.join(__dirname, 'public')));

// Fallback to index.html for SPA routing
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Node.js/Express server is running on http://localhost:${PORT}`);
});
