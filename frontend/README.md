# Frontend - AI Social Automation

React + Vite + TailwindCSS frontend for the AI Social Media Automation platform.

## Setup

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## Pages

| Page | Route | Description |
|------|-------|-------------|
| Login | `/login` | User login |
| Register | `/register` | Account creation |
| Dashboard | `/` | Overview & stats |
| Generate | `/generate` | AI content generation |
| Posts | `/posts` | Post management |
| Settings | `/settings` | API key management |

## Configuration

The frontend proxies API requests to `http://localhost:8000` in development.

For production, update `vite.config.js` or set `VITE_API_URL` environment variable.
