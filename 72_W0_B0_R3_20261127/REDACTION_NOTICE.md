# REDACTION NOTICE — LOCAL_ONLY clause text

This directory publishes the r34 candidate of SST PH01 W0 B0 R3 (work root
`SST_PH01_W0_B0_R3_20261127`).

## 1. What was redacted in this wave (29 files actually in the commit)

The clause value carried by the B0 envelope is LOCAL_ONLY for its declared consumers.
Every published copy replaces exactly that sentence with `<LOCAL_ONLY_REDACTED>`.

| path | original sha256 | published sha256 | occurrences |
|---|---|---|---|
| `00_PREFLIGHT/DEPLOYMENT_prod_20261127.json` | `4528119b59f6d8414c96e2e024ef5b77b38eabaee41872a2098dc87306b8cff6` | `89745a94e1e95a85ab0721c47c5fd49931c96da911f8db03ab3e197354ab2294` | 12 |
| `00_PREFLIGHT/DEPLOYMENT_prod_20261127_r10.json` | `c5efcca4e2b4798ee91b5f6a5384bc9de073d4ea036d954e0704fb1a0c75a669` | `7aba6fc56a63922a0e25a6a229c7e57dff6c75ef05580fd28178b54d6a29a894` | 12 |
| `00_PREFLIGHT/DEPLOYMENT_prod_20261127_r11.json` | `9d89781cbce772c14fa1d6edcc7ffa8231331827cef1150644736ea8666a4571` | `20ed763e12768c66e3e181dc6c04ce92632ce7f6ea87af1f0b4228d090e3e3e3` | 12 |
| `00_PREFLIGHT/DEPLOYMENT_prod_20261127_r12.json` | `30f402a3f47ed399b8bf0d2d04eec9f11dec30a8c09c58cc3a3080a7ae43cb91` | `ec60eb04275655b32d5544d335f21af7ccd8b8711f7a7e385754e5ae6d2b8f91` | 12 |
| `00_PREFLIGHT/DEPLOYMENT_prod_20261127_r8.json` | `78c78defe5058cab817fbb916e6656b4f3d061ac7bc4ada1381ebe4248e4aac3` | `f201b7dcb7ea17adc97d4e018c2eedafeed12a75bcae16d0770c2fbefde11124` | 12 |
| `00_PREFLIGHT/DEPLOYMENT_prod_20261127_r9.json` | `8348c7ca686718e591741c0ca92959145e24da16d9948a5265c8cf7ecb069f1d` | `ae41b52c8b9e0da639a22786c0ed5145a271762abfa9f3411a174c56e9a0e573` | 12 |
| `00_PREFLIGHT/T1_BASELINE_20261127.json` | `a7a9a2a4c8d903b6fbc27f2a7db46b8fcb71970062e54686a1eeaf74dba3cf5f` | `bf697510500e40cd792cf557407df5c4b5c8f1a9221eedebaf43304beaf72aa8` | 4 |
| `00_PREFLIGHT/required_set_req12_read_all_2026-11-25.json` | `50ca45c106bb58fd8a3bfdf1cfaf7400fd3a06d1f95cea7f1fe8c6166eda4764` | `ea59efc53df9cdac8bd5d6a0e873092a63e7973e4836431f1ab9856807ccc4dc` | 1 |
| `00_PREFLIGHT/required_set_req12_read_w0m_2026-11-25.json` | `bc7afa530677746b8c681fc32109041a04e1fd1e7fc201c375d8edff34e6615c` | `a4b7a1c39b4c9809e4e02556bc434e4b29003584fb6b05a6f7387540df990312` | 1 |
| `20_DEV/tests/test_b0_return.py` | `7f4fbaff3ca399145b22aee84476297a02577e6142f20d06ce7d6a5c5e7540fd` | `e2ecc19b9da2264c436bb6294efd60f0a3f917f2159917300157c5afca177af5` | 2 |
| `20_DEV/tests/test_product_read.py` | `9e2d808ab821c9ac5e9ca2fcb844401dcfa342f9808e55515b30f2b6c24adeac` | `4cb095a785746a868874e332e2f908fb8f5a59da534a58b2e70de637a00f1c7b` | 3 |
| `20_DEV/tests/trust_fixture.py` | `c4db3fac39c7d0b76210b54e298b5fc4548cf6e03e3604ef57f0d2d93a0c255f` | `6b551f07f49a42279c2aae4d69722a913c885606e805f683263637f7ba77c132` | 2 |
| `40_OPS/b0_read_stdout_r8_20261127.json` | `abb5546cbf36b94195fa8935ceb170f163cbe5c7832fbf55d5f778e0f6702d2e` | `5b9775931f06a8013845ba61f42197248c9a1663763554959e4dcca37349856a` | 2 |
| `40_OPS/b0_sourcereadset_r10_20261127.json` | `0f13e6890f2e761cbc404452d1a23051e6b85d47e53c2200a988f0a06109d23c` | `528bc8886eeb78e0c4c9600973a7d035ce3eebb9383309d85a4b09c5fb7b7340` | 2 |
| `40_OPS/b0_sourcereadset_r11_20261127.json` | `fc7269789632cf29edd0671e70e688cece836afe3778147046e0566688dfeb6a` | `30e82536296d39ab8dc551054250eeef72d3338911266209094a9d22337a6dce` | 2 |
| `40_OPS/b0_sourcereadset_r8_20261127.json` | `abb5546cbf36b94195fa8935ceb170f163cbe5c7832fbf55d5f778e0f6702d2e` | `5b9775931f06a8013845ba61f42197248c9a1663763554959e4dcca37349856a` | 2 |
| `40_OPS/b0_sourcereadset_r9_20261127.json` | `5d264bdc9035879a958c03cec17a8e83c185856f0c8b860d044c0003af14c480` | `a29928f72897ac4c619bbca95ea6533c9f1e06c4f07e4c356e8664c40cc2bb0e` | 2 |
| `40_OPS/r10_consumer_B1_receipt.json` | `cb9be7dfe5fd1c46ad2674771a0563e9eae721b54c3c600bf169a461e6932197` | `c700684f1c817b0775060ab6551314ee2ad5bca998410093c9802c1c0cc6dd7e` | 2 |
| `40_OPS/r10_consumer_B2_receipt.json` | `372003e3eef1c64fc2a9146833f5946718b8801ea8dc3b304d0663a9385a280c` | `2b5f1393b82754300faa7a5a1a23b6c75f6f7eb47e406041da5bdb7667ec8e7e` | 2 |
| `40_OPS/r10_consumer_B3_receipt.json` | `0258834a444d78297c5427abc56ac56ea72a960a4d8196a263e23fd5aa55640f` | `487844af46c803b5b1e2ddde6ba071a5c6f9360ff6c196a8d9a692c48bd7cfc3` | 2 |
| `40_OPS/r8_consumer_B1_receipt.json` | `73d94d23a8930b5a880ff005d7cadd127c7bd9b760118b752cae254d8a0c4a4c` | `f3658406d507661e967ce6b3cf6344fbc6d6ec76915ac39bc9d002e7333b6019` | 2 |
| `40_OPS/r8_consumer_B2_receipt.json` | `315f83d51a0f04b5f557a2a8922d0c6ad8cbc497cad2cdd53cc8029a670a253b` | `385ef15a024c15856c8fb1126bf873e11112bfe112db6dcf762e1979f189fd39` | 2 |
| `40_OPS/r8_consumer_B3_receipt.json` | `621ebc68c26a81589ca45751d5c052d4e742b9b001167a279e4447b0b3fa3763` | `f1ae8038d80d828d2c2a97c3243acbe41a8496d96798a17eb77ae2bd4d6e53c9` | 2 |
| `40_OPS/r9_consumer_B1_receipt.json` | `7320f9f9a7525cfd801e960365de5558aa798d7d97beebc63158600da1a3381d` | `30990159d5456924ce9460de29e049969e40018c96d56e38d5876f494ac544a5` | 2 |
| `40_OPS/r9_consumer_B2_receipt.json` | `6b277f9603866d782a69539c9399f3c7fc3e88c46b4d6f5eb0c0ee845527755c` | `1a7d17e6dd2beaf87032278f7c055dd4101385e24e070680e4f714bf2d67a5aa` | 2 |
| `40_OPS/r9_consumer_B3_receipt.json` | `26b6845d95dd242c80d6d4d81a798aacc47923270d53a02fb222764ba0067004` | `4e74cca4bd4531e3de386ed0a233342b60a6a387538635e4df2522184b5d6e75` | 2 |
| `70_PUBLISH/publish_redacted.py` | `7b1d4e5a82e30f60c10ba6e9e1ff385dd16d9d9049903e7e4f2d46f6bee1a923` | `5239380c6feddcf7ecb3449e09fac210995036091cb7a27ef9e354a7bb015eaa` | 1 |
| `70_PUBLISH/publish_v3.py` | `d0fcba1a0f4c3e8030149a114f9993185c07b68628b754412999d253e5850acb` | `135d06071a997064f39ad363118f9224756eb20438c742ab77680505fb17f4b8` | 1 |
| `70_PUBLISH/publish_v4.py` | `3735285bfc0b86fa0a126f062b7d54ed228f8f5ee69ea58297ed1266009d6a5a` | `964f587214c4fe9b3d930103d2c118e8cf2c0242575065c71b8fa78fa5264264` | 1 |

