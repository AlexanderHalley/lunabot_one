#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>

#include <SparkFlex.hpp>

class SparkFlexDriver : public rclcpp::Node {
public:
    SparkFlexDriver() : Node("sparkflex_driver"), x_(0.0), y_(0.0), theta_(0.0) {
        // Declare parameters
        this->declare_parameter("can_interface", "can0");
        this->declare_parameter("wheel_separation", 0.7620);  // 30 inches
        this->declare_parameter("wheel_radius", 0.1778);      // 7 inch wheels
        this->declare_parameter("max_rpm", 5700.0);
        this->declare_parameter("current_limit", 40);
        this->declare_parameter("pid_p", 0.0001);
        this->declare_parameter("pid_i", 0.0);
        this->declare_parameter("pid_d", 0.0);
        this->declare_parameter("pid_ff", 0.000176);

        // Motor CAN IDs
        this->declare_parameter("front_left_id", 1);
        this->declare_parameter("front_right_id", 2);
        this->declare_parameter("rear_left_id", 3);
        this->declare_parameter("rear_right_id", 4);

        // Get parameters
        auto can_name = this->get_parameter("can_interface").as_string();
        wheel_separation_ = this->get_parameter("wheel_separation").as_double();
        wheel_radius_ = this->get_parameter("wheel_radius").as_double();
        max_rpm_ = this->get_parameter("max_rpm").as_double();

        int current_limit = this->get_parameter("current_limit").as_int();
        double pid_p = this->get_parameter("pid_p").as_double();
        double pid_i = this->get_parameter("pid_i").as_double();
        double pid_d = this->get_parameter("pid_d").as_double();
        double pid_ff = this->get_parameter("pid_ff").as_double();

        int fl_id = this->get_parameter("front_left_id").as_int();
        int fr_id = this->get_parameter("front_right_id").as_int();
        int bl_id = this->get_parameter("rear_left_id").as_int();
        int br_id = this->get_parameter("rear_right_id").as_int();

        // Initialize motors with CAN IDs from config
        // SparkFlex handles CAN interface internally
        try {
            fl_motor_ = std::make_unique<SparkFlex>(can_name, fl_id);
            fr_motor_ = std::make_unique<SparkFlex>(can_name, fr_id);
            bl_motor_ = std::make_unique<SparkFlex>(can_name, bl_id);
            br_motor_ = std::make_unique<SparkFlex>(can_name, br_id);

            RCLCPP_INFO(this->get_logger(), "Motors initialized: FL=%d, FR=%d, BL=%d, BR=%d",
                        fl_id, fr_id, bl_id, br_id);
        } catch (const std::exception& e) {
            RCLCPP_ERROR(this->get_logger(), "Failed to initialize motors: %s", e.what());
            rclcpp::shutdown();
            return;
        }

        // Configure motors
        configureMotors(current_limit, pid_p, pid_i, pid_d, pid_ff);

        // Create subscribers
        cmd_vel_sub_ = this->create_subscription<geometry_msgs::msg::Twist>(
            "cmd_vel", 10,
            std::bind(&SparkFlexDriver::cmdVelCallback, this, std::placeholders::_1));

        // Create publishers
        odom_pub_ = this->create_publisher<nav_msgs::msg::Odometry>("odom", 10);
        joint_state_pub_ = this->create_publisher<sensor_msgs::msg::JointState>("joint_states", 10);

        // Create timer for odometry updates and heartbeat (50 Hz)
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(20),
            std::bind(&SparkFlexDriver::timerCallback, this));

        last_time_ = this->now();

        RCLCPP_INFO(this->get_logger(), "SparkFlex driver initialized successfully");
        RCLCPP_INFO(this->get_logger(), "Wheel separation: %.4f m, Wheel radius: %.4f m",
                    wheel_separation_, wheel_radius_);
    }

