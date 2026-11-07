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
