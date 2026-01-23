'use client';

import { useState } from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ChartDataPoint } from '@/types/sales';

interface SalesTrendChartProps {
    data: ChartDataPoint[];
}

type PeriodTab = 'daily' | 'weekly' | 'monthly';

export function SalesTrendChart({ data }: SalesTrendChartProps) {
    const [activePeriod, setActivePeriod] = useState<PeriodTab>('daily');

    const formatYAxis = (value: number) => {
        if (value >= 1000000) return `¥${(value / 1000000).toFixed(1)}M`;
        if (value >= 1000) return `¥${(value / 1000).toFixed(0)}K`;
        return `¥${value}`;
    };

    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="glass-card p-3 shadow-lg">
                    <p className="text-sm font-semibold text-gray-900 mb-1">{payload[0].payload.date}</p>
                    <p className="text-sm text-gray-600">
                        売上: <span className="font-bold text-blue-600">¥{payload[0].value.toLocaleString()}</span>
                    </p>
                    {payload[0].payload.orderCount && (
                        <p className="text-sm text-gray-600">
                            件数: <span className="font-semibold">{payload[0].payload.orderCount}</span>
                        </p>
                    )}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="glass-card p-6 animate-slide-up">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">売上推移</h2>
                <div className="flex gap-2">
                    {(['daily', 'weekly', 'monthly'] as PeriodTab[]).map((period) => (
                        <button
                            key={period}
                            onClick={() => setActivePeriod(period)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activePeriod === period
                                    ? 'bg-blue-600 text-white shadow-md'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                }`}
                        >
                            {period === 'daily' && '日次'}
                            {period === 'weekly' && '週次'}
                            {period === 'monthly' && '月次'}
                        </button>
                    ))}
                </div>
            </div>

            <ResponsiveContainer width="100%" height={350}>
                <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                        <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#2196f3" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#2196f3" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                    <XAxis
                        dataKey="date"
                        stroke="#666"
                        style={{ fontSize: '12px' }}
                    />
                    <YAxis
                        tickFormatter={formatYAxis}
                        stroke="#666"
                        style={{ fontSize: '12px' }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Area
                        type="monotone"
                        dataKey="amount"
                        stroke="#2196f3"
                        strokeWidth={3}
                        fillOpacity={1}
                        fill="url(#colorAmount)"
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
