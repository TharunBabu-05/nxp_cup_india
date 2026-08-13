# Copyright 2024-2026 NXP
# Apache-2.0 License
#
# FIXED: Committed intersection turns, active patient-seek state,
#        strong sign-directed navigation, no more looping.

import rclpy
from rclpy.node import Node
import math, time
from sensor_msgs.msg import Joy, LaserScan
from std_msgs.msg import String
from synapse_msgs.msg import EdgeVectors, ServerCommunication

# ═══════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
PI = math.pi

SPEED_MAX      = 1.0
SPEED_NORMAL   = 0.20
SPEED_TURN     = 0.12
SPEED_SLOW     = 0.09
SPEED_CREEP    = 0.06
SPEED_STOP     = 0.0

KP_LANE        = 0.010   # proportional gain
KD_LANE        = 0.003   # derivative gain
MAX_STEER      = 0.80
STEER_ALPHA    = 0.30    # low-pass coefficient

# LiDAR
LIDAR_STOP_DIST  = 0.22   # emergency stop - very close (was 0.35, too sensitive)
LIDAR_SLOW_DIST  = 0.55   # start slowing down
LIDAR_FRONT_HALF = 20    # ±deg around front (narrower = less false triggers on walls)
LIDAR_SIDE_DEG   = 15    # side sector deg

# Timings
STARTUP_GRACE_S    = 2.5
TURN_COMMIT_S      = 2.8   # hold a committed turn for this long
TURN_STEER_VAL     = 0.75  # full steer value during a committed turn
AVOIDANCE_S        = 2.0
SIGN_CONFIRM_CNT   = 1     # trust object recognizer's internal 3-frame confirmation
SIGN_COOLDOWN_S    = 6.0   # after a committed turn, ignore signs (matches lock release in detector)
QR_DWELL_S         = 2.0   # creep time before zone wait
SERVER_TIMEOUT_S   = 8.0   # re-send patient ID if no response after this many seconds

VALID_PATIENTS  = {'PATIENT_1', 'PATIENT_2', 'PATIENT_3'}
VALID_HOSPITALS = {'HOSPITAL_1', 'HOSPITAL_2', 'HOSPITAL_3'}
FAKE_HOSPITALS  = {'FAKE_HOSPITAL_1', 'FAKE_HOSPITAL_2'}

# Sign label → destination (must match detect node output)
SIGN_DEST_MAP = {
    'PATIENT_1': 'A',
    'PATIENT_2': 'B',
    'PATIENT_3': 'C',
    'HOSPITAL_1': 'X',
    'HOSPITAL_2': 'Y',
    'HOSPITAL_3': 'Z',
}

# ═══════════════════════════════════════════════════════════════════
#  STATES
# ═══════════════════════════════════════════════════════════════════
class S:
    STARTUP              = 'STARTUP'
    SEEK_PATIENT         = 'SEEK_PATIENT'       # navigating toward next patient
    COMMITTED_TURN       = 'COMMITTED_TURN'     # executing a sign-directed turn
    AVOID_OBSTACLE       = 'AVOID_OBSTACLE'
    PATIENT_QR_SEEN      = 'PATIENT_QR_SEEN'
    PATIENT_ZONE_WAIT    = 'PATIENT_ZONE_WAIT'
    WAIT_HOSPITAL        = 'WAIT_HOSPITAL'
    SEEK_HOSPITAL        = 'SEEK_HOSPITAL'      # navigating toward assigned hospital
    HOSPITAL_QR_SEEN     = 'HOSPITAL_QR_SEEN'
    HOSPITAL_ZONE_WAIT   = 'HOSPITAL_ZONE_WAIT'
    WAIT_NEXT_PATIENT    = 'WAIT_NEXT_PATIENT'
    MISSION_COMPLETE     = 'MISSION_COMPLETE'
    PARKING              = 'PARKING'
    STOPPED              = 'STOPPED'


