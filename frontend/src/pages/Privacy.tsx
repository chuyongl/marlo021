const sections = [
  {
    id: "overview",
    title: "Overview",
    content: `Marlo ("we," "our," or "us") is an AI-powered marketing agent for small businesses. This Privacy Policy explains how we collect, use, and protect your information when you use our service at marlo021.ai. By using Marlo, you agree to the collection and use of information in accordance with this policy.`,
  },
  {
    id: "information-we-collect",
    title: "Information We Collect",
    subsections: [
      {
        title: "Account Information",
        content:
          "When you sign up, we collect your name, email address, business name, and business description. This information is used to create your account and personalize your marketing content.",
      },
      {
        title: "Business Information",
        content:
          "We collect details about your business including your industry, target audience, brand voice preferences, and posting schedule. This information is used exclusively to generate marketing content on your behalf.",
      },
      {
        title: "Social Media Connections",
        content:
          "When you connect your Instagram account, we receive an access token that allows us to publish content on your behalf. We store only the minimum required: your Instagram account ID and username. We do not access your followers, direct messages, or any data beyond what is necessary for content publishing.",
      },
      {
        title: "Usage Data",
        content:
          "We collect information about how you interact with our service, including which posts you approve or reject and your scheduling preferences. This helps us improve the quality of generated content.",
      },
    ],
  },
  {
    id: "how-we-use",
    title: "How We Use Your Information",
    items: [
      "Generate AI-written social media captions and images tailored to your business",
      "Publish approved posts to your connected Instagram account",
      "Send you weekly content previews and approval emails",
      "Improve the quality and relevance of generated content",
      "Process payments and manage your subscription",
      "Communicate service updates and important notices",
    ],
  },
  {
    id: "data-sharing",
    title: "Data Sharing & Third Parties",
    content:
      "We do not sell your personal information. We share data only with the following third-party services required to operate Marlo:",
    items: [
      "Meta (Instagram) — to publish content to your Instagram account via the Instagram Graph API",
      "OpenAI — to generate marketing copy (only your business description and strategy summary are shared; no personal data)",
      "fal.ai — to generate marketing images (only image prompts are shared)",
      "Stripe — to process subscription payments securely",
      "Railway — our cloud hosting provider, which stores application data in encrypted databases",
    ],
    footer:
      "All third-party providers are contractually obligated to use your data only to provide their services to us.",
  },
  {
    id: "instagram-permissions",
    title: "Instagram Permissions",
    content:
      "When you connect your Instagram account, Marlo requests the following permissions:",
    items: [
      "instagram_business_basic — to verify your account and retrieve your username",
      "instagram_business_content_publish — to publish approved posts to your feed",
      "instagram_business_manage_insights — to track basic post performance so we can improve future content",
    ],
    footer:
      "You can revoke these permissions at any time via Instagram Settings → Apps and Websites → Remove Marlo.",
  },
  {
    id: "data-retention",
    title: "Data Retention",
    content:
      "We retain your data for as long as your account is active. If you delete your account:",
    items: [
      "Your business information and posting history are deleted within 30 days",
      "Instagram access tokens are revoked immediately",
      "Payment records are retained for 7 years as required by law",
      "Anonymized, aggregated usage data may be retained for service improvement",
    ],
  },
  {
    id: "security",
    title: "Security",
    content:
      "We implement industry-standard security measures to protect your information:",
    items: [
      "All data is transmitted over HTTPS/TLS encryption",
      "Social media access tokens are encrypted at rest",
      "Infrastructure hosted on Railway with automatic security updates",
      "Regular security reviews of our codebase and infrastructure",
    ],
    footer:
      "No method of transmission over the internet is 100% secure. While we strive to protect your data, we cannot guarantee absolute security.",
  },
  {
    id: "your-rights",
    title: "Your Rights",
    content: "You have the following rights regarding your personal data:",
    items: [
      "Access — request a copy of all data we hold about you",
      "Correction — update or correct inaccurate information",
      "Deletion — request deletion of your account and associated data",
      "Portability — receive your data in a machine-readable format",
      "Opt-out — unsubscribe from marketing emails at any time via any email we send",
    ],
    footer: "To exercise any of these rights, email us at privacy@marlo021.ai",
  },
  {
    id: "cookies",
    title: "Cookies",
    content:
      "Marlo uses minimal cookies strictly necessary for the service to function:",
    items: [
      "Session cookies — to keep you logged in during your session",
      "Authentication tokens — to securely identify your account",
    ],
    footer:
      "We do not use advertising cookies, tracking pixels, or third-party analytics cookies.",
  },
  {
    id: "childrens-privacy",
    title: "Children's Privacy",
    content:
      "Marlo is not directed at children under the age of 13. We do not knowingly collect personal information from children under 13. If you believe a child has provided us with personal information, please contact us at privacy@marlo021.ai and we will delete it immediately.",
  },
  {
    id: "changes",
    title: "Changes to This Policy",
    content:
      "We may update this Privacy Policy from time to time. We will notify you of material changes by email at least 14 days before the change takes effect. Your continued use of Marlo after the effective date constitutes acceptance of the updated policy.",
  },
  {
    id: "contact",
    title: "Contact Us",
    content:
      "If you have questions about this Privacy Policy or how we handle your data, please contact us:",
    contact: {
      email: "privacy@marlo021.ai",
      address: "Marlo, Seattle, WA, United States",
    },
  },
]

const Privacy: React.FC = () => {
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
            Privacy Policy
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
              Privacy Policy
            </h1>
            <p className="text-gray-500 text-base leading-relaxed max-w-lg">
              We believe in radical transparency. Here's exactly what we collect,
              why we collect it, and what we do with it.
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

              {"footer" in section && section.footer && (
                <p className="text-xs text-gray-600 italic mt-4 leading-relaxed">
                  {section.footer}
                </p>
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
            <a href="/" className="text-gray-600 hover:text-gray-400 no-underline">
              Back to marlo021.ai →
            </a>
          </div>
        </main>
      </div>
    </div>
  )
}

export default Privacy