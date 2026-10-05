import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
import tf2_ros
from tf2_ros import TransformException


class TCPPathPublisher(Node):
    def __init__(self):
        super().__init__('tcp_path_publisher')
        
        self.base_frame = 'base'
        self.tcp_frame = 'tool_base'
        
        self.path = Path()
        self.path.header.frame_id = self.base_frame
        
        self.path_pub = self.create_publisher(Path, '/tcp_path', 10)
        
        # TF2 listener
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        self.timer = self.create_timer(0.05, self.timer_callback)
        
        self.get_logger().info(f'TCP path publisher started for frame: {self.tcp_frame}')

    def timer_callback(self):
        try:
            # Get latest transform from base to TCP frame
            trans = self.tf_buffer.lookup_transform(self.base_frame, self.tcp_frame, rclpy.time.Time())
            
            stamp = self.get_clock().now().to_msg()
            
            pose_stamped = PoseStamped()
            pose_stamped.header.stamp = stamp
            pose_stamped.header.frame_id = self.base_frame
            pose_stamped.pose.position.x = trans.transform.translation.x
            pose_stamped.pose.position.y = trans.transform.translation.y
            pose_stamped.pose.position.z = trans.transform.translation.z
            pose_stamped.pose.orientation = trans.transform.rotation
            
            self.path.poses.append(pose_stamped)
            
            # Limit path length to prevent memory growth
            if len(self.path.poses) > 1000:
                self.path.poses.pop(0)
            
            # Update header and publish
            self.path.header.stamp = stamp
            self.path_pub.publish(self.path)
            
        except TransformException as ex:
            pass # normal at startup until TF is available

def main(args=None):    
    rclpy.init(args=args)
    
    node = TCPPathPublisher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()