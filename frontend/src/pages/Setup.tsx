export function Setup() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        <div className="text-6xl mb-6">📧</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-3">Check your email!</h1>
        <p className="text-gray-500 text-base leading-relaxed mb-6">
          Marlo just sent you the first setup email. Follow the steps in the email
          to connect your Google, Instagram, and email accounts.
        </p>
        <div className="bg-white rounded-xl border border-gray-100 p-5 text-left space-y-3">
          {['Connect Google Ads & Analytics', 'Connect Facebook & Instagram',
            'Connect Mailchimp', 'Tell Marlo about your business'].map((step, i) => (
            <div key={i} className="flex items-center gap-3 text-sm text-gray-600">
              <div className="w-6 h-6 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center text-xs font-bold flex-shrink-0">{i+1}</div>
              {step}
            </div>
          ))}
        </div>
        <p className="text-gray-400 text-sm mt-6">
          The whole setup takes about 20 minutes.<br />
          After that, just check your email every morning. That's it.
        </p>
      </div>
    </div>
  )
}