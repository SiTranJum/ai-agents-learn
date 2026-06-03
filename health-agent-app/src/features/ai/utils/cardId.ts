// 卡片唯一 ID 生成（跨组件共享）
//
// 必须保证 useStreamingChat（写入状态）、ChatMessageList（读取状态）、
// HomeScreen（首页确认/取消后同步状态）三处使用同一份实现，
// 否则 aiStore.cardStatus 的 key 不一致，确认后卡片不会变灰。
//
// 该 id 同时作为发给后端的 card_id（见 useStreamingChat.sendCardAction）。
// 后端仅把它当不透明字符串存储（chat.card_id, max_length=64），不解析格式。
//
// 注意：不能用 JSON.stringify(payload).slice(0, N) 截断——同餐次的多张
// diet_parse 卡片 payload 前缀完全相同（如 {"foods":[{"name":"鸡蛋",...），
// 截断后会得到相同 id，导致多张卡片共用一个状态。这里对完整 payload 做
// djb2 哈希，保证不同 payload 一定得到不同 id。

import type { ChatCard } from '../types/ai.types';

/** djb2 字符串哈希，返回无符号十六进制字符串（确定性、与平台无关） */
function hashString(input: string): string {
  let hash = 5381;
  for (let i = 0; i < input.length; i++) {
    hash = (hash * 33) ^ input.charCodeAt(i);
  }
  // >>> 0 转无符号，避免负号；toString(36) 进一步压缩长度
  return (hash >>> 0).toString(36);
}

export function getCardId(card: ChatCard): string {
  return `card_${card.type}_${hashString(JSON.stringify(card.payload))}`;
}

