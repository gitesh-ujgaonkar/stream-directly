import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import WatchPage from './pages/WatchPage'

function App() {
    return (
        <BrowserRouter>
            <div className="min-h-screen relative">
                <div className="animated-bg" />
                <Navbar />
                <main className="pt-20">
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/watch" element={<WatchPage />} />
                    </Routes>
                </main>
            </div>
        </BrowserRouter>
    )
}

export default App
