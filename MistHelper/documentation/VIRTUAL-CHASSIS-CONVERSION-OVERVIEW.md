# Virtual Chassis to Virtual MAC Conversion Guide
## MistHelper Options 92 & 93 - Junior NOC Engineer Guide

---

## 🎯 What This Document Is For

This document helps **junior NOC engineers** understand MistHelper's virtual chassis conversion options (92 and 93) and choose the right one for their network maintenance tasks.

**This is your starting point for virtual chassis conversion operations.**

---

## 🤔 Which Option Should I Use?

### Use Option 92 (Single Switch) If:
- ✅ Converting **one switch** during a **single maintenance window**
- ✅ You need to **select the specific switch** from a site inventory
- ✅ This is your **first virtual chassis conversion** operation
- ✅ You're working on a **specific trouble ticket** for one device
- ✅ You want **maximum control** and **lowest risk** approach
- ✅ **Incident response**: Fixing a specific switch as part of troubleshooting

### Use Option 93 (Bulk Site Operation) If:
- ✅ Converting **all virtual chassis switches** at **multiple sites**
- ✅ Working on a **planned migration project** with approved change control
- ✅ You have **extensive NOC experience** and are comfortable with bulk operations
- ✅ **Extended maintenance window** scheduled for infrastructure changes
- ✅ **Project deployment**: Part of a larger network infrastructure upgrade
- ✅ **NOC lead or senior engineer** has assigned this as a bulk operation

---


## 🛠️ Prerequisites

### MistHelper Setup
- **📖 Installation Required**: If MistHelper isn't set up yet, see **INSTALLATION-GUIDE.md**
- **📖 First-Time Setup**: For initial configuration, see **README.md** 
- **⚙️ Environment Configuration**: MistHelper must be properly configured with API credentials
- **🔧 Test Run**: Verify MistHelper works by running a simple read-only operation first

### Authorization Requirements
- **📋 Work Order**: You must have a valid work order or change request
- **👤 Senior Approval**: Senior network engineer or NOC lead approval required
- **📞 Contact List**: Emergency contacts identified and available
- **🕐 Maintenance Window**: Scheduled and approved maintenance window

### Network Prerequisites  
- **📊 Network Monitoring**: Active monitoring of all affected sites
- **🔄 Backup Connectivity**: Verify backup connections are functional
- **👥 User Notification**: All affected users notified in advance
- **🛡️ Rollback Plan**: Documented procedure for emergency rollback

---

## ⚠️ CRITICAL SAFETY WARNINGS FOR NOC ENGINEERS

### 🚨 BOTH OPTIONS ARE DESTRUCTIVE OPERATIONS 🚨

**These operations will:**
- ❗ **Permanently modify switch configurations** 
- ❗ **Cannot be easily reversed** - requires manual reconfiguration to undo

**NOC Engineer Responsibilities:**
- ✅ **Verify change approval** is in place before proceeding
- ✅ **Coordinate with help desk** about expected impact
- ✅ **Monitor network status** continuously during operation
- ✅ **Document all actions** in your NOC incident/change tracking system
- ✅ **Escalate immediately** if unexpected issues occur
- ✅ **Follow your site's emergency procedures** if rollback is needed

---

## 📚 Documentation Available

### For Option 92 (Single Switch Conversion):
- **📖 BEGINNER-GUIDE-OPTION-92.md** - Complete step-by-step guide
- Covers everything from opening command prompt to completion
- Includes troubleshooting and safety information
- Perfect for first-time users

### For Option 93 (Bulk Site Conversion):
- **📖 BEGINNER-GUIDE-OPTION-93.md** - Complete step-by-step guide  
- Includes how to create the required CSV file
- Covers bulk operation monitoring and error handling
- Designed for more advanced operations

### Supporting Files:
- **📄 VCConvertSample.CSV** - Example site list file for Option 93
- Use this as a template for creating your own site list

---

## 🎯 NOC Engineer Decision Tree

### Step 1: Do you have proper authorization?
- **No** → Stop. Get change approval through your NOC's change management process
- **Yes** → Continue to Step 2

### Step 2: What type of work order is this?
- **Single device incident/trouble ticket** → Use Option 92
- **Multiple sites planned maintenance** → Use Option 93
- **Emergency/urgent fix** → Use Option 92 (safer for urgent work)

### Step 3: What's your NOC experience level?
- **Junior NOC engineer** → Use Option 92, escalate if bulk conversion needed
- **Senior NOC engineer** → Either option based on scope
- **NOC lead/supervisor** → Use appropriate option based on change requirements

### Step 4: What's your maintenance window?
- **Standard maintenance window (1-2 hours)** → Option 92 for individual sites
- **Extended maintenance window (3+ hours)** → Option 93 for bulk operations
- **Emergency after-hours** → Option 92 only, document thoroughly

---

## 🔄 NOC Workflows

