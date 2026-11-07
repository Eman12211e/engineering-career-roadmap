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
