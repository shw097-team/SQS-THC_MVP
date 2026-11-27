# REDACTION NOTICE — LOCAL_ONLY clause text

This directory publishes the r11 candidate of SST PH01 W0 B0 R3 (work root
`SST_PH01_W0_B0_R3_20261127`).

## 1. What was redacted in this wave

The clause value carried by the B0 envelope is LOCAL_ONLY for its declared consumers.
Every published copy replaces exactly that sentence with `<LOCAL_ONLY_REDACTED>`.

| path | original sha256 | published sha256 | occurrences |
|---|---|---|---|
| `00_PREFLIGHT/DEPLOYMENT_prod_20261127.json` | `4528119b59f6d8414c96e2e024ef5b77b38eabaee41872a2098dc87306b8cff6` | `89745a94e1e95a85ab0721c47c5fd49931c96da911f8db03ab3e197354ab2294` | 12 |
| `00_PREFLIGHT/DEPLOYMENT_prod_20261127_r8.json` | `78c78defe5058cab817fbb916e6656b4f3d061ac7bc4ada1381ebe4248e4aac3` | `f201b7dcb7ea17adc97d4e018c2eedafeed12a75bcae16d0770c2fbefde11124` | 12 |
| `00_PREFLIGHT/DEPLOYMENT_prod_20261127_r9.json` | `8348c7ca686718e591741c0ca92959145e24da16d9948a5265c8cf7ecb069f1d` | `ae41b52c8b9e0da639a22786c0ed5145a271762abfa9f3411a174c56e9a0e573` | 12 |
| `00_PREFLIGHT/T1_BASELINE_20261127.json` | `a7a9a2a4c8d903b6fbc27f2a7db46b8fcb71970062e54686a1eeaf74dba3cf5f` | `bf697510500e40cd792cf557407df5c4b5c8f1a9221eedebaf43304beaf72aa8` | 4 |
| `00_PREFLIGHT/required_set_req12_read_all_2026-11-25.json` | `50ca45c106bb58fd8a3bfdf1cfaf7400fd3a06d1f95cea7f1fe8c6166eda4764` | `ea59efc53df9cdac8bd5d6a0e873092a63e7973e4836431f1ab9856807ccc4dc` | 1 |
| `00_PREFLIGHT/required_set_req12_read_w0m_2026-11-25.json` | `bc7afa530677746b8c681fc32109041a04e1fd1e7fc201c375d8edff34e6615c` | `a4b7a1c39b4c9809e4e02556bc434e4b29003584fb6b05a6f7387540df990312` | 1 |
| `20_DEV/exec_r4_wave1_receipt.json.logs/attempt-5364-1795578140-1-stdout.txt` | `0a1dfaa4fd25213298625d70a30dafb8a3bb1f9e018504b127b7d34d922ae362` | `c5de167edae49f2db13815eb0e11f52832586b374a4211b8eeda2dac2fb551c4` | 68 |
| `20_DEV/exec_r4_wave2_receipt.json.logs/attempt-5400-1795580545-1-stdout.txt` | `f2e9f0a846d739cfebb4dd7e11d8e5b126a13591703c66106ba1edea0a9fc382` | `d45bdec826c69b8d562670f0ac880dda5a1227bd791413520e8241ef465d5934` | 37 |
| `20_DEV/exec_r4_wave3_receipt.json.logs/attempt-5420-1795582887-1-stdout.txt` | `135d42d53625bb16c5b21eebad6372c4e2378242c0746ea3fa867e5947b2f245` | `566b4ee8cd8ce845b8d4f3082bad136b47a329f760128d070af7e8561209e081` | 55 |
| `20_DEV/exec_r4_wave4_receipt.json.logs/attempt-17240-1795585835-1-stdout.txt` | `c2f573f48e6394131c404aa5c3fa18e6398dacfc97de1480a5d2787789de09d5` | `0224634e627eb23e7ea1aa4bdc3a7a76efc0f1ceb825f1be36357829411784ad` | 230 |
| `20_DEV/exec_r4_wave5_receipt.json.logs/attempt-11492-1795588517-1-stdout.txt` | `5b0aae468c160027cc3cb75ffefbd806c12a30089902cfcd23ddc995551166a3` | `e8dd27022ffb66348512d334ec52c78381adb7729e6a4799882255ef769ede01` | 26 |
| `20_DEV/tests/test_b0_return.py` | `7f4fbaff3ca399145b22aee84476297a02577e6142f20d06ce7d6a5c5e7540fd` | `e2ecc19b9da2264c436bb6294efd60f0a3f917f2159917300157c5afca177af5` | 2 |
| `20_DEV/tests/test_product_read.py` | `9e2d808ab821c9ac5e9ca2fcb844401dcfa342f9808e55515b30f2b6c24adeac` | `4cb095a785746a868874e332e2f908fb8f5a59da534a58b2e70de637a00f1c7b` | 3 |
| `20_DEV/tests/trust_fixture.py` | `c4db3fac39c7d0b76210b54e298b5fc4548cf6e03e3604ef57f0d2d93a0c255f` | `6b551f07f49a42279c2aae4d69722a913c885606e805f683263637f7ba77c132` | 2 |
| `40_OPS/b0_read_stdout_r8_20261127.json` | `abb5546cbf36b94195fa8935ceb170f163cbe5c7832fbf55d5f778e0f6702d2e` | `5b9775931f06a8013845ba61f42197248c9a1663763554959e4dcca37349856a` | 2 |
| `40_OPS/b0_sourcereadset_r8_20261127.json` | `abb5546cbf36b94195fa8935ceb170f163cbe5c7832fbf55d5f778e0f6702d2e` | `5b9775931f06a8013845ba61f42197248c9a1663763554959e4dcca37349856a` | 2 |
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

## 2. What this publication cannot retract

Commit `b144f63` in this repository published the unredacted r8 copies. History is not
rewritten. This notice is the record that those bytes disclosed one clause sentence.

## 3. Pre-existing residue elsewhere in this repository (56 files at `21cdd44b5c40`)

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

## 4. Consequences a reader must know

1. A redacted `observed.value` / `expected_value` no longer re-derives from the source, so the
   published envelope and receipts are a *projection*. Verify them against the local originals
   whose digests are in this table.
2. `20_TESTS/fixture/TEST_ONLY_keypair.json` is withheld (test private key). Its public half and
   the receipt it signed are published, so fixture verification still works.
3. Engine receipts git ignores (`*.logs`, `*.attempts.ndjson`) are not published and not counted.
