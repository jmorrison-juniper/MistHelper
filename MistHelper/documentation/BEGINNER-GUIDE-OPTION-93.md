# NOC Engineer Guide: MistHelper Option 93
## Bulk Convert Virtual Chassis Switches to Virtual MAC (Multi-Site Operation)

---

## 🎯 For Senior NOC Engineers

This guide walks **senior NOC engineers** through bulk virtual chassis to virtual MAC conversion across multiple sites. This is typically used for:
- **Large-scale network migration projects**
- **Multi-site infrastructure standardization**
- **Planned bulk maintenance operations**
- **Project deployments during extended maintenance windows**

**⚠️ This is an ADVANCED operation** - junior NOC engineers should use Option 92 for single switches.

**For overview and decision-making**, see **VIRTUAL-CHASSIS-CONVERSION-OVERVIEW.md** first.

---

## 📚 What This Operation Does

**Bulk Virtual Chassis → Virtual MAC Conversion:**
- Processes **ALL virtual chassis switches** at **multiple sites** from a predefined list
- Requires **extensive coordination** with help desk teams and site personnel

**When senior NOC engineers use this:**
- Multi-site network migration projects with change approval
- Infrastructure standardization initiatives  
- Planned bulk maintenance during extended windows
- Project deployments coordinated with network engineering

---

## ⚠️ ADVANCED NOC OPERATION REQUIREMENTS

**READ VIRTUAL-CHASSIS-CONVERSION-OVERVIEW.md FIRST** for complete safety information, prerequisites, and authorization requirements.

**Senior NOC Engineer Responsibilities:**
- ✅ **Project-level authorization** obtained from NOC management
- ✅ **Extended maintenance window** coordinated (3-6 hours typical)
- ✅ **Multi-site help desk coordination** completed
- ✅ **Centralized monitoring** setup for all target sites
- ✅ **Escalation procedures** established with network engineering
- ✅ **Rollback plans** documented and approved

---

## 🛠️ Before You Start

### Prerequisites
- **📖 MistHelper Setup**: If not installed, see **INSTALLATION-GUIDE.md**
- **📖 Initial Configuration**: See **README.md** for first-time setup
- **🔧 Test MistHelper**: Verify with read-only operations first

### Advanced Preparation Required
- **Project documentation** with complete site list and justification
- **Change management approval** for bulk infrastructure modification
- **Cross-functional coordination** with help desk, field teams, and management
- **Comprehensive monitoring setup** for real-time visibility across all sites

---

## 📋 Step-by-Step Execution

### Step 1: Create the Site List File (VCConvert.CSV)

**📄 See VCConvertSample.CSV for format example**

1. **Create a new text file** using Notepad or text editor
2. **Add site names** exactly as they appear in Mist (one per line, no headers)
3. **Save as** `VCConvert.CSV` in the MistHelper folder
4. **Verify accuracy** - incorrect site names will cause failures

**Example file content:**
```
Main Office New York
Branch Office Chicago
Warehouse Dallas
Manufacturing Plant Detroit
```

### Step 2: Launch MistHelper

**📖 For basic command prompt help, see INSTALLATION-GUIDE.md**

1. **Open Command Prompt** and navigate to MistHelper folder
2. **Start MistHelper:** `python MistHelper.py`
3. **Select Option 93** from the menu

### Step 3: Review Site List Verification

1. **MistHelper reads your VCConvert.CSV** and displays found sites
2. **Verify all expected sites are listed** - if any are missing, press Ctrl+C to stop
3. **Check for typos or missing sites** - fix CSV file if needed

### Step 4: Review Target Switches

1. **MistHelper scans all listed sites** for virtual chassis switches
2. **Displays complete inventory** including:
   - Site name
   - Switch name, MAC, model, serial
   - Total count of switches to convert

3. **CRITICAL REVIEW STEP:**
   - Verify this matches your project documentation
   - Count switches to estimate time (2-5 minutes per switch)
   - Ensure no critical production switches are included unexpectedly

### Step 5: Execute Bulk Conversion

**⚠️ FINAL AUTHORIZATION STEP ⚠️**

