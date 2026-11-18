# Sealed unseen evaluation set (round 6)

Written by an independent reviewer under contract Revision 2 + R2.8.1–12 (commit `a5c0fd3`).
It is stored outside the repository. Agent C must never read it, and nobody runs it before
session 3. Only the hashes are kept here, so anyone can later check that the set wasn't changed.

- **Sealed (UTC):** 2026-11-07T18:23:22Z
- **Files:** 14 posting + résumé pairs (`kind: "unseen"`)
- **Hashes checked by the coordinator:** every per-file hash and the combined hash match the
  manifest. The check used `sha256sum` only; no file was opened.

**Timing disclosure:** the set was sealed after session 1's code (last commit `ccc9e91`,
2026-11-07T12:17Z) and before session 2 began. The author never ran or imported engine code.
Keeping the set from Agent C relies on instructions; nothing on the filesystem enforces it.
The hashes show the set was fixed before session 2, not that it stayed secret.

```
adf9ed8a41d9a2e5db9de7ff5e207a95060a3dcee0691da66c4b32a8157a0397  u6_bigco_basic_desired.json
927a3cdce79b282cf7a065fe4daa4b15633df0db9b604dcc7732dd4d9802474a  u6_culture_benefits_heavy.json
14ad634bed7b8310167d75997c64776c2a41cd1bcc18f829bb0d93979309036b  u6_duty_lines_as_required.json
860d1a7d49797699f9eed6dad6002ee6c1d482060622addc3962ec1ab7aee1a9  u6_gov_defense_clearance.json
893a41e1020b64e5807d6a8ded07fd5cd3aa66ca5f2237d5ca543545c16e32ed  u6_headingless_blurb.json
d22feceb7be46ddce7cad576e0d49e52a4f2e104d93e4bcd090ba75e58d904f5  u6_linkedin_lost_bullets.json
4214c6031ba0954717474325083628da2cdde669d2bbaf3035b4313bd451e0f9  u6_mfg_technician.json
752e1cf5b0e00e2a55dced34bbe4545157ded73287036cd32568fc05fdd71962  u6_not_required_but_plus.json
b29251d89426ac37ee4c5f297eb7af035150ba6579f624f7b9bd23dc452b20f8  u6_numbered_lists.json
e3b491b461f67ba071070a2277098b78006ce29bd9c601bc45351214feb6b869  u6_pdf_hardwrap.json
d28d9db8c01c3dc0c7cbb1a148b0f3038212ea6926f4119ac940069d06b6168b  u6_sentence_case_no_colons.json
019c136fa571e916a1e78a937b43ad2474558b6a43ae1df9fcda23b2926bf605  u6_staffing_agency.json
a2342a30ba2741a8cb5757ac7faeb3252c45f94cd539c34673a4fb5a0e9e0e1b  u6_startup_emoji_ev.json
b9880423ba788a6c942a08271d702781a7ccaad9549e8b1da9b69b6459bfad9f  u6_startup_emoji_robotics.json

combined  3cb73bf8293fa09db1e4a3f9f74c5a7c7a8d4a15ecdf086eefc39a104cf7ee32
```

---

# Sealed unseen set (round 7)

Written by a new independent author under contract Revision 3, at HEAD `2813129`. It is
stored outside the repository and runs only in the final review. The round-6 set above is
now locked regression data in `tests/fixtures/regression_r6/`.

- **Sealed (UTC):** 2026-11-07T19:20:16Z. That is after Revision 3 was frozen (`2813129`,
  19:05Z) and before any Stage 4 code change.
- **Files:** 12 posting + résumé pairs (`kind: "unseen"`, ids `u7_`)
- **Hashes checked by the coordinator:** every per-file hash and the combined hash match the
  manifest. The check used `sha256sum` only; no file was opened.

```
6611c36e70bf6a02defa4169d0429c431a0e8db4bce176972e2acfa7e55e2ac4  u7_aero_pdf_wrap_scope.json
b4d0e2f679f5ed163e4fc39f4d411c1f2d45e78e3b00874d0793bef7bc5848e5  u7_bigco_pay_transparency.json
27352c8dbe9673e63ea26d12b5ecde13a03407c73158d9fc7eb1411fe9e725d8  u7_cad_contrast_resets.json
718a841fc7ec053751d42c4c35ac88853df089eb1edf95da65c317262dce354a  u7_controls_learning_scope.json
8ba39373382b34fcf65007df205d95590b88163511604c40b1e44c03aec4f6c1  u7_cue_bound_preferred.json
c9829687a333cf006280c064734994a591c1833ba2f56e4f867ee6878351c29e  u7_culture_benefits_heavy.json
cb91c9a9c84028770ba61ed40cb2c1ce9820a5ed4059ca7613baa994dcf93ade  u7_ev_familiar_vs_not.json
3e34b01a89f1ad9655bb61bc8080f6fa75a5f645f2bc117ae79fbd28f906c12d  u7_gov_later_cue_state.json
a3032010c52b8bad01b7ce8153218fc9dfa621570be5dc2900fccd4e3c8bc388  u7_headingless_blurb.json
42147876c39621c14350c5a6c03ee22f328781d3d6a111fbf2d94f2edc43f4d7  u7_markdown_known_limit_line_end.json
07956ebeb1ac9aa439986876bb917a79c9b6076b27f31ea42204d42c1199d005  u7_numbered_posting_cues.json
0351b83a7fc5b4e42a04ec8e801fb6ee5152e694fdad63171f10edb55ede12c9  u7_staffing_negation_gap.json

combined  2c0c7ac8568f98c2ec615c12952b977e9d65f19e2b9d02dd77873d22479d8f22
```