# ═══════════════════════════════════════════════════════════════════
#  NODE
# ═══════════════════════════════════════════════════════════════════
class LineFollower(Node):

    def __init__(self):
        super().__init__('line_follower')

        # Subscriptions
        self.create_subscription(EdgeVectors, '/edge_vectors',
                                 self._cb_vectors, 10)
        self.create_subscription(LaserScan, '/scan',
                                 self._cb_lidar, 10)
        self.create_subscription(ServerCommunication, '/ServerCommunication',
                                 self._cb_server, 10)
        self.create_subscription(String, '/qr_detection',
                                 self._cb_qr, 10)
        self.create_subscription(String, '/sign_board_detection',
                                 self._cb_sign, 10)

        # Publishers
        self.pub_joy    = self.create_publisher(Joy, '/cerebri/in/joy', 10)
        self.pub_server = self.create_publisher(
            ServerCommunication, '/ServerCommunication', 10)

        # Lane state
        self._steer_filt = 0.0
        self._prev_err   = 0.0
        self._speed_cmd  = SPEED_STOP
        self._steer_cmd  = 0.0

        # LiDAR
        self._front_dist = 99.0
        self._left_dist  = 99.0
        self._right_dist = 99.0

        # Sign buffer (for confirmation)
        self._sign_buf_dest  = ''
        self._sign_buf_dir   = ''
        self._sign_buf_cnt   = 0
        self._last_sign_dest = ''
        self._last_sign_dir  = ''
        self._sign_lock_until = 0.0  # epoch time: ignore signs until this time

        # Committed turn state
        self._turn_steer      = 0.0
        self._turn_end_t      = 0.0
        self._pre_turn_state  = S.SEEK_PATIENT

        # Avoidance state
        self._avoid_steer    = 0.0
        self._avoid_end_t    = 0.0
        self._pre_avoid_state= S.SEEK_PATIENT

        # Mission state
        self._state           = S.STARTUP
        self._state_enter_t   = time.time()
        self._start_t         = time.time()

        self._uid_ctr         = 10
        self._pending_uid     = None
        self._server_sent_t   = 0.0

        self._current_patient  = 'PATIENT_1'  # we always seek patient 1 first
        self._assigned_hospital= None
        self._seen_hosp_qr     = None
        self._patients_done    = 0
        self._zone_enter_t     = 0.0
        self._last_tx_time     = 0.0
        self._wait_hosp_start  = 0.0

        self.create_timer(0.1, self._loop)
        self.get_logger().info('[MISSION] Started — will seek PATIENT_1')

    # ──────────────────────────────────────────────────────────────
    #  UTILITIES
    # ──────────────────────────────────────────────────────────────
    def _publish(self):
        msg = Joy()
        msg.buttons = [1, 0, 0, 0, 0, 0, 0, 1]
        msg.axes    = [0.0, float(self._speed_cmd), 0.0, float(self._steer_cmd)]
        self.pub_joy.publish(msg)

    def _drive(self, speed, steer):
        self._speed_cmd = max(min(float(speed), SPEED_MAX), -SPEED_MAX)
        self._steer_cmd = max(min(float(steer), 1.0), -1.0)

    def _set_state(self, s):
        if s != self._state:
            self.get_logger().info(f'[MISSION] {self._state} → {s}')
        self._state         = s
        self._state_enter_t = time.time()

    def _uid(self):
        self._uid_ctr = (self._uid_ctr + 1) % 256
        return self._uid_ctr

    def _send_server(self, text):
        u = self._uid()
        m = ServerCommunication()
        m.src = 1; m.dest = 2; m.uid = u; m.ack = 0; m.msg = text
        self.pub_server.publish(m)
        self._pending_uid   = u
        self._server_sent_t = time.time()
        self.get_logger().info(f'[SERVER] → uid={u} "{text}"')

    def _ack(self, uid):
        m = ServerCommunication()
        m.src = 1; m.dest = 2; m.uid = uid; m.ack = 1; m.msg = ''
        self.pub_server.publish(m)

    # ──────────────────────────────────────────────────────────────
    #  LANE VECTOR CALLBACK
    # ──────────────────────────────────────────────────────────────
    def _cb_vectors(self, msg):
        w  = float(msg.image_width)
        hw = w / 2.0

        if msg.vector_count == 0:
            return   # hold last steer

        if msg.vector_count == 1:
            v   = msg.vector_1
            cx  = (v[0].x + v[1].x) / 2.0
            # Estimate where the midpoint should be (assume lane width ~300px)
            if cx > hw:
                mid = cx - 150.0  # Line on right, mid is to the left
            else:
                mid = cx + 150.0  # Line on left, mid is to the right
            err = hw - mid
        else:
            v1  = msg.vector_1
            v2  = msg.vector_2
            cx1 = (v1[0].x + v1[1].x) / 2.0
            cx2 = (v2[0].x + v2[1].x) / 2.0
            mid = (cx1 + cx2) / 2.0
            err = hw - mid  # positive → steer left

        deriv         = err - self._prev_err
        self._prev_err = err
        raw = KP_LANE * err + KD_LANE * deriv
        raw = max(min(raw, MAX_STEER), -MAX_STEER)
        self._steer_filt = STEER_ALPHA * raw + (1 - STEER_ALPHA) * self._steer_filt

    # ──────────────────────────────────────────────────────────────
    #  LIDAR CALLBACK
    # ──────────────────────────────────────────────────────────────
    def _cb_lidar(self, msg):
        n = len(msg.ranges)
        if n == 0:
            return

        def sec(center_deg, half_deg):
            ci   = int(center_deg / 360.0 * n) % n
            hi   = max(1, int(half_deg / 360.0 * n))
            vals = []
            for i in range(-hi, hi + 1):
                r = msg.ranges[(ci + i) % n]
                if math.isfinite(r) and r > 0.02:
                    vals.append(r)
            return min(vals) if vals else 99.0

        self._front_dist = sec(180, LIDAR_FRONT_HALF)
        self._left_dist  = sec(270, LIDAR_SIDE_DEG)
        self._right_dist = sec(90,  LIDAR_SIDE_DEG)

    # ──────────────────────────────────────────────────────────────
    #  SERVER CALLBACK
    # ──────────────────────────────────────────────────────────────
    def _cb_server(self, msg):
        if msg.dest != 1:
            return
        payload = (msg.msg or '').strip().upper()
        self.get_logger().info(
            f'[SERVER] ← uid={msg.uid} ack={msg.ack} "{payload}"')

        # Quick ACK for our outbound message
        if msg.ack == 1 and msg.uid == self._pending_uid:
            return

        if self._state == S.WAIT_HOSPITAL and payload in VALID_HOSPITALS:
            self._assigned_hospital = payload
            self._ack(msg.uid)
            self.get_logger().info(f'[SERVER] Hospital: {payload}')
            self._set_state(S.SEEK_HOSPITAL)
            return

        if self._state == S.WAIT_NEXT_PATIENT:
            if payload in VALID_PATIENTS:
                self._current_patient   = payload
                self._assigned_hospital = None
                self._seen_hosp_qr      = None
                self._ack(msg.uid)
                self._patients_done += 1
                self.get_logger().info(
                    f'[SERVER] Next patient: {payload} '
                    f'(delivered={self._patients_done})')
                if self._patients_done >= 3:
                    self._set_state(S.MISSION_COMPLETE)
                else:
                    self._set_state(S.SEEK_PATIENT)
                return
            elif payload == 'INVALID':
                self.get_logger().warn('[SERVER] INVALID delivery — staying')
                return

        if self._state == S.PARKING and payload in ('OK', 'PARKED'):
            self._set_state(S.STOPPED)

    # ──────────────────────────────────────────────────────────────
    #  QR CALLBACK
    # ──────────────────────────────────────────────────────────────
    def _cb_qr(self, msg):
        code = (msg.data or '').strip().upper()
        self.get_logger().info(f'[QR] {code}')

        if code in FAKE_HOSPITALS:
            self.get_logger().warn('[QR] Fake hospital — ignored')
            return

        if code in VALID_PATIENTS:
            if self._state in (S.SEEK_PATIENT, S.COMMITTED_TURN, S.STARTUP):
                if code == self._current_patient:
                    self._zone_enter_t = time.time()
                    self._set_state(S.PATIENT_QR_SEEN)
                else:
                    self.get_logger().info(f'[QR] Ignored {code} (Seeking {self._current_patient})')

        elif code in VALID_HOSPITALS:
            if self._state in (S.SEEK_HOSPITAL, S.COMMITTED_TURN):
                if self._assigned_hospital and self._assigned_hospital != 'HOSPITAL' and code != self._assigned_hospital:
                    self.get_logger().warn(
                        f'[QR] Wrong hospital {code}≠{self._assigned_hospital}')
                    return
                self._seen_hosp_qr = code
                self._zone_enter_t = time.time()
                self._set_state(S.HOSPITAL_QR_SEEN)

    # ──────────────────────────────────────────────────────────────
    #  SIGN CALLBACK
    # ──────────────────────────────────────────────────────────────
    def _cb_sign(self, msg):
        """
        Receive sign detections formatted as "DESTINATION:DIRECTION"
        e.g. "PATIENT_1:LEFT"  or  "HOSPITAL_2:RIGHT"
        Only act when we are actively seeking that destination.
        """
        raw = (msg.data or '').strip()
        parts = raw.split(':')
        if len(parts) != 2:
            return
        dest, direction = parts[0].strip(), parts[1].strip().upper()

        now = time.time()
        if now < self._sign_lock_until:
            return  # in cooldown after a committed turn

        # Buffer confirmation
        if dest == self._sign_buf_dest and direction == self._sign_buf_dir:
            self._sign_buf_cnt += 1
        else:
            self._sign_buf_dest = dest
            self._sign_buf_dir  = direction
            self._sign_buf_cnt  = 1

        if self._sign_buf_cnt < SIGN_CONFIRM_CNT:
            return

        # Determine the valid target for the current seek state
        if self._state in (S.SEEK_PATIENT, S.COMMITTED_TURN, S.STARTUP, S.PATIENT_QR_SEEN):
            target = self._current_patient  # e.g. 'PATIENT_1' from server, or we accept any
            # Accept ANY patient sign if we're in generic patient-seeking mode
            patient_seeking = True
        else:
            target = self._assigned_hospital  # e.g. 'HOSPITAL_3' from server, or 'HOSPITAL'
            patient_seeking = False

        if patient_seeking:
            if not dest.startswith('PATIENT'):
                return  # we want patient signs, not hospital signs
            # Accept the specific patient we're seeking, OR any patient if target is generic
            if target and not target.startswith('PATIENT'):
                return
            if target and target.startswith('PATIENT') and dest != target:
                return  # sign is for a different patient
        else:
            if not dest.startswith('HOSPITAL'):
                return  # we want hospital signs, not patient signs
            # Accept the specific hospital assigned, OR any hospital if target is generic
            if target and target != 'HOSPITAL' and dest != target:
                return  # sign is for a different hospital

        if direction == 'STRAIGHT':
            return   # no turn needed, keep lane following

        # Commit to this turn
        self._commit_turn(direction, now)

    def _commit_turn(self, direction, now=None):
        now = now or time.time()
        steer = TURN_STEER_VAL if direction == 'LEFT' else -TURN_STEER_VAL
        self._turn_steer      = steer
        self._turn_end_t      = now + TURN_COMMIT_S
        self._sign_lock_until = now + SIGN_COOLDOWN_S
        self._pre_turn_state  = self._state
        self._sign_buf_cnt    = 0
        self.get_logger().info(
            f'[SIGN] Committed {direction} steer={steer:.2f} '
            f'for {TURN_COMMIT_S}s toward {self._sign_buf_dest}')
        self._set_state(S.COMMITTED_TURN)

    # ──────────────────────────────────────────────────────────────
    #  LANE SPEED HELPER
    # ──────────────────────────────────────────────────────────────
    def _lane_speed(self, steer):
        a = abs(steer)
        if a > 0.50:
            return SPEED_TURN
        elif a > 0.25:
            return SPEED_SLOW
        return SPEED_NORMAL

    # ──────────────────────────────────────────────────────────────
    #  OBSTACLE CHECK
    # ──────────────────────────────────────────────────────────────
    def _obstacle_check(self, current_state):
        """Returns True if we triggered avoidance."""
        if self._front_dist > LIDAR_SLOW_DIST:
            return False
        if self._front_dist < LIDAR_STOP_DIST:
            self._drive(SPEED_STOP, 0.0)
            self.get_logger().warn(
                f'[OBSTACLE] STOP front={self._front_dist:.2f}m')
            return True
        # Choose avoidance direction
        avoid = TURN_STEER_VAL if self._left_dist > self._right_dist else -TURN_STEER_VAL
        self._avoid_steer     = avoid
        self._avoid_end_t     = time.time() + AVOIDANCE_S
        self._pre_avoid_state = current_state
        self.get_logger().warn(
            f'[OBSTACLE] Avoid {"L" if avoid>0 else "R"} '
            f'front={self._front_dist:.2f}m')
        self._set_state(S.AVOID_OBSTACLE)
        return True

    # ──────────────────────────────────────────────────────────────
    #  MAIN LOOP (10 Hz)
    # ──────────────────────────────────────────────────────────────
    def _loop(self):
        now = time.time()

        # ── STOPPED ───────────────────────────────────────────────
        if self._state == S.STOPPED:
            self._drive(SPEED_STOP, 0.0)
            self._publish()
            return

        # ── STARTUP ───────────────────────────────────────────────
        if self._state == S.STARTUP:
            elapsed = now - self._start_t
            self._drive(SPEED_SLOW, self._steer_filt)
            self._publish()
            if elapsed > STARTUP_GRACE_S:
                self.get_logger().info(
                    f'[MISSION] Seeking {self._current_patient}')
                self._set_state(S.SEEK_PATIENT)
            return

        # ── MISSION COMPLETE → PARKING ────────────────────────────
        if self._state == S.MISSION_COMPLETE:
            self.get_logger().info('[MISSION] All delivered → PARKING')
            self._set_state(S.PARKING)
            return

        # ── PARKING ───────────────────────────────────────────────
        if self._state == S.PARKING:
            dt = now - self._state_enter_t
            if dt < 3.0:
                self._drive(SPEED_CREEP, 0.0)
            else:
                self._drive(SPEED_STOP, 0.0)
                if 3.2 < dt < 3.4:
                    self._send_server('PARKED')
            self._publish()
            return

        # ── OBSTACLE AVOIDANCE ────────────────────────────────────
        if self._state == S.AVOID_OBSTACLE:
            if now < self._avoid_end_t and self._front_dist > LIDAR_STOP_DIST:
                self._drive(SPEED_SLOW, self._avoid_steer)
            else:
                self.get_logger().info('[AVOID] Done — back to lane')
                self._set_state(self._pre_avoid_state)
            self._publish()
            return

        # ── COMMITTED TURN ────────────────────────────────────────
        if self._state == S.COMMITTED_TURN:
            if now < self._turn_end_t:
                # Obstacle check during turn
                if self._front_dist < LIDAR_STOP_DIST:
                    self._drive(SPEED_STOP, 0.0)
                else:
                    self._drive(SPEED_TURN, self._turn_steer)
            else:
                self.get_logger().info('[SIGN] Turn complete — back to seek')
                # Return to the appropriate seek state
                if self._assigned_hospital:
                    self._set_state(S.SEEK_HOSPITAL)
                else:
                    self._set_state(S.SEEK_PATIENT)
            self._publish()
            return

        # ── PATIENT QR SEEN ───────────────────────────────────────
        if self._state == S.PATIENT_QR_SEEN:
            self._drive(SPEED_CREEP, self._steer_filt)
            if now - self._zone_enter_t >= QR_DWELL_S:
                self._set_state(S.PATIENT_ZONE_WAIT)
            self._publish()
            return

        # ── PATIENT ZONE WAIT ─────────────────────────────────────
        if self._state == S.PATIENT_ZONE_WAIT:
            self._drive(SPEED_STOP, 0.0)
            dt = now - self._state_enter_t
            if dt < 0.5:
                self._publish()
                return
            # Re-send if timed out
            if (now - self._server_sent_t > SERVER_TIMEOUT_S
                    or self._server_sent_t == 0.0):
                self._send_server(self._current_patient)
                self.get_logger().info(
                    f'[SERVER] Sending patient: {self._current_patient}')
                self._wait_hosp_start = time.time()
                self._set_state(S.WAIT_HOSPITAL)
            self._publish()
            return

        # ── WAIT FOR HOSPITAL ─────────────────────────────────────
        if self._state == S.WAIT_HOSPITAL:
            self._drive(SPEED_STOP, 0.0)
            if now - self._server_sent_t > SERVER_TIMEOUT_S:
                self.get_logger().warn('[SERVER] Timeout — resending patient')
                self._send_server(self._current_patient)
            
            # Fallback to nearest hospital if server never replies
            if getattr(self, '_wait_hosp_start', 0) > 0 and now - self._wait_hosp_start > 5.0:
                self.get_logger().warn('[FSM] Server timeout! Going to nearest HOSPITAL.')
                self._assigned_hospital = 'HOSPITAL'
                self._set_state(S.SEEK_HOSPITAL)
                
            self._publish()
            return

        # ── SEEK HOSPITAL ─────────────────────────────────────────
        if self._state == S.SEEK_HOSPITAL:
            if self._obstacle_check(S.SEEK_HOSPITAL):
                self._publish()
                return
            s = self._steer_filt
            self._drive(self._lane_speed(s), s)
            self._publish()
            return

        # ── HOSPITAL QR SEEN ──────────────────────────────────────
        if self._state == S.HOSPITAL_QR_SEEN:
            self._drive(SPEED_CREEP, self._steer_filt)
            if now - self._zone_enter_t >= QR_DWELL_S:
                self._set_state(S.HOSPITAL_ZONE_WAIT)
            self._publish()
            return

        # ── HOSPITAL ZONE WAIT ────────────────────────────────────
        if self._state == S.HOSPITAL_ZONE_WAIT:
            self._drive(SPEED_STOP, 0.0)
            hosp = self._seen_hosp_qr
            if not hosp:
                self._publish()
                return
            # Accept if this hospital matches or the assigned was generic 'HOSPITAL'
            assigned = self._assigned_hospital or 'HOSPITAL'
            if hosp != assigned and assigned != 'HOSPITAL':
                self.get_logger().error(
                    f'[DELIVERY] WRONG {hosp}≠{self._assigned_hospital}')
                self._seen_hosp_qr = None
                self._set_state(S.SEEK_HOSPITAL)
                self._publish()
                return
            # Correct hospital! Update assigned to the real one
            self._assigned_hospital = hosp
            dt = now - self._state_enter_t
            if dt < 0.5:
                self._publish()
                return
            if (now - self._server_sent_t > SERVER_TIMEOUT_S
                    or self._server_sent_t == 0.0):
                self.get_logger().info(
                    f'[DELIVERY] Correct! Sending {hosp}')
                self._send_server(hosp)
                self._set_state(S.WAIT_NEXT_PATIENT)
            self._publish()
            return

        # ── WAIT NEXT PATIENT ─────────────────────────────────────
        if self._state == S.WAIT_NEXT_PATIENT:
            self._drive(SPEED_STOP, 0.0)
            if now - self._server_sent_t > SERVER_TIMEOUT_S:
                retry = getattr(self, '_wait_next_retry', 0)
                if retry >= 3:
                    # After 3 retries (~24s), auto-advance to next patient
                    self._patients_done += 1
                    self._wait_next_retry = 0
                    if self._patients_done >= 3:
                        self.get_logger().warn('[FSM] 3 patients done → MISSION_COMPLETE')
                        self._set_state(S.MISSION_COMPLETE)
                    else:
                        # Advance to next patient in sequence
                        seq = ['PATIENT_1', 'PATIENT_2', 'PATIENT_3']
                        next_p = seq[self._patients_done] if self._patients_done < len(seq) else None
                        if next_p:
                            self._current_patient = next_p
                            self._assigned_hospital = None
                            self._seen_hosp_qr = None
                            self.get_logger().warn(
                                f'[FSM] No server reply — auto-advancing to {next_p}')
                            self._set_state(S.SEEK_PATIENT)
                else:
                    self.get_logger().warn(
                        f'[SERVER] Timeout waiting next patient (retry {retry+1}/3)')
                    self._send_server(self._seen_hosp_qr or 'DONE')
                    self._wait_next_retry = retry + 1
            self._publish()
            return

        # ── SEEK PATIENT (default) ────────────────────────────────
        if self._obstacle_check(S.SEEK_PATIENT):
            self._publish()
            return
        s = self._steer_filt
        self._drive(self._lane_speed(s), s)
        self._publish()


# ═══════════════════════════════════════════════════════════════════
def main(args=None):
    rclpy.init(args=args)
    node = LineFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()