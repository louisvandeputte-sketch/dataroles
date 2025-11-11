# Web Server Moet Herstarten! 🔄

## Probleem

Je ziet de **Hiring Model** sectie niet in de UI, ook al:
- ✅ Database heeft `hiring_model: 'direct'` voor Accountable
- ✅ UI template is aangepast met nieuwe sectie
- ✅ Accountable is enriched met v15 (23:38:08)

## Oorzaak

De **web server draait nog met de oude template** (zonder Hiring Model sectie).

Flask cached de templates en je moet de server herstarten om de nieuwe template te laden.

## Oplossing

### Stap 1: Stop de Web Server

In de terminal waar de web server draait:
```bash
Ctrl + C
```

Of als het in de achtergrond draait:
```bash
pkill -f "run_web.py"
# Of
pkill -f "python.*web"
```

### Stap 2: Start de Web Server Opnieuw

```bash
cd /Users/louisvandeputte/datarole
python run_web.py
```

### Stap 3: Hard Refresh Browser

Na server restart:
```
Mac:     Cmd + Shift + R
Windows: Ctrl + Shift + R
```

Dit cleared de browser cache en laadt de nieuwe template.

## Verificatie

### 1. Check Server Logs

Bij opstarten zou je moeten zien:
```
 * Running on http://127.0.0.1:8000
 * Running on http://localhost:8000
```

### 2. Open Accountable Details

1. Ga naar: `http://localhost:8000/companies`
2. Search: "Accountable"
3. Click: "View Details"
4. Scroll naar beneden

**Verwacht:**
```
┌─────────────────────────────────────┐
│ Company Size Classification         │
│ Category: Scaleup                   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐  ← NIEUW!
│ 💼 Hiring Model                     │
│ ┌─────────┐                         │
│ │ Direct  │ (green badge)           │
│ └─────────┘                         │
│ 🇬🇧 Direct                          │
│ 🇳🇱 Direct                          │
│ 🇫🇷 Direct                          │
│ 🏭 This company hires directly...   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ AI Enriched Information             │
│ Bedrijfswebsite: ...                │
└─────────────────────────────────────┘
```

## Database Status ✅

Accountable heeft de juiste data:
```
hiring_model:    direct
hiring_model_en: Direct
hiring_model_nl: Direct
hiring_model_fr: Direct
Enriched at:     2025-11-09T22:38:08
```

## Waarom Gebeurt Dit?

### Flask Template Caching

Flask cached templates in productie mode. Wijzigingen aan `.html` files worden niet automatisch herladen.

### Browser Caching

Browsers cachen ook HTML/CSS/JS. Een hard refresh is nodig om de nieuwe versie te laden.

## Quick Commands

```bash
# Stop server
pkill -f "run_web.py"

# Start server
cd /Users/louisvandeputte/datarole
python run_web.py

# In browser: Cmd+Shift+R (Mac) of Ctrl+Shift+R (Windows)
```

## Troubleshooting

### Sectie nog steeds niet zichtbaar?

**Check 1: Template file**
```bash
grep -n "Hiring Model" web/templates/companies.html
```
Verwacht: Regel ~421

**Check 2: Server logs**
Kijk of er errors zijn bij opstarten

**Check 3: Browser console**
Open DevTools (F12) → Console tab
Kijk of er JavaScript errors zijn

**Check 4: Alpine.js**
Check of Alpine.js werkt:
```javascript
// In browser console
console.log(window.Alpine)
```
Moet een object returnen, niet `undefined`

### Sectie is zichtbaar maar leeg?

Check API response:
```javascript
// In browser DevTools → Network tab
// Click on company details
// Find API call to /api/companies/{id}
// Check response includes hiring_model fields
```

## Development Mode

Voor development kun je auto-reload aanzetten:

**In `run_web.py` of `web/app.py`:**
```python
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True  # ← Auto-reload bij file changes
    )
```

⚠️ **Let op:** Debug mode in productie is niet veilig!

## Samenvatting

1. ✅ Database heeft hiring_model
2. ✅ Template is aangepast
3. ❌ Server moet herstarten
4. ❌ Browser moet hard refresh

**Actie:** Stop server → Start server → Hard refresh browser → Klaar! 🎯
