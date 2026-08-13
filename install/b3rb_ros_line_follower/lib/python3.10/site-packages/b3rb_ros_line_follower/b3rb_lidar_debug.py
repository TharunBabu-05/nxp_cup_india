#!/usr/bin/env python3
"""
LiDAR debug utility - prints min range at each 30-degree sector.
Run this while the buggy is stationary (with no obstacle in front)
to find which angle index corresponds to the front.
"""
import rclpy
from rclpy.node import Node
import math
from sensor_msgs.msg import LaserScan


class LidarDebugger(Node):
    def __init__(self):
        super().__init__('lidar_debug')
        self.sub = self.create_subscription(
            LaserScan,
            '/world/default/model/b3rb/link/lidar_link/sensor/lidar/scan',
            self._cb,
            10
        )
        self._count = 0
        self.get_logger().info('[LIDAR DEBUG] Waiting for scan...')

    def _cb(self, msg):
        self._count += 1
        if self._count % 10 != 0:   # print every 10th scan
            return
        n = len(msg.ranges)
        self.get_logger().info(f'[LIDAR DEBUG] n={n}  angle_min={math.degrees(msg.angle_min):.1f}°  angle_max={math.degrees(msg.angle_max):.1f}°  angle_inc={math.degrees(msg.angle_increment):.2f}°')

        # Print min range for every 30-degree sector
        print('\n--- Sector mins ---')
        for deg in range(0, 360, 30):
            idx = int(deg / 360.0 * n) % n
            half = max(1, int(15 / 360.0 * n))
            vals = []
            for i in range(-half, half + 1):
                r = msg.ranges[(idx + i) % n]
                if math.isfinite(r) and r > 0.02:
                    vals.append(r)
            mn = min(vals) if vals else 99.0
            bar = '#' * max(0, int(10 - mn * 5))
            print(f'  {deg:3d}°: {mn:6.3f}m  {bar}')


def main():
    rclpy.init()
    node = LidarDebugger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
