import React from "react";

interface CategoryData {
  label: string;
  score: number; // 0 - 100
}

interface RadarChartProps {
  categories: CategoryData[];
  title?: string;
}

export const RadarChart: React.FC<RadarChartProps> = ({ categories, title = "Skill Domain Radar" }) => {
  const size = 300;
  const center = size / 2;
  const radius = 105;
  const totalAxes = categories.length;

  if (totalAxes < 3) return null;

  // Calculate coordinates for a given angle and ratio
  const getCoordinates = (index: number, valueRatio: number) => {
    const angle = (Math.PI * 2 * index) / totalAxes - Math.PI / 2;
    const r = radius * valueRatio;
    const x = center + r * Math.cos(angle);
    const y = center + r * Math.sin(angle);
    return { x, y };
  };

  // Generate background concentric web rings
  const webRings = [0.25, 0.5, 0.75, 1.0];

  // Data polygon points
  const polygonPoints = categories
    .map((cat, idx) => {
      const ratio = Math.max(0.1, Math.min(1.0, cat.score / 100));
      const { x, y } = getCoordinates(idx, ratio);
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className="glass-panel p-5 rounded-xl border border-border flex flex-col items-center justify-center relative overflow-hidden bg-black/40">
      <div className="w-full flex items-center justify-between mb-2">
        <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider font-mono">{title}</h3>
        <span className="text-[10px] text-zinc-500 font-mono">6 Domain Axes</span>
      </div>

      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="overflow-visible">
        {/* Background Concentric Polygon Web Rings */}
        {webRings.map((ringRatio, ringIdx) => {
          const points = categories
            .map((_, axisIdx) => {
              const { x, y } = getCoordinates(axisIdx, ringRatio);
              return `${x},${y}`;
            })
            .join(" ");
          return (
            <polygon
              key={ringIdx}
              points={points}
              fill={ringRatio === 1.0 ? "rgba(255,255,255,0.01)" : "none"}
              stroke="rgba(255, 255, 255, 0.08)"
              strokeWidth="1"
              strokeDasharray={ringRatio < 1.0 ? "3,3" : "none"}
            />
          );
        })}

        {/* Radial Axis Lines */}
        {categories.map((_, idx) => {
          const outerCoords = getCoordinates(idx, 1.0);
          return (
            <line
              key={idx}
              x1={center}
              y1={center}
              x2={outerCoords.x}
              y2={outerCoords.y}
              stroke="rgba(255, 255, 255, 0.12)"
              strokeWidth="1"
            />
          );
        })}

        {/* Skill Match Filled Data Area */}
        <polygon
          points={polygonPoints}
          fill="rgba(250, 204, 21, 0.25)"
          stroke="#facc15"
          strokeWidth="2"
          className="transition-all duration-700 ease-out"
        />

        {/* Data Vertices Dots */}
        {categories.map((cat, idx) => {
          const ratio = Math.max(0.1, Math.min(1.0, cat.score / 100));
          const { x, y } = getCoordinates(idx, ratio);
          return (
            <g key={idx}>
              <circle
                cx={x}
                cy={y}
                r="4"
                fill="#facc15"
                stroke="#000"
                strokeWidth="1.5"
                className="transition-all duration-700"
              />
            </g>
          );
        })}

        {/* Axis Labels */}
        {categories.map((cat, idx) => {
          const labelCoords = getCoordinates(idx, 1.25);
          const isLeft = labelCoords.x < center - 10;
          const isRight = labelCoords.x > center + 10;
          const textAnchor = isLeft ? "end" : isRight ? "start" : "middle";

          return (
            <text
              key={idx}
              x={labelCoords.x}
              y={labelCoords.y}
              textAnchor={textAnchor}
              fill="#d4d4d8"
              fontSize="10"
              fontWeight="600"
              fontFamily="monospace"
              className="select-none"
            >
              {cat.label} ({cat.score}%)
            </text>
          );
        })}
      </svg>
    </div>
  );
};
