import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Navbar() {
    const [query, setQuery] = useState('')
    const navigate = useNavigate()

    const handleSubmit = (e) => {
        e.preventDefault()
        if (query.trim()) {
            navigate(`/watch?id=${encodeURIComponent(query.trim())}`)
            setQuery('')
        }
    }

    return (
        <nav className="fixed top-0 inset-x-0 z-50 glass border-b border-accent/10">
            <div className="max-w-7xl mx-auto flex items-center justify-between px-4 sm:px-6 py-3">
                {/* Logo */}
                <a href="/" className="flex items-center gap-2 group">
                    <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent to-neon-cyan flex items-center justify-center shadow-lg shadow-accent/20 group-hover:shadow-accent/40 transition-shadow">
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M8 5v14l11-7z" />
                        </svg>
                    </div>
                    <span className="text-xl font-bold tracking-tight">
                        <span className="gradient-text">TG Stream</span>
                    </span>
                </a>

                {/* Search / Direct ID */}
                <form onSubmit={handleSubmit} className="flex-1 max-w-md mx-4 sm:mx-8">
                    <div className="relative group">
                        <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-accent/20 via-neon-cyan/20 to-accent/20 blur-sm opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="relative flex items-center">
                            <svg xmlns="http://www.w3.org/2000/svg" className="absolute left-3 w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                            <input
                                id="direct-id-input"
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Paste file_id or search…"
                                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-surface-800/80 border border-surface-600 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/30 transition-all"
                            />
                        </div>
                    </div>
                </form>

                {/* Status indicator */}
                <div className="hidden sm:flex items-center gap-2 text-xs text-gray-400">
                    <div className="pulse-dot" />
                    <span>Online</span>
                </div>
            </div>
        </nav>
    )
}
