import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import { ForMarkets, ForVendors } from './pages/Audience'
import { NominatePage, SharePage, StoriesPage, StoryPage, UnsubscribePage, VendorPage, VenuePage } from './pages/PublicPages'
import Report from './pages/Report'
import { Privacy, Terms } from './pages/Legal'
import { WhyLocal } from './pages/WhyLocal'
import { VendorAuth, VendorCard, VendorHome, VendorJoin } from './pages/vendor/VendorApp'
import EditorHome from './pages/editor/EditorApp'
import { Notice, Page } from './ui/kit'

function NotFound() {
  return <Page narrow><div className="py-16"><h1 className="font-serif text-[36px] font-medium">Page not found</h1><div className="mt-4"><Notice>That link doesn't go anywhere. <a href="/">Go to the home page</a>.</Notice></div></div></Page>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public site */}
        <Route path="/" element={<Home />} />
        <Route path="/stories" element={<StoriesPage />} />
        <Route path="/s/:slug" element={<StoryPage />} />
        <Route path="/v/:code" element={<VendorPage />} />
        <Route path="/m/:slug" element={<VenuePage />} />
        <Route path="/share" element={<SharePage />} />
        <Route path="/nominate" element={<NominatePage />} />
        <Route path="/unsubscribe" element={<UnsubscribePage />} />
        <Route path="/for-vendors" element={<ForVendors />} />
        <Route path="/for-markets" element={<ForMarkets />} />
        <Route path="/report/:token" element={<Report />} />
        <Route path="/why-local" element={<WhyLocal />} />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/terms" element={<Terms />} />

        {/* Vendor app */}
        <Route path="/vendor" element={<VendorHome />} />
        <Route path="/vendor/join" element={<VendorJoin />} />
        <Route path="/vendor/auth" element={<VendorAuth />} />
        <Route path="/vendor/card" element={<VendorCard />} />

        {/* Editor app */}
        <Route path="/editor" element={<EditorHome />} />

        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}
