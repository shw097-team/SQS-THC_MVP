# b3_r5_neg_mutations.json — 讀法與上限

44 個原 NEG 案，逐案對「變異後的 Unit 集合」呼叫產品入口（`op_child` ＋ `op_route`），全數拒絕。

| 變異 | 案數 | first_fail | 強度 |
|---|---:|---|---|
| DELETE_CHILD | 12 | ATOM_ABSENT | 弱：原子被移出集合，缺席本身即拒絕 |
| DELETE_NEG | 11 | ATOM_ABSENT | 弱：同上 |
| GENERIC_REMOVE | 10 | ATOM_ABSENT | 弱：同上 |
| **PROTECTED_FIELD** | **11** | **DIRECT_CLAUSE_SHA_MISMATCH** | **強**：受保護身份欄被改，產品以 SHA 不符拒絕，是真的屬性檢查 |

基線：365 Unit，變異前 22 個 atom 為 READY_ATOM。

## 上限
33 案是「集合內缺席」型拒絕，接近必然，**不足以**證明下游波次會拒絕；11 案是真正的內容一致性檢查。
本檔是 B3 研究證據，`B3_ACCEPTED` 未成立；B3 產品施工依 Owner 指示暫停。