### Standard Single-Site Conversion (Option 92):
1. **Verify change approval** in your ticketing system
2. **Coordinate with help desk** about expected user impact
3. **Open monitoring dashboards** for the target site
4. **Follow BEGINNER-GUIDE-OPTION-92.md** for execution steps
5. **Monitor post-conversion** for 30 minutes minimum
6. **Update ticket/incident** with completion status
7. **Hand off to day shift** if needed for extended monitoring

### Large-Scale Project Conversion (Option 93):
1. **Confirm project authorization** with NOC lead/manager
2. **Coordinate with multiple help desk teams** across sites
3. **Setup centralized monitoring** for all target sites
4. **Follow BEGINNER-GUIDE-OPTION-93.md** for execution steps
5. **Maintain real-time communication** with stakeholders
6. **Document all results** in project tracking system
7. **Conduct post-implementation review** with senior staff

---

## 📞 NOC Escalation Procedures

**Level 1 - NOC Engineer Actions:**
- Execute single-site conversions (Option 92)
- Monitor and document all operations
- Follow standard NOC incident procedures
- Escalate if issues arise beyond normal parameters

**Level 2 - Senior NOC/NOC Lead:**
- Approve bulk operations (Option 93)
- Handle complex troubleshooting
- Coordinate with network engineering teams  

**Level 3 - Network Engineering:**
- Design rollback procedures for failed conversions
- Handle vendor escalations if hardware issues occur
- Approve emergency procedures outside normal change windows

**Emergency Contacts (have these ready):**
- 📞 **NOC Lead/Supervisor** - for operational approval and escalation
- 📞 **Senior Network Engineer** - for technical issues and rollback decisions
- 📞 **Network Operations Manager** - for business impact decisions
- 📞 **Vendor Support (Juniper/Mist)** - for hardware/firmware issues

---

## 📋 NOC Pre-Operation Checklist

### For Both Options:
- [ ] **Change approved** in NOC change management system
- [ ] **Maintenance window scheduled** and stakeholders notified
- [ ] **Help desk coordinated** - expected impact communicated
- [ ] **Monitoring dashboards open** for affected sites
- [ ] **Emergency contacts verified** and available
- [ ] **MistHelper tested** with a read-only operation first

### Additional for Option 93:
- [ ] **Site list verified** (VCConvert.CSV) against change documentation
- [ ] **Extended monitoring setup** for multiple sites
- [ ] **NOC lead approval** documented in change record
- [ ] **Cross-site coordination** established with remote teams
- [ ] **Project tracking updated** with planned execution details

---

## 💡 Best Practices

### General:
1. **Start small**: If you're new to this, try Option 92 on a test switch first
2. **Document everything**: Keep detailed records of what you do and when
3. **Monitor actively**: Watch for network issues during and after conversion
4. **Communicate proactively**: Keep stakeholders informed of progress
5. **Have a fallback plan**: Know what to do if something goes wrong

### For Option 92:
1. **Double-check site and switch selection** before confirming
2. **Work during low-usage hours** to minimize impact
3. **Test connectivity immediately** after conversion

### For Option 93:
1. **Verify your CSV file thoroughly** before starting
2. **Stagger operations** - don't hit all sites simultaneously during business hours
3. **Have dedicated monitoring staff** for each major site
4. **Plan for partial failures** - some switches may need individual attention

---

## 🔍 After Completion

### Immediate Actions:
1. **Verify network connectivity** at all affected locations
2. **Check Mist dashboard** for proper device status
3. **Test critical network functions** (internet, internal connectivity, etc.)
4. **Document any issues** that need follow-up

### Follow-up Actions:
1. **Update network documentation** to reflect the changes
2. **Inform stakeholders** that the work is complete
3. **Monitor for 24-48 hours** for any delayed issues
4. **Schedule any needed cleanup** of failed conversions

---

## 📞 When to Get Help

**Contact your network administrator immediately if:**
- You're not sure which option to use
- You don't have proper authorization
- You encounter any error messages during the process
- Network connectivity issues occur during or after conversion
- More than 10-20% of conversions fail (Option 93)
- Users report network problems after the operation

**Remember: It's always better to ask for help than to guess with network infrastructure.**

---

## 🔗 Quick Links

- **📖 [Option 92 Complete Guide](BEGINNER-GUIDE-OPTION-92.md)** - Single switch conversion
- **📖 [Option 93 Complete Guide](BEGINNER-GUIDE-OPTION-93.md)** - Bulk site conversion  
- **📄 [Sample CSV File](VCConvertSample.CSV)** - Template for Option 93
- **🌐 [Mist Dashboard](https://manage.mist.com)** - Monitor switch status after conversion

---

*This overview was created to help complete beginners understand and safely use MistHelper's virtual chassis conversion options. Always prioritize safety and proper authorization when working with network infrastructure.*
