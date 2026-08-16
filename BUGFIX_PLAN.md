# Barcode Printer Bugfix & Enhancement Plan

## Branch: fix/template-sync-and-licensing
Created: 2026-08-16

---

## Priority 1: Template Sync Bug
**Issue:** When user edits template in Settings (TPSL or ZPL), the changes are saved but don't appear when returning to the print table.

**Root Cause Analysis:**
- Settings are stored via `QSettings` (Windows Registry) in `modules/Configurations.py`
- Multiple settings files exist (settings.py, settings2.py, settings3.py) causing confusion
- When template is edited and saved, it updates the QSettings store
- When returning to print table, the app either:
  1. Reads from an old/cached JSON file instead of QSettings, OR
  2. The table doesn't refresh/reload templates after settings change

**Solution:**
1. Identify which settings file is actually being used (appears to be settings3.py based on code patterns)
2. Ensure BarcodeApp properly listens to `config.setting_changed` signal for template updates
3. Add a refresh mechanism to reload templates when returning to print screen
4. Consider consolidating all three settings files into one (cleanup task)

**Files to Modify:**
- `modules/ui/app.py` - BarcodeApp main class
- `modules/Configurations.py` - Config management
- Remove/consolidate: settings.py, settings2.py, settings3.py

**Testing:**
- Edit TPSL template → Save → Return to print table → Verify new template is used
- Test with multiple template sizes (75x50mm, 80x50mm, 35x25mm, 60x40mm)

---

## Priority 2: Finish Layout Designer with Millimeter Accuracy
**Issue:** Layout designer incomplete; needs to support multiple sticker sizes with accurate mm-based calculations.

**Sizes Needed:**
- 35 x 25 mm
- 75 x 50 mm  
- 60 x 40 mm

**Current State:**
- barcode_designer.py has BaseElement, CustomTextItem, CustomRectItem, CustomLineItem classes
- Elements can be moved/resized but mm-to-pixel conversion may be inaccurate

**Solution:**
1. Implement proper DPI-aware mm-to-pixel conversion (assuming 72 DPI standard)
2. Create size presets for each label dimension
3. Add dimension display/input fields (show current size in mm)
4. Add visual rulers showing mm grid
5. Save/load layout per size in JSON or QSettings

**Formula:** pixels = mm * DPI / 25.4
- For 72 DPI: pixels = mm * 2.834...
- Should allow custom DPI setting

**Files to Modify:**
- `modules/barcode_designer.py` - Layout designer class
- `modules/Configurations.py` - Store multiple layouts per size

---

## Priority 3: Modernize UI with CSS Stylesheets
**Goal:** Make UI more attractive and professional for selling.

**Current State:**
- PyQt5 using basic stylesheets
- Some gradient backgrounds in dashboard.py

**Tasks:**
1. Define color scheme (suggest: dark modern theme with accent colors)
2. Create centralized stylesheet file (`.qss`)
3. Update button styles (modern, rounded, hover effects)
4. Update text input styles (clean, professional)
5. Add icons to buttons
6. Improve layout spacing and alignment

**Files to Modify:**
- Create `ui/styles.qss` - Master stylesheet
- Update `modules/ui/app.py` - Apply stylesheet
- Update individual UI files

---

## Priority 4: Add Licensing System
**Requirement:** One license = one PC. Cannot run without valid license.

**Implementation:**
1. Generate hardware fingerprint (CPU ID, MAC address, or combo)
2. License key format: `ALPHA-XXXX-XXXX-XXXX-XXXX` (human readable)
3. License verification on app startup
4. License storage: encrypted in config file or registry
5. Server-side validation (optional for MVP)

**Licensing Logic:**
- On first run: generate hardware ID, show license request dialog
- On startup: validate license against hardware ID
- If invalid/missing: show license purchase/input dialog, disable features

**Files to Create/Modify:**
- Create `modules/licensing.py` - License generation/validation
- Modify `main.py` - Check license before starting app
- Create `modules/ui/license_dialog.py` - License input/display

**Security Notes:**
- Don't store plaintext license keys
- Use encryption (AES or similar) for storage
- Consider server-side validation for production

---

## Next Steps

1. ✅ Cloned repo, created branch
2. ⏳ Fix template sync bug (Priority 1)
3. ⏳ Finish layout designer (Priority 2)
4. ⏳ Modernize UI (Priority 3)
5. ⏳ Add licensing (Priority 4)

Each step should be committed separately with clear messages.
Revenue target: 1000 RM per customer, 50/50 split with Wong.
