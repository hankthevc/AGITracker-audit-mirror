import { Metadata } from "next"
import Link from "next/link"
import { SafeLink } from "@/lib/SafeLink"

export const metadata: Metadata = {
  title: "Terms of Service | AGI Signpost Tracker",
  description: "Terms of service for the AGI Signpost Tracker",
}

export default function TermsPage() {
  return (
    <div className="container mx-auto py-12 px-4 max-w-4xl">
      <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
      
      <div className="prose prose-slate max-w-none">
        <p className="text-lg text-muted-foreground mb-8">
          Last updated: {new Date().toLocaleDateString()}
        </p>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">1. Acceptance of Terms</h2>
          <p>
            By accessing or using the AGI Signpost Tracker website and API (the "Service"), 
            you agree to be bound by these Terms of Service ("Terms"). If you do not agree 
            to these Terms, you may not use the Service.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">2. Description of Service</h2>
          <p>
            The AGI Signpost Tracker is an <strong>open-source, evidence-first dashboard</strong> that 
            tracks progress toward Artificial General Intelligence (AGI) via measurable benchmarks 
            and research milestones.
          </p>
          <p>
            The Service provides:
          </p>
          <ul className="list-disc pl-6 mb-4">
            <li>Public dashboard displaying AGI progress metrics</li>
            <li>REST API for programmatic access to data</li>
            <li>Research event feeds and analysis</li>
            <li>Weekly digest summaries</li>
          </ul>
          <p>
            All data is sourced from publicly available research and is provided under the{" "}
            <SafeLink href="https://creativecommons.org/licenses/by/4.0/" className="text-blue-600 hover:underline">
              CC BY 4.0 license
            </SafeLink>.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">3. Use of Service</h2>
          
          <h3 className="text-xl font-semibold mb-3 mt-6">3.1 Permitted Use</h3>
          <p>You may use the Service for:</p>
          <ul className="list-disc pl-6 mb-4">
            <li>Personal research and education</li>
            <li>Academic research and publications</li>
            <li>Commercial applications (with attribution)</li>
            <li>Building derivative works and tools</li>
          </ul>

          <h3 className="text-xl font-semibold mb-3 mt-6">3.2 Prohibited Use</h3>
          <p>You may NOT use the Service to:</p>
          <ul className="list-disc pl-6 mb-4">
            <li>Abuse rate limits or attempt to overwhelm the API</li>
            <li>Use automated tools that generate excessive requests</li>
            <li>Misrepresent the source of data (attribution required)</li>
            <li>Scrape the website in violation of robots.txt</li>
            <li>Use the Service for illegal purposes</li>
            <li>Attempt to access admin endpoints without authorization</li>
            <li>Reverse engineer or compromise the Service's security</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">4. API Access and Rate Limits</h2>
          
          <h3 className="text-xl font-semibold mb-3 mt-6">4.1 Rate Limits</h3>
          <p>API access is rate-limited based on your authentication tier:</p>
          <ul className="list-disc pl-6 mb-4">
            <li><strong>Public (no key):</strong> 60 requests per minute</li>
            <li><strong>Authenticated (API key):</strong> 300 requests per minute</li>
            <li><strong>Admin:</strong> Unlimited (for authorized maintainers only)</li>
          </ul>
          <p>
            Rate limits are subject to change. We will provide notice of increases or decreases.
          </p>

          <h3 className="text-xl font-semibold mb-3 mt-6">4.2 API Keys</h3>
          <p>
            API keys are provided on request for authenticated access. You are responsible for:
          </p>
          <ul className="list-disc pl-6 mb-4">
            <li>Keeping your API key secure (treat it like a password)</li>
            <li>Not sharing your API key with unauthorized parties</li>
            <li>Reporting any suspected compromise immediately</li>
          </ul>
          <p>
            We may revoke API keys that violate these Terms or generate excessive load.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">5. Data and Attribution</h2>
          
          <h3 className="text-xl font-semibold mb-3 mt-6">5.1 Open Data License</h3>
          <p>
            All data provided by the Service is licensed under{" "}
            <SafeLink href="https://creativecommons.org/licenses/by/4.0/" className="text-blue-600 hover:underline">
              Creative Commons Attribution 4.0 (CC BY 4.0)
            </SafeLink>.
          </p>
          <p>
            You must provide attribution when using our data:
          </p>
          <div className="bg-gray-100 p-4 rounded font-mono text-sm mb-4">
            "Data from AGI Signpost Tracker (agi-tracker.vercel.app)"
          </div>

          <h3 className="text-xl font-semibold mb-3 mt-6">5.2 Source Attribution</h3>
          <p>
            All research events include links to original sources. When using our data, 
            we encourage (but do not require) citing the original research papers and announcements.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">6. Disclaimer of Warranties</h2>
          <p className="font-semibold mb-2">
            THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND.
          </p>
          <p>
            We make no warranties that:
          </p>
          <ul className="list-disc pl-6 mb-4">
            <li>The Service will be uninterrupted or error-free</li>
            <li>Data will be 100% accurate or complete</li>
            <li>Defects will be corrected</li>
            <li>The Service is free of viruses or harmful components</li>
          </ul>
          <p>
            <strong>Research Disclaimer:</strong> Our analysis and index scores represent our 
            interpretation of public data. They should not be used as the sole basis for critical 
            decisions. Always verify data with original sources.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">7. Limitation of Liability</h2>
          <p>
            TO THE MAXIMUM EXTENT PERMITTED BY LAW, WE SHALL NOT BE LIABLE FOR ANY:
          </p>
          <ul className="list-disc pl-6 mb-4">
            <li>Indirect, incidental, special, or consequential damages</li>
            <li>Loss of profits, data, or business opportunities</li>
            <li>Damages resulting from reliance on Service data</li>
            <li>Costs of substitute services</li>
          </ul>
          <p>
            This limitation applies even if we have been advised of the possibility of such damages.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">8. Intellectual Property</h2>
          
          <h3 className="text-xl font-semibold mb-3 mt-6">8.1 Service Content</h3>
          <p>
            The Service's source code is open-source under the MIT license (see{" "}
            <SafeLink href="https://github.com/hankthevc/AGITracker" className="text-blue-600 hover:underline">
              GitHub repository
            </SafeLink>).
          </p>
          <p>
            The AGI Signpost Tracker name, logo, and branding are property of the project maintainers.
          </p>

          <h3 className="text-xl font-semibold mb-3 mt-6">8.2 User Content</h3>
          <p>
            The Service does not accept user-generated content. All data is curated from public sources.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">9. Termination</h2>
          <p>
            We reserve the right to:
          </p>
          <ul className="list-disc pl-6 mb-4">
            <li>Suspend or terminate access to the Service at any time</li>
            <li>Revoke API keys for violations of these Terms</li>
            <li>Modify or discontinue the Service without notice</li>
          </ul>
          <p>
            You may stop using the Service at any time without notice.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">10. Changes to Terms</h2>
          <p>
            We may modify these Terms at any time. Material changes will be announced on the 
            homepage for 30 days. Continued use of the Service after changes indicates acceptance 
            of the new Terms.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">11. Governing Law</h2>
          <p>
            These Terms are governed by the laws of the jurisdiction where the Service operators 
            are located, without regard to conflict of law principles.
          </p>
          <p>
            Any disputes will be resolved through binding arbitration in accordance with local rules.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">12. Contact</h2>
          <p>
            Questions about these Terms? Contact us:
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
          <h2 className="text-2xl font-semibold mb-4">13. Severability</h2>
          <p>
            If any provision of these Terms is found to be unenforceable, the remaining provisions 
            will continue in full force and effect.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">14. Entire Agreement</h2>
          <p>
            These Terms, along with our{" "}
            <Link href="/legal/privacy" className="text-blue-600 hover:underline">
              Privacy Policy
            </Link>, constitute the entire agreement between you and the AGI Signpost Tracker.
          </p>
        </section>

        <div className="mt-12 pt-8 border-t border-gray-200">
          <p className="text-sm text-muted-foreground">
            Also see:{" "}
            <Link href="/legal/privacy" className="text-blue-600 hover:underline">
              Privacy Policy
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
