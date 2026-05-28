---
tags: [user, implementing_velocity_pid_control_for_shooter_subsystem, claude, ai-conversation]
---



# Implementing velocity PID control for shooter subsystem

**Created:** 2026-01-17 12:30  
**Updated:** 2026-01-17 12:35

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-01-17 12:30

```java
package frc.robot.subsystems;

import com.revrobotics.RelativeEncoder;
import com.revrobotics.spark.SparkBase.ControlType;
import com.revrobotics.spark.SparkClosedLoopController;
import com.revrobotics.spark.SparkMax;
import com.revrobotics.spark.SparkLowLevel.MotorType;

import edu.wpi.first.wpilibj.DutyCycleEncoder;
import edu.wpi.first.wpilibj.smartdashboard.SmartDashboard;
import edu.wpi.first.wpilibj2.command.SubsystemBase;
import frc.robot.Constants;
import frc.robot.staticConstants.HardwareMap;

public class Shooter extends SubsystemBase {

    private final SparkMax shooterMotor;
    private final SparkClosedLoopController velocityController;
    private final RelativeEncoder motorEncoder;

    // Optional absolute encoder (for position/angle reference)
    private final DutyCycleEncoder absoluteEncoder;
    private boolean useAbsoluteEncoder;

    // Velocity target tracking
    private double targetVelocity;

    //canaddress for our shooter motor 
    public Shooter() {
        shooterMotor = new SparkMax(Constants.CAN_ADDRESS_SHOOTER_MOTOR, MotorType.kBrushless);

        velocityController = shooterMotor.getClosedLoopController();
        motorEncoder = shooterMotor.getEncoder();

        // Start with a known state
        motorEncoder.setPosition(0.0);

        // Configure PID values for velocity control
        velocityController.setP(Constants.SHOOTER_VELOCITY_PID_kP);
        velocityController.setI(Constants.SHOOTER_VELOCITY_PID_kI);
        velocityController.setD(Constants.SHOOTER_VELOCITY_PID_kD);
        velocityController.setFF(Constants.SHOOTER_VELOCITY_PID_kF);
        velocityController.setOutputRange(-1.0, 1.0);
        //velocityController.setIZone(0.0);
        velocityController.setClosedLoopRampRate(0.0);

        // Default target
        targetVelocity = 0.0;
    }

    /** Call once (or occasionally) if you want to re-sync the relative position to the absolute sensor. */
    public void syncToAbsolute() {
        if (useAbsoluteEncoder && absoluteEncoder.isConnected()) {
            motorEncoder.setPosition(absoluteEncoder.get());
        }
    }

    /** Reset relative encoder position (does not affect velocity control). */
    public void resetEncoderPosition() {
        motorEncoder.setPosition(0.0);
    }

    /** Closed-loop velocity setpoint (RPM by default on REV RelativeEncoder). */
    public void setWheelSpeed(double rpm) {
        targetVelocity = rpm;
        velocityController.setReference(rpm, ControlType.kVelocity);
    }

    public void setWheelSpeedToPreset() {
        setWheelSpeed(Constants.SHOOTER_PRESET_SPEED);
    }

    public void stop() {
        shooterMotor.stopMotor();
        targetVelocity = 0.0;
    }

    public double getVelocity() {
        return motorEncoder.getVelocity();
    }

    public double getPosition() {
        return motorEncoder.getPosition();
    }



    /** True when current velocity is within tolerance of target. */
    public boolean isAtSpeed() {
        double error = Math.abs(getVelocity() - targetVelocity);
        return error <= Constants.SHOOTER_SPEED_TOLERANCE;
    }

    @Override
    public void periodic() {
        SmartDashboard.putNumber("Shooter Target RPM", targetVelocity);
        SmartDashboard.putNumber("Shooter RPM", getVelocity());
        SmartDashboard.putNumber("Shooter RPM Error", Math.abs(getVelocity() - targetVelocity));
        SmartDashboard.putBoolean("Shooter At Speed", isAtSpeed());

        SmartDashboard.putBoolean("Shooter Abs Connected", absoluteEncoder.isConnected());
        SmartDashboard.putNumber("Shooter Abs Pos", getAbsolutePosition());
    }
}

```


