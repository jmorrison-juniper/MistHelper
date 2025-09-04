# NOC Engineer Guide: MistHelper Option 92
## Convert Single Virtual Chassis Switch to Virtual MAC

---

## For Junior NOC Engineers

This guide walks junior NOC engineers through converting a single virtual chassis switch to virtual MAC configuration. This is typically used for:
- Individual device incidents during maintenance windows
- Specific trouble ticket resolution 
- Single-site network modifications
- First-time virtual chassis conversion operations

For overview and decision-making, see **VIRTUAL-CHASSIS-CONVERSION-OVERVIEW.md** first.

---

## What This Operation Does

**Virtual Chassis to Virtual MAC Conversion:**
- Changes how switches handle MAC address learning and forwarding
- Provides more flexibility for certain network configurations  
- Required for some network designs and integrations
- **Permanent change** - requires manual reconfiguration to reverse

**When NOC engineers typically use this:**
- Work orders specifying virtual chassis to virtual MAC conversion
- Network engineering requests for specific switches
- Incident resolution where virtual MAC is required
- Pre-planned maintenance for network standardization

---

## ⚠️ NOC SAFETY REQUIREMENTS

**READ VIRTUAL-CHASSIS-CONVERSION-OVERVIEW.md FIRST** for complete safety information, prerequisites, and authorization requirements.

**Quick Safety Checklist:**
- ✅ Change approval obtained through NOC change management
- ✅ Maintenance window scheduled and users notified  
- ✅ Help desk coordinated about expected 2-5 minute outage
- ✅ Network monitoring active for target site
- ✅ Emergency contacts available and documented

---

## 🛠️ Before You Start

### Prerequisites
- **📖 MistHelper Setup**: If not installed, see **INSTALLATION-GUIDE.md**
- **📖 First-Time Configuration**: See **README.md** for initial setup
- **🔧 Test MistHelper**: Run a read-only operation first (like menu option 11)

### What You Need Ready
- **Work order number** or change request ID
- **Site name** where the target switch is located
- **Switch name/identifier** (if known from the work order)
- **Monitoring dashboards** open for the target site

---

## 📋 Step-by-Step Execution

### Step 1: Open Command Prompt and Navigate to MistHelper

**📖 If you need help with basic command prompt usage, see INSTALLATION-GUIDE.md**

1. **Open Command Prompt** (Windows: Start → cmd)
2. **Navigate to MistHelper folder:**
   ```
   cd " work folder here "
   ```
3. **Start MistHelper:**
   ```
   python MistHelper.py
   ```

### Step 2: Select Option 92

1. **In the MistHelper menu, find option 92** (Virtual Chassis conversion)
2. **Type:** `92`  
3. **Press Enter**

### Step 3: Select Your Site

1. **MistHelper displays all sites in your organization**
2. **Find your target site** from the work order
3. **Note the number in brackets** next to your site (e.g., [5])
4. **Type the site number** and press Enter

**Example:**
```
[1] Main Office - New York
[2] Branch Office - Chicago  
[3] Warehouse - Dallas
```
For Chicago office: type `2`

### Step 4: Select Your Switch

1. **MistHelper shows all virtual chassis switches at the selected site**
2. **Each switch displays:**
   - Index number [0], [1], [2], etc.
   - Switch name
   - MAC address, model, serial number

3. **Choose the switch by:**
   - **Typing the index number** (e.g., `0`) OR
   - **Typing the exact switch name**

### Step 5: Confirm the Operation

**⚠️ FINAL CONFIRMATION REQUIRED ⚠️**

1. **MistHelper shows conversion details** including switch name, site, and warnings
2. **To proceed:** Type exactly `CONVERT` (all capitals)
3. **To cancel:** Type anything else (like `no`)
4. **Press Enter**

### Step 6: Monitor Execution

1. **If confirmed, conversion begins immediately**
2. **Success**: ✅ message appears
3. **Failure**: ❌ message with error details appears
4. **Document the result** in your work order/ticket

---

## 🔍 Post-Operation NOC Procedures

### Immediate Actions (First 15 minutes):
1. **Monitor target site** for connectivity issues
2. **Check Mist dashboard** at https://manage.mist.com for device status
3. **Verify network functionality** - ping tests, user connectivity
4. **Update work order/ticket** with completion status and timestamp

### Extended Monitoring (30-60 minutes):
1. **Watch for user complaints** via help desk tickets
2. **Monitor network performance metrics** for the converted switch
3. **Document any anomalies** that require follow-up
4. **Close work order** if no issues detected

### If Issues Occur:
1. **Document exact symptoms** and affected systems
2. **Check error logs** in Mist dashboard
3. **Escalate to NOC lead** if user impact is significant
4. **Follow your site's incident escalation procedures**

---

## 📞 NOC Escalation Guidelines

**Escalate to NOC Lead/Senior if:**
- Conversion fails with error messages
- Network connectivity is not restored within 10 minutes
- Multiple user complaints are received
- Switch shows offline status in Mist dashboard after 15 minutes

**Escalate to Network Engineering if:**
- Physical switch hardware appears to be malfunctioning
- Rollback procedures are needed
- Vendor support contact is required

---

## 🆘 Common NOC Troubleshooting

### Issue: "python: command not found"
**Solution:** MistHelper environment not set up - see **INSTALLATION-GUIDE.md** or escalate to NOC lead

### Issue: "Authentication failed"  
**Solution:** API credentials expired/incorrect - check with NOC lead for credential refresh

### Issue: "No virtual chassis switches found"
**Solution:** 
- Verify you selected the correct site
- Check work order for correct site name
- Switch may already be in virtual MAC mode

### Issue: "Conversion failed" with API error
**Solution:**
- Document the exact error message
- Check if switch is online in Mist dashboard
- Escalate to NOC lead with error details

### Issue: Users report connectivity problems post-conversion
**Solution:**
- Check switch status in monitoring dashboard
- Verify all switch ports are operational
- If problems persist >15 minutes, escalate immediately

---

## 📋 Quick Reference Card

**To run Option 92:**
1. Open command prompt
2. `cd " work folder "`
3. `python MistHelper.py`
4. Type `92` and press Enter
5. Select your site by number
6. Select your switch by index or name
7. Type `CONVERT` to confirm (or anything else to cancel)
8. Wait for completion

**Remember:** This is a permanent change that affects network infrastructure. Only proceed if you have explicit authorization and understand the consequences.

---

*This guide was created to help complete beginners safely use MistHelper Option 92. When in doubt, always ask for help rather than guessing.*
