import {
    SalesRecord,
    CustomerType,
    DailySummary,
    ChartDataPoint,
    TopProduct,
} from '@/types/sales';
import { startOfMonth, eachDayOfInterval, format } from 'date-fns';
import { ja } from 'date-fns/locale';

/** サンプル業種コードデータ */
const sampleIndustryCodes = [
    { code: '001', name: '神奈川トヨタ販売店A', customerType: '神奈川トヨタグループ' as CustomerType },
    { code: '002', name: '神奈川トヨタ販売店B', customerType: '神奈川トヨタグループ' as CustomerType },
    { code: '101', name: 'ウエインズ販売店A', customerType: 'ウエインズグループ' as CustomerType },
    { code: '102', name: 'ウエインズ販売店B', customerType: 'ウエインズグループ' as CustomerType },
    { code: '201', name: '〇〇板金工場', customerType: '外販' as CustomerType },
    { code: '202', name: '△△ガソリンスタンド', customerType: '外販' as CustomerType },
    { code: '203', name: '部品商A', customerType: '外販' as CustomerType },
];

/** サンプル商品カテゴリ */
const categories = [
    'エンジン部品',
    'ブレーキ部品',
    'サスペンション',
    '電装品',
    'ボディ部品',
    'タイヤ・ホイール',
    'オイル・液類',
    '内装品',
];

/** ランダムな日次売上データを生成 */
export function generateSampleSalesData(days: number = 30): SalesRecord[] {
    const records: SalesRecord[] = [];
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - days);

    const dateRange = eachDayOfInterval({ start: startDate, end: endDate });

    dateRange.forEach((date) => {
        // 1日あたり10〜30件の取引を生成
        const transactionCount = Math.floor(Math.random() * 20) + 10;

        for (let i = 0; i < transactionCount; i++) {
            const industryCode = sampleIndustryCodes[Math.floor(Math.random() * sampleIndustryCodes.length)];
            const category = categories[Math.floor(Math.random() * categories.length)];

            records.push({
                id: `${format(date, 'yyyyMMdd')}-${i}`,
                date,
                industryCode: industryCode.code,
                customerType: industryCode.customerType,
                category,
                amount: Math.floor(Math.random() * 500000) + 50000, // 5万〜55万円
                quantity: Math.floor(Math.random() * 20) + 1,
            });
        }
    });

    return records;
}

/** 日次サマリーを計算 */
export function calculateDailySummary(records: SalesRecord[]): DailySummary[] {
    const groupedByDate = records.reduce((acc, record) => {
        const dateKey = format(record.date, 'yyyy-MM-dd');
        if (!acc[dateKey]) {
            acc[dateKey] = [];
        }
        acc[dateKey].push(record);
        return acc;
    }, {} as Record<string, SalesRecord[]>);

    return Object.entries(groupedByDate).map(([dateStr, dayRecords]) => {
        const totalSales = dayRecords.reduce((sum, r) => sum + r.amount, 0);
        const orderCount = dayRecords.length;

        // 販売先区分別集計
        const customerTypeMap = new Map<CustomerType, number>();
        dayRecords.forEach((r) => {
            const current = customerTypeMap.get(r.customerType) || 0;
            customerTypeMap.set(r.customerType, current + r.amount);
        });

        const customerTypeBreakdown = Array.from(customerTypeMap.entries()).map(([type, amount]) => ({
            customerType: type,
            amount,
            percentage: (amount / totalSales) * 100,
        }));

        // カテゴリ別集計
        const categoryMap = new Map<string, number>();
        dayRecords.forEach((r) => {
            const current = categoryMap.get(r.category) || 0;
            categoryMap.set(r.category, current + r.amount);
        });

        const categoryBreakdown = Array.from(categoryMap.entries()).map(([category, amount]) => ({
            category,
            amount,
            percentage: (amount / totalSales) * 100,
        }));

        return {
            date: new Date(dateStr),
            totalSales,
            orderCount,
            averageOrderValue: totalSales / orderCount,
            customerTypeBreakdown,
            categoryBreakdown,
        };
    });
}

/** チャート用データポイントに変換 */
export function toChartData(summaries: DailySummary[]): ChartDataPoint[] {
    return summaries
        .sort((a, b) => a.date.getTime() - b.date.getTime())
        .map((summary) => ({
            date: format(summary.date, 'M/d', { locale: ja }),
            amount: summary.totalSales,
            orderCount: summary.orderCount,
        }));
}

/** 売れ筋商品トップ10を計算 */
export function calculateTopProducts(records: SalesRecord[]): TopProduct[] {
    // カテゴリ別に集計（実際は商品名で集計するが、サンプルなのでカテゴリで代用）
    const categoryMap = new Map<string, { totalSales: number; quantity: number }>();

    records.forEach((r) => {
        const current = categoryMap.get(r.category) || { totalSales: 0, quantity: 0 };
        categoryMap.set(r.category, {
            totalSales: current.totalSales + r.amount,
            quantity: current.quantity + r.quantity,
        });
    });

    const topProducts = Array.from(categoryMap.entries())
        .map(([category, data]) => ({
            productName: category,
            category,
            totalSales: data.totalSales,
            quantity: data.quantity,
            rank: 0,
        }))
        .sort((a, b) => b.totalSales - a.totalSales)
        .slice(0, 10)
        .map((item, index) => ({ ...item, rank: index + 1 }));

    return topProducts;
}