```java
// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

package frc.robot.subsystems;

import com.revrobotics.spark.SparkBase.PersistMode;
import com.revrobotics.spark.SparkBase.ResetMode;
import com.revrobotics.spark.SparkLowLevel.MotorType;
import com.revrobotics.spark.SparkMax;
import com.revrobotics.spark.config.SparkBaseConfig.IdleMode;
import com.revrobotics.spark.config.SparkMaxConfig;
import com.revrobotics.spark.config.ClosedLoopConfig.FeedbackSensor;
import edu.wpi.first.wpilibj.DigitalInput;
import edu.wpi.first.wpilibj.smartdashboard.SmartDashboard;
import edu.wpi.first.wpilibj2.command.SubsystemBase;
import frc.robot.staticConstants.HardwareMap;
import frc.robot.staticConstants.MaxMotorAmps;

public class shooterFlywheels extends SubsystemBase {

    // Define the SparkMax motor controllers for the flywheels
    SparkMax shooterLeadFlyWheel;
    SparkMax shooterFollowFlyWheel;

    // Our IR sensor to detect shooter
    DigitalInput shooterIRSensor;
    // Tracks if we have shooter
    boolean haveshooter;

    /** Creates a new algaeFlywheels. */
    public shooterFlywheels() {
        // Address our shooterFlyWheel on the CAN
        shooterLeadFlyWheel = new SparkMax(HardwareMap.CAN_ADDRESS_SHOOTER_LEAD_MOTOR, MotorType.kBrushless);
        // Address our shooterFollowFlyWheel on the CAN
        shooterFollowFlyWheel = new SparkMax(HardwareMap.CAN_ADDRESS_SHOOTER_FOLLOW_MOTOR, MotorType.kBrushless);

        // configure the shooterLeadFlyWheel
        SparkMaxConfig flyWheelLeadConfig = new SparkMaxConfig();
        flyWheelLeadConfig
                .inverted(false) // This one is inverted. May need to switch
                .idleMode(IdleMode.kBrake);
        // flyWheelLeadConfig.encoder
        // .positionConversionFactor(1);
        // .velocityConversionFactor(1000);
        // flyWheelLeadConfig.closedLoop
        // .feedbackSensor(FeedbackSensor.kPrimaryEncoder)
        // .pid(1.0, 0.0, 0.0);
        flyWheelLeadConfig.smartCurrentLimit(MaxMotorAmps.MAX_AMPS_STATOR_LIMIT_NEO550);
        shooterLeadFlyWheel.configure(flyWheelLeadConfig, ResetMode.kResetSafeParameters,
                PersistMode.kPersistParameters);

        // configure the shooterFollowFlyWheel
        SparkMaxConfig flyWheelFollowConfig = new SparkMaxConfig();
        flyWheelFollowConfig
                .idleMode(IdleMode.kBrake)
                // Follow the lead flywheel but invert the direction
                .follow(shooterLeadFlyWheel, true);
        // flyWheelFollowConfig.encoder
        // .positionConversionFactor(1);
        // flyWheelFollowConfig.closedLoop
        // .feedbackSensor(FeedbackSensor.kPrimaryEncoder)
        // .pid(1, 0, 0);
        flyWheelFollowConfig.smartCurrentLimit(MaxMotorAmps.MAX_AMPS_STATOR_LIMIT_NEO550);
        shooterFollowFlyWheel.configure(flyWheelFollowConfig, ResetMode.kResetSafeParameters,
                PersistMode.kPersistParameters);

    }

    // Set the speed of the flywheel
    public void setFlyWheelLeadSpeed(double speed) {
        shooterLeadFlyWheel.set(speed);
        // shooterFollowFlyWheel.set(-speed);
    }

    // Stop the flywheel
    public void stopFlyWheelLead() {
        shooterLeadFlyWheel.stopMotor();
        shooterFollowFlyWheel.stopMotor();
    }

    // Set the speed of the flywheel follow
    public void setFlyWheelFollowSpeed(double speed) {
        shooterFollowFlyWheel.set(speed);
    }

    // Stop the flyWheel follow
    public void stopFlyWheelFollow() {
        shooterFollowFlyWheel.stopMotor();
    }
}

```