---

# Sealed unseen set (round 8)

Written by a new independent author under contract Revision 4 (`fix/comma-lists` at
`11af7e0`). It is stored outside the repository and runs only in the final review. Round 7 is
now retrospective regression data.

- **Sealed (UTC):** 2026-11-07T20:28:48Z. That is after the R4 contract and the
  coordinator tests were committed (`11af7e0`, 20:18Z) and before any implementation.
- **Files:** 12 posting + résumé pairs (`kind: "unseen"`, ids `u8_`)
- **Hashes checked by the coordinator:** every per-file hash and the combined hash match the
  manifest. The check used `sha256sum` only; no file was opened.

```
07d604f8a25012c476a71c8cb74a1c8d3e143fcb35c22726462ab49ef5847156  u8_composites_culture_benefits.json
d941ccf8abd45842bc7487db9f21639290eadf41c3ba08fe792ddcbe62360c60  u8_controls_hypothetical_lists.json
86e4dd10ea9f5abd2435b3f0ea991cdd718a9b79fbc9ca5e2bdd6549e06856db  u8_design_agency_whereas_reset.json
b0febe0412ffea7cb57bcca447d140d99ca409b592f7a7866ccd190a6b7eae8d  u8_ev_pack_modal_and_adverb_prefix.json
aa8c6220233419fdb566cda34cd2f0af4aff2fa75970f4bc2c5879a97dbb56ac  u8_molding_pdf_wraps.json
c4ca1745172debaa266556ab4e39ddcef0f186cfc47623d110e5250a81f9cc7e  u8_quality_staffing_negation_lists.json
46eb6f3cd903912ce99efe532bbba50fec11f62ae5bd0b5253ef221f008003a7  u8_recruiter_email_inline_cues.json
43570876522f2ffb8bb24ca6756951c9d262bbafa6ead32fb7437c44729f4c61  u8_robotics_startup_emoji.json
d6d419772ee8edf2390aa408a5d1611c020aab47842383262b7a3fd13db1f7f4  u8_sensor_test_nice_to_have.json
c1e03567c78fb0317cfd5b1aa372fdaa4e0e411a84544560115273ab429d4eb9  u8_stress_bonus_and_conservative_list.json
9c1bc5f55db06617168ddb6fd885ab9bf40ee0f23ca65b845e19e07ba7bbceb8  u8_systems_test_mixed_cues.json
4172d7e1e104b83aa23de6f171a8416fa2aac350835102cb68a43bf23553a33d  u8_valve_mfg_required_label_in_preferred.json

combined  5b30627c341c7009191f9af31a2cf81b7e08f321db646125837f3049548b8c27

---

# Sealed unseen set (round 9)

Written by a new independent author for the Path B (confirmation-first) acceptance criteria,
from the author kit committed at `dd6ae28` (`docs/proposals/contract-v4-line-rule/round9/`).
It is stored outside the repository. Implementers and their prompts must never read it.
Gate 1 remains blocked.

- **Sealed (UTC):** 2026-11-14T07:27:34Z. That is after the acceptance criteria were frozen
  (`dd6ae28`, 07:10Z) and before any production change on the integration branch (still at `fa1555e`).
- **Files:** 30 posting + résumé pairs (`split: "holdout"`, ids `u9_`), 3 in each of the eight
  trap categories and 6 ordinary pairs.
- **Hashes checked by the coordinator (2026-11-14):** every per-file hash and the combined hash
  match the author's manifest.
- **Blind validation:** a script that prints only counts, rule names, filenames and hashes checked
  the file shape, one pair per file, unique ids equal to filenames, unique texts, category counts, canonical
  skill names, `resume_has` within required plus preferred, 3 to 12 skills per pair and the
  word-count limits. 0 failures. No pair text or label was shown to the coordinator.
- **Author isolation:** a fresh general-purpose agent whose prompt named only its kit folder.
  Its recorded tool calls read only the three kit files and wrote only inside that folder. The
  kit holds skill names and aliases only; it does not hold `data/match_rules.json`.
- **Not checked:** the rule that each trap category puts a doubtful skill in the required list
  at least once, and the quality of the labels. Both need a reader of the pairs. Keeping the
  set from implementers relies on instructions; nothing on the filesystem enforces it.

```
1be2ed606f20da95f96452a9430c1cea5ee9c0f9e27b6dc1cbd52a7b15643a8b  u9_aero_marks.json
08f61afd71fa68a3e00fdd5bec3d977d3bfa5396c7e0a2fc4dec4504b7d4e0ec  u9_april_sitting.json
66981d9578a480c57d241e604329db5ba9d259c16240837a99a8b869a01f3e63  u9_blister_columns.json
2d816b942e0bd401f3e412cba168c274cd0c77f8ea71ae9acd2936ab2f962197  u9_bus_bms.json
d6210605b1499f7208fce73aac6eb073b6e8fdc4835b9b64dc7ec334512e5f18  u9_contractor_ladder.json
18343f1d4a59271f0fc05b45db8515ea6632298b846f52cd51aad50b8492d73a  u9_cordless_housings.json
c022df25199f033495f74d45a3e9032ed5d62da9f0073f23997dbaf9c58858de  u9_drive_unit_pagebreak.json
e399cdf51ae6f4017560ccc52d51f068f91d8dd2b956d8d7cdf8fa3ce2882d47  u9_ferry_pack_next.json
99ffb6421f17754d172f4da8bce3e9828d2aec5335387424c2d5e6be3c541ba0  u9_fixture_symbols.json
c9b1774d6870d082961e1685010c7daceed05775a7d2886543f5849af54c609b  u9_forge_matrix.json
967e005cbed530dd8fc5f67d388cc233581b090367af96b95a150ad3052073dd  u9_headlamp_launch.json
472e89f5f38e06352515192e3529989006f85846a828c237df43d7d46d7e5b2d  u9_honing_zero.json
f62fc9861fa82cfc41db9793321ea84250bdd93b978e3aa9585c5a1b08c782ed  u9_integrator_robots.json
dc7838311eccc97492116fba9e0703d6bcfce1385920cc66ba8e273985f40d33  u9_kiosk_wrapped.json
cf1ea9af5de1ddcfdf270b222ae6499e39d2a35cd8915eefb16cd7259cdb5ed8  u9_kitchen_lack.json
8831f8a42010774e14b5cfd7432952bbf58f9eda2f8985932296260da06a06e9  u9_landing_gear_stress.json
6e3dc6403d872aa0b850e6cad7c1e6b42d99cbeb812a60838c34e74e10192932  u9_lathe_cells_goals.json
3708b8b1a70b9ad745d20eae56aa7c489b7dcc6ed53ec0838d6ab222af8a4a61  u9_mill_downtime.json
3db798fcfaeb56fda42db9e5bc19837999cadafb9cfd8b6fecdc449557eb4489  u9_parcel_sorter.json
8c1e33b24774c8121657570c98c9605238a0567b35a1d73011f8bcbdba5924f2  u9_partner_cfrp.json
f2c9da516a4e272c7857f368cfa92d6b841fbd57b14b1d20749bfc4dc180adc2  u9_projector_cfd.json
fc18cfc028e0746cf524504f3a40da950222ecc2a143129b2bc436b0c9d0f9b7  u9_pump_caveat.json
38c6d7569969cd8cc2ebd38d5da3ba9a54d2f2e24924a31e63398408352891a1  u9_scooter_gaps.json
46727d2ed53a89a1c0edb5ee7810840afd2bec8f08e3da1096b0becd4d23153a  u9_seat_form.json
9d85e2cb3ec3ffa3bf34c3e5800fe32ca0c00b8a228450ba67faaea4c7008de5  u9_supplier_ticks.json
977d8fb2a2d21c56a7df6a2051b98642281d9a4a4baa20cc5c49c4e9c079c4be  u9_van_legend.json
4c40b2e7b3db2e66242fd2bef6007a301147850c12c5d6af11f7124a5184595d  u9_viewer_catia.json
a291fdf202e9f75353658b05d70b39941bc96e45016e8e6f177b0482078d4dc8  u9_weeder_robot.json
89a18ae878b24ea23f59e9f4802849c0ccdc538210e636f4f9da864c79aa211f  u9_weld_cells_upfront.json
c64f345fd1de7ea63355f317c001b50c121c90e758f6759178ed678ce7e793b1  u9_wing_fold_found.json

combined  f6f9febe86289556109cc0cf932ebc4e76b8e4fc5e1de27e55817afa73df0a80
```
