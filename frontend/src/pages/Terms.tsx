const sections = [
  {
    id: "acceptance",
    title: "Acceptance of Terms",
    content:
      "By signing up for or using Marlo ('Service'), you agree to be bound by these Terms of Service ('Terms'). If you do not agree to these Terms, do not use the Service. These Terms apply to all users of Marlo, including business owners and their authorized representatives.",
  },
  {
    id: "description",
    title: "Description of Service",
    content:
      "Marlo is an AI-powered marketing agent for small businesses. The Service generates social media content, publishes posts to connected platforms (including Instagram), and sends weekly marketing plans and performance reports via email. Marlo operates primarily through email — no dashboard login is required for day-to-day use.",
  },
  {
    id: "eligibility",
    title: "Eligibility",
    items: [
      "You must be at least 18 years old to use Marlo",
      "You must have the legal authority to bind the business you are registering",
      "You must provide accurate and complete information during signup",
      "You must have a valid email address that you check regularly",
    ],
  },
  {
    id: "account",
    title: "Your Account",
    content:
      "You are responsible for maintaining the security of your account and for all activity that occurs under your account. Notify us immediately at hello@marlo021.ai if you suspect unauthorized access. Marlo is not liable for any loss resulting from unauthorized use of your account.",
  },
  {
    id: "subscription",
    title: "Subscription & Payment",
    subsections: [
      {
        title: "Trial Period",
        content:
          "New accounts receive a 14-day free trial with full access to all features. No credit card is required to start your trial.",
      },
      {
        title: "Paid Subscription",
        content:
          "After the trial, continued use requires a paid subscription at $99/month. Payments are processed securely via Stripe. Your subscription renews automatically each month unless cancelled.",
      },
      {
        title: "Cancellation",
        content:
          "You may cancel your subscription at any time. Cancellation takes effect at the end of your current billing period. No refunds are issued for partial months.",
      },
      {
        title: "Failed Payments",
        content:
          "If a payment fails, Marlo will pause content generation and posting until payment is resolved. We will notify you by email before any service interruption.",
      },
    ],
  },
  {
    id: "your-content",
    title: "Your Content & Data",
    content:
      "You retain ownership of all content you provide to Marlo, including your business description, brand assets, and any photos you submit. By using the Service, you grant Marlo a limited license to use your content solely to provide the Service — generating posts, publishing to connected platforms, and improving content quality.",
  },
  {
    id: "ai-content",
    title: "AI-Generated Content",
    content:
      "Marlo uses AI to generate social media captions, images, and marketing copy. You are responsible for reviewing and approving all content before it is published. By approving a post, you confirm that the content complies with applicable laws and platform policies. Marlo is not liable for any claims arising from content you approve and publish.",
    items: [
      "Always review AI-generated content before approving",
      "Do not approve content that is false, misleading, or violates any law",
      "You are solely responsible for compliance with Instagram's Community Guidelines and Terms of Use",
      "Marlo does not guarantee that AI-generated content will achieve specific marketing results",
    ],
  },
  {
    id: "instagram",
    title: "Instagram & Third-Party Platforms",
    content:
      "When you connect your Instagram account, you authorize Marlo to publish content on your behalf using the Instagram API. This connection is subject to Instagram's Terms of Use and Platform Policy. You may disconnect your Instagram account at any time via Instagram Settings → Apps and Websites. Marlo's ability to post depends on continued access to Instagram's API — we are not responsible for service interruptions caused by changes to Instagram's policies or API.",
  },
  {
    id: "prohibited",
    title: "Prohibited Uses",
    content: "You may not use Marlo to:",
    items: [
      "Post content that is illegal, defamatory, harassing, or discriminatory",
      "Violate any third-party intellectual property rights",
      "Impersonate any person or entity",
      "Distribute spam or unsolicited commercial messages",
      "Attempt to reverse engineer, hack, or disrupt the Service",
      "Use the Service for any purpose other than legitimate business marketing",
    ],
  },
  {
    id: "availability",
    title: "Service Availability",
    content:
      "Marlo aims for high availability but does not guarantee uninterrupted service. We may perform maintenance, updates, or experience outages. Scheduled posts that fail due to service outages will be retried automatically. We are not liable for missed posts caused by service interruptions beyond our control, including third-party API outages (Instagram, OpenAI, fal.ai).",
  },
  {
    id: "termination",
    title: "Termination",
    content:
      "Either party may terminate this agreement at any time. Marlo reserves the right to suspend or terminate accounts that violate these Terms, engage in fraudulent activity, or abuse the Service. Upon termination, your data will be deleted within 30 days per our Privacy Policy.",
  },
  {
    id: "disclaimer",
    title: "Disclaimer of Warranties",
    content:
      'Marlo is provided "as is" and "as available" without warranties of any kind. We do not warrant that the Service will meet your specific business requirements, that AI-generated content will be accurate or effective, or that the Service will be error-free. Use of the Service is at your own risk.',
  },
  {
    id: "liability",
    title: "Limitation of Liability",
    content:
      "To the maximum extent permitted by law, Marlo's total liability for any claims arising from use of the Service is limited to the amount you paid in the three months preceding the claim. Marlo is not liable for indirect, incidental, or consequential damages including lost profits, lost data, or reputational harm.",
  },
  {
    id: "changes",
    title: "Changes to These Terms",
    content:
      "We may update these Terms from time to time. We will notify you of material changes by email at least 14 days before they take effect. Your continued use of Marlo after the effective date constitutes acceptance of the updated Terms.",
  },
  {
    id: "governing-law",
    title: "Governing Law",
    content:
      "These Terms are governed by the laws of the State of Washington, United States, without regard to conflict of law principles. Any disputes arising from these Terms shall be resolved in the courts of King County, Washington.",
  },
  {
    id: "contact",
    title: "Contact Us",
    content:
      "If you have questions about these Terms, please contact us:",
    contact: {
      email: "hello@marlo021.ai",
      address: "Marlo, Seattle, WA, United States",
    },
  },
]

