import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Landing } from './pages/Landing'
import { Signup } from './pages/Signup'
import { Setup } from './pages/Setup'
import { Help } from './pages/Help'
import { Blog } from './pages/Blog'
import { BlogPost_HowMarloThinks as HowMarloThinks } from './pages/BlogPost_HowMarloThinks'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/setup" element={<Setup />} />
        <Route path="/help" element={<Help />} />
        <Route path="/blog" element={<Blog />} />
        <Route path="/blog/how-marlo-thinks" element={<HowMarloThinks />} />
      </Routes>
    </BrowserRouter>
  )
}