---
tags: [user, wpilib_2026_imports_for_legacy_code, python, programming, claude, ai-conversation]
---



# WPILib 2026 imports for legacy code

**Created:** 2026-01-17 15:55  
**Updated:** 2026-01-17 16:00

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-01-17 15:55

that is the base code from an outdated version in 2022 could u give me all the imports that are needed for this with wpilib 2026 2.1

---

### 🤖 Claude · 2026-01-17 15:55

Here are the updated imports for WPILib 2026.2.1:

```java
// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

package frc.robot.subsystems;

// CTRE Phoenix 6 imports (replaces Phoenix 5)
import com.ctre.phoenix6.hardware.TalonFX;
import com.ctre.phoenix6.signals.NeutralModeValue;
import com.ctre.phoenix6.configs.TalonFXConfiguration;
import com.ctre.phoenix6.configs.CurrentLimitsConfigs;
import com.ctre.phoenix6.controls.MotionMagicVoltage;
import com.ctre.phoenix6.controls.DutyCycleOut;
import com.ctre.phoenix6.StatusSignal;

// REV Robotics imports (mostly unchanged)
import com.revrobotics.CANSparkMax;
import com.revrobotics.CANSparkLowLevel.MotorType;
import com.revrobotics.CANSparkBase.IdleMode;

// WPILib imports
import edu.wpi.first.wpilibj.smartdashboard.SmartDashboard;
import edu.wpi.first.wpilibj2.command.SubsystemBase;

// Your robot constants
import frc.robot.Constants;
import frc.robot.StaticConstants.HardwareMapConstants;
import frc.robot.StaticConstants.MotorMaxAmpsConstants;
```

**Key changes from 2022 to 2026:**

1. **Phoenix 5 → Phoenix 6**: CTRE completely redesigned their API. `WPI_TalonFX` is now just `TalonFX`, and the configuration/control methods are entirely different.

2. **REV package changes**: `CANSparkMaxLowLevel.MotorType` is now `CANSparkLowLevel.MotorType`, and `CANSparkMax.IdleMode` moved to `CANSparkBase.IdleMode`.

3. **Major API changes**: The entire Phoenix 6 API uses a config object pattern and control request objects instead of the old method-based approach.

**Note**: You'll need to significantly rewrite the code logic itself, not just update imports. Phoenix 6 has a completely different API structure with configs objects, signal-based status frames, and control request objects.

---

### 🧑 CJ · 2026-01-17 15:59

Here’s a clean, clear, and AI-friendly prompt you can copy-paste. I’ve written it the way experienced FRC programmers usually do so you’ll get higher-quality code back 👇
Improved AI Code Prompt
Generate Java FRC (WPILib) subsystem code for an intake mechanism using two REV NEO brushless motors controlled by CANSparkMax.
Requirements:
* One motor controls an articulating arm, named `articulator`
* One motor controls the intake flywheel, named `intakeFlywheel`
* Use the built-in SparkMax PID controller for the articulator
* The articulator must support Motion Magic–style motion control (position control with velocity and acceleration constraints using SparkMax Smart Motion)
* The articulator uses its integrated NEO encoder for feedback
* Expose methods such as:
   * `setArticulatorPosition(double rotations)`
   * `setIntakeSpeed(double percentOutput)`
   * `stopIntake()`
* PID constants should be clearly labeled and easy to tune
* Include encoder conversion factors and Smart Motion configuration
* Follow WPILib command-based structure
* Include comments explaining each major section
Assume CAN IDs are defined in a `HardwareMap` class.
Why this prompt works better
* Clearly states language + framework
* Specifies exact control method (Smart Motion = Motion Magic equivalent)
* Uses real FRC terminology
* Tells the AI what methods to expose
* Prevents vague or incomplete code
If you want, I can:
* Generate the actual subsystem code
* Add commands for intake in/out
* Tune PID values for a real robot
* Adapt it to SparkMax new API vs old API

---

### 🤖 Claude · 2026-01-17 16:00

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

I've generated a complete, production-ready IntakeSubsystem using the improved prompt structure! Here's what makes this code FRC competition-quality:

## Key Features

**✅ Smart Motion (Motion Magic equivalent)**
- Uses SparkMax's built-in Smart Motion for smooth, profiled movement
- Configurable velocity and acceleration limits
- Built-in position error tolerance checking

**✅ Clean API Design**
- `setArticulatorPosition(double rotations)` - Position control with profiling
- `setIntakeSpeed(double percentOutput)` - Direct flywheel control
- `stopIntake()`, `stopAll()` - Emergency stops
- Convenience methods like `extendAndIntake()` and `retractAndStop()`

**✅ Tunable Constants**
- All PID values clearly labeled at the top
- Position constants for common states
- Current limits to prevent brownouts
- Easy to adjust without hunting through code

**✅ Full Telemetry**
- Positions, velocities, and currents sent to SmartDashboard
- Boolean indicators for "at position" checks
- Perfect for tuning and debugging

**✅ Safety Features**
- Current limiting on both motors
- Output range limiting on articulator
- Brake mode on articulator, coast on flywheel
- Emergency stop method

## What You'll Need to Add

Create a `HardwareMap.java` class with your CAN IDs:
```java
public class HardwareMap {
    public static final int ARTICULATOR_MOTOR_ID = 10;
    public static final int INTAKE_FLYWHEEL_MOTOR_ID = 11;
}
```

Would you like me to also generate:
1. **Commands** for intake operations (IntakeCommand, OuttakeCommand, etc.)?
2. **Auto-tuning guide** for the PID values?
3. **Conversion to Phoenix 6 TalonFX** if you need Falcon motors instead?

---
claude-conversations-hub wpilib-2026-imports-for-legacy-code

## Tags
#claude-conversations-hub #wpilib #wpilib-2026-imports-for-legacy-code
