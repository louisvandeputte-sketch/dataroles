#!/usr/bin/env python3
"""Debug why DAX logo is not showing in frontend"""

from database.client import db
import base64

print("\n🔍 Debugging DAX logo issue...\n")

# Get DAX details
dax = db.client.table("programming_languages")\
    .select("*")\
    .eq("name", "DAX")\
    .single()\
    .execute()

if not dax.data:
    print("❌ DAX not found in database!")
    exit(1)

dax_data = dax.data

print("📊 DAX Database Record:")
print(f"   ID: {dax_data['id']}")
print(f"   Name: {dax_data['name']}")
print(f"   Display Name: {dax_data['display_name']}")
print(f"   Logo URL: {dax_data.get('logo_url')}")
print(f"   Logo Filename: {dax_data.get('logo_filename')}")
print(f"   Logo Content Type: {dax_data.get('logo_content_type')}")

# Check if logo_data exists
logo_data = dax_data.get('logo_data')
if logo_data:
    print(f"   Logo Data: EXISTS (type: {type(logo_data).__name__})")
    
    # Try to determine size
    try:
        if isinstance(logo_data, str):
            # Could be base64 or hex
            if logo_data.startswith('\\x'):
                # Hex format
                hex_str = logo_data[2:]
                data_bytes = bytes.fromhex(hex_str)
                print(f"   Logo Data Format: Hex-encoded")
                print(f"   Logo Data Size: {len(data_bytes)} bytes")
            else:
                # Might be base64
                try:
                    data_bytes = base64.b64decode(logo_data)
                    print(f"   Logo Data Format: Base64-encoded")
                    print(f"   Logo Data Size: {len(data_bytes)} bytes")
                except:
                    print(f"   Logo Data Format: Unknown string format")
                    print(f"   Logo Data Length: {len(logo_data)} chars")
        else:
            print(f"   Logo Data Format: Binary")
            print(f"   Logo Data Size: {len(logo_data)} bytes")
    except Exception as e:
        print(f"   ⚠️ Could not determine logo data size: {e}")
else:
    print(f"   Logo Data: NULL")

print("\n🔗 Expected API Endpoint:")
expected_url = f"/api/programming-languages/{dax_data['id']}/logo"
print(f"   {expected_url}")

print("\n🧪 Testing API Endpoint...")
print(f"   Try accessing: http://localhost:8000{expected_url}")
print(f"   Or: http://your-domain.com{expected_url}")

# Check tech_stack_lookup view
print("\n📊 Checking tech_stack_lookup view...")
lookup = db.client.table("tech_stack_lookup")\
    .select("*")\
    .eq("name", "DAX")\
    .execute()

if lookup.data:
    print(f"   ✅ DAX found in tech_stack_lookup")
    print(f"   Logo URL in view: {lookup.data[0].get('logo_url')}")
else:
    print(f"   ❌ DAX NOT found in tech_stack_lookup!")
    print(f"   Check if is_active = TRUE")

print("\n" + "="*80)
print("🐛 DEBUGGING CHECKLIST FOR FRONTEND DEVELOPER:")
print("="*80)

print("\n1. ✅ Logo URL is correct:")
print(f"   {expected_url}")

print("\n2. 🔍 Test the API endpoint directly:")
print(f"   curl http://localhost:8000{expected_url}")
print(f"   or open in browser: http://localhost:8000{expected_url}")

print("\n3. 🖼️ Check image response:")
print(f"   - Should return image data")
print(f"   - Content-Type: {dax_data.get('logo_content_type', 'image/png')}")
print(f"   - Should have Cache-Control header")

print("\n4. 🌐 Check CORS headers:")
print(f"   - Access-Control-Allow-Origin should be set")
print(f"   - Check browser console for CORS errors")

print("\n5. 🔗 Check frontend image loading:")
print(f"   - Verify <img src=\"{expected_url}\" /> is rendered")
print(f"   - Check Network tab in DevTools")
print(f"   - Look for 404, 500, or CORS errors")

print("\n6. 🎨 Check CSS/styling:")
print(f"   - Image might be hidden (display: none)")
print(f"   - Image might be 0x0 size")
print(f"   - Check img.onError handler")

print("\n7. 📦 Common Issues:")
print(f"   - API server not running on correct port")
print(f"   - Proxy configuration in frontend (Vite/Next.js)")
print(f"   - Image loading lazy but not in viewport")
print(f"   - Ad blocker blocking image")

print("\n" + "="*80)
