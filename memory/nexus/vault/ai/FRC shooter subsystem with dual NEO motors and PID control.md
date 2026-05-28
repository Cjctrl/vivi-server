---
tags: [user, frc_shooter_subsystem_with_dual_neo_motors_and_pid_control, frc, robotics, claude, ai-conversation]
---



# FRC shooter subsystem with dual NEO motors and PID control

**Created:** 2026-01-17 17:05  
**Updated:** 2026-01-17 17:10

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-01-17 17:05

i have a frc wpilib with two Revrobotic neo  motors, and called (lead and follow) with a velocity based (PID) with it, i also need a boolean with that says "fuel is in", i need another boolean with is at speed. update it for 2026  Generate FRC WPILib Java (2026 season / WPILib 2026) code for a Shooter/Flywheel subsystem using two REV Robotics NEO brushless motors on SPARK MAX controllers.
Hardware
* Two NEO motors:
   * `lead` (main motor)
   * `follow` (follows `lead`)
* Both are CANSparkMax (brushless).
* The `follow` motor must follow the `lead` motor (invert if needed).
Control Requirements
* Use closed-loop velocity control (PID) on the `lead` motor using the REV SparkMax PID controller (not WPILib PIDController).
* Use the integrated NEO encoder for velocity feedback.
* Target speed is in RPM (or clearly state the units and conversions).
Booleans / State
Create and maintain these booleans:
1. `fuelIsIn`
* True when the robot has a game piece (“fuel”) detected.
* Assume a sensor exists (beam break or limit switch). Use `DigitalInput` and make the polarity easy to flip.
* Provide a public getter: `boolean fuelIsIn()`
1. `isAtSpeed`
* True when measured RPM is within a tolerance of the target RPM for a minimum stable time (recommended: tolerance + debounce).
* Provide a public getter: `boolean isAtSpeed()`
API / Methods
Expose clean subsystem methods:
* `setTargetRPM(double rpm)`
* `stopShooter()`
* `double getRPM()`
* `boolean fuelIsIn()`
* `boolean isAtSpeed()`
Tuning + Constants
* Put tunables in `Constants` (or `ShooterConstants`) including:
   * CAN IDs for lead and follow
   * PID gains: kP, kI, kD, kFF
   * Max/min output limits if used
   * `AT_SPEED_TOLERANCE_RPM`
   * `AT_SPEED_DEBOUNCE_SECONDS`
   * DIO port for the fuel sensor
* Comment clearly where to tune PID and tolerance.
Telemetry
* Publish to SmartDashboard (or NetworkTables) at least:
   * target RPM
   * current RPM
   * fuelIsIn
   * isAtSpeed
Command-Based Structure
* Make it a `SubsystemBase`
* Show safe defaults (stopped on init)
* Include best practices: restore factory defaults, set idle mode, current limit (optional), burn flash (optional)
Output
Return:
1. `ShooterSubsystem.java`
2. `Constants.java` (or `ShooterConstants` inner class)
Keep the code clean, compile-ready, and consistent with WPILib 2026 conventions.

---

### 🤖 Claude · 2026-01-17 17:07

I'll create a modern FRC 2026 WPILib shooter subsystem using REV Robotics NEO motors with velocity PID control and the required boolean states.
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

I've created a complete, modern FRC 2026 WPILib shooter subsystem for you! Here's what I've included:

## Key Features:

### Hardware Setup
- Two REV NEO motors (lead and follow) on CANSparkMax controllers
- Follow motor automatically mirrors the lead motor
- Built-in encoder from the NEO motor for velocity feedback

### Control System
- **Velocity PID control** using the SparkMax's onboard PID controller (more efficient than WPILib PID)
- Configurable PID gains (kP, kI, kD, kFF) in Constants
- Target speed in **RPM** (the NEO encoder returns RPM by default)

### Required Booleans
1. **`fuelIsIn()`** - Detects game piece via DigitalInput sensor (beam break or limit switch)
2. **`isAtSpeed()`** - Returns true when:
   - Current RPM is within tolerance of target RPM
   - Has remained stable for the debounce time (prevents false positives)

### Clean API
- `setTargetRPM(double rpm)` - Set target velocity
- `stopShooter()` - Stop motors
- `getRPM()` - Get current velocity
- `fuelIsIn()` - Check if fuel is detected
- `isAtSpeed()` - Check if at target speed

### Smart Features
- **Debounced "at speed" detection** - won't report ready until stable
- **Comprehensive telemetry** - all important values published to SmartDashboard
- **Current limiting** - protects motors from damage
- **Factory defaults restored** - ensures clean state on startup

## TODO Items to Configure:
1. Set correct CAN IDs for your motors (lines 17-20 in Constants)
2. Set correct DIO port for fuel sensor (line 27)
3. Test motor inversions (lines 23-26)
4. **Tune PID values** - start with the defaults and adjust based on testing
5. Adjust shooting RPM targets for your game (lines 46-48)
6. Verify fuel sensor polarity matches your wiring

The code is ready to compile and follows 2026 WPILib best practices!

---

### 🧑 CJ · 2026-01-17 17:10

```java
// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

package frc.robot;

/**
 * The Constants class provides a convenient place for teams to hold robot-wide numerical or boolean
 * constants. This class should not be used for any other purpose. All constants should be declared
 * globally (i.e. public static). Do not put anything functional in this class.
 *
 * <p>It is advised to statically import this class (or one of its inner classes) wherever the
 * constants are needed, to reduce verbosity.
 */
public final class Constants {
  public static class OperatorConstants {
    public static final int kDriverControllerPort = 0;
  }
}
 
```

add to the constant

---

### 🤖 Claude · 2026-01-17 17:10

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Perfect! I've updated the Constants file to include your existing `OperatorConstants` class and added the `ShooterConstants` below it. The file now contains both sets of constants and is ready to use with your existing robot code.

---
claude-conversations-hub frc-shooter-subsystem-with-dual-neo-motors-and-pid-control

## Tags
#claude-conversations-hub #frc #frc-shooter-subsystem-with-dual-neo-motors-and-pid-control
