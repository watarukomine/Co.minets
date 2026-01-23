'use client';

import { useEffect, useState, useMemo } from 'react';
import { SummaryCards } from '@/components/dashboard/summary-cards';
import { SalesTrendChart } from '@/components/dashboard/sales-trend-chart';
import { CategoryBreakdownChart } from '@/components/dashboard/category-breakdown-chart';
import { CustomerTypeChart } from '@/components/dashboard/customer-type-chart';
import { TopProductsTable } from '@/components/dashboard/top-products-table';
import {
  generateSampleSalesData,
  calculateDailySummary,
  toChartData,
  calculateTopProducts,
} from '@/lib/sample-data';
import { SalesRecord, DailySummary, CategoryBreakdown, CustomerTypeBreakdown } from '@/types/sales';

export default function DashboardPage() {
  const [salesData, setSalesData] = useState<SalesRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // サンプルデータを生成（実際にはFirebaseから取得）
    const sampleData = generateSampleSalesData(30);
    setSalesData(sampleData);
    setIsLoading(false);
  }, []);

  const analytics = useMemo(() => {
    if (salesData.length === 0) {
      return null;
    }

    const dailySummaries = calculateDailySummary(salesData);
    const chartData = toChartData(dailySummaries);
    const topProducts = calculateTopProducts(salesData);

    // 当月の合計
    const totalSales = salesData.reduce((sum, r) => sum + r.amount, 0);
    const orderCount = salesData.length;
    const averageOrder = totalSales / (dailySummaries.length || 1);

    // 前月の模擬データ（実際にはFirebaseから取得）
    const previousMonthSales = totalSales * 0.85;
    const previousMonthOrders = Math.floor(orderCount * 0.9);
    const growthRate = ((totalSales - previousMonthSales) / previousMonthSales) * 100;

    // カテゴリ別集計
    const categoryMap = new Map<string, number>();
    salesData.forEach((r) => {
      const current = categoryMap.get(r.category) || 0;
      categoryMap.set(r.category, current + r.amount);
    });
    const categoryBreakdown: CategoryBreakdown[] = Array.from(categoryMap.entries()).map(
      ([category, amount]) => ({
        category,
        amount,
        percentage: (amount / totalSales) * 100,
      })
    );

    // 販売先区分別集計
    const customerTypeMap = new Map<string, number>();
    salesData.forEach((r) => {
      const current = customerTypeMap.get(r.customerType) || 0;
      customerTypeMap.set(r.customerType, current + r.amount);
    });
    const customerTypeBreakdown: CustomerTypeBreakdown[] = Array.from(
      customerTypeMap.entries()
    ).map(([customerType, amount]) => ({
      customerType: customerType as any,
      amount,
      percentage: (amount / totalSales) * 100,
    }));

    return {
      totalSales,
      orderCount,
      averageOrder,
      growthRate,
      previousMonthSales,
      previousMonthOrders,
      chartData,
      categoryBreakdown,
      customerTypeBreakdown,
      topProducts,
    };
  }, [salesData]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">データを読み込んでいます...</p>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">データがありません</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* サマリーカード */}
        <SummaryCards
          totalSales={analytics.totalSales}
          orderCount={analytics.orderCount}
          averageOrder={analytics.averageOrder}
          growthRate={analytics.growthRate}
          previousMonthSales={analytics.previousMonthSales}
          previousMonthOrders={analytics.previousMonthOrders}
        />

        {/* チャート行1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <SalesTrendChart data={analytics.chartData} />
          <CategoryBreakdownChart data={analytics.categoryBreakdown} />
        </div>

        {/* チャート行2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <CustomerTypeChart data={analytics.customerTypeBreakdown} />
          <TopProductsTable products={analytics.topProducts} />
        </div>

        {/* フッター */}
        <div className="text-center py-8">
          <p className="text-sm text-gray-500">
            © 2026 トヨタモビリティパーツ神奈川支社 All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
}
