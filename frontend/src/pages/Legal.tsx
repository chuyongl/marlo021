import { Page } from '../ui/kit'

function Doc({ title, updated, sections }: { title: string; updated: string; sections: [string, string[]][] }) {
  return (
    <Page narrow>
      <article className="py-12">
        <h1 className="font-serif text-[40px] font-medium">{title}</h1>
        <p className="mt-1 text-[14px] text-soft">Last updated {updated}</p>
        {sections.map(([h, ps]) => (
          <section key={h} className="mt-8">
            <h2 className="font-serif text-[24px] font-medium">{h}</h2>
            {ps.map((p, i) => <p key={i} className="mt-3 leading-relaxed text-ink/90">{p}</p>)}
          </section>
        ))}
      </article>
    </Page>
  )
}

export function Privacy() {
  return (
    <Doc title="Privacy" updated="October 15, 2026" sections={[
      ['Who we are', ['Brown Bag is a free weekly email about local market vendors and makers in Seattle. This page explains what we collect, why, and what you can do about it.']],
      ['If you read Brown Bag', [
        'We keep your email address, which vendors you follow, when you scanned a vendor or market code, and which links in our emails you click. We use this only to decide what goes in your weekly email and to show vendors and market organizers totals (for example, "64 people follow you"). Vendors and markets never see your email address.',
        'If you send us a photo or a note about something you made, we may publish it with the name you gave us. Your email address is never published.',
        'We do not sell your information, and we do not use it for advertising outside Brown Bag. Ads in the email, if any, are the same for every reader in an area and are never targeted using health information or anything you have told us privately.',
      ]],
      ['If you are a vendor', [
        'We keep your business details, your email, the conversations you have with our interviewer, the photos you upload, and the drafts and stories made from them. Your words are processed by an AI service (Anthropic) to suggest questions and write drafts. You see every draft before an editor does, and nothing is published without your chance to correct it.',
        'You can hide any published story from the website, ask us to correct it, or ask us to delete your account and content.',
      ]],
      ['Health information', ['Some vendors sell things related to health or wellness. Following them never feeds any inference about your health, and we never use such follows for ad targeting. Washington residents have additional rights under the My Health My Data Act; contact us to use them.']],
      ['Services we use', ['Email is delivered by Resend. Data is stored with our hosting provider (Railway) in the United States. Drafting uses Anthropic\'s API. These providers process data only to run Brown Bag.']],
      ['On your device', ['After you follow a vendor, your browser remembers a random code so you can follow others in one tap. Vendors and editors stay signed in the same way. We do not use advertising cookies or third-party trackers.']],
      ['Your choices', ['Every email has a one-click unsubscribe link. To see, correct or delete what we hold about you, reply to any Brown Bag email or use the contact form on our For markets page. We will respond within 30 days.']],
      ['Children', ['Brown Bag is not directed at children under 13 and we do not knowingly collect their information.']],
    ]} />
  )
}

export function Terms() {
  return (
    <Doc title="Terms" updated="October 15, 2026" sections={[
      ['The service', ['Brown Bag publishes a free weekly email and website about local vendors. Readers, vendors and market organizations can use it free of charge during the current pilot.']],
      ['Readers', ['You can follow and unfollow vendors and unsubscribe at any time. Photos and notes you send us must be yours to share, and you give us permission to publish them in Brown Bag with the credit you choose.']],
      ['Vendors', [
        'You are responsible for the accuracy of what you tell us about your own business. Only share stories that are yours to tell; do not share private information about customers or other people.',
        'You keep ownership of your words and photos. You give Brown Bag permission to edit them into stories and updates and to publish them in the email, on the website, and in material you choose to share yourself. You can ask us to stop publishing a story at any time.',
      ]],
      ['Editorial decisions', ['Brown Bag editors decide what runs and may edit for length and clarity. We do not publish anything a vendor has told us is factually wrong until it is fixed.']],
      ['No warranty', ['Brown Bag is provided as is. We do our best to keep vendor schedules and details accurate, but check with the vendor before making a special trip.']],
      ['Changes', ['We may update these terms. If we make a significant change we will say so in the weekly email.']],
    ]} />
  )
}
