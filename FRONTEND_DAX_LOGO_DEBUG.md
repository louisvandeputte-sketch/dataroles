# DAX Logo Debugging Guide

## ✅ Database Status

**Logo is correct in database:**
- ✅ Logo data exists (78,256 bytes PNG)
- ✅ Logo URL in lookup: `/api/programming-languages/689b1716-1887-4825-ad2a-1efe52a34fe3/logo`
- ✅ Content-Type: `image/png`
- ✅ Filename: `dax-logo.png`

**The logo EXISTS and the URL is CORRECT!** 🎉

---

## 🐛 Waarom Toont Frontend Geen Logo?

Er zijn **7 mogelijke oorzaken**:

---

### **1. 🔌 API Server Draait Niet / Verkeerde Port**

**Symptoom:** Image laadt niet, 404 of connection refused error

**Check:**
```bash
# Test of API server draait
curl http://localhost:8000/api/programming-languages/689b1716-1887-4825-ad2a-1efe52a34fe3/logo

# Of in browser:
http://localhost:8000/api/programming-languages/689b1716-1887-4825-ad2a-1efe52a34fe3/logo
```

**Oplossing:**
- Start backend server: `uvicorn web.main:app --reload --port 8000`
- Check of port 8000 correct is (niet 3000, 5000, etc.)

---

### **2. 🌐 CORS Issues**

**Symptoom:** Browser console toont CORS error

**Check in Browser DevTools Console:**
```
Access to image at 'http://localhost:8000/api/...' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**Oplossing:**
Backend moet CORS headers sturen. Check `/web/api/tech_stack.py`:
```python
return Response(
    content=logo_bytes,
    media_type=content_type,
    headers={
        "Cache-Control": "public, max-age=86400",
        "Access-Control-Allow-Origin": "*",  # ✅ This is needed!
        "Content-Disposition": f'inline; filename="{seo_filename}"'
    }
)
```

---

### **3. 🔗 Frontend Gebruikt Verkeerde Base URL**

**Symptoom:** Image URL is relatief maar wijst naar verkeerde server

**Check in Browser DevTools Network Tab:**
- Klik op failed image request
- Check "Request URL"
- Is het `http://localhost:3000/api/...` (FOUT) of `http://localhost:8000/api/...` (GOED)?

**Oplossing A: Absolute URL in lookup**
```typescript
// In useTechStackLookup hook:
const baseUrl = 'http://localhost:8000'; // or from env var

data.forEach((item: TechStackItem) => {
  if (item.logo_url && !item.logo_url.startsWith('http')) {
    item.logo_url = baseUrl + item.logo_url;
  }
});
```

**Oplossing B: Proxy in Vite/Next.js**
```javascript
// vite.config.js
export default {
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
}

// next.config.js
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*'
      }
    ]
  }
}
```

---

### **4. 🎨 CSS/Styling Verbergt Image**

**Symptoom:** Image laadt wel (200 OK in Network tab) maar is niet zichtbaar

**Check in Browser DevTools:**
```javascript
// In console:
document.querySelector('img[src*="dax"]')
// Check computed styles:
// - display: none?
// - width: 0px?
// - height: 0px?
// - opacity: 0?
// - visibility: hidden?
```

**Oplossing:**
```css
/* Ensure images are visible */
.tech-badge img {
  display: inline-block !important;
  width: 20px !important;
  height: 20px !important;
  opacity: 1 !important;
  visibility: visible !important;
}
```

---

### **5. 🖼️ Image onError Handler Verbergt Image**

**Symptoom:** Image laadt maar wordt meteen verborgen

**Check in TechStackBadge component:**
```typescript
<img
  src={tech.logo_url}
  onError={(e) => {
    // ⚠️ This might be hiding the image!
    e.currentTarget.style.display = 'none';
  }}
/>
```

**Debug:**
```typescript
<img
  src={tech.logo_url}
  onError={(e) => {
    console.error('Image failed to load:', tech.logo_url);
    console.error('Error:', e);
    e.currentTarget.style.display = 'none';
  }}
  onLoad={() => {
    console.log('Image loaded successfully:', tech.logo_url);
  }}
/>
```

---

### **6. 📦 Lazy Loading + Not in Viewport**

**Symptoom:** Image laadt pas als je scrollt

**Check:**
```typescript
<img
  src={tech.logo_url}
  loading="lazy"  // ⚠️ This delays loading!
/>
```

**Oplossing:**
```typescript
// Remove lazy loading for debugging
<img
  src={tech.logo_url}
  loading="eager"  // Load immediately
/>
```

---

### **7. 🔒 Ad Blocker / Browser Extension**

**Symptoom:** Werkt in incognito mode maar niet in normale mode

**Check:**
- Open DevTools Network tab
- Look for blocked requests (red)
- Try in incognito mode
- Disable ad blockers

---

## 🧪 Step-by-Step Debugging

### **Stap 1: Check Backend**
```bash
# Start backend
cd /Users/louisvandeputte/datarole
source venv/bin/activate
uvicorn web.main:app --reload --port 8000

# Test endpoint
curl http://localhost:8000/api/programming-languages/689b1716-1887-4825-ad2a-1efe52a34fe3/logo --output dax-test.png

# Check file
file dax-test.png
# Should output: dax-test.png: PNG image data, ...
```

