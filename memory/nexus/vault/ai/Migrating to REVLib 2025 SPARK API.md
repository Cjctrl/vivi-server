---
tags: [user, migrating_to_revlib_2025_spark_api, claude, ai-conversation]
---



# Migrating to REVLib 2025 SPARK API

**Created:** 2026-01-17 17:25  
**Updated:** 2026-01-24 14:44

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-01-17 17:25

Summary
The 2025 version of REVLib introduced a series of breaking changes from the previous year. These changes include:
* An overhauled configuration system
* Updated import paths
* Renamed classes
For a more complete changelog, please see our 2025 beta release notes on GitHub.
Below shows how to migrate certain common tasks from previous versions of REVLib to the 2025 release.
Including the library and creating a SPARK object
In the 2025 version, all SPARK related classes moved to a `spark` package in Java and a `spark` namespace in C++.
In addition, some of the classes were renamed:
* `CANSparkMax` is now `SparkMax`
* `CANSparkFlex` is now `SparkFlex`
* `CANSparkLowLevel` is now `SparkLowLevel`
* `SparkPIDController` is now `SparkClosedLoopController `Java
Before
Copy

```
import com.revrobotics.CANSparkMax;
import com.revrobotics.CANSparkFlex;
import com.revrobotics.CANSparkLowLevel.MotorType;
import com.revrobotics.SparkPIDController;

CANSparkMax max = new CANSparkMax(1, MotorType.kBrushless);
CANSparkFlex flex = new CANSparkFlex(2, MotorType.kBrushless);
SparkPIDController maxPid = max.getPIDController();
```

After
Copy

```
import com.revrobotics.spark.SparkMax;
import com.revrobotics.spark.SparkFlex;
import com.revrobotics.spark.SparkLowLevel.MotorType;
import com.revrobotics.spark.SparkClosedLoopController;

SparkMax max = new SparkMax(1, MotorType.kBrushless);
SparkFlex flex = new SparkFlex(2, MotorType.kBrushless);
SparkClosedLoopController maxPid = max.getClosedLoopController();
```

Configuring a SPARK
Instead of imperatively configuring parameters of the SPARK by calling methods directly on it and its auxiliary objects (sensors, closed loop controller, etc.), configuration parameters are set in a more declarative way through configuration objects and applying that configuration to the SPARK.
A more complete guide on the new configuration system will soon be available.
For simplicity, only an example for SPARK MAX is provided. The following will still be valid for a SPARK Flex object.
Java
Before
Copy

```
CANSparkMax max = new CANSparkMax(1, MotorType.kBrushless);
RelativeEncoder enc = max.getEncoder();
SparkPIDController pid = max.getPIDController();

max.restoreFactoryDefaults();

max.setInverted(true);
max.setIdleMode(IdleMode.kBrake);
enc.setPositionConversionFactor(1000);
enc.setVelocityConversionFactor(1000);
pid.setFeedbackDevice(enc);
pid.setP(1.0);
pid.setI(0.0);
pid.setD(0.0);

max.burnFlash();
```

After
Copy

```
SparkMax max = new SparkMax(1, MotorType.kBrushless);
SparkMaxConfig config = new SparkMaxConfig();

config
    .inverted(true)
    .idleMode(IdleMode.kBrake);
config.encoder
    .positionConversionFactor(1000)
    .velocityConversionFactor(1000);
config.closedLoop
    .feedbackSensor(FeedbackSensor.kPrimaryEncoder)
    .pid(1.0, 0.0, 0.0);
    
max.configure(config, ResetMode.kResetSafeParameters, PersistMode.kPersistParameters);
```

Retrieving a configuration parameter from a SPARK
With the new configuration system, parameter getters moved to a `configAccessor` field in the `SparkMax` and `SparkFlex`.
For simplicity, only an example for SPARK MAX is provided. The following will still be valid for a SPARK Flex object.
Java
Before
Copy

```
CANSparkMax max = new CANSparkMax(1, MotorType.kBrushless);
RelativeEncoder enc = max.getEncoder();

boolean isInverted = max.getInverted();
double positionConversionFactor = enc.getPositionConversionFactor();
double velocityConversionFactor = enc.getVelocityConversionFactor();
```

After
Copy

```
SparkMax max = new SparkMax(1, MotorType.kBrushless);

boolean isInverted = max.configAccessor.getInverted();
double positionFactor = max.configAccessor.encoder.getPositionConversionFactor();
double velocityFactor = max.configAccessor.encoder.getVelocityConversionFactor();
```

Setting status periods
Previously, setting status periods required the user to know which periodic status frame a signal belonged to. Now, status signals' periods can be individually configured, and REVLib will handle figuring out which status frame to adjust.
These values can be configured through the new configuration system.
For simplicity, only an example for SPARK MAX is provided. The following will still be valid for a SPARK Flex object.
Java
Before
Copy

