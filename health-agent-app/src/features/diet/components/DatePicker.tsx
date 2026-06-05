// DatePicker（原生平台：iOS / Android）
// 用 @react-native-community/datetimepicker 弹出系统原生日期选择器。
// 这个文件没有平台后缀，因此：
//   - iOS/Android 打包时 Metro 选中它（无 .native 文件则回落到 .tsx）
//   - TypeScript 也以它作为 ./DatePicker 的类型来源
// Web 打包时 Metro 会优先选 DatePicker.web.tsx，不会引入本文件，
// 因此原生库不会进入 Web bundle。

import React, { useState } from 'react';
import { TouchableOpacity, Platform } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { todayStr } from '@shared/utils/date';

export interface DatePickerProps {
  /** 当前选中的日期 YYYY-MM-DD */
  date: string;
  onDateChange: (date: string) => void;
  /** 是否禁止选未来日期，默认 true */
  disableFuture?: boolean;
  /** 触发区域的可视内容（日期文字 + 图标） */
  children: React.ReactNode;
}

export function DatePicker({
  date,
  onDateChange,
  disableFuture = true,
  children,
}: DatePickerProps) {
  const [show, setShow] = useState(false);

  // YYYY-MM-DD 字符串 → Date 对象（补 T00:00:00 用本地时区解析，避免 UTC 偏移）
  const currentDate = new Date(`${date}T00:00:00`);
  const maximumDate = disableFuture ? new Date() : undefined;

  // 选择器回调：Android 选完即关；iOS 的 spinner 常驻，由用户点遮罩关闭
  const handleChange = (_event: unknown, selected?: Date) => {
    if (Platform.OS === 'android') setShow(false);
    if (selected) {
      const yyyy = selected.getFullYear();
      const mm = String(selected.getMonth() + 1).padStart(2, '0');
      const dd = String(selected.getDate()).padStart(2, '0');
      onDateChange(`${yyyy}-${mm}-${dd}`);
    }
  };

  return (
    <>
      <TouchableOpacity activeOpacity={0.7} onPress={() => setShow(true)}>
        {children}
      </TouchableOpacity>

      {show && (
        <DateTimePicker
          value={currentDate}
          mode="date"
          display={Platform.OS === 'ios' ? 'spinner' : 'default'}
          maximumDate={maximumDate}
          onChange={handleChange}
        />
      )}
    </>
  );
}
