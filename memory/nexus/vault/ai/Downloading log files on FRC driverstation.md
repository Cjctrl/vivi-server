---
tags: [user, downloading_log_files_on_frc_driverstation, frc, robotics, claude, ai-conversation]
---



# Downloading log files on FRC driverstation

**Created:** 2026-03-08 20:31  
**Updated:** 2026-03-08 20:32

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-03-08 20:31

on frc driverstation how do i download log filies

---

### 🤖 Claude · 2026-03-08 20:31

The user is asking about how to download log files from FRC (FIRST Robotics Competition) Driver Station.## FRC Driver Station Log Files

FRC Driver Station log files are stored locally on your computer — there's no "download" needed. Here's how to access them:

**Location on your computer:**
```
C:\Users\Public\Documents\FRC\Log Files\
```

**To view logs using the FRC Log Viewer:**
1. Open the **FRC Driver Station** application
2. Click the **gear icon** (Setup tab) in the Driver Station
3. Click **"Log Viewer"** — this opens the built-in log viewer
4. You can browse and inspect past match logs there

**Alternatively**, you can open the Log Viewer directly:
- Search for **"FRC Log File Viewer"** in your Start Menu (it installs with the Driver Station software)

**What the logs contain:**
- Battery voltage over time
- Robot enable/disable events
- Communication status
- CPU usage
- Trip time / packet loss

**If you're trying to share logs** (e.g., with a mentor or for troubleshooting):
1. Navigate to `C:\Users\Public\Documents\FRC\Log Files\`
2. Copy the `.dslog` and `.dsevents` files from the relevant match/date
3. Share those files — teammates can open them with their own FRC Log File Viewer

**Tip:** Log files are named by timestamp, so look for the date/time of the session you want to review.

---

### 🧑 CJ · 2026-03-08 20:32

im having errors on my driverstation

---

### 🤖 Claude · 2026-03-08 20:32

The user uploaded FRC Driver Station log files. Let me read the .dsevents files to see what errors are occurring. These are binary files likely, so let me check them.Let me read those log files to see what's going on!
```
This block is not supported on your current device yet.
```

Binary files. Let me try to read them with strings or hexdump.
```
This block is not supported on your current device yet.
```

Good, I have a clear picture of the errors. Let me summarize the key issues:

1. **PhotonVision not connected** - Both RearRightCam and RearLeftCam are not connecting to NetworkTables. This is causing loop overruns because `PhotoVisionSubsystem_DualCamera.periodic()` takes way too long (0.27s, 0.37s).

2. **Loop overruns** - The robot loop (20ms) is being overrun repeatedly, primarily caused by the PhotonVision subsystem.

3. **CAN bus issues** - "talon fx 2" on the CANivore is reporting stale CAN frames at around the 2-minute mark. This could be a wiring issue with that specific Talon FX.


4. **PathPlanner 'fire' command not registered** - The named command registry is missing the 'fire' command that's being called.

5. **Joystick Button 5 on port 0** - The Xbox controller's LB button is being referenced but isn't available, likely a button binding or controller configuration issue.

6. **E-stops and communication loss** - Multiple emergency stops triggered at the end of the second session, followed by lost DS communication.

The critical issues are the PhotonVision coprocessors failing to connect, which is directly causing the loop overruns, and the CAN bus stale frames on that specific Talon FX.Here's a breakdown of what's going on with your robot — there are a few distinct issues:

---

**🔴 #1 — PhotonVision not connecting (biggest issue)**

Both `RearRightCam` and `RearLeftCam` are failing to connect to NetworkTables. The error repeats throughout both logs:
> "Could not find **any** PhotonVision coprocessors on NetworkTables."

This is also the **root cause of your loop overruns** — `PhotoVisionSubsystem_DualCamera.periodic()` is taking up to **0.37 seconds** when it should finish in under 0.02s. That's why you're seeing "Loop time of 0.02s overrun" and "CommandScheduler loop overrun" constantly.

**Fix:** Make sure PhotonVision is actually running on your coprocessor (Raspberry Pi / Orange Pi). Check that it's powered, booted, and on the same network as the RoboRIO (IP `10.47.79.11` is showing up, so it's connecting to NT eventually — but the cameras themselves aren't starting). Also check the TimeSyncServer warning — PhotonVision needs time sync configured properly.

---

**🔴 #2 — CAN bus stale frames on Talon FX 2**

Around the 2-minute mark in the second session, `talon fx 2` on the CANivore starts reporting stale position and velocity signals:
> "CAN frame not received/too-stale. Check CAN bus wiring, CAN bus utilization, and power to the device."

This points to a loose or damaged CAN wire on that specific motor controller, or a power brownout affecting it.

**Fix:** Physically inspect the CAN H/L wires on Talon FX ID 2. Reseat the connectors and check for any crimping or damage.

---

**🟡 #3 — PathPlanner 'fire' command not registered**

> "PathPlanner attempted to create a command 'fire' that has not been registered with NamedCommands.registerCommand"

Your auto routine uses a command named `fire` but it was never registered in code.

**Fix:** In your robot code (likely `RobotContainer.java`), add:
```java
NamedCommands.registerCommand("fire", yourFireCommand);
```

---

**🟡 #4 — Joystick Button 5 on port 0 (Xbox controller)**

The warning about "Joystick Button 5 on port 0 not available" fires constantly. Button 5 on an Xbox controller is the **left bumper (LB)**. Something in your code is polling it even when it might not be mapped yet at startup.

This is likely harmless noise once the robot is fully connected, but double-check your button bindings.

---

**🔵 #5 — DS A-Stop and communication loss at the end**

The second log ends with multiple `DS A-Stop Disable` events followed by `The Driver Station has lost communication with the robot`. This likely happened because someone hit E-stop or the robot was powered down.

---

**Priority order to fix:** PhotonVision → CAN wiring on Talon FX 2 → Register the `fire` command. Fixing PhotonVision alone will probably resolve most of your loop overrun issues.

---
claude-conversations-hub downloading-log-files-on-frc-driverstation

## Tags
#1 #2 #3 #4 #5 #claude-conversations-hub #downloading #downloading-log-files-on-frc-driverstation
