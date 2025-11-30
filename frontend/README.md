# AutoShield Frontend

Modern React dashboard for AutoShield security platform.

## Features

- **React 18** with Vite for fast development
- **React Router** for navigation
- **TanStack Query** for data fetching and caching
- **React Icons** for UI elements
- **Responsive Design** - works on desktop and mobile
- **Real-time Updates** - auto-refresh every 3-10 seconds
- **Dark Theme** - optimized for security operations

## Pages

### Dashboard
- Real-time statistics
- Critical alerts count
- Active threats monitoring
- System health status
- Quick actions

### Alerts
- View all security alerts
- Filter by severity (Critical, High, Medium, Low, Info)
- Acknowledge and resolve alerts
- Auto-refresh every 5 seconds

### Threats
- Threat intelligence view
- Threat type classification
- Mitigation status tracking
- Apply automated mitigations

### Scans
- Initiate new security scans
- Monitor scan progress
- View scan results
- Multiple scan types (Network, Port, Vulnerability, Malware, Full)

## Development

### Prerequisites
- Node.js 18+ and npm

### Install Dependencies
```bash
npm install
```

### Run Development Server
```bash
npm run dev
```

Open http://localhost:3000

### Build for Production
```bash
npm run build
```

Output in `dist/` directory

## Docker Build

```bash
# Build image
docker build -t autoshield-frontend:2.0.0 .

# Run container
docker run -p 80:80 \
  -e VITE_API_URL=http://localhost:8080 \
  autoshield-frontend:2.0.0
```

## Configuration

Environment variables:
- `VITE_API_URL` - Backend API URL (default: http://localhost:8080)

## API Integration

The frontend communicates with the Java backend via REST API:
- `/api/dashboard` - Dashboard statistics
- `/api/alerts` - Alert management
- `/api/threats` - Threat intelligence
- `/api/scans` - Security scanning
- `/api/health` - Health check

Authentication: HTTP Basic Auth (default: admin/admin123)

## Architecture

```
src/
├── components/      # Reusable UI components
│   └── Layout.jsx   # Main layout with sidebar
├── pages/          # Page components
│   ├── Dashboard.jsx
│   ├── Alerts.jsx
│   ├── Threats.jsx
│   └── Scans.jsx
├── services/       # API service layer
│   └── api.js      # Axios configuration
├── App.jsx         # Main app component
└── main.jsx        # Entry point
```

## Deployment

### Nginx Production
The Dockerfile uses nginx for serving the built React app with:
- Gzip compression
- Security headers
- API proxy to backend
- SPA routing support
- Static asset caching

### With Docker Compose
Frontend is included in the main `docker-compose.yml` and accessible at:
- http://localhost:3000 (development)
- http://[LXC-IP]:3000 (production)

## Security

- **CORS** handled by backend
- **HTTP Basic Auth** for API access
- **Security Headers** in nginx
- **XSS Protection** enabled
- **No sensitive data** in frontend code

**⚠️ Change default admin credentials in production!**

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

MIT License - See LICENSE file