const Terms: React.FC = () => {
  return (
    <div className="min-h-screen bg-black text-gray-300 font-sans">

      {/* Header */}
      <header className="sticky top-0 z-50 flex items-center justify-between px-8 py-4 border-b border-gray-900 bg-black/90 backdrop-blur-sm">
        <a href="/" className="flex items-center gap-2 no-underline">
          <div className="w-8 h-8 bg-[#c8f135] rounded-lg flex items-center justify-center font-black text-black text-lg">
            M
          </div>
          <span className="text-white font-bold text-lg tracking-tight">marlo</span>
        </a>
        <div className="flex items-center gap-4">
          <span className="text-xs font-semibold uppercase tracking-widest text-[#c8f135] bg-gray-900 border border-gray-800 px-3 py-1 rounded-full">
            Terms of Service
          </span>
          <span className="text-gray-600 text-sm">Effective May 1, 2025</span>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-8 py-16 flex gap-16">

        {/* Sidebar */}
        <nav className="hidden lg:block w-52 shrink-0 sticky top-24 self-start">
          <p className="text-xs font-bold uppercase tracking-widest text-gray-600 mb-4">
            Contents
          </p>
          {sections.map(({ id, title }) => (
            <a
              key={id}
              href={`#${id}`}
              className="block py-1.5 pl-3 text-sm text-gray-600 hover:text-[#c8f135] border-l-2 border-gray-900 hover:border-[#c8f135] transition-colors mb-1 no-underline"
            >
              {title}
            </a>
          ))}
        </nav>

        {/* Main */}
        <main className="min-w-0 flex-1">

          {/* Hero */}
          <div className="mb-16">
            <h1 className="text-5xl font-extrabold text-white tracking-tight leading-tight mb-4">
              Terms of Service
            </h1>
            <p className="text-gray-500 text-base leading-relaxed max-w-lg">
              Plain-language terms for using Marlo. We've kept it simple and honest.
            </p>
            <div className="w-12 h-0.5 bg-[#c8f135] mt-8" />
          </div>

          {/* Sections */}
          {sections.map((section) => (
            <section
              key={section.id}
              id={section.id}
              className="mb-14 pb-14 border-b border-gray-900 scroll-mt-24"
            >
              <h2 className="text-xl font-bold text-white mb-5 tracking-tight">
                {section.title}
              </h2>

              {"content" in section && section.content && (
                <p className="text-gray-500 text-sm leading-relaxed mb-4">
                  {section.content}
                </p>
              )}

              {"subsections" in section &&
                section.subsections?.map((sub, i) => (
                  <div key={i} className="mb-6 pl-4 border-l-2 border-gray-900">
                    <h3 className="text-sm font-semibold text-gray-300 mb-2">
                      {sub.title}
                    </h3>
                    <p className="text-gray-500 text-sm leading-relaxed">
                      {sub.content}
                    </p>
                  </div>
                ))}

              {"items" in section && section.items && (
                <ul className="mt-4 space-y-0">
                  {section.items.map((item, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-3 py-3 border-b border-gray-900 text-sm text-gray-500 leading-relaxed"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-[#c8f135] shrink-0 mt-2" />
                      {item}
                    </li>
                  ))}
                </ul>
              )}

              {"contact" in section && section.contact && (
                <div className="mt-4 border border-gray-900 rounded-xl overflow-hidden">
                  <div className="flex items-center gap-6 px-5 py-4 border-b border-gray-900">
                    <span className="text-xs font-bold uppercase tracking-widest text-gray-600 w-16 shrink-0">
                      Email
                    </span>
                    <a
                      href={`mailto:${section.contact.email}`}
                      className="text-[#c8f135] text-sm no-underline hover:underline"
                    >
                      {section.contact.email}
                    </a>
                  </div>
                  <div className="flex items-center gap-6 px-5 py-4">
                    <span className="text-xs font-bold uppercase tracking-widest text-gray-600 w-16 shrink-0">
                      Address
                    </span>
                    <span className="text-gray-500 text-sm">
                      {section.contact.address}
                    </span>
                  </div>
                </div>
              )}
            </section>
          ))}

          {/* Footer */}
          <div className="flex justify-between items-center pt-6 text-gray-700 text-sm">
            <span>© 2025 Marlo. All rights reserved.</span>
            <a href="/privacy" className="text-gray-600 hover:text-gray-400 no-underline">
              Privacy Policy →
            </a>
          </div>
        </main>
      </div>
    </div>
  )
}

export default Terms