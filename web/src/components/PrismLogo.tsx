import React from 'react';

const PrismLogo = ({ size = 32, color = '#3b82f6' }: { size?: number, color?: string }) => (
    <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ filter: 'drop-shadow(0 0 8px rgba(59, 130, 246, 0.3))' }}
    >
        {/* The Prism Triangle */}
        <path
            d="M50 15L85 75H15L50 15Z"
            stroke={color}
            strokeWidth="4"
            strokeLinejoin="round"
        />

        {/* Inner refraction lines */}
        <path
            d="M50 35L70 75M50 35L30 75M50 35V75"
            stroke={color}
            strokeWidth="2"
            strokeOpacity="0.5"
        />

        {/* Light beam entering from left */}
        <path
            d="M0 45 L35 48"
            stroke="#94a3b8"
            strokeWidth="2"
            strokeDasharray="4 2"
        />

        {/* Refracted spectrum leaving from right */}
        <path d="M65 55 L100 40" stroke="#ef4444" strokeWidth="2" strokeOpacity="0.8" />
        <path d="M68 58 L100 50" stroke="#f59e0b" strokeWidth="2" strokeOpacity="0.8" />
        <path d="M71 61 L100 60" stroke="#10b981" strokeWidth="2" strokeOpacity="0.8" />
        <path d="M74 64 L100 70" stroke="#3b82f6" strokeWidth="2" strokeOpacity="0.8" />
        <path d="M77 67 L100 80" stroke="#8b5cf6" strokeWidth="2" strokeOpacity="0.8" />
    </svg>
);

export default PrismLogo;
