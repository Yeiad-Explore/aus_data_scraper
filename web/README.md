# StudyNet Scraper Frontend

Modern React + TypeScript frontend for the StudyNet Scraper web scraping tool, built with Vite, Tailwind CSS, and shadcn/ui components.

## Features

- 🎨 **Beautiful UI**: Modern design with infinite grid background animation
- 📊 **Dashboard**: View all scraping jobs and their status
- 📝 **Job Submission**: Easy-to-use form for submitting new scraping jobs
- 🌙 **Dark Mode**: Toggle between light and dark themes
- ⚡ **Real-time Updates**: Auto-refreshing dashboard with live job status
- 📱 **Responsive**: Works on desktop and mobile devices

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS
- **shadcn/ui** - Component library structure
- **Framer Motion** - Animations
- **Lucide React** - Icons

## Setup Instructions

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Python 3.11+ with all backend dependencies installed
- The backend API server running on `http://localhost:8000`

### Complete Setup Steps

**⚠️ Important: Start the backend first!**

1. **Start the Backend API Server** (in project root):
   ```bash
   python -m src.main api
   ```
   
   Keep this terminal open - the backend needs to keep running!
   
   The API will be available at `http://localhost:8000`
   - API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

2. **Navigate to the web directory** (in a new terminal):
   ```bash
   cd web
   ```

3. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   ```

5. **Open your browser:**
   The app will be available at `http://localhost:3000`

### Running Both Servers

You need **two terminal windows**:

**Terminal 1 - Backend (project root):**
```bash
python -m src.main api
```

**Terminal 2 - Frontend (web directory):**
```bash
cd web
npm run dev
```

### Building for Production

```bash
npm run build
# or
yarn build
# or
pnpm build
```

The built files will be in the `dist` directory.

### Preview Production Build

```bash
npm run preview
# or
yarn preview
# or
pnpm preview
```

## Project Structure

```
web/
├── src/
│   ├── components/
│   │   ├── ui/              # shadcn/ui components
│   │   │   ├── infinite-grid-background.tsx
│   │   │   ├── card.tsx
│   │   │   ├── button.tsx
│   │   │   └── ...
│   │   ├── job-form.tsx     # Job submission form
│   │   └── dashboard.tsx    # Jobs dashboard
│   ├── lib/
│   │   └── utils.ts         # Utility functions (cn helper)
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles + Tailwind
├── components.json           # shadcn/ui configuration
├── tailwind.config.js        # Tailwind configuration
├── vite.config.ts            # Vite configuration
├── tsconfig.json             # TypeScript configuration
└── package.json              # Dependencies
```

## shadcn/ui Setup

This project uses the shadcn/ui component structure. The `components/ui` folder contains reusable UI components.

### Why `/components/ui`?

The `/components/ui` folder is the standard location for shadcn/ui components. This structure:
- Keeps UI components organized and separate from feature components
- Makes it easy to add more shadcn/ui components via CLI
- Follows shadcn/ui conventions
- Makes components easily reusable across the app

### Adding More shadcn/ui Components

If you want to add more shadcn/ui components in the future:

```bash
npx shadcn-ui@latest add [component-name]
```

For example:
```bash
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
```

## API Integration

The frontend connects to the backend API at `http://localhost:8000`. Make sure the backend server is running before using the frontend.

### API Endpoints Used

- `POST /scrape` - Submit a new scraping job
- `GET /jobs` - Get all jobs
- `GET /jobs/{job_id}` - Get specific job status

The Vite dev server is configured to proxy `/api` requests to `http://localhost:8000`, but the components currently use direct API calls. You can modify this if needed.

## Customization

### Colors & Themes

Edit `src/index.css` to customize the color scheme. The project uses CSS variables for theming:

```css
:root {
  --primary: 222.2 47.4% 11.2%;
  --background: 0 0% 100%;
  /* ... */
}

.dark {
  --primary: 210 40% 98%;
  --background: 222.2 84% 4.9%;
  /* ... */
}
```

### Grid Background

The infinite grid background component can be customized in `src/components/ui/infinite-grid-background.tsx`. You can adjust:
- Grid size (default: 40px)
- Animation speed
- Blur sphere colors
- Mouse interaction radius

## Development Tips

- **Hot Module Replacement**: Vite provides instant HMR - changes appear immediately
- **TypeScript**: All components are typed for better IDE support
- **Tailwind IntelliSense**: Install the Tailwind CSS IntelliSense VS Code extension for autocomplete
- **Component Structure**: Follow the existing pattern for new components

## Troubleshooting

### Port Already in Use

If port 3000 is already in use, Vite will automatically try the next available port. You can also specify a port:

```bash
npm run dev -- --port 3001
```

### API Connection Issues

- Make sure the backend server is running on port 8000
- Check CORS settings in the backend if you see CORS errors
- Verify the API URL in the components matches your backend URL

### Build Errors

- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 18+)
- Clear Vite cache: `rm -rf node_modules/.vite`

## License

Same as the main project.