```
CANSparkMax max = new CANSparkMax(1, MotorType.kBrushless);

max.restoreFactoryDefaults();
// Adjust periodic status frame 2, which includes encoder position data
max.setPeriodicFramePeriod(PeriodicFrame.kStatus2, 5);
max.burnFlash();

double position = max.getEncoder().getPosition();
```

After
Copy

```
SparkMax max = new SparkMax(1, MotorType.kBrushless);
SparkMaxConfig config = new SparkMaxConfig();

config.signals.primaryEncoderPositionPeriodMs(5);

max.configure(config, ResetMode.kResetSafeParameters, PersistMode.kPersistParameters);

double position = max.getEncoder().getPosition();
```

fix my code with the new spark max

---

### 🤖 Claude · 2026-01-17 17:26

I'll help you update your shooter subsystem code to work with the 2025 REVLib changes. Here are the main issues I need to fix:

1. Updated import paths (moved to `spark` package)
2. Renamed `SparkPIDController` to `SparkClosedLoopController`
3. Use the new configuration system instead of imperative configuration
4. Update method calls (`getPIDController()` → `getClosedLoopController()`)
5. Fix configuration methods (use config objects instead of direct calls)
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

## Key Changes Made:

**1. Updated Imports:**
- Changed from `com.revrobotics.CANSparkMax` to `com.revrobotics.spark.SparkMax`
- Changed from `com.revrobotics.CANSparkLowLevel` to `com.revrobotics.spark.SparkLowLevel`
- Changed from `com.revrobotics.SparkPIDController` to `com.revrobotics.spark.SparkClosedLoopController`
- Added new config imports: `SparkMaxConfig`, `PersistMode`, `ResetMode`

**2. Renamed Variable:**
- Changed `m_pidController` to `m_closedLoopController` throughout

**3. New Configuration System:**
- Replaced imperative configuration calls (`setInverted()`, `setIdleMode()`, etc.) with the new declarative config objects
- Created `SparkMaxConfig` objects for both motors
- Used `configure()` method with `ResetMode` and `PersistMode` parameters
- Configured PID gains through `leadConfig.closedLoop` instead of direct `setPID()` calls
- Set up follower using `.follow()` in the config instead of calling it on the motor object

**4. Updated Method Calls:**
- Changed `getPIDController()` to `getClosedLoopController()`
- Used `velocityFF()` instead of `setFF()` for the feedforward gain
- Used `pid()` method for P, I, D gains together

**5. Updated `setIdleMode()` Method:**
- Now uses the new configuration system instead of direct method calls
- Uses `ResetMode.kNoResetSafeParameters` to avoid resetting other parameters
- Uses `PersistMode.kNoPersistParameters` for temporary changes

The code now follows the 2025 REVLib standards and should compile without errors!

---

### 🧑 CJ · 2026-01-17 17:28

do the same to this and fix

---

### 🤖 Claude · 2026-01-17 17:28

I'll update this intake subsystem to use the 2025 REVLib API. Since this file includes stub classes, I'll remove those and use the actual 2025 REVLib imports.
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

## Key Changes Made to IntakeSubsystem:

**1. Removed Stub Classes:**
- Deleted all the internal stub classes (`CANSparkMax`, `RelativeEncoder`, `SparkPIDController`, etc.)
- Now using actual 2025 REVLib imports

**2. Updated Imports:**
- Changed to `com.revrobotics.spark.SparkMax`
- Changed to `com.revrobotics.spark.SparkLowLevel.MotorType`
- Changed to `com.revrobotics.spark.SparkClosedLoopController`
- Added `SparkMaxConfig` and related config classes
- Added `PersistMode` and `ResetMode`

**3. Renamed Variables:**
- Changed `intakePIDController` to `intakeClosedLoopController`

**4. Consolidated Configuration:**
- Removed separate `configureIntakeMotors()` and `configurePIDAndSmartMotion()` logic
- Combined all configuration into a single `configureIntakeMotors()` method using the new config system
- Created `SparkMaxConfig` objects for both lead and follow motors
- All PID, Smart Motion, current limits, and motor settings now configured through config objects

**5. New Configuration System:**
- PID gains set using `leadConfig.closedLoop.pid()`
- Feed forward set using `.velocityFF()` instead of `.setFF()`
- I-Zone set using `.iZone()` instead of `.setIZone()`
- Smart Motion parameters set through config: `.smartMotionMaxVelocity()`, `.smartMotionMaxAccel()`, `.smartMotionAllowedClosedLoopError()`
- Follower configured using `.follow()` in the config instead of calling it on the motor
- Applied configuration with `configure()` method using `ResetMode.kResetSafeParameters` and `PersistMode.kPersistParameters`

**6. Updated Method Calls:**
- Changed `getPIDController()` to `getClosedLoopController()`
- All `setReference()` calls now use the `intakeClosedLoopController` variable

The code is now fully compliant with 2025 REVLib standards and removes the need for stub classes!

---
claude-conversations-hub migrating-to-revlib-2025-spark-api

## Tags
#claude-conversations-hub #migrating #migrating-to-revlib-2025-spark-api
