import { Metadata } from "next"
import Link from "next/link"
import { SafeLink } from "@/lib/SafeLink"

export const metadata: Metadata = {
  title: "Privacy Policy | AGI Signpost Tracker",
  description: "Privacy policy for the AGI Signpost Tracker",
}

export default function PrivacyPage() {
  return (
    <div className="container mx-auto py-12 px-4 max-w-4xl">
      <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
      
      <div className="prose prose-slate max-w-none">
        <p className="text-lg text-muted-foreground mb-8">
          Last updated: {new Date().toLocaleDateString()}
        </p>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Our Commitment to Privacy</h2>
          <p>
            The AGI Signpost Tracker is committed to transparency and user privacy. This privacy 
            policy explains how we handle data and protect your privacy when you use our service.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Data We Collect</h2>
          
          <h3 className="text-xl font-semibold mb-3 mt-6">Public Research Data</h3>
          <p>
            We collect and display publicly available information about AI research progress, including:
          </p>
          <ul className="list-disc pl-6 mb-4">
            <li>Published research papers from arXiv and academic journals</li>
            <li>Public announcements from AI research organizations</li>
            <li>Benchmark results from public leaderboards</li>
            <li>Press releases and blog posts from AI companies</li>
          </ul>
          <p>
            <strong>This data is public domain and contains no personal information.</strong> All sources 
            are properly attributed with links to original publications.
          </p>

          <h3 className="text-xl font-semibold mb-3 mt-6">Website Usage</h3>
          <p>
            We <strong>do not use cookies, tracking pixels, or analytics services</strong> that collect 
            personal information. We do not track individual users across sessions.
          </p>
          
          <h3 className="text-xl font-semibold mb-3 mt-6">API Access</h3>
          <p>
            When you access our API, we collect:
          </p>
          <ul className="list-disc pl-6 mb-4">
            <li><strong>IP Addresses</strong> - Anonymized (last octet set to 0) for rate limiting purposes</li>
            <li><strong>API Keys</strong> - If you create one, we store usage statistics (request counts, timestamps)</li>
            <li><strong>Request Logs</strong> - Retained for 30 days for debugging and security</li>
          </ul>
          <p>
            We <strong>never</strong> sell, share, or use this data for marketing purposes.
          </p>

          <h3 className="text-xl font-semibold mb-3 mt-6">No User Accounts</h3>
          <p>
            We do not require user accounts, email addresses, or personal information to access the 
            dashboard. The service is free and open to all.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">How We Use Data</h2>
          <ul className="list-disc pl-6">
            <li>
              <strong>Research Tracking:</strong> To monitor progress toward AGI via public benchmarks 
              and research milestones
            </li>
            <li>
              <strong>Rate Limiting:</strong> Anonymized IP addresses prevent API abuse
            </li>
            <li>
              <strong>Service Improvement:</strong> Error logs help us fix bugs and improve reliability
            </li>
            <li>
              <strong>Open Data:</strong> All aggregated data is made available under CC BY 4.0 license
            </li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Data Retention</h2>
          <table className="min-w-full border-collapse border border-gray-300 mb-4">
            <thead>
              <tr className="bg-gray-100">
                <th className="border border-gray-300 px-4 py-2 text-left">Data Type</th>
                <th className="border border-gray-300 px-4 py-2 text-left">Retention Period</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border border-gray-300 px-4 py-2">Research events & analysis</td>
                <td className="border border-gray-300 px-4 py-2">2 years (public archive)</td>
              </tr>
              <tr>
                <td className="border border-gray-300 px-4 py-2">API request logs</td>
                <td className="border border-gray-300 px-4 py-2">30 days</td>
              </tr>
              <tr>
                <td className="border border-gray-300 px-4 py-2">Anonymized IP addresses</td>
                <td className="border border-gray-300 px-4 py-2">24 hours</td>
              </tr>
              <tr>
                <td className="border border-gray-300 px-4 py-2">API keys (inactive)</td>
                <td className="border border-gray-300 px-4 py-2">90 days after revocation</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">GDPR Compliance</h2>
          <p>
            We comply with the EU General Data Protection Regulation (GDPR):
          </p>
          <ul className="list-disc pl-6 mb-4">
            <li><strong>No PII Collection:</strong> We do not collect personally identifiable information</li>
            <li><strong>IP Anonymization:</strong> IP addresses are anonymized before storage</li>
            <li><strong>Data Minimization:</strong> We only collect what is necessary for service operation</li>
            <li><strong>Transparency:</strong> All data sources and methodology are documented</li>
            <li><strong>Right to Access:</strong> All our data is publicly accessible via the API</li>
            <li><strong>Right to Erasure:</strong> Contact us to delete any API keys or data</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Third-Party Services</h2>
          <p>
            We use the following third-party services:
          </p>
          <ul className="list-disc pl-6 mb-4">
            <li>
              <strong>Vercel:</strong> Website hosting (see{" "}
              <SafeLink href="https://vercel.com/legal/privacy-policy" className="text-blue-600 hover:underline">
                Vercel Privacy Policy
              </SafeLink>)
            </li>
            <li>
              <strong>Railway:</strong> API hosting (see{" "}
              <SafeLink href="https://railway.app/legal/privacy" className="text-blue-600 hover:underline">
                Railway Privacy Policy
              </SafeLink>)
            </li>
            <li>
              <strong>OpenAI:</strong> LLM analysis of research papers (no personal data sent)
            </li>
          </ul>
          <p>
            We do <strong>not</strong> use Google Analytics, Facebook Pixel, or any tracking services.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Your Rights</h2>
          <p>You have the right to:</p>
          <ul className="list-disc pl-6 mb-4">
            <li>Access any data associated with your API key</li>
            <li>Request deletion of your API key and usage logs</li>
            <li>Opt-out of data collection (simply don't use the API)</li>
            <li>Export your API usage statistics</li>
          </ul>
          <p>
            To exercise these rights, contact us at the email below.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Security</h2>
          <p>
            We implement industry-standard security measures:
          </p>
          <ul className="list-disc pl-6 mb-4">
            <li>HTTPS encryption for all connections</li>
            <li>API keys hashed using SHA-256 (not stored in plaintext)</li>
            <li>Rate limiting to prevent abuse</li>
            <li>Regular security audits and updates</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Changes to This Policy</h2>
          <p>
            We may update this privacy policy from time to time. We will notify users of significant 
            changes by updating the "Last updated" date at the top of this page.
          </p>
          <p>
            For material changes, we will post a notice on the homepage for 30 days.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Contact Us</h2>
          <p>
            If you have questions about this privacy policy or want to exercise your data rights, 
            please contact us:
          </p>
          <ul className="list-none pl-0 mb-4">
            <li><strong>GitHub:</strong>{" "}
              <SafeLink href="https://github.com/hankthevc/AGITracker/issues" className="text-blue-600 hover:underline">
                Open an issue
              </SafeLink>
            </li>
            <li><strong>Website:</strong>{" "}
              <Link href="/" className="text-blue-600 hover:underline">
                agi-tracker.vercel.app
              </Link>
            </li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Open Data License</h2>
          <p>
            All research data and analysis provided by the AGI Signpost Tracker is licensed under{" "}
            <SafeLink href="https://creativecommons.org/licenses/by/4.0/" className="text-blue-600 hover:underline">
              Creative Commons Attribution 4.0 (CC BY 4.0)
            </SafeLink>.
          </p>
          <p>
            You are free to share and adapt our data for any purpose, including commercial use, 
            as long as you provide attribution.
          </p>
        </section>

        <div className="mt-12 pt-8 border-t border-gray-200">
          <p className="text-sm text-muted-foreground">
            Also see:{" "}
            <Link href="/legal/terms" className="text-blue-600 hover:underline">
              Terms of Service
            </Link>
            {" | "}
            <Link href="/methodology" className="text-blue-600 hover:underline">
              Methodology
            </Link>
            {" | "}
            <Link href="/" className="text-blue-600 hover:underline">
              Home
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
