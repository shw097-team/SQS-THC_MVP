# FIXTURE｜B0 SourceReadSet reception fixture (authored, not an SST source)

- **Requirement**：FIX-REQ-01 fixture requirement used only by the receiver tests.
- **Owner**：fixture
- **How／Predicate**：READ FROM THE FIXTURE SOURCE ONLY; NO DEV EFFECT.
- **Polarity**：POSITIVE_READ_AND_DEV_DENY
- **Note**：this document exists so the receive path can be exercised without any
  original-domain bytes.

| key | value |
|---|---|
| requirement | FIX-REQ-01 |
| span | 4-6 |