### **Stap 2: Check Browser Network Tab**
1. Open DevTools (F12)
2. Go to Network tab
3. Filter: "Img" or "dax"
4. Reload page
5. Look for the logo request

**What to check:**
- ✅ Status: 200 OK (good)
- ❌ Status: 404 (URL wrong)
- ❌ Status: 500 (server error)
- ❌ Status: (failed) CORS (CORS error)
- ❌ Status: (canceled) (request cancelled by browser/code)

### **Stap 3: Check Image Element**
```javascript
// In browser console:
const img = document.querySelector('img[src*="689b1716"]');
console.log('Image element:', img);
console.log('Computed style:', window.getComputedStyle(img));
console.log('Natural size:', img.naturalWidth, 'x', img.naturalHeight);
console.log('Display size:', img.width, 'x', img.height);
```

**Expected:**
- `naturalWidth` and `naturalHeight` > 0 (image loaded)
- `width` and `height` > 0 (image visible)

### **Stap 4: Check React Component**
```typescript
// Add debug logging to TechStackBadge:
export function TechStackBadge({ tech }: { tech: TechStackItem }) {
  console.log('Rendering badge for:', tech.name, 'Logo URL:', tech.logo_url);
  
  return (
    <span>
      {tech.logo_url ? (
        <>
          <img
            src={tech.logo_url}
            alt={tech.name}
            onLoad={() => console.log('✅ Logo loaded:', tech.name)}
            onError={(e) => console.error('❌ Logo failed:', tech.name, e)}
          />
          <span>{tech.display_name}</span>
        </>
      ) : (
        <span>No logo for {tech.display_name}</span>
      )}
    </span>
  );
}
```

---

## 🎯 Quick Fix Checklist

Voor je frontend developer:

```typescript
// 1. Add base URL to logo URLs
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useTechStackLookup() {
  return useQuery({
    queryKey: ['tech-stack-lookup'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/tech-stack/lookup`);
      const { data } = await response.json();
      
      // Transform relative URLs to absolute
      const transformedData = data.map((item: TechStackItem) => ({
        ...item,
        logo_url: item.logo_url 
          ? (item.logo_url.startsWith('http') 
              ? item.logo_url 
              : `${API_BASE_URL}${item.logo_url}`)
          : null
      }));
      
      // Create lookup maps
      const languages = new Map();
      const ecosystems = new Map();
      
      transformedData.forEach((item: TechStackItem) => {
        const key = item.name.toLowerCase();
        if (item.type === 'language') {
          languages.set(key, item);
        } else {
          ecosystems.set(key, item);
        }
      });
      
      return { languages, ecosystems };
    },
    staleTime: 1000 * 60 * 60,
  });
}

// 2. Add debug logging to badge component
export function TechStackBadge({ tech }: { tech: TechStackItem }) {
  const [imageError, setImageError] = React.useState(false);
  const [imageLoaded, setImageLoaded] = React.useState(false);

  return (
    <span className="tech-badge">
      {tech.logo_url && !imageError ? (
        <img
          src={tech.logo_url}
          alt={`${tech.display_name} logo`}
          className="w-5 h-5 object-contain"
          loading="eager"  // Don't lazy load for debugging
          onLoad={() => {
            setImageLoaded(true);
            console.log('✅ Logo loaded:', tech.name, tech.logo_url);
          }}
          onError={(e) => {
            setImageError(true);
            console.error('❌ Logo failed:', tech.name, tech.logo_url, e);
          }}
        />
      ) : (
        <div className="w-5 h-5 bg-gray-200 rounded flex items-center justify-center">
          <span className="text-xs font-bold text-gray-600">
            {tech.name.charAt(0).toUpperCase()}
          </span>
        </div>
      )}
      <span className="font-medium">{tech.display_name}</span>
      {imageError && <span className="text-red-500 text-xs ml-1">⚠️</span>}
    </span>
  );
}
```

---

## 📞 Test Commands

Geef deze commands aan je frontend developer:

```bash
# 1. Test backend endpoint
curl -I http://localhost:8000/api/programming-languages/689b1716-1887-4825-ad2a-1efe52a34fe3/logo

# Expected output:
# HTTP/1.1 200 OK
# content-type: image/png
# cache-control: public, max-age=86400
# access-control-allow-origin: *

# 2. Download image to verify
curl http://localhost:8000/api/programming-languages/689b1716-1887-4825-ad2a-1efe52a34fe3/logo --output test-dax.png
open test-dax.png  # Should open the DAX logo

# 3. Test lookup endpoint
curl http://localhost:8000/api/tech-stack/lookup | jq '.data[] | select(.name == "DAX")'

# Expected output:
# {
#   "name": "DAX",
#   "display_name": "DAX",
#   "logo_url": "/api/programming-languages/689b1716-1887-4825-ad2a-1efe52a34fe3/logo",
#   "category": "...",
#   "type": "language"
# }
```

---

## 🎯 Most Likely Cause

Based on experience, **90% of the time** it's one of these:

1. **Backend not running** (50%)
2. **Wrong base URL / proxy not configured** (30%)
3. **CORS issue** (10%)

**Start by checking these three first!** 🎯
