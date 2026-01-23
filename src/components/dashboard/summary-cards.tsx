'use client';

import { TrendingUp, TrendingDown, DollarSign, ShoppingCart, Users, Calendar } from 'lucide-react';

interface SummaryCardProps {
    title: string;
    value: string;
    change: number;
    icon: 'sales' | 'orders' | 'average' | 'growth';
    trend?: 'up' | 'down';
}

const iconMap = {
    sales: DollarSign,
    orders: ShoppingCart,
    average: Users,
    growth: Calendar,
};

export function SummaryCard({ title, value, change, icon, trend }: SummaryCardProps) {
    const Icon = iconMap[icon];
    const isPositive = change >= 0;
    const TrendIcon = isPositive ? TrendingUp : TrendingDown;

    return (
        <div className="glass-card p-6 animate-slide-up">
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
                    <h3 className="text-3xl font-bold text-gray-900 mb-2">{value}</h3>
                    <div className="flex items-center gap-1">
                        <TrendIcon
                            size={16}
                            className={isPositive ? 'text-green-600' : 'text-red-600'}
                        />
                        <span className={`text-sm font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                            {isPositive ? '+' : ''}{change.toFixed(1)}%
                        </span>
                        <span className="text-sm text-gray-500 ml-1">前月比</span>
                    </div>
                </div>
                <div className="w-12 h-12 rounded-xl gradient-secondary flex items-center justify-center">
                    <Icon size={24} className="text-white" />
                </div>
            </div>
        </div>
    );
}

interface SummaryCardsProps {
    totalSales: number;
    orderCount: number;
    averageOrder: number;
    growthRate: number;
    previousMonthSales: number;
    previousMonthOrders: number;
}

export function SummaryCards({
    totalSales,
    orderCount,
    averageOrder,
    growthRate,
    previousMonthSales,
    previousMonthOrders,
}: SummaryCardsProps) {
    const salesChange = previousMonthSales > 0
        ? ((totalSales - previousMonthSales) / previousMonthSales) * 100
        : 0;

    const ordersChange = previousMonthOrders > 0
        ? ((orderCount - previousMonthOrders) / previousMonthOrders) * 100
        : 0;

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <SummaryCard
                title="総売上（当月）"
                value={`¥${(totalSales / 1000000).toFixed(1)}M`}
                change={salesChange}
                icon="sales"
            />
            <SummaryCard
                title="販売件数"
                value={orderCount.toLocaleString()}
                change={ordersChange}
                icon="orders"
            />
            <SummaryCard
                title="平均日次売上"
                value={`¥${(averageOrder / 10000).toFixed(0)}万`}
                change={salesChange}
                icon="average"
            />
            <SummaryCard
                title="成長率"
                value={`${growthRate >= 0 ? '+' : ''}${growthRate.toFixed(1)}%`}
                change={growthRate}
                icon="growth"
            />
        </div>
    );
}
