# 🚂 Railway Setup - Auto-Enrichment Uitschakelen

## ✅ Code is Gepushed naar GitHub

De fix is nu live op GitHub. Railway zal automatisch deployen.

---

## 🔧 Volgende Stap: Environment Variable Toevoegen

### In Railway Dashboard:

1. **Ga naar je project:** https://railway.app/
2. **Selecteer je service** (datarole web app)
3. **Klik op "Variables"** tab
4. **Voeg nieuwe variable toe:**
   ```
   Name:  DISABLE_AUTO_ENRICHMENT
   Value: true
   ```
5. **Klik "Add"**
6. Railway zal automatisch **herstarten**

---

## ✅ Verificatie

### Check 1: Deployment Status

In Railway:
- Wacht tot deployment compleet is (groen vinkje)
- Check logs voor errors

### Check 2: Auto-Enrichment Gestopt

In OpenAI Dashboard (https://platform.openai.com/usage):
- Kijk of er nog nieuwe requests komen
- Na ~5 minuten: geen nieuwe enrichments meer

### Check 3: Logs Checken

In Railway logs, zoek naar:
```
Auto-enrichment service started
```

Dit zou NIET meer moeten verschijnen als `DISABLE_AUTO_ENRICHMENT=true`.

---

## 📊 Verwachte Resultaten

**Voor:**
- Elke 60 seconden: nieuwe enrichments
- ~100+ enrichments per dag
- Kosten: ~$1-2/dag

**Na:**
- Geen auto-enrichments meer
- Alleen nieuwe jobs 's nachts (via scraper)
- Kosten: ~$0.20/dag

**Besparing: ~80-90%** 💰

---

## 🐛 Als Het Nog Steeds Draait

### Check Environment Variable

In Railway logs, voeg tijdelijk debug toe:
```python
import os
print(f"DISABLE_AUTO_ENRICHMENT = {os.getenv('DISABLE_AUTO_ENRICHMENT')}")
```

### Force Restart

In Railway:
1. Ga naar "Deployments"
2. Klik op "Redeploy" bij laatste deployment

---

## 📞 Troubleshooting

### Probleem: Enrichments blijven komen

**Mogelijke oorzaken:**
1. Environment variable niet correct gezet
2. Railway heeft niet herstart
3. Oude deployment draait nog

**Oplossing:**
1. Check Variables tab in Railway
2. Force redeploy
3. Check logs voor `DISABLE_AUTO_ENRICHMENT`

### Probleem: App crasht na deployment

**Check logs voor:**
- Import errors
- Syntax errors
- Database connection issues

**Rollback:**
```bash
git revert HEAD
git push origin main
```

---

## ✅ Success Checklist

- [x] Code gepushed naar GitHub
- [ ] `DISABLE_AUTO_ENRICHMENT=true` toegevoegd in Railway
- [ ] Railway deployment compleet
- [ ] Geen nieuwe enrichments in OpenAI dashboard (check na 5 min)
- [ ] Kosten gedaald

---

## 🎉 Klaar!

Na deze stappen:
- Auto-enrichment is uitgeschakeld
- Kosten zijn ~80% lager
- Alleen nieuwe jobs worden enriched (via scraper)
