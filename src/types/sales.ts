/** 販売先区分 */
export type CustomerType = '神奈川トヨタグループ' | 'ウエインズグループ' | '外販';

/** 業種コード */
export interface IndustryCode {
  code: string;
  name: string;
  customerType: CustomerType;
}

/** 個別売上レコード */
export interface SalesRecord {
  id: string;
  date: Date;
  industryCode: string;
  customerType: CustomerType;
  category: string;
  amount: number;
  quantity: number;
}

/** 日次集計データ */
export interface DailySummary {
  date: Date;
  totalSales: number;
  orderCount: number;
  averageOrderValue: number;
  customerTypeBreakdown: CustomerTypeBreakdown[];
  categoryBreakdown: CategoryBreakdown[];
}

/** 販売先区分別内訳 */
export interface CustomerTypeBreakdown {
  customerType: CustomerType;
  amount: number;
  percentage: number;
}

/** カテゴリ別内訳 */
export interface CategoryBreakdown {
  category: string;
  amount: number;
  percentage: number;
}

/** チャート用データポイント */
export interface ChartDataPoint {
  date: string;
  amount: number;
  orderCount?: number;
}

/** 売れ筋商品 */
export interface TopProduct {
  productName: string;
  category: string;
  totalSales: number;
  quantity: number;
  rank: number;
}

/** 期間集計タイプ */
export type PeriodType = 'daily' | 'weekly' | 'monthly';
