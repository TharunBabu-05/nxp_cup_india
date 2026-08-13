#!/usr/bin/env python3
"""
Local Municipality Server Simulator
====================================
Mimics the real competition Municipality Server.
- Listens on /ServerCommunication (src=1, dest=2)
- Responds with hospital assignment for each patient
- Responds with next patient after hospital delivery

Patient → Hospital mapping (change to match the actual competition):
  PATIENT_1 → HOSPITAL_2
  PATIENT_2 → HOSPITAL_3
  PATIENT_3 → HOSPITAL_1
"""

import rclpy
from rclpy.node import Node
import time
from synapse_msgs.msg import ServerCommunication

# ── Assignment table ─────────────────────────────────────────────────
# Modify this table to match what the actual competition server will use.
PATIENT_TO_HOSPITAL = {
    'PATIENT_1': 'HOSPITAL_2',
    'PATIENT_2': 'HOSPITAL_3',
    'PATIENT_3': 'HOSPITAL_1',
}

PATIENT_SEQUENCE = ['PATIENT_1', 'PATIENT_2', 'PATIENT_3']


class MunicipalityServer(Node):

    def __init__(self):
        super().__init__('municipality_server')
        self._sub = self.create_subscription(
            ServerCommunication,
            '/ServerCommunication',
            self._cb,
            10
        )
        self._pub = self.create_publisher(
            ServerCommunication,
            '/ServerCommunication',
            10
        )
        self._uid_ctr = 100
        self._delivered = []
        self.get_logger().info('=== Municipality Server Started ===')
        self.get_logger().info(f'Assignments: {PATIENT_TO_HOSPITAL}')

    def _uid(self):
        self._uid_ctr = (self._uid_ctr + 1) % 256
        return self._uid_ctr

    def _send(self, msg_str, dest=1, ack=0, uid=None):
        m = ServerCommunication()
        m.src  = 2
        m.dest = dest
        m.uid  = uid if uid is not None else self._uid()
        m.ack  = ack
        m.msg  = msg_str
        self._pub.publish(m)
        self.get_logger().info(
            f'[SERVER → BUGGY] uid={m.uid} ack={m.ack} msg="{msg_str}"')

    def _cb(self, msg):
        # Only handle messages addressed to the server (dest=2) from buggy (src=1)
        if msg.src != 1 or msg.dest != 2:
            return

        payload = (msg.msg or '').strip().upper()
        self.get_logger().info(
            f'[BUGGY → SERVER] uid={msg.uid} ack={msg.ack} msg="{payload}"')

        # ACK only — buggy just acknowledged our message, ignore
        if msg.ack == 1:
            return

        # ── PATIENT delivery request ─────────────────────────
        if payload.startswith('PATIENT_'):
            hospital = PATIENT_TO_HOSPITAL.get(payload)
            if hospital:
                # Wait a short moment then reply
                time.sleep(0.3)
                # ACK the patient message
                self._send('', dest=1, ack=1, uid=msg.uid)
                # Send the hospital assignment
                time.sleep(0.2)
                self._send(hospital, dest=1, ack=0)
                self.get_logger().info(
                    f'[ASSIGN] {payload} → {hospital}')
            else:
                self.get_logger().warn(f'[SERVER] Unknown patient: {payload}')
            return

        # ── HOSPITAL delivery confirmation ────────────────────
        if payload.startswith('HOSPITAL_'):
            self._delivered.append(payload)
            n = len(self._delivered)
            # ACK
            time.sleep(0.3)
            self._send('', dest=1, ack=1, uid=msg.uid)
            # Determine next patient
            remaining = [p for p in PATIENT_SEQUENCE if p not in
                         [pt for pt in PATIENT_TO_HOSPITAL
                          if PATIENT_TO_HOSPITAL[pt] in self._delivered]]
            if n >= len(PATIENT_SEQUENCE):
                self.get_logger().info('[SERVER] All patients delivered! Mission complete.')
                time.sleep(0.3)
                self._send('MISSION_COMPLETE', dest=1, ack=0)
            else:
                next_patient = PATIENT_SEQUENCE[n] if n < len(PATIENT_SEQUENCE) else None
                if next_patient:
                    time.sleep(0.5)
                    self._send(next_patient, dest=1, ack=0)
                    self.get_logger().info(
                        f'[SERVER] Next patient: {next_patient}')
            return

        # ── PARKED ────────────────────────────────────────────
        if payload in ('PARKED', 'PARKED_OK'):
            self.get_logger().info('[SERVER] Buggy parked. Mission complete!')
            time.sleep(0.3)
            self._send('OK', dest=1, ack=0)
            return


def main(args=None):
    rclpy.init(args=args)
    node = MunicipalityServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()