i want you to fix the shooter subsystem to allow for a velocity pid

---

### 🤖 Claude · 2026-01-17 12:31

I'll help you fix the Shooter subsystem to properly implement velocity PID control. Here are the issues I found and the corrected code:

**Problems identified:**
1. Missing `CAN_ADDRESS_SHOOTER_MOTOR` constant in Constants.java
2. Absolute encoder initialization is missing but referenced in code
3. Missing `getAbsolutePosition()` method
4. No proper configuration applied to the SparkMax

Here's the corrected Shooter subsystem:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Now you need to add this constant to your `HardwareMap` class (or Constants.java if you prefer):

```java
// In HardwareMap.java or Constants.java
public static final int CAN_ADDRESS_SHOOTER_MOTOR = 10; // Change to your actual CAN ID
```

**Key improvements:**

1. **Proper configuration using SparkMaxConfig**: The new REV API requires configuration through `SparkMaxConfig` objects
2. **Fixed absolute encoder handling**: Added null checks and proper initialization
3. **Added missing `getAbsolutePosition()` method**: This was referenced in `periodic()` but never defined
4. **Proper PID configuration**: Uses the new API's `closedLoop` configuration chain
5. **Better initialization**: Applies configuration with `ResetMode` and `PersistMode` for reliability
6. **Added getter for target velocity**: Useful for debugging and commands

**To use this code:**

1. Add `CAN_ADDRESS_SHOOTER_MOTOR` to your HardwareMap
2. Tune your PID constants (start with the defaults and adjust)
3. If you have an absolute encoder, uncomment the initialization and add the DIO channel constant
4. Test the velocity control and adjust the tolerance if needed

The velocity PID will now work properly with the REV 2025 API!

---

### 🧑 CJ · 2026-01-17 12:31

why do i if i am using the flywheel's as the motors?

---

### 🤖 Claude · 2026-01-17 12:32

You're absolutely right! Looking at your code, you have **two separate subsystems**:

1. **`shooterFlywheels`** - Controls the actual flywheel motors (lead and follow motors)
2. **`Shooter`** - Appears to be for a different mechanism (maybe a pivot/angle mechanism based on the absolute encoder references)

If you want velocity PID control on your **flywheels**, you should add it to the `shooterFlywheels` subsystem, not the `Shooter` subsystem.

Here's the corrected `shooterFlywheels` with velocity PID:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

**Key changes:**

1. **Added velocity PID to the lead flywheel** - The follower automatically mirrors it
2. **Created proper velocity control methods** - `setFlywheelVelocity()`, `setFlywheelToPreset()`, etc.
3. **Changed to Coast mode** - Better for flywheels (less brake wear, faster spindown)
4. **Added velocity tracking** - `isAtSpeed()`, `getVelocity()`, `getTargetVelocity()`
5. **Kept legacy methods** - Marked as `@Deprecated` for backward compatibility
6. **Added SmartDashboard telemetry** - Shows RPM, error, and status

**Now your `Shooter` subsystem** (the other one) is probably for:
- Pivot/angle control (hence the absolute encoder)
- Hood adjustment
- Some other shooter mechanism

The two subsystems work together - the flywheels spin the wheels, and the other mechanism aims/positions them!

---

### 🧑 CJ · 2026-01-17 12:33

wait wait  i wan

---

### 🤖 Claude · 2026-01-17 12:33

I'm listening! What do you want? Go ahead and finish your thought - I'm here to help! 😊

---

### 🧑 CJ · 2026-01-17 12:33

wait wait  i want the shooter subsystem to contain all the pid stuff for the flywheels

---

### 🤖 Claude · 2026-01-17 12:34