1. **MistHelper asks for confirmation** with total switch count
2. **Type `yes`** to proceed with bulk conversion
3. **Type `no`** to cancel operation

### Step 6: Monitor Bulk Progress

1. **Real-time progress display** shows:
   ```
   [3/15] Converting 'Switch-Main-Floor2' at site 'Chicago Office'...
   ✅ Conversion triggered successfully.
   ```

2. **Monitor each conversion:**
   - Success (✅) or failure (❌) status  
   - Error messages for failed conversions
   - Running totals of successes/failures

3. **Do NOT close the window** until all conversions complete

### Step 7: Review Final Results

1. **Conversion summary displays:**
   ```
   📊 Conversion Summary:
      ✅ Successful conversions: 12
      ❌ Failed conversions: 3  
      📊 Total switches processed: 15
   ```

2. **Document results** in project tracking system
3. **Note any failures** for follow-up action

---

## 🔍 Advanced NOC Monitoring Procedures

### Post-Operation Validation (First Hour):
1. **Site-by-site connectivity verification** using monitoring tools
2. **Mist dashboard review** - confirm all switches show proper status
3. **User impact assessment** - review help desk tickets and reports
4. **Failed conversion analysis** - determine root cause and remediation plan
5. **Project status update** - communicate results to stakeholders

### Extended Monitoring (24 Hours):
1. **Performance baseline comparison** - verify no degradation
2. **Ongoing user impact tracking** via help desk metrics
3. **Switch stability monitoring** - watch for recurring issues
4. **Documentation completion** - finalize project records

---

## 📞 Advanced NOC Escalation

**During Operation - Escalate to Network Engineering if:**
- >20% conversion failure rate
- Critical sites lose connectivity >10 minutes
- Hardware failures detected during conversion

**Post-Operation - Escalate to Management if:**
- Significant user impact persists >2 hours
- Business-critical systems affected
- Multiple sites require emergency rollback
- Vendor support escalation needed

---

## 🆘 Advanced Troubleshooting

### Issue: High Failure Rate (>20%)
**NOC Response:**
- Stop operation immediately if possible
- Document all error messages from failed conversions
- Verify API connectivity and authentication status
- Escalate to network engineering with detailed failure logs

### Issue: Site-Wide Connectivity Loss
**NOC Response:**  
- Immediately escalate to network engineering
- Coordinate with field teams for physical verification
- Document affected users and business impact
- Prepare for emergency rollback procedures

### Issue: Partial Conversion Success with User Impact
**NOC Response:**
- Continue monitoring affected sites closely
- Work with help desk to triage user reports
- Use Option 92 to retry failed individual switches
- Document lessons learned for future operations

### Issue: API Rate Limiting or System Overload
**NOC Response:**
- Allow operation to continue (MistHelper handles rate limiting)  
- Monitor for system recovery
- Document timing for future planning
- Consider scheduling future bulk operations during lower-usage periods

---

## 📋 Senior NOC Quick Reference

**Pre-execution Checklist:**
- [ ] VCConvert.CSV created with exact site names
- [ ] Project authorization and change approval verified
- [ ] Extended maintenance window coordinated
- [ ] Multi-site monitoring dashboards active
- [ ] Help desk teams notified across all sites
- [ ] Network engineering escalation contacts confirmed

**Execution Steps:**
1. Navigate to MistHelper folder, run `python MistHelper.py`
2. Select option `93`
3. Review site list verification
4. Review target switch inventory  
5. Type `yes` to confirm bulk operation
6. Monitor real-time progress and results
7. Document completion status and any failures

**Expected Timeline:**
- Setup and review: 10-15 minutes
- Conversion execution: 5-15 minutes per switch
- Post-operation validation: 30-60 minutes
- Extended monitoring: 24 hours

**Success Criteria:**
- >80% conversion success rate
- No critical site connectivity loss >10 minutes
- User impact within acceptable parameters
- Complete documentation in project tracking system

---

*This guide was created for senior NOC engineers managing bulk virtual chassis conversion operations. Always coordinate with network engineering and follow your organization's change management procedures.*
