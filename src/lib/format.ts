const AR_DIGITS = '٠١٢٣٤٥٦٧٨٩';
export const toAr = (n: number | string) => String(n).replace(/[0-9]/g, (d) => AR_DIGITS[+d]);
export const GRADE_KEY: Record<string, string> = { صح: 'صحيح', ح: 'حسن', ض: 'ضعيف' };
