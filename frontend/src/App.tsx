import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Landing } from './pages/Landing'
import { Signup } from './pages/Signup'
import { Setup } from './pages/Setup'
import { Help } from './pages/Help'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/setup" element={<Setup />} />
        <Route path="/help" element={<Help />} />
        <Route path="/help/*" element={<Help />} />
      </Routes>
    </BrowserRouter>
  )
}