'use client';

import { useState } from 'react';
import { TopProduct } from '@/types/sales';
import { ArrowUp, ArrowDown } from 'lucide-react';

interface TopProductsTableProps {
    products: TopProduct[];
}

type SortKey = 'rank' | 'totalSales' | 'quantity';

export function TopProductsTable({ products }: TopProductsTableProps) {
    const [sortKey, setSortKey] = useState<SortKey>('rank');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

    const handleSort = (key: SortKey) => {
        if (sortKey === key) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortKey(key);
            setSortOrder('asc');
        }
    };

    const sortedProducts = [...products].sort((a, b) => {
        const multiplier = sortOrder === 'asc' ? 1 : -1;
        if (sortKey === 'rank') return (a.rank - b.rank) * multiplier;
        if (sortKey === 'totalSales') return (a.totalSales - b.totalSales) * multiplier;
        if (sortKey === 'quantity') return (a.quantity - b.quantity) * multiplier;
        return 0;
    });

    const SortIcon = ({ active }: { active: boolean }) => {
        if (!active) return null;
        return sortOrder === 'asc' ? (
            <ArrowUp size={16} className="inline ml-1" />
        ) : (
            <ArrowDown size={16} className="inline ml-1" />
        );
    };

    return (
        <div className="glass-card p-6 animate-slide-up">
            <h2 className="text-xl font-bold text-gray-900 mb-6">売れ筋商品ランキング</h2>
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className="border-b-2 border-gray-200">
                            <th
                                className="text-left py-3 px-4 text-sm font-semibold text-gray-700 cursor-pointer hover:bg-gray-50 transition-colors"
                                onClick={() => handleSort('rank')}
                            >
                                順位 <SortIcon active={sortKey === 'rank'} />
                            </th>
                            <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                                カテゴリ
                            </th>
                            <th
                                className="text-right py-3 px-4 text-sm font-semibold text-gray-700 cursor-pointer hover:bg-gray-50 transition-colors"
                                onClick={() => handleSort('totalSales')}
                            >
                                売上金額 <SortIcon active={sortKey === 'totalSales'} />
                            </th>
                            <th
                                className="text-right py-3 px-4 text-sm font-semibold text-gray-700 cursor-pointer hover:bg-gray-50 transition-colors"
                                onClick={() => handleSort('quantity')}
                            >
                                販売数量 <SortIcon active={sortKey === 'quantity'} />
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedProducts.map((product, index) => (
                            <tr
                                key={index}
                                className="border-b border-gray-100 hover:bg-blue-50/50 transition-colors"
                            >
                                <td className="py-4 px-4">
                                    <div className="flex items-center gap-2">
                                        <div
                                            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${product.rank <= 3
                                                    ? 'bg-gradient-to-br from-yellow-400 to-yellow-600 text-white'
                                                    : 'bg-gray-200 text-gray-700'
                                                }`}
                                        >
                                            {product.rank}
                                        </div>
                                    </div>
                                </td>
                                <td className="py-4 px-4">
                                    <div>
                                        <p className="font-semibold text-gray-900">{product.productName}</p>
                                        <p className="text-sm text-gray-500">{product.category}</p>
                                    </div>
                                </td>
                                <td className="py-4 px-4 text-right">
                                    <span className="font-semibold text-gray-900">
                                        ¥{product.totalSales.toLocaleString()}
                                    </span>
                                </td>
                                <td className="py-4 px-4 text-right">
                                    <span className="text-gray-700">{product.quantity.toLocaleString()}</span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
