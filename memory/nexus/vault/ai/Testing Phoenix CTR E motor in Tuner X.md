---
tags: [user, testing_phoenix_ctr_e_motor_in_tuner_x, claude, ai-conversation]
---



# Testing Phoenix CTR E motor in Tuner X

**Created:** 2026-02-07 16:22  
**Updated:** 2026-02-07 16:22

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-02-07 16:22

how can i test out my Phoenix CTR E motor in Phoenix Tuner X versoin 2026.2.7.0? I'm getting errors

---

### 🤖 Claude · 2026-02-07 16:22

I can see you're experiencing compatibility issues between your Talon FX motor controller and Phoenix Tuner X. Here's what's happening and how to fix it:

## The Problem

The error message at the bottom of your screenshot is clear: **"Firmware version is not compatible with this version of Phoenix. Make sure your firmware and API major versions match."**

Your setup shows:
- **Phoenix Tuner X**: 2026.2.7.0
- **Talon FX App Version**: 26.1.0.0 (Phoenix 6)
- **Server Version**: 2025.1.0

There's a version mismatch causing the self-test failure and the "DISABLED" status.

## How to Fix It

You have two options:

**Option 1: Update the Talon FX Firmware** (Recommended)
1. In the Info tab (first screenshot), click **"Update Firmware"**
2. Select the firmware version that matches your Phoenix Tuner X (2026.x)
3. Wait for the update to complete
4. After updating, click **"Refresh"** in the Self Test tab

**Option 2: Use Compatible Software Versions**
If updating firmware doesn't work, you may need to ensure all components are on compatible versions. Check CTR Electronics' documentation for version compatibility.

## After Updating

Once the versions match:
1. Go to the **Self Test** tab
2. Click **"Refresh"** to run the self-test
3. The motor should show as enabled in the **Control** tab
4. You can then test the motor by enabling it and adjusting control parameters

The self-test failure you're seeing is purely due to the version incompatibility - once that's resolved, you should be able to control and test your motor normally.

---
claude-conversations-hub testing-phoenix-ctr-e-motor-in-tuner-x

## Tags
#claude-conversations-hub #testing #testing-phoenix-ctr-e-motor-in-tuner-x
