import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { RefreshCw, CheckCircle2, Circle, Loader2, FileText, Sparkles, Layers } from 'lucide-react';
import { cn } from '@/lib/utils';

const API_URL = 'http://localhost:8000';

interface JobProgressProps {
  jobId: string;
  jobName: string;
}

type JobStage = 'queued' | 'crawling' | 'enriching' | 'synthesizing' | 'completed' | 'failed';

interface StageInfo {
  label: string;
  icon: React.ReactNode;
  description: string;
}

const stages: Record<JobStage, StageInfo> = {
  queued: {
    label: 'Queued',
    icon: <Circle className="w-4 h-4" />,
    description: 'Job is waiting to start...',
  },
  crawling: {
    label: 'Crawling Pages',
    icon: <FileText className="w-4 h-4" />,
    description: 'Discovering and scraping pages...',
  },
  enriching: {
    label: 'Enriching Content',
    icon: <Sparkles className="w-4 h-4" />,
    description: 'Enhancing pages with LLM...',
  },
  synthesizing: {
    label: 'Final Synthesis',
    icon: <Layers className="w-4 h-4" />,
    description: 'Combining all pages...',
  },
  completed: {
    label: 'Completed',
    icon: <CheckCircle2 className="w-4 h-4" />,
    description: 'Job finished successfully!',
  },
  failed: {
    label: 'Failed',
    icon: <Circle className="w-4 h-4" />,
    description: 'Job encountered an error',
  },
};

export function JobProgress({ jobId, jobName }: JobProgressProps) {
  const [currentStage, setCurrentStage] = useState<JobStage>('queued');
  const [logs, setLogs] = useState<string[]>([]);
  const [isPolling, setIsPolling] = useState(true);

  useEffect(() => {
    if (!isPolling) return;

    const fetchStatus = async () => {
      try {
        const response = await fetch(`${API_URL}/jobs/${jobId}`);
        const job = await response.json();

        // Determine stage based on job status and result
        if (job.status === 'completed') {
          setCurrentStage('completed');
          setIsPolling(false);
          addLog('✓ Job completed successfully!');
        } else if (job.status === 'failed') {
          setCurrentStage('failed');
          setIsPolling(false);
          addLog(`✗ Job failed: ${job.error || 'Unknown error'}`);
        } else if (job.status === 'running') {
          // Estimate stage based on timing (simple heuristic)
          // In a real implementation, the backend would provide stage info
          const elapsed = job.created_at
            ? (Date.now() - new Date(job.created_at).getTime()) / 1000
            : 0;

          if (elapsed < 30) {
            setCurrentStage('crawling');
            addLog('🕷️ Crawling pages...');
          } else if (elapsed < 60) {
            setCurrentStage('enriching');
            addLog('✨ Enriching content with LLM...');
          } else {
            setCurrentStage('synthesizing');
            addLog('📚 Synthesizing final result...');
          }
        } else {
          setCurrentStage('queued');
          addLog('⏳ Job queued, waiting to start...');
        }
      } catch (error) {
        console.error('Error fetching job status:', error);
        addLog(`Error: ${error instanceof Error ? error.message : 'Failed to fetch status'}`);
      }
    };

    // Initial fetch
    fetchStatus();
    addLog(`📋 Job "${jobName}" started (ID: ${jobId.slice(0, 8)}...)`);

    // Poll every 2 seconds
    const interval = setInterval(fetchStatus, 2000);

    return () => clearInterval(interval);
  }, [jobId, jobName, isPolling]);

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => {
      const newLog = `[${timestamp}] ${message}`;
      // Prevent duplicates
      if (prev[prev.length - 1] !== newLog) {
        return [...prev.slice(-49), newLog]; // Keep last 50 logs
      }
      return prev;
    });
  };

  const getStageIndex = (stage: JobStage): number => {
    const order: JobStage[] = ['queued', 'crawling', 'enriching', 'synthesizing', 'completed'];
    return order.indexOf(stage);
  };

  const currentStageIndex = getStageIndex(currentStage);

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Job Progress: {jobName}</CardTitle>
            <CardDescription>Live updates on scraping progress</CardDescription>
          </div>
          {isPolling && (
            <Badge variant="outline" className="gap-2">
              <Loader2 className="w-3 h-3 animate-spin" />
              Live
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Progress Stages */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            {(['crawling', 'enriching', 'synthesizing'] as JobStage[]).map((stage, index) => {
              const stageInfo = stages[stage];
              const isActive = currentStageIndex >= getStageIndex(stage);
              const isCurrent = currentStage === stage;

              return (
                <div key={stage} className="flex-1 flex flex-col items-center">
                  <div
                    className={cn(
                      'w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all',
                      isActive
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'bg-muted text-muted-foreground border-muted',
                      isCurrent && 'ring-2 ring-primary ring-offset-2 animate-pulse'
                    )}
                  >
                    {isCurrent && currentStage !== 'completed' ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      stageInfo.icon
                    )}
                  </div>
                  <div className="mt-2 text-center">
                    <p
                      className={cn(
                        'text-sm font-medium',
                        isActive ? 'text-foreground' : 'text-muted-foreground'
                      )}
                    >
                      {stageInfo.label}
                    </p>
                    {isCurrent && (
                      <p className="text-xs text-muted-foreground mt-1">{stageInfo.description}</p>
                    )}
                  </div>
                  {index < 2 && (
                    <div
                      className={cn(
                        'absolute h-0.5 w-full top-5 -z-10 transition-colors',
                        currentStageIndex > getStageIndex(stage)
                          ? 'bg-primary'
                          : 'bg-muted',
                        'hidden md:block'
                      )}
                      style={{ left: 'calc(50% + 40px)', width: 'calc(100% - 80px)' }}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Activity Log */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Activity Log</h3>
            <button
              onClick={() => setLogs([])}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Clear
            </button>
          </div>
          <div className="h-48 w-full rounded-md border bg-muted/50 p-4 font-mono text-sm overflow-auto">
            {logs.length === 0 ? (
              <p className="text-muted-foreground">Waiting for activity...</p>
            ) : (
              <div className="space-y-1">
                {logs.map((log, index) => (
                  <div key={index} className="text-foreground/80">
                    {log}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Tips */}
        {currentStage === 'crawling' && (
          <div className="rounded-lg bg-blue-500/10 border border-blue-500/20 p-3 text-sm text-blue-500">
            💡 <strong>Tip:</strong> The scraper is discovering and crawling pages. This may take a
            few minutes depending on the number of pages.
          </div>
        )}
        {currentStage === 'enriching' && (
          <div className="rounded-lg bg-purple-500/10 border border-purple-500/20 p-3 text-sm text-purple-500">
            💡 <strong>Tip:</strong> Each page is being enhanced with AI. This stage processes pages
            one by one.
          </div>
        )}
        {currentStage === 'synthesizing' && (
          <div className="rounded-lg bg-green-500/10 border border-green-500/20 p-3 text-sm text-green-500">
            💡 <strong>Tip:</strong> All pages are being combined into a final result. Almost done!
          </div>
        )}
      </CardContent>
    </Card>
  );
}

