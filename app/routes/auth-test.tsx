import { AuthComponent } from '~/components/auth/AuthComponent'

export default function AuthTestPage() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold">Authentication Test</h1>
          <p className="text-muted-foreground">
            Phase 1: Supabase Authentication Integration
          </p>
        </div>

        <AuthComponent />

        <div className="mt-8 p-6 border rounded-lg bg-card">
          <h2 className="text-xl font-semibold mb-4">Setup Instructions</h2>
          <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
            <li>Create a Supabase account at <a href="https://supabase.com" target="_blank" rel="noopener noreferrer" className="text-primary underline">supabase.com</a></li>
            <li>Create a new project</li>
            <li>Go to Project Settings → API</li>
            <li>Copy the Project URL and anon/public key</li>
            <li>Add them to your <code className="bg-muted px-1 py-0.5 rounded">.env</code> file:
              <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-x-auto">
{`VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here`}
              </pre>
            </li>
            <li>Restart your dev server</li>
            <li>Try signing up with a test email</li>
          </ol>
        </div>

        <div className="p-6 border rounded-lg bg-card">
          <h2 className="text-xl font-semibold mb-4">Next Steps</h2>
          <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground">
            <li>Phase 1.2: Backend JWT verification</li>
            <li>Phase 2: GCS integration for file storage</li>
            <li>Phase 3: Update frontend upload flows</li>
            <li>Phase 4: Remove render server dependencies</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
