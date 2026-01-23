'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { CategoryBreakdown } from '@/types/sales';

interface CategoryBreakdownChartProps {
    data: CategoryBreakdown[];
}

const COLORS = [
    'var(--chart-blue)',
    'var(--chart-purple)',
    'var(--chart-green)',
    'var(--chart-orange)',
    'var(--chart-red)',
    '#3f51b5',
    '#ff5722',
    '#009688',
];

export function CategoryBreakdownChart({ data }: CategoryBreakdownChartProps) {
    const chartData = data.map((item) => ({
        name: item.category,
        value: item.amount,
        percentage: item.percentage,
    }));

    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="glass-card p-3 shadow-lg">
                    <p className="text-sm font-semibold text-gray-900 mb-1">{payload[0].name}</p>
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

    const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percentage }: any) => {
        const RADIAN = Math.PI / 180;
        const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);

        if (percentage < 5) return null;

        return (
            <text
                x={x}
                y={y}
                fill="white"
                textAnchor={x > cx ? 'start' : 'end'}
                dominantBaseline="central"
                className="text-sm font-bold"
            >
                {`${percentage.toFixed(0)}%`}
            </text>
        );
    };

    return (
        <div className="glass-card p-6 animate-slide-up">
            <h2 className="text-xl font-bold text-gray-900 mb-6">商品カテゴリ別内訳</h2>
            <ResponsiveContainer width="100%" height={350}>
                <PieChart>
                    <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={renderCustomLabel}
                        outerRadius={120}
                        innerRadius={60}
                        fill="#8884d8"
                        dataKey="value"
                        paddingAngle={2}
                    >
                        {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend
                        verticalAlign="bottom"
                        height={36}
                        iconType="circle"
                        formatter={(value, entry: any) => (
                            <span className="text-sm text-gray-700">{value}</span>
                        )}
                    />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
}
