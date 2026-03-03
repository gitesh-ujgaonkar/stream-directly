import { useEffect, useRef, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import Plyr from 'plyr'
import 'plyr/dist/plyr.css'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:10000'

export default function WatchPage() {
    const [searchParams] = useSearchParams()
    const fileId = searchParams.get('id')
    const videoRef = useRef(null)
    const playerRef = useRef(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (!fileId || !videoRef.current) return

        // Initialize Plyr
        playerRef.current = new Plyr(videoRef.current, {
            controls: [
                'play-large', 'rewind', 'play', 'fast-forward',
                'progress', 'current-time', 'duration',
                'mute', 'volume', 'captions',
                'settings', 'pip', 'airplay', 'fullscreen',
            ],
            settings: ['quality', 'speed'],
            speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] },
            keyboard: { focused: true, global: true },
            tooltips: { controls: true, seek: true },
        })

        playerRef.current.on('ready', () => setLoading(false))
        playerRef.current.on('error', () => {
            setError('Failed to load the video. The file_id may be invalid or the stream timed out.')
            setLoading(false)
        })

        return () => {
            playerRef.current?.destroy()
        }
    }, [fileId])

    // ── No ID provided ──
    if (!fileId) {
        return (
            <div className="max-w-3xl mx-auto px-4 py-20 text-center space-y-5 animate-slide-up">
                <div className="w-20 h-20 mx-auto rounded-2xl bg-surface-700 flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-10 h-10 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
                    </svg>
                </div>
                <h2 className="text-2xl font-bold text-white">No Video Selected</h2>
                <p className="text-gray-400 max-w-md mx-auto">
                    Paste a <code className="px-1.5 py-0.5 rounded bg-surface-700 text-accent-light font-mono text-sm">file_id</code> in
                    the search bar above, or send a video to the Telegram bot to get a link.
                </p>
                <Link
                    to="/"
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-accent/10 text-accent hover:bg-accent/20 transition-colors text-sm font-medium"
                >
                    ← Back to Dashboard
                </Link>
            </div>
        )
    }

    const streamUrl = `${BACKEND_URL}/stream/${fileId}`

    return (
        <div className="max-w-5xl mx-auto px-4 py-6 space-y-6 animate-slide-up">
            {/* Breadcrumb */}
            <div className="flex items-center gap-2 text-sm text-gray-500">
                <Link to="/" className="hover:text-accent transition-colors">Dashboard</Link>
                <span>/</span>
                <span className="text-gray-400">Now Playing</span>
            </div>

            {/* Player container */}
            <div className="relative rounded-2xl overflow-hidden neon-border bg-black">
                {/* Loading skeleton */}
                {loading && (
                    <div className="absolute inset-0 z-10 flex items-center justify-center bg-surface-900/80">
                        <div className="flex flex-col items-center gap-4">
                            <div className="w-12 h-12 border-2 border-accent border-t-transparent rounded-full animate-spin" />
                            <span className="text-sm text-gray-400 animate-pulse">Loading stream…</span>
                        </div>
                    </div>
                )}

                {/* Error overlay */}
                {error && (
                    <div className="absolute inset-0 z-10 flex items-center justify-center bg-surface-900/90">
                        <div className="text-center space-y-3 p-6">
                            <div className="w-14 h-14 mx-auto rounded-full bg-red-500/10 flex items-center justify-center">
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-7 h-7 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                                </svg>
                            </div>
                            <p className="text-sm text-red-300">{error}</p>
                        </div>
                    </div>
                )}

                <video
                    ref={videoRef}
                    className="w-full aspect-video"
                    playsInline
                >
                    <source src={streamUrl} type="video/mp4" />
                </video>
            </div>

            {/* Stream info */}
            <div className="glass neon-border rounded-2xl p-5 space-y-3">
                <h3 className="text-lg font-semibold text-white">Stream Info</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                    <div>
                        <span className="text-gray-500">File ID</span>
                        <p className="font-mono text-xs text-gray-300 break-all mt-0.5">{fileId}</p>
                    </div>
                    <div>
                        <span className="text-gray-500">Stream URL</span>
                        <p className="font-mono text-xs text-gray-300 break-all mt-0.5">{streamUrl}</p>
                    </div>
                </div>
            </div>
        </div>
    )
}
