import { useState, useEffect } from 'react';
import { InfiniteGridBackground } from '@/components/ui/infinite-grid-background';
import { JobForm } from '@/components/job-form';
import { Dashboard } from '@/components/dashboard';
import { Button } from '@/components/ui/button';
import { Sun, Moon, LayoutDashboard, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

type View = 'form' | 'dashboard';

function App() {
  const [isDark, setIsDark] = useState(false);
  const [currentView, setCurrentView] = useState<View>('form');

  useEffect(() => {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      setIsDark(true);
    } else if (savedTheme === null) {
      // Default to dark mode if no preference
      setIsDark(true);
    }
  }, []);

  useEffect(() => {
    // Sync dark mode state with HTML class
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDark]);

  return (
    <div className="w-full relative min-h-screen">
      {/* Infinite Grid Background */}
      <InfiniteGridBackground />

      {/* Header */}
      <header className="relative z-40 border-b border-border/40 bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold tracking-tight">StudyNet Scraper</h1>
            <div className="flex gap-2">
              <Button
                variant={currentView === 'form' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setCurrentView('form')}
                className="gap-2"
              >
                <FileText className="w-4 h-4" />
                New Job
              </Button>
              <Button
                variant={currentView === 'dashboard' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setCurrentView('dashboard')}
                className="gap-2"
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Button>
            </div>
          </div>

          {/* Theme Toggle */}
          <Button
            onClick={() => setIsDark(!isDark)}
            variant="ghost"
            size="icon"
            className="hover:scale-110 active:scale-95 transition-all"
            aria-label="Toggle Theme"
          >
            {isDark ? (
              <Sun className="w-5 h-5 text-yellow-500" />
            ) : (
              <Moon className="w-5 h-5 text-indigo-500" />
            )}
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 container mx-auto px-4 py-8">
        <div className="max-w-5xl mx-auto">
          {currentView === 'form' ? (
            <div className="space-y-6">
              <div className="text-center space-y-2 mb-8">
                <h2 className="text-4xl font-bold tracking-tight">Submit Scraping Job</h2>
                <p className="text-muted-foreground text-lg">
                  Configure and submit a new web scraping job
                </p>
              </div>
              <JobForm />
            </div>
          ) : (
            <Dashboard />
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-40 border-t border-border/40 bg-background/80 backdrop-blur-sm mt-12">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <p>StudyNet Scraper v1.0.0</p>
            <p className="font-mono text-xs">
              API: <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="hover:underline">http://localhost:8000/docs</a>
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;

