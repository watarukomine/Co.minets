'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { CustomerTypeBreakdown } from '@/types/sales';

interface CustomerTypeChartProps {
    data: CustomerTypeBreakdown[];
}

const CUSTOMER_TYPE_COLORS: Record<string, string> = {
    '神奈川トヨタグループ': '#e60012',
    'ウエインズグループ': '#0066cc',
    '外販': '#00a0e9',
};

export function CustomerTypeChart({ data }: CustomerTypeChartProps) {
    const chartData = data.map((item) => ({
        name: item.customerType,
        value: item.amount,
        percentage: item.percentage,
    }));

    const formatYAxis = (value: number) => {
        if (value >= 1000000) return `¥${(value / 1000000).toFixed(1)}M`;
        if (value >= 1000) return `¥${(value / 1000).toFixed(0)}K`;
        return `¥${value}`;
    };

    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="glass-card p-3 shadow-lg">
                    <p className="text-sm font-semibold text-gray-900 mb-1">{payload[0].payload.name}</p>
                    <p className="text-sm text-gray-600">
                        売上: <span className="font-bold">¥{payload[0].value.toLocaleString()}</span>
                    </p>
                    <p className="text-sm text-gray-600">
                        割合: <span className="font-semibold">{payload[0].payload.percentage.toFixed(1)}%</span>
                    </p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="glass-card p-6 animate-slide-up">
            <h2 className="text-xl font-bold text-gray-900 mb-6">販売先区分別売上</h2>
            <ResponsiveContainer width="100%" height={350}>
                <BarChart
                    data={chartData}
                    layout="vertical"
                    margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                    <XAxis
                        type="number"
                        tickFormatter={formatYAxis}
                        stroke="#666"
                        style={{ fontSize: '12px' }}
                    />
                    <YAxis
                        type="category"
                        dataKey="name"
                        stroke="#666"
                        style={{ fontSize: '13px' }}
                        width={90}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar
                        dataKey="value"
                        radius={[0, 8, 8, 0]}
                        barSize={40}
                    >
                        {chartData.map((entry, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={CUSTOMER_TYPE_COLORS[entry.name] || '#888'}
                            />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
