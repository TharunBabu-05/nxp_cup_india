import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/sanjay/cognipilot/cranium/install/b3rb_ros_line_follower'
