# Multi-Level Summarization Frontend

A modern, responsive web interface for the Jharkhand Multi-Level Summarization System built with Next.js 15 and Tailwind CSS.

## 🚀 Features

- **Intelligent Query Routing**: Automatically routes queries to the most appropriate server level
- **Multi-Server Support**: Direct access to individual servers (Server 1, 2, 3)
- **Real-time System Status**: Live monitoring of server health and statistics
- **Beautiful UI**: Modern gradient design with smooth animations
- **Citation Display**: Rich source citations with relevance scores
- **Responsive Design**: Works perfectly on desktop and mobile

## 🎨 UI Components

### Header
- System status indicator with color-coded health
- Server selection dropdown (Auto Route, Server 1, 2, 3)
- Document ingestion button
- Real-time server count display

### Main Interface
- Welcome screen with query examples
- Chat interface with message bubbles
- Routing information display
- Citation panels with source details
- Prompt viewer for debugging

### Footer
- Input field with send button
- Configuration controls (Top-K, Max Tokens)
- Backend connection status

## 🔧 Configuration

### Environment Variables
Create a `.env.local` file in the frontend directory:

```env
# Backend API URL
NEXT_PUBLIC_API_BASE=http://localhost:8000

# Alternative server URLs
NEXT_PUBLIC_SERVER1_URL=http://localhost:8001
NEXT_PUBLIC_SERVER2_URL=http://localhost:8002
NEXT_PUBLIC_SERVER3_URL=http://localhost:8003
```

### Server Selection Options
- **Auto Route**: Uses intelligent routing via orchestrator
- **Server 1**: Direct access to full document index
- **Server 2**: Direct access to L2 summary index
- **Server 3**: Direct access to L3 ultra-summary index

## 🎯 Query Types & Routing

The system automatically routes queries based on complexity:

| Query Type | Keywords | Routed To | UI Color |
|------------|----------|-----------|----------|
| **Simple** | "key points", "bullet", "concise" | Server 3 | 🟣 Purple |
| **Moderate** | "summary", "overview", "brief" | Server 2 | 🟢 Green |
| **Detailed** | "detailed", "full", "specific" | Server 1 | 🔵 Blue |
| **Comprehensive** | "comprehensive", "complete" | Server 1 | 🔴 Red |

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- Backend servers running (ports 8000-8003)

### Installation
```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

### Production Build
```bash
# Build for production
npm run build

# Start production server
npm start
```

## 🎨 Design System

### Color Palette
- **Primary**: Blue gradient (#3b82f6 to #8b5cf6)
- **Success**: Green (#10b981)
- **Warning**: Yellow (#f59e0b)
- **Error**: Red (#ef4444)
- **Background**: Slate gradient (#0f172a to #1e293b)

### Typography
- **Font**: Geist Sans (system fallback)
- **Headings**: Bold, large sizes
- **Body**: Regular weight, readable sizes
- **Code**: Geist Mono

### Components
- **Buttons**: Rounded corners, gradient backgrounds
- **Inputs**: Dark theme with blue focus states
- **Cards**: Subtle borders, rounded corners
- **Animations**: Smooth transitions, loading states

## 🔍 Features in Detail

### System Status Dashboard
- Real-time server health monitoring
- Vector count and file statistics
- Connection status indicators
- Expandable/collapsible panel

### Message Interface
- User messages: Blue gradient bubbles
- AI responses: Dark slate bubbles
- Routing info: Color-coded server badges
- Citations: Expandable source panels

### Query Processing
- Loading states with spinners
- Error handling with fallback messages
- Timeout management
- Retry mechanisms

## 🛠️ Development

### File Structure
```
src/
├── app/
│   ├── globals.css      # Global styles
│   ├── layout.tsx       # Root layout
│   └── page.tsx         # Main page component
└── components/          # Reusable components (future)
```

### Key Components
- **HomePage**: Main application component
- **MessageBubble**: Chat message display
- **PromptViewer**: Debug prompt viewer
- **SystemStatus**: Server monitoring panel

## 🎯 Integration Points

### Backend APIs
- `GET /health` - Server health checks
- `GET /stats` - System statistics
- `POST /query` - Intelligent query routing
- `POST /query/{server}` - Direct server queries
- `POST /ingest` - Document ingestion

### Error Handling
- Connection timeouts
- Server unavailability
- Fallback to direct server access
- User-friendly error messages

## 🚀 Deployment

### Vercel (Recommended)
```bash
# Deploy to Vercel
npx vercel

# Set environment variables in Vercel dashboard
NEXT_PUBLIC_API_BASE=https://your-backend-url.com
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 🔧 Troubleshooting

### Common Issues
1. **Backend Connection Failed**: Check if servers are running
2. **CORS Errors**: Ensure backend allows frontend origin
3. **Environment Variables**: Verify `.env.local` configuration
4. **Build Errors**: Check Node.js version compatibility

### Debug Mode
Enable debug logging by adding to `.env.local`:
```env
NEXT_PUBLIC_DEBUG=true
```

## 📱 Mobile Support

The interface is fully responsive and optimized for:
- **Desktop**: Full feature set with sidebar
- **Tablet**: Adapted layout with collapsible panels
- **Mobile**: Touch-friendly interface with bottom input

## 🎨 Customization

### Themes
The current design uses a dark theme. To customize:
1. Update CSS variables in `globals.css`
2. Modify Tailwind color classes
3. Adjust gradient backgrounds

### Branding
To customize branding:
1. Update logo in header component
2. Change color scheme in CSS
3. Modify title and description in layout

---

**Built with ❤️ for the Jharkhand Multi-Level Summarization System**