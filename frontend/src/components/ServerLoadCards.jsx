import { useState, useEffect, useRef } from 'react'

function useAnimatedCounter(target, duration = 2000) {
    const [value, setValue] = useState(0)
    const ref = useRef(null)

    useEffect(() => {
        let start = null
        const from = value

        const step = (ts) => {
            if (!start) start = ts
            const progress = Math.min((ts - start) / duration, 1)
            setValue(Math.floor(from + (target - from) * progress))
            if (progress < 1) ref.current = requestAnimationFrame(step)
        }

        ref.current = requestAnimationFrame(step)
        return () => cancelAnimationFrame(ref.current)
    }, [target])

    return value
}

export default function ServerLoadCards() {
    const [activeUsers, setActiveUsers] = useState(142)
    const [bandwidth, setBandwidth] = useState(68)

    // Simulate live fluctuations
    useEffect(() => {
        const interval = setInterval(() => {
            setActiveUsers((prev) => Math.max(50, Math.min(500, prev + Math.floor(Math.random() * 21) - 10)))
            setBandwidth((prev) => Math.max(20, Math.min(95, prev + Math.floor(Math.random() * 11) - 5)))
        }, 3000)
        return () => clearInterval(interval)
    }, [])

    const animatedUsers = useAnimatedCounter(activeUsers, 1500)
    const animatedBw = useAnimatedCounter(bandwidth, 1500)

    const cards = [
        {
            label: 'Active Users',
            value: animatedUsers,
            suffix: '',
            icon: (
                <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
                </svg>
            ),
            color: 'from-accent to-accent-light',
            barColor: 'bg-accent',
            barPercent: Math.min(100, (animatedUsers / 500) * 100),
            trend: '+12%',
            trendUp: true,
        },
        {
            label: 'Bandwidth Usage',
            value: animatedBw,
            suffix: '%',
            icon: (
                <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                </svg>
            ),
            color: 'from-neon-cyan to-neon-green',
            barColor: 'bg-neon-cyan',
            barPercent: animatedBw,
            trend: '-3%',
            trendUp: false,
        },
    ]

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {cards.map((card) => (
                <div
                    key={card.label}
                    className="glass neon-border rounded-2xl p-6 hover:scale-[1.02] transition-transform duration-300 animate-slide-up"
                >
                    {/* Header */}
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center text-white shadow-lg`}>
                                {card.icon}
                            </div>
                            <span className="text-sm font-medium text-gray-400">{card.label}</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <div className="pulse-dot" />
                            <span className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">Live</span>
                        </div>
                    </div>

                    {/* Value */}
                    <div className="flex items-end gap-2 mb-4">
                        <span className="text-4xl font-bold font-mono gradient-text">
                            {card.value.toLocaleString()}{card.suffix}
                        </span>
                        <span className={`text-xs font-medium px-1.5 py-0.5 rounded-md mb-1 ${card.trendUp ? 'bg-neon-green/10 text-neon-green' : 'bg-neon-pink/10 text-neon-pink'}`}>
                            {card.trend}
                        </span>
                    </div>

                    {/* Progress bar */}
                    <div className="w-full h-1.5 rounded-full bg-surface-700 overflow-hidden">
                        <div
                            className={`h-full rounded-full ${card.barColor} transition-all duration-1000 ease-out`}
                            style={{ width: `${card.barPercent}%` }}
                        />
                    </div>
                </div>
            ))}
        </div>
    )
}
