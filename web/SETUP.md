# Setup Guide - StudyNet Scraper Frontend

This guide will help you set up the React + TypeScript + Tailwind CSS frontend for StudyNet Scraper.

## Prerequisites

Before starting, ensure you have:

- **Node.js 18 or higher** installed
- **npm**, **yarn**, or **pnpm** package manager
- **Python 3.11+** with backend dependencies installed
- The backend API server running (see instructions below)

## ⚠️ Important: Start Backend First!

The frontend requires the backend API server to be running. **Start the backend before starting the frontend.**

### Starting the Backend API Server

From the **project root directory**:

```bash
python -m src.main api
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The API will be available at:
- Main API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

**Keep this terminal window open** - the backend needs to keep running while you use the frontend!

## Step-by-Step Setup

### 1. Navigate to the Web Directory

```bash
cd web
```

### 2. Install Dependencies

Install all required npm packages:

```bash
npm install
```

This will install:
- React and React DOM
- TypeScript
- Vite (build tool)
- Tailwind CSS and PostCSS
- Framer Motion (animations)
- Lucide React (icons)
- clsx and tailwind-merge (utility functions)

### 3. Verify Installation

Check that all dependencies were installed correctly:

```bash
npm list --depth=0
```

You should see all packages listed without errors.

### 4. Start the Development Server

```bash
npm run dev
```

You should see output like:
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

### 5. Open in Browser

Open your browser and navigate to:
```
http://localhost:3000
```

You should see the StudyNet Scraper interface with:
- The infinite grid background
- Navigation header with "New Job" and "Dashboard" buttons
- Theme toggle button (sun/moon icon)

## Project Structure Explained

```
web/
├── src/
│   ├── components/
│   │   ├── ui/                          # shadcn/ui components
│   │   │   ├── infinite-grid-background.tsx  # Grid animation component
│   │   │   ├── card.tsx                 # Card component
│   │   │   ├── button.tsx               # Button component
│   │   │   ├── input.tsx                # Input field component
│   │   │   ├── label.tsx                # Label component
│   │   │   ├── select.tsx               # Select dropdown component
│   │   │   ├── checkbox.tsx             # Checkbox component
│   │   │   ├── badge.tsx                # Badge component
│   │   │   └── alert.tsx                # Alert/notification component
│   │   ├── job-form.tsx                 # Job submission form
│   │   └── dashboard.tsx                # Jobs dashboard
│   ├── lib/
│   │   └── utils.ts                     # Utility functions (cn helper for class merging)
│   ├── App.tsx                          # Main app component with routing
│   ├── main.tsx                         # React entry point
│   └── index.css                        # Global styles + Tailwind directives
├── components.json                      # shadcn/ui configuration
├── tailwind.config.js                   # Tailwind CSS configuration
├── vite.config.ts                       # Vite configuration
├── tsconfig.json                        # TypeScript configuration
├── package.json                         # Dependencies and scripts
└── index.html                           # HTML template
```

## Understanding shadcn/ui Structure

### What is shadcn/ui?

shadcn/ui is a collection of reusable components built with Radix UI and Tailwind CSS. Unlike traditional component libraries, you copy the components directly into your project, giving you full control.

### Why `/components/ui`?

The `/components/ui` folder is the standard location for shadcn/ui components. This structure:

1. **Organization**: Keeps UI components separate from feature components
2. **Convention**: Follows shadcn/ui best practices
3. **Maintainability**: Makes it easy to find and update components
4. **Extensibility**: Allows easy addition of more components via CLI

### Current UI Components

All components in `/components/ui` are built following shadcn/ui patterns:

- **Card**: Container component for content sections
- **Button**: Various button styles and sizes
- **Input**: Text input fields
- **Label**: Form labels
- **Select**: Dropdown selects (simplified native version)
- **Checkbox**: Checkbox inputs
- **Badge**: Status badges
- **Alert**: Notification/alerts
- **infinite-grid-background**: Custom animated grid background

## Tailwind CSS Configuration

Tailwind is configured in `tailwind.config.js` with:

- **Dark mode**: Class-based (`.dark` class on HTML)
- **Color system**: CSS variables for theming (defined in `src/index.css`)
- **Custom colors**: Primary, secondary, muted, accent, etc.
- **Custom animations**: Accordion animations

The color system uses HSL values stored in CSS variables, allowing easy theme switching.

## TypeScript Configuration

TypeScript is configured with:

- **Strict mode**: Enabled for better type safety
- **Path aliases**: `@/*` maps to `src/*`
- **React JSX**: Modern React JSX transform
- **ES2020 target**: Modern JavaScript features

## Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter (if configured)
npm run lint
```

## Troubleshooting

### Issue: `npm install` fails

**Solution**: 
- Make sure Node.js 18+ is installed: `node --version`
- Clear npm cache: `npm cache clean --force`
- Delete `node_modules` and `package-lock.json`, then reinstall

### Issue: Port 3000 already in use

**Solution**: 
- Use a different port: `npm run dev -- --port 3001`
- Or stop the process using port 3000

### Issue: Cannot connect to API

**Solution**:
- Make sure the backend server is running on `http://localhost:8000`
- Check the API URL in components matches your backend
- Verify CORS settings in the backend allow requests from `http://localhost:3000`

### Issue: TypeScript errors

**Solution**:
- Run `npm install` to ensure all type definitions are installed
- Check `tsconfig.json` is properly configured
- Restart your IDE/editor

### Issue: Styles not applying

**Solution**:
- Make sure `src/index.css` is imported in `src/main.tsx`
- Check Tailwind directives are in `src/index.css`
- Restart the dev server

## Next Steps

1. **Start the backend server** (see main README)
2. **Open the frontend** at `http://localhost:3000`
3. **Submit a test job** using the "New Job" form
4. **View jobs** in the Dashboard

## Adding More shadcn/ui Components

If you want to add more shadcn/ui components:

1. Use the shadcn CLI:
   ```bash
   npx shadcn-ui@latest add [component-name]
   ```

2. Or manually copy components from [shadcn/ui website](https://ui.shadcn.com)

3. Components will be added to `src/components/ui/`

## Customization

- **Colors**: Edit CSS variables in `src/index.css`
- **Components**: Modify components in `src/components/ui/`
- **Layout**: Edit `src/App.tsx` for main layout changes
- **Grid Background**: Customize in `src/components/ui/infinite-grid-background.tsx`

## Need Help?

- Check the main project README
- Review the API documentation at `http://localhost:8000/docs`
- Check browser console for errors
- Review component code comments