private:
    void configureMotors(int current_limit, double pid_p, double pid_i, double pid_d, double pid_ff) {
        std::vector<SparkFlex*> motors = {
            fl_motor_.get(), fr_motor_.get(),
            bl_motor_.get(), br_motor_.get()
        };

        for (auto* motor : motors) {
            // Set to brake mode for better control
            motor->SetIdleMode(IdleMode::kBrake);

            // Set motor type to brushless
            motor->SetMotorType(MotorType::kBrushless);

            // Set sensor type (hall sensor for NEO motors)
            motor->SetSensorType(SensorType::kHallSensor);

            // Set control type to velocity
            motor->SetCtrlType(CtrlType::kVelocity);

            // Set current limits
            motor->SetSmartCurrentStallLimit(current_limit);
            motor->SetSmartCurrentFreeLimit(current_limit);

            // Configure PID for velocity control (slot 0)
            motor->SetP(0, pid_p);
            motor->SetI(0, pid_i);
            motor->SetD(0, pid_d);
            motor->SetF(0, pid_ff);
            motor->SetOutputMin(0, -1.0);
            motor->SetOutputMax(0, 1.0);

            // Set conversion factors (keep in RPM and rotations)
            motor->SetVelocityConversionFactor(1.0);
            motor->SetPositionConversionFactor(1.0);

            // Save configuration to flash
            motor->BurnFlash();
        }

        // Invert right side motors for differential drive
        fr_motor_->SetInverted(true);
        br_motor_->SetInverted(true);

        RCLCPP_INFO(this->get_logger(), "Motors configured: Current limit=%dA, PID=(P:%.6f, FF:%.6f)",
                    current_limit, pid_p, pid_ff);
    }

    void cmdVelCallback(const geometry_msgs::msg::Twist::SharedPtr msg) {
        // Differential drive kinematics
        double linear = msg->linear.x;   // m/s
        double angular = msg->angular.z; // rad/s

        // Calculate wheel velocities in m/s
        double left_vel = linear - (angular * wheel_separation_ / 2.0);
        double right_vel = linear + (angular * wheel_separation_ / 2.0);

        // Convert m/s to RPM: vel (m/s) / (2*pi*r) * 60
        double left_rpm = (left_vel / (2.0 * M_PI * wheel_radius_)) * 60.0;
        double right_rpm = (right_vel / (2.0 * M_PI * wheel_radius_)) * 60.0;

        // Clamp to max RPM
        left_rpm = std::clamp(left_rpm, -max_rpm_, max_rpm_);
        right_rpm = std::clamp(right_rpm, -max_rpm_, max_rpm_);

        // Send velocity commands to all four motors using SetVelocity
        try {
            fl_motor_->SetVelocity(left_rpm);
            bl_motor_->SetVelocity(left_rpm);
            fr_motor_->SetVelocity(right_rpm);
            br_motor_->SetVelocity(right_rpm);
        } catch (const std::exception& e) {
            RCLCPP_ERROR_THROTTLE(this->get_logger(), *this->get_clock(), 1000,
                                  "Failed to send motor commands: %s", e.what());
        }
    }

    void timerCallback() {
        auto current_time = this->now();
        double dt = (current_time - last_time_).seconds();
        last_time_ = current_time;

        // Send heartbeat to keep motors alive
        try {
            fl_motor_->Heartbeat();
            fr_motor_->Heartbeat();
            bl_motor_->Heartbeat();
            br_motor_->Heartbeat();
        } catch (const std::exception& e) {
            RCLCPP_ERROR_THROTTLE(this->get_logger(), *this->get_clock(), 1000,
                                  "Heartbeat failed: %s", e.what());
            return;
        }

        // Read motor velocities (RPM) and calculate odometry
        try {
            double left_rpm = (fl_motor_->GetVelocity() + bl_motor_->GetVelocity()) / 2.0;
            double right_rpm = (fr_motor_->GetVelocity() + br_motor_->GetVelocity()) / 2.0;

            // Convert RPM to m/s: rpm / 60 * (2*pi*r)
            double left_vel = (left_rpm / 60.0) * (2.0 * M_PI * wheel_radius_);
            double right_vel = (right_rpm / 60.0) * (2.0 * M_PI * wheel_radius_);

            // Calculate robot velocities
            double linear_vel = (left_vel + right_vel) / 2.0;
            double angular_vel = (right_vel - left_vel) / wheel_separation_;

            // Update odometry
            double delta_x = linear_vel * cos(theta_) * dt;
            double delta_y = linear_vel * sin(theta_) * dt;
            double delta_theta = angular_vel * dt;

            x_ += delta_x;
            y_ += delta_y;
            theta_ += delta_theta;

            // Publish odometry
            publishOdometry(current_time, linear_vel, angular_vel);

            // Publish joint states
            publishJointStates(current_time);

        } catch (const std::exception& e) {
            RCLCPP_ERROR_THROTTLE(this->get_logger(), *this->get_clock(), 1000,
                                  "Failed to read motor data: %s", e.what());
        }
    }

    void publishOdometry(const rclcpp::Time& current_time, double linear_vel, double angular_vel) {
        auto odom_msg = nav_msgs::msg::Odometry();
        odom_msg.header.stamp = current_time;
        odom_msg.header.frame_id = "odom";
        odom_msg.child_frame_id = "base_link";

        // Position
        odom_msg.pose.pose.position.x = x_;
        odom_msg.pose.pose.position.y = y_;
        odom_msg.pose.pose.position.z = 0.0;

        // Orientation (quaternion from theta)
        tf2::Quaternion q;
        q.setRPY(0, 0, theta_);
        odom_msg.pose.pose.orientation = tf2::toMsg(q);

        // Covariance for pose (tune these values based on testing)
        odom_msg.pose.covariance[0] = 0.001;  // x
        odom_msg.pose.covariance[7] = 0.001;  // y
        odom_msg.pose.covariance[35] = 0.01;  // theta

        // Velocity
        odom_msg.twist.twist.linear.x = linear_vel;
        odom_msg.twist.twist.angular.z = angular_vel;

        // Covariance for twist
        odom_msg.twist.covariance[0] = 0.001;  // linear x
        odom_msg.twist.covariance[35] = 0.01;  // angular z

        odom_pub_->publish(odom_msg);
    }

    void publishJointStates(const rclcpp::Time& current_time) {
        auto joint_msg = sensor_msgs::msg::JointState();
        joint_msg.header.stamp = current_time;

        // Match joint names from URDF
        joint_msg.name = {"left_front_wheel_joint", "right_front_wheel_joint",
                          "left_wheel_joint", "right_wheel_joint"};

        // Read positions (rotations) and convert to radians
        joint_msg.position = {
            fl_motor_->GetPosition() * 2.0 * M_PI,
            fr_motor_->GetPosition() * 2.0 * M_PI,
            bl_motor_->GetPosition() * 2.0 * M_PI,
            br_motor_->GetPosition() * 2.0 * M_PI
        };

        // Read velocities (RPM) and convert to rad/s
        joint_msg.velocity = {
            fl_motor_->GetVelocity() * 2.0 * M_PI / 60.0,
            fr_motor_->GetVelocity() * 2.0 * M_PI / 60.0,
            bl_motor_->GetVelocity() * 2.0 * M_PI / 60.0,
            br_motor_->GetVelocity() * 2.0 * M_PI / 60.0
        };

        // Read currents
        joint_msg.effort = {
            fl_motor_->GetCurrent(),
            fr_motor_->GetCurrent(),
            bl_motor_->GetCurrent(),
            br_motor_->GetCurrent()
        };

        joint_state_pub_->publish(joint_msg);
    }

    // Motors (SparkFlex handles CAN internally)
    std::unique_ptr<SparkFlex> fl_motor_;
    std::unique_ptr<SparkFlex> fr_motor_;
    std::unique_ptr<SparkFlex> bl_motor_;
    std::unique_ptr<SparkFlex> br_motor_;

    // ROS2 communication
    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_sub_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
    rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr joint_state_pub_;
    rclcpp::TimerBase::SharedPtr timer_;

    // Robot parameters
    double wheel_separation_;
    double wheel_radius_;
    double max_rpm_;

    // Odometry state
    double x_, y_, theta_;
    rclcpp::Time last_time_;
};

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<SparkFlexDriver>());
    rclcpp::shutdown();
    return 0;
}
