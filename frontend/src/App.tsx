import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Landing } from './pages/Landing'
import { WhyLocal } from './pages/WhyLocal'
import Privacy from './pages/Privacy'
import Terms from './pages/Terms'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/why-local" element={<WhyLocal />} />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/terms" element={<Terms />} />

        {/*
          Removed — all describe the archived Instagram product:
            /signup  /setup  /help  /blog  /blog/how-marlo-thinks
          The page files are still in src/pages/ but no longer routed.
          Delete them, or rebuild for Brown Bag.

          Coming with the Brown Bag build:
            /brownbag              reader-facing subscribe page
            /v/:scanCode           QR scan landing
            /unsubscribe           one-click, required by CAN-SPAM
        */}
      </Routes>
    </BrowserRouter>
  )
}