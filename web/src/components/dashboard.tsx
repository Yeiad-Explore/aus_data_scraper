import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { JobProgress } from '@/components/job-progress';
import { RefreshCw, CheckCircle2, XCircle, Clock, ExternalLink, FileText, Eye } from 'lucide-react';
import { cn } from '@/lib/utils';

const API_URL = 'http://localhost:8000';

interface JobResult {
  pages_scraped?: number;
  duration_seconds?: number;
  output_path?: string;
  failed_urls?: string[];
}

interface Job {
  job_id: string;
  job_name: string;
  url: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  created_at?: string;
  result?: JobResult;
  error?: string;
}

interface JobsResponse {
  total: number;
  jobs: Job[];
}

export function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewingJobId, setViewingJobId] = useState<string | null>(null);
  const [viewingJobName, setViewingJobName] = useState<string | null>(null);

  const fetchJobs = async () => {
    try {
      setError(null);
      const response = await fetch(`${API_URL}/jobs`);
      if (!response.ok) throw new Error('Failed to fetch jobs');
      const data: JobsResponse = await response.json();
      // Sort by created_at descending (newest first)
      const sortedJobs = data.jobs.sort((a, b) => {
        const aTime = a.created_at ? new Date(a.created_at).getTime() : 0;
        const bTime = b.created_at ? new Date(b.created_at).getTime() : 0;
        return bTime - aTime;
      });
      setJobs(sortedJobs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error fetching jobs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: Job['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'running':
        return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusBadge = (status: Job['status']) => {
    const variants = {
      completed: 'bg-green-500/10 text-green-500 border-green-500/20',
      failed: 'bg-red-500/10 text-red-500 border-red-500/20',
      running: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
      queued: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    };
    return (
      <Badge className={cn('capitalize', variants[status])}>
        {status}
      </Badge>
    );
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}m ${secs}s`;
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Dashboard</CardTitle>
          <CardDescription>Loading jobs...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">View all scraping jobs and their status</p>
        </div>
        <Button onClick={fetchJobs} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {error && (
        <Card className="border-red-500/50 bg-red-500/10">
          <CardContent className="pt-6">
            <p className="text-red-500">Error: {error}</p>
          </CardContent>
        </Card>
      )}

      {viewingJobId && viewingJobName && (
        <div className="mb-6">
          <JobProgress jobId={viewingJobId} jobName={viewingJobName} />
          <div className="mt-4 flex justify-end">
            <Button variant="outline" onClick={() => { setViewingJobId(null); setViewingJobName(null); }}>
              Close Progress Viewer
            </Button>
          </div>
        </div>
      )}

      {jobs.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <FileText className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No jobs yet</h3>
              <p className="text-muted-foreground">Submit a scraping job to get started</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {jobs.map((job) => (
            <Card key={job.job_id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(job.status)}
                      <CardTitle className="text-xl">{job.job_name}</CardTitle>
                      {getStatusBadge(job.status)}
                    </div>
                    <CardDescription className="flex items-center gap-2 mt-2">
                      <ExternalLink className="w-4 h-4" />
                      <a
                        href={job.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:underline break-all"
                      >
                        {job.url}
                      </a>
                    </CardDescription>
                  </div>
                  {(job.status === 'running' || job.status === 'queued') && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setViewingJobId(job.job_id);
                        setViewingJobName(job.job_name);
                      }}
                      className="gap-2"
                    >
                      <Eye className="w-4 h-4" />
                      View Progress
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Job ID</p>
                    <p className="font-mono text-xs mt-1 break-all">{job.job_id}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Created At</p>
                    <p className="mt-1">{formatDate(job.created_at)}</p>
                  </div>
                  {job.result && (
                    <>
                      <div>
                        <p className="text-muted-foreground">Pages Scraped</p>
                        <p className="mt-1 font-semibold">{job.result.pages_scraped || 0}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Duration</p>
                        <p className="mt-1 font-semibold">{formatDuration(job.result.duration_seconds)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Output Path</p>
                        <p className="mt-1 font-mono text-xs break-all">{job.result.output_path || 'N/A'}</p>
                      </div>
                      {job.result.failed_urls && job.result.failed_urls.length > 0 && (
                        <div className="md:col-span-3">
                          <p className="text-muted-foreground">Failed URLs</p>
                          <p className="mt-1 text-red-500 font-semibold">{job.result.failed_urls.length}</p>
                        </div>
                      )}
                    </>
                  )}
                  {job.error && (
                    <div className="md:col-span-3">
                      <p className="text-muted-foreground">Error</p>
                      <p className="mt-1 text-red-500 font-mono text-xs break-all">{job.error}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

