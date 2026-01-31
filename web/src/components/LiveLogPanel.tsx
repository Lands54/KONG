import React, { useEffect, useRef, useState } from 'react';

export interface LogEntry {
    message: string;
    level: string;
    timestamp: string;
}

interface LiveLogPanelProps {
    logs: LogEntry[];
    height?: string;
}

export const LiveLogPanel: React.FC<LiveLogPanelProps> = ({ logs, height = '300px' }) => {
    const scrollRef = useRef<HTMLDivElement>(null);
    const [autoScroll, setAutoScroll] = useState(true);

    useEffect(() => {
        if (autoScroll && scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs, autoScroll]);

    const handleScroll = () => {
        if (!scrollRef.current) return;
        const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
        // If user scrolls up, disable auto-scroll
        const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
        setAutoScroll(isAtBottom);
    };

    const getLevelColor = (level: string) => {
        switch (level.toUpperCase()) {
            case 'ERROR': return '#f87171'; // red
            case 'WARNING': return '#fbbf24'; // amber
            case 'DEBUG': return '#9ca3af'; // gray
            default: return '#e2e8f0'; // slate-200
        }
    };

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            height: height,
            backgroundColor: '#0f172a',
            borderRadius: '8px',
            overflow: 'hidden',
            border: '1px solid #334155',
            fontFamily: '"JetBrains Mono", "Fira Code", monospace',
        }}>
            <div style={{
                padding: '8px 16px',
                backgroundColor: '#1e293b',
                borderBottom: '1px solid #334155',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#22c55e', boxShadow: '0 0 8px #22c55e' }} />
                    <span style={{ fontSize: '11px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Live Terminal
                    </span>
                </div>
                <div style={{ fontSize: '10px', color: '#64748b' }}>
                    {logs.length} Lines • {autoScroll ? 'Following' : 'Paused'}
                </div>
            </div>

            <div
                ref={scrollRef}
                onScroll={handleScroll}
                style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '12px',
                    fontSize: '11px',
                    lineHeight: '1.6',
                    color: '#e2e8f0'
                }}
            >
                {logs.length === 0 ? (
                    <div style={{ color: '#475569', fontStyle: 'italic', textAlign: 'center', marginTop: '40px' }}>
                        Waiting for log stream...
                        <div style={{ marginTop: '8px', fontSize: '10px' }}>
                            (Initializing WebSocket connection)
                        </div>
                    </div>
                ) : (
                    logs.map((log, index) => (
                        <div key={index} style={{ marginBottom: '2px', display: 'flex', gap: '12px' }}>
                            <span style={{ color: '#64748b', minWidth: '70px', userSelect: 'none' }}>
                                {new Date(Number(log.timestamp) * 1000).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                            </span>
                            <span style={{ color: getLevelColor(log.level), fontWeight: 700, minWidth: '50px', userSelect: 'none' }}>
                                {log.level}
                            </span>
                            <span style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                                {log.message}
                            </span>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
