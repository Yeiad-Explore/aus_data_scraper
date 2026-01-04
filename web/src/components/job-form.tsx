import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { JobProgress } from '@/components/job-progress';
import { Loader2, CheckCircle2, XCircle, Info } from 'lucide-react';

const API_URL = 'http://localhost:8000';

interface ScrapeRequest {
  url: string;
  name: string;
  depth: number;
  max_pages: number;
  filter: 'same_path' | 'same_domain' | 'all';
  save_individual_pages: boolean;
  final_synthesis: boolean;
}

interface ScrapeResponse {
  status: string;
  message: string;
  job_id: string;
  job_name: string;
  url: string;
}

export function JobForm() {
  const [formData, setFormData] = useState<ScrapeRequest>({
    url: '',
    name: '',
    depth: 1,
    max_pages: 10,
    filter: 'same_path',
    save_individual_pages: true,
    final_synthesis: true,
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submittedJobId, setSubmittedJobId] = useState<string | null>(null);
  const [submittedJobName, setSubmittedJobName] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${API_URL}/scrape`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data: ScrapeResponse = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to submit job');
      }

      setSuccess(`Job "${data.job_name}" submitted successfully!`);
      setSubmittedJobId(data.job_id);
      setSubmittedJobName(data.job_name);
      // Reset form
      setFormData({
        url: '',
        name: '',
        depth: 1,
        max_pages: 10,
        filter: 'same_path',
        save_individual_pages: true,
        final_synthesis: true,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Submit Scraping Job</CardTitle>
        <CardDescription>Configure and submit a new web scraping job</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="url">
              Website URL <span className="text-red-500">*</span>
            </Label>
            <Input
              id="url"
              type="url"
              placeholder="https://example.com/page"
              value={formData.url}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="name">
              Job Name <span className="text-red-500">*</span>
            </Label>
            <Input
              id="name"
              type="text"
              placeholder="my_scrape_job"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="depth">Crawl Depth</Label>
              <Input
                id="depth"
                type="number"
                min="0"
                max="5"
                value={formData.depth}
                onChange={(e) => setFormData({ ...formData, depth: parseInt(e.target.value) || 0 })}
              />
              <p className="text-xs text-muted-foreground">How many levels of links to follow</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="max_pages">Max Pages</Label>
              <Input
                id="max_pages"
                type="number"
                min="1"
                max="1000"
                value={formData.max_pages}
                onChange={(e) => setFormData({ ...formData, max_pages: parseInt(e.target.value) || 1 })}
              />
              <p className="text-xs text-muted-foreground">Maximum number of pages to scrape</p>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="filter">Link Filter</Label>
            <Select
              id="filter"
              value={formData.filter}
              onValueChange={(value: 'same_path' | 'same_domain' | 'all') =>
                setFormData({ ...formData, filter: value })
              }
            >
              <option value="same_path">Same Path (Recommended)</option>
              <option value="same_domain">Same Domain</option>
              <option value="all">All Links</option>
            </Select>
            <p className="text-xs text-muted-foreground">How to filter discovered links</p>
          </div>

          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="save_individual_pages"
                checked={formData.save_individual_pages}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, save_individual_pages: checked === true })
                }
              />
              <Label htmlFor="save_individual_pages" className="cursor-pointer">
                Save individual page extractions
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="final_synthesis"
                checked={formData.final_synthesis}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, final_synthesis: checked === true })
                }
              />
              <Label htmlFor="final_synthesis" className="cursor-pointer">
                Perform final LLM synthesis
              </Label>
            </div>
          </div>

          {error && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {success && (
            <Alert className="border-green-500/50 bg-green-500/10">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <AlertTitle className="text-green-500">Success</AlertTitle>
              <AlertDescription className="text-green-500">{success}</AlertDescription>
            </Alert>
          )}

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Submitting...
              </>
            ) : (
              'Start Scraping'
            )}
          </Button>
        </form>

        {/* Job Progress Viewer */}
        {submittedJobId && submittedJobName && (
          <div className="mt-6 pt-6 border-t">
            <JobProgress jobId={submittedJobId} jobName={submittedJobName} />
            <div className="mt-4 flex justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSubmittedJobId(null);
                  setSubmittedJobName(null);
                  setSuccess(null);
                }}
              >
                Close Progress Viewer
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

