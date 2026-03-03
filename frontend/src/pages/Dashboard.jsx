import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ServerLoadCards from '../components/ServerLoadCards'

export default function Dashboard() {
    const [fileId, setFileId] = useState('')
    const navigate = useNavigate()

    const handleWatch = (e) => {
        e.preventDefault()
        if (fileId.trim()) {
            navigate(`/watch?id=${encodeURIComponent(fileId.trim())}`)
        }
    }

    return (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-12">
            {/* ── Hero ── */}
            <section className="text-center space-y-6 animate-slide-up">
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass neon-border text-xs text-gray-400">
                    <div className="pulse-dot" />
                    <span>Backend streaming from Telegram — zero disk writes</span>
                </div>

                <h1 className="text-4xl sm:text-6xl font-extrabold leading-tight tracking-tight">
                    <span className="gradient-text">Stream Anything.</span>
                    <br />
                    <span className="text-white">Directly From Telegram.</span>
                </h1>

                <p className="max-w-2xl mx-auto text-gray-400 text-lg leading-relaxed">
                    Paste a <code className="px-1.5 py-0.5 rounded bg-surface-700 text-accent-light font-mono text-sm">file_id</code> and
                    watch your Telegram video in the browser — no downloads, no waiting.
                    Powered by an async memory pipe for blazing speed.
                </p>

                {/* Direct ID box */}
                <form
                    onSubmit={handleWatch}
                    className="mx-auto max-w-xl flex items-center gap-3"
                >
                    <div className="flex-1 relative group">
                        <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-accent/30 to-neon-cyan/30 blur-md opacity-0 group-hover:opacity-100 transition-opacity" />
                        <input
                            id="hero-file-id"
                            type="text"
                            value={fileId}
                            onChange={(e) => setFileId(e.target.value)}
                            placeholder="Paste file_id here…"
                            className="relative w-full px-5 py-3.5 rounded-xl bg-surface-800/90 border border-surface-600 text-white placeholder-gray-500 font-mono text-sm focus:outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20 transition-all"
                        />
                    </div>
                    <button
                        type="submit"
                        className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-accent to-accent-dark text-white font-semibold text-sm shadow-lg shadow-accent/25 hover:shadow-accent/40 hover:scale-105 active:scale-95 transition-all"
                    >
                        ▶ Watch
                    </button>
                </form>
            </section>

            {/* ── Live Server Load ── */}
            <section className="space-y-5">
                <div className="flex items-center gap-3">
                    <h2 className="text-xl font-bold text-white">Live Server Load</h2>
                    <span className="text-[10px] font-mono text-gray-500 px-2 py-0.5 rounded-full border border-surface-600 uppercase tracking-widest">
                        real-time
                    </span>
                </div>
                <ServerLoadCards />
            </section>

            {/* ── How it works ── */}
            <section className="space-y-5">
                <h2 className="text-xl font-bold text-white">How It Works</h2>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                    {[
                        {
                            step: '01',
                            title: 'Send Video',
                            desc: 'Forward any video to the Telegram bot.',
                            accent: 'text-accent',
                        },
                        {
                            step: '02',
                            title: 'Get Link',
                            desc: 'The bot replies with a unique streaming URL.',
                            accent: 'text-neon-cyan',
                        },
                        {
                            step: '03',
                            title: 'Watch',
                            desc: 'Open the link — video plays instantly in your browser.',
                            accent: 'text-neon-pink',
                        },
                    ].map((item) => (
                        <div
                            key={item.step}
                            className="glass neon-border rounded-2xl p-6 hover:scale-[1.02] transition-transform duration-300 group"
                        >
                            <span className={`text-3xl font-extrabold ${item.accent} opacity-30 group-hover:opacity-60 transition-opacity`}>
                                {item.step}
                            </span>
                            <h3 className="mt-2 text-lg font-semibold text-white">{item.title}</h3>
                            <p className="mt-1 text-sm text-gray-400 leading-relaxed">{item.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── Footer ── */}
            <footer className="text-center text-xs text-gray-600 pt-8 pb-4 border-t border-surface-700">
                TG Stream &middot; Zero-cost hosting on Render + Vercel &middot; Built with FastAPI &amp; React
            </footer>
        </div>
    )
}
