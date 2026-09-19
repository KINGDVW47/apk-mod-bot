# 🤖 APK Mod Bot — Telegram

Yon bot Telegram konplè pou modifye fichye **APK** (instriman legitimate
"APK modding" — menm kalite ak *APKTool*, *MT Manager*, oswa *Lucky Patcher*).

Konstwi pou devlopè ki vle teste modifikasyon sou **pwogram yo posede**.

---

## ✨ Fonksyonalite

| # | Fonksyonalite | Deskripsyon |
|---|---------------|-------------|
| 1 | Resevwa `.apk` | Telechaje APK atravè Telegram |
| 2 | Dekonpilasyon | `apktool d -f -o <dir> <apk>` |
| 3 | Chanje non | Modifye `android:label` (literal oswa referans `@string/`) |
| 4 | Resous pèsonalize | Enjekte `mod_name`, `mod_email`, `mod_phone` nan `strings.xml` |
| 5 | Toast notifikasyon | Enjekte `Toast` nan `onCreate()` aktivite launcher (smali) |
| 6 | Patch opsyonèl | LVL lisans, SDK anons, root deteksyon, verifikasyon siyati |
| 7 | Rekonstwi & siyen | `apktool b` → `zipalign` → `apksigner` |
| 8 | Voye tounen | Voye APK modifye a nan chat la |
| 9 | Estaj konvèsasyon | Fichye JSON pou chak itilizatè |
| 10 | Long polling | Kou san webhook |

## 🔧 Patch opsyonèl (aktive/desaktive)

- 🧾 **LVL** — retire verifikasyon lisans Google LVL
- 📢 **ADS** — retire SDK anons (AdMob, Facebook, Unity, MoPub, AppLovin, …)
- 🪪 **ROOT** — retire root deteksyon (RootBeer, SafetyNet, Magisk, …)
- 🔐 **SIGNATURE** — retire verifikasyon siyati PackageManager
- 💎 **PLAN/CREDIT/TOKEN** — debloke plan/premium + kredi + token valide

## 📦 Estrikti pwojè

```
apk-mod-bot/
├── bot.py           # Bot prensipal (python-telegram-bot v20, async)
├── config.py        # Konfigirasyon (token, chenm ekzekitab, limit)
├── apk_ops.py        # dekonpilasyon / rekonstwi / aliyen
├── patcher.py       # Tout operasyon patch (smali + res)
├── state.py         # Jesyon estaj konvèsasyon (JSON)
├── utils.py         # Validasyon + siyati + netwayaj
├── requirements.txt # Depandans Python
├── install.sh       # Enstalasyon otomatik (sèvè nimewo)
├── start.sh         # Script demaraj (Docker/Railway)
├── Dockerfile       # Imaj Docker pou deplwaman 24/7
├── railway.json     # Konfigirasyon Railway
├── .dockerignore    # Fichye yo eskli nan imaj Docker
└── README.md        # Dokiman sa a
```

## 🚀 Enstalasyon

### 1. Ranpli depandans sistèm

```bash
bash install.sh
```

Script sa a enstale `apktool`, `zipalign`, `apksigner`, `default-jdk`,
`python3` + `pip`, epi kreye yon `keystore` siyati otomatikman.

### 2. Konfigure token bot la

1. Pale ak [@BotFather](https://t.me/BotFather) sou Telegram
2. Kreye yon nouvo bot → kopye **token** la
3. Kole li nan `config.py`:

```python
BOT_TOKEN = "123456:ABC-DEF_ghijklmnopqrstuvwxyz"
```

(Oswa ekspòte li kòm varyab anviwònman: `export BOT_TOKEN=...`)

### 3. Lanse bot la

```bash
python3 bot.py
```

Se sa! Bot la ap kouri ak **long polling** (pa bezwen webhook / SSL).

---

## ☁️ Deplwaye 24/7 sou Railway (rekomande)

Pou bot la kouri **toujou** (24/7) san ou bezwen kite yon machin limen, deplwaye l
sou [Railway](https://railway.app). Pwojè a gen tout fichye nesesè deja.

### Etap pa etap

1. **Kreye yon kont Railway** (ou ka konekte ak GitHub).

2. **Telechaje pwojè a** nan yon repo GitHub, oswa sèvi ak Railway CLI:
   ```bash
   railway login
   railway init
   railway up
   ```
   (Railway pral detekte `Dockerfile` a epi bati imaj la otomatikman.)

3. **Mete BOT_TOKEN** kòm varyab anviwònman:
   - Nan Railway dashboard → pwojè → **Variables**
   - Ajoute: `BOT_TOKEN` = `<token botan ou>`

4. **Deplwaye** — Railway ap bati imaj la epi kouri `start.sh` a, ki:
   - Verifye zouti yo (apktool, zipalign, apksigner, java)
   - Kreye keystore siyati a otomatikman
   - Lanse bot la ak long polling ✅

> 💡 **Remak**: Sou plan gratis Railway, aplikasyon an domi apre kèk tan
> inaktivite. Pou 24/7 vre, ou bezwen yon plan peye (oswa yon VPS).

### Altènativ: VPS / sèvè pwòp ou

Sou yon VPS Linux (DigitalOcean, Linode, Vultr, elatriye), annik kouri:
```bash
git clone <repo> && cd apk-mod-bot
bash install.sh
export BOT_TOKEN=<token>
nohup python3 bot.py > bot.log 2>&1 &
```

---

## 🖥️ Kijan pou itilize

1. Voye `/start` nan chat bot la
2. Voye yon fichye `.apk`
3. Swiv enstriksyon: bay **non**, **imèl**, **telefòn** (ou ka `/skip` chak)
4. Chwazi **patch opsyonèl** yo (tappe bouton pou aktive ✅ / desaktive ➖)
5. Klike **✅ KONFIME & KONSTWI**
6. Resevwa **rapò** + **APK modifye** a

> 💡 Bot la netwaye tout repèrtwar tanporè apre chak operasyon.

---

## ⚙️ Konfigirasyon (config.py)

| Variab | Deskripsyon | Default |
|--------|-------------|---------|
| `BOT_TOKEN` | Token Telegram | — (obligatwa) |
| `MAX_APK_SIZE` | Limit gwosè APK | 300 MB |
| `KEYSTORE_PATH` | Chemine keystore | `keys/release.keystore` |
| `KEYSTORE_ALIAS` | Alias kle | `modbot` |
| `KEYSTORE_PASS` | Modpas keystore | `android` |

---

## 📝 Nòt teknik

- **Lang**: Python 3.10+ ak `python-telegram-bot` v20 (asynchrone)
- **Rezon pa PHP**: Se yon chwa deftèse pou yon bot asynchrone ak
  jesyon estaj; `python-telegram-bot` siprè long polling san pyès konplikasyon.
- **Jesyon erè**: apktool ka echwe, ficher twò gran, metòd manke — tout sa
  trape ak rapòte avèk klè.
- **Validasyon**: imèl + telefòn verifiche ak regex.
- **Sekirite**: aktyalize `KEYSTORE_PASS` default la anvan itilizasyon anpwodiksyon.

---

## ⚠️ Avètisman legal

Sèvi ak zouti sa a **sèlman sou aplikasyon ou posede** oswa ou gen pèmisyon
eksplisit pou modifye. Pa modifye aplikasyon pwopriyetè san otorizasyon.
