// DatePicker（Web 平台）
// 用浏览器原生 <input type="date"> 的 showPicker() 弹出系统日期面板。
// 文件名带 .web 后缀，Metro 在 Web 打包时优先选中它，
// 因此原生库 @react-native-community/datetimepicker 不会进入 Web bundle。

import React, { useRef } from 'react';
import { todayStr } from '@shared/utils/date';
import type { DatePickerProps } from './DatePicker';

export function DatePicker({
  date,
  onDateChange,
  disableFuture = true,
  children,
}: DatePickerProps) {
  // 持有真实 DOM input 节点的引用（类比 Java 里持有一个对象引用的字段）
  const inputRef = useRef<HTMLInputElement | null>(null);

  const maxDate = disableFuture ? todayStr() : undefined;

  // 点击触发区：调起浏览器原生日期选择器
  const handlePress = () => {
    const input = inputRef.current;
    if (!input) return;
    if (typeof input.showPicker === 'function') {
      input.showPicker(); // 现代浏览器：直接弹出原生日历面板
    } else {
      input.focus();
      input.click(); // 老浏览器兜底
    }
  };

  return (
    <div style={{ display: 'inline-flex', position: 'relative' }}>
      <div onClick={handlePress} style={{ cursor: 'pointer' }}>
        {children}
      </div>

      {/* 隐藏的原生输入框：视觉不可见，但仍可被 showPicker() 调起 */}
      <input
        ref={inputRef}
        type="date"
        value={date}
        max={maxDate}
        onChange={(e) => {
          // input[type=date] 的 value 本身就是 YYYY-MM-DD，直接透传
          if (e.target.value) onDateChange(e.target.value);
        }}
        style={{
          position: 'absolute',
          opacity: 0,
          width: 0,
          height: 0,
          border: 'none',
          padding: 0,
          pointerEvents: 'none',
        }}
      />
    </div>
  );
}