Ah, I understand now! You want the `Shooter` subsystem to control the flywheel motors with velocity PID, and you want to get rid of the separate `shooterFlywheels` subsystem (or incorporate it into `Shooter`).

Here's the corrected `Shooter` subsystem that controls the flywheel motors with velocity PID:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Perfect! Now your `Shooter` subsystem:

1. **Controls both flywheel motors** (lead and follow from your `shooterFlywheels` code)
2. **Has velocity PID** configured on the lead motor
3. **Has all the convenience methods** like `setIntakeSpeed()`, `setEjectSpeed()`, etc.
4. **Tracks velocity and provides `isAtSpeed()`** for automated sequences
5. **Optional IR sensor support** for game piece detection
6. **Optional absolute encoder support** if you add a pivot mechanism later

You can now **delete the `shooterFlywheels` subsystem** since all that functionality is now in `Shooter`.

**To use it in your commands:**
```java
// Spin up to preset speed
shooter.setWheelSpeedToPreset();

// Wait until at speed
if (shooter.isAtSpeed()) {
    // Ready to shoot!
}

// Custom speed
shooter.setWheelSpeed(5000); // 5000 RPM

// Stop
shooter.stop();
```

---

### 🧑 CJ · 2026-01-17 12:35

why would i do that and not have a seaprate subsysytem? for each

---

### 🤖 Claude · 2026-01-17 12:35

Great question! There are actually good reasons for **both** approaches. Let me explain the trade-offs:

## Keep Separate Subsystems When:

**1. Different Physical Mechanisms**
- If your shooter has **flywheels** (spinning wheels) AND a **pivot/hood** (aiming mechanism), they should be separate subsystems
- Each mechanism needs independent control and can move at the same time

**2. Independent Operation**
- Flywheels might spin up while the pivot is still moving to position
- You can command them separately: `shooter.setAngle(45)` and `flywheels.setSpeed(4500)`

**3. Better Code Organization**
- Easier to understand: "This subsystem controls flywheels, this one controls the pivot"
- Different teams can work on different subsystems
- Clearer responsibility

**4. Command Flexibility**
- You can create commands that use only one subsystem
- Example: `SpinUpFlywheels` command only requires `shooterFlywheels`
- Example: `AdjustAngle` command only requires `shooterPivot`

## Combined Subsystem When:

**1. Tightly Coupled Mechanisms**
- If the flywheels and any other mechanism ALWAYS move together
- Simpler state management

**2. Single Logical Unit**
- If you think of it as one "shooter" that does everything
- Fewer subsystems to manage

## My Recommendation for You:

Looking at your code, I'd suggest **TWO separate subsystems**:

1. **`ShooterFlywheels`** - Controls the spinning wheels (velocity PID)
2. **`ShooterPivot`** (rename current `Shooter`) - Controls angle/position (if you have one)

Here's why this is better for your robot:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

**Then create a separate `ShooterPivot` subsystem if you have an angle adjustment mechanism:**

```java
public class ShooterPivot extends SubsystemBase {
    // This would control your absolute encoder mechanism
    // Position PID for angle control
    // Separate from flywheel velocity
}
```

**Benefits of this architecture:**

✅ **Parallel Commands** - Spin up flywheels while adjusting angle  
✅ **Clear Requirements** - Each command only requires what it uses  
✅ **Easier Testing** - Test flywheels without needing the pivot  
✅ **Better Organization** - One subsystem = one mechanism  
✅ **Reusability** - Flywheel commands work even if pivot breaks  

**In your commands:**
```java
// Command that uses both
new ParallelCommandGroup(
    new SpinUpFlywheels(shooterFlywheels, 4500),
    new AdjustPivot(shooterPivot, 45)
).andThen(new Shoot(shooterFlywheels, feeder));
```

Does your robot have a pivot/angle mechanism, or is it just fixed flywheels?

---
claude-conversations-hub implementing-velocity-pid-control-for-shooter-subsystem

## Tags
#claude-conversations-hub #implementing #implementing-velocity-pid-control-for-shooter-subsystem