## 2. What this publication cannot retract

Commit `b144f63` in this repository published the unredacted r8 copies. History is not
rewritten. This notice is the record that those bytes disclosed one clause sentence.

## 3. Pre-existing residue elsewhere in this repository (56 files at `4602fc1f3782`)

The same sentence also sits in files this wave did not author. They are listed so the
disclosure is complete; redacting them would rewrite other rounds' delivered bytes and is
left to the rights holder.

- `00_PREFLIGHT/required_set_req12_read_all_2026-11-25.json`
- `00_PREFLIGHT/required_set_req12_read_w0m_2026-11-25.json`
- `20_DEV/tests/test_b0_return.py`
- `20_DEV/tests/test_product_read.py`
- `20_DEV/tests/trust_fixture.py`
- `30_VERIFY/commander_recheck_2026-11-25.json`
- `40_OPS/ops_r4_f_neg_pin.json`
- `40_OPS/ops_r4_f_neg_pin.raw/stdout.txt`
- `40_OPS/ops_r4_f_neg_span.json`
- `40_OPS/ops_r4_f_neg_span.raw/stdout.txt`
- `40_OPS/ops_r4_f_pos.json`
- `40_OPS/ops_r4_f_pos.raw/stdout.txt`
- `40_OPS/ops_r4_g_neg_pin.json`
- `40_OPS/ops_r4_g_neg_pin.raw/stdout.txt`
- `40_OPS/ops_r4_g_neg_span.json`
- `40_OPS/ops_r4_g_neg_span.raw/stdout.txt`
- `40_OPS/ops_r4_g_pos.json`
- `40_OPS/ops_r4_g_pos.raw/stdout.txt`
- `40_OPS/ops_r4_h_neg_pin.json`
- `40_OPS/ops_r4_h_neg_pin.raw/stdout.txt`
- `40_OPS/ops_r4_h_neg_span.json`
- `40_OPS/ops_r4_h_neg_span.raw/stdout.txt`
- `40_OPS/ops_r4_h_pos.json`
- `40_OPS/ops_r4_h_pos.raw/stdout.txt`
- `40_OPS/ops_r4_neg_pin.json`
- `40_OPS/ops_r4_neg_pin.raw/stdout.txt`
- `40_OPS/ops_r4_pos.json`
- `40_OPS/ops_r4_pos.raw/stdout.txt`
- `40_OPS/ops_r4_possealed.json`
- `40_OPS/ops_r4_possealed.raw/stdout.txt`
- `40_OPS/ops_r4_r1_neg_pin.json`
- `40_OPS/ops_r4_r1_neg_pin.raw/stdout.txt`
- `40_OPS/ops_r4_r1_pos.json`
- `40_OPS/ops_r4_r1_pos.raw/stdout.txt`
- `40_OPS/ops_r4_r2_neg_pin.json`
- `40_OPS/ops_r4_r2_neg_pin.raw/stdout.txt`
- `40_OPS/ops_r4_r2_pos.json`
- `40_OPS/ops_r4_r2_pos.raw/stdout.txt`
- `40_OPS/ops_r4_r3_neg_pin.json`
- `40_OPS/ops_r4_r3_neg_pin.raw/stdout.txt`
- `40_OPS/ops_r4_r3_pos.json`
- `40_OPS/ops_r4_r3_pos.raw/stdout.txt`
- `40_OPS/ops_r4_r4_neg_pin.json`
- `40_OPS/ops_r4_r4_neg_pin.raw/stdout.txt`
- `40_OPS/ops_r4_r4_pos.json`
- `40_OPS/ops_r4_r4_pos.raw/stdout.txt`
- `40_OPS/ops_r4_r5_neg_pin.json`
- `40_OPS/ops_r4_r5_neg_pin.raw/stdout.txt`
- `40_OPS/ops_r4_r5_pos.json`
- `40_OPS/ops_r4_r5_pos.raw/stdout.txt`
- `40_OPS/ops_run_r4_pos1.json`
- `40_OPS/ops_run_r4_pos1.raw/stdout.txt`
- `40_OPS/ops_run_r4_pos2.json`
- `40_OPS/ops_run_r4_pos2.raw/stdout.txt`
- `SST_PLP_PH01_W0_B0_CLOSEOUT.md`
- `SST_PLP_PH01_W0_B0_HANDOFF.md`

## 4. Conventions and consequences

1. `PUBLISH_MANIFEST.tsv` uses LF line endings and lists every tracked file under this
   directory except itself; `git ls-tree -r` count == rows + 1 by construction.
2. A redacted `observed.value` / `expected_value` no longer re-derives from the source, so the
   published envelope and receipts are a *projection*. Verify them against the local originals.
3. `20_TESTS/fixture/TEST_ONLY_keypair.json` is withheld (test private key). Its public half and
   the receipt it signed are published, so fixture verification still works.
4. Engine receipts git ignores (`*.logs/`, `*.ndjson`) are neither copied nor counted.
