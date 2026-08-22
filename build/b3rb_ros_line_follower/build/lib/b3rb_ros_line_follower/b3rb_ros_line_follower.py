# Copyright 2024-2026 NXP
# Apache-2.0 License
#
# FIXED: Committed intersection turns, active patient-seek state,
#        strong sign-directed navigation, no more looping.
#
# MERGE NOTE: Obstacle avoidance ported from the earlier "committed timed
# steer" implementation (proven reliable) to replace the camera-PID lane-hug
# approach, which could stall waiting for LiDAR front_dist to clear. Sign /
# junction navigation logic is unchanged.

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
SPEED_NORMAL   = 0.40
SPEED_TURN     = 0.12
SPEED_SLOW     = 0.09
SPEED_CREEP    = 0.06
SPEED_STOP     = 0.0

KP_LANE        = 0.010   # proportional gain
KD_LANE        = 0.003   # derivative gain
MAX_STEER      = 0.80
STEER_ALPHA    = 0.30    # low-pass coefficient

# LiDAR
LIDAR_STOP_DIST       = 0.22   # emergency stop - very close
LIDAR_SLOW_DIST       = 0.40   # obstacle detection threshold (was 0.55, too sensitive for track curves)
LIDAR_FRONT_HALF      = 15    # ±deg around front (narrower = fewer false triggers on walls)
LIDAR_SIDE_DEG        = 15    # side sector deg
OBSTACLE_PERSIST_CNT  = 3     # consecutive LiDAR ticks before triggering avoidance (filters track-wall noise)

# Timings
STARTUP_GRACE_S       = 2.5
TURN_COMMIT_S         = 3.0
TURN_STEER_VAL        = 1.0
AVOIDANCE_S           = 2.0    # duration of the committed obstacle-avoidance steer
OBSTACLE_AVOID_STEER  = 0.75   # fixed steer magnitude used during obstacle avoidance (proven-reliable value)
SIGN_CONFIRM_CNT      = 2     # consecutive frames to confirm a sign
SIGN_COOLDOWN_S       = 8.0   # MUST be > LOCK_RELEASE_S in detect node (6s) to prevent re-arm
SIGN_TO_JUNCTION_MIN_S = 1.5  # min seconds after FIRST sign sight before junction can fire
JUNCTION_TIMEOUT_S    = 8.0   # safety: clear junction nav if stuck for this long
JUNCTION_DETECT_COUNT = 4     # consecutive frames confirming junction geometry
LANE_HUG_OFFSET       = 135.0  # px: how close to hug the lane edge while seeking a junction
QR_DWELL_S            = 2.0
SERVER_TIMEOUT_S      = 8.0

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
        self._front_dist  = 99.0
        self._left_dist   = 99.0
        self._right_dist  = 99.0
        self._obstacle_cnt = 0   # consecutive frames seeing an obstacle (filters false positives)

        # Sign buffer (for confirmation)
        self._sign_buf_dest  = ''
        self._sign_buf_dir   = ''
        self._sign_buf_cnt   = 0
        self._last_sign_dest = ''
        self._last_sign_dir  = ''
        self._sign_lock_until = 0.0  # epoch time: ignore signs until this time

        # Pending direction: remembered from sign board, executed at junction
        self._pending_direction = None   # 'LEFT' / 'RIGHT' / 'STRAIGHT' — waiting for junction
        self._pending_dest      = None   # e.g. 'PATIENT_1' the pending dir belongs to
        self._sign_seen_t       = 0.0    # when sign was stored
        self._sign_lock_until   = 0.0    # cooldown end time
        self._sign_buffer       = {}     # buffer for multi-sign confirmation

        # Junction navigation state
        self._junction_active   = False   # True while steering through a junction
        self._junction_start_t  = 0.0    # when junction nav started (for timeout)
        self._last_vec_count    = 2      # last known vector count
        self._junction_detect_cnt = 0    # frames since 0 or 1 vector detected

        # Committed turn state
        self._turn_steer      = 0.0
        self._turn_end_t      = 0.0
        self._pre_turn_state  = S.SEEK_PATIENT

        # Avoidance state (committed timed steer — ported from the proven implementation)
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
        """Lane vector callback — handles PID following + camera-guided junction turning.

        When a sign direction is set (_pending_direction):
          - The buggy drifts toward the correct side of its current lane (hug left or right).
          - The moment a new lane appears on that side (vector_count goes from 1 to 2,
            with a line on the expected side), the buggy naturally follows it.
          - No timer, no blind commit — the camera confirms the turn at every step.

        NOTE: Obstacle avoidance no longer biases this PID — it now uses a fixed,
        timed steer command issued directly in the AVOID_OBSTACLE state (see _loop),
        which overrides whatever this callback computes for the duration of the maneuver.
        """
        w   = float(msg.image_width)
        hw  = w / 2.0
        now = time.time()
        self._last_vec_count = msg.vector_count

        # ── No lines at all — hold last steer ─────────────────────────
        if msg.vector_count == 0:
            return

        # ── Extract lane line centers ──────────────────────────────────
        v1  = msg.vector_1
        cx1 = (v1[0].x + v1[1].x) / 2.0

        if msg.vector_count == 1:
            # Only one line visible. Use it as a reference with an assumed offset.
            if cx1 > hw:
                # Right line only
                cx_left  = None
                cx_right = cx1
            else:
                # Left line only
                cx_left  = cx1
                cx_right = None
        else:
            v2   = msg.vector_2
            cx2  = (v2[0].x + v2[1].x) / 2.0
            # Sort: lower x = left line, higher x = right line
            if cx1 < cx2:
                cx_left, cx_right = cx1, cx2
            else:
                cx_left, cx_right = cx2, cx1

        # ── Compute PID target mid-point ───────────────────────────────
        # Priority: sign-directed junction hug → normal following
        hug_dir = (
            self._pending_direction
            if self._pending_direction and now - self._sign_seen_t >= SIGN_TO_JUNCTION_MIN_S
            else None
        )

        if hug_dir == 'LEFT':
            # Hug left: track the left line edge
            if cx_left is not None:
                mid = cx_left + LANE_HUG_OFFSET
            else:
                mid = cx_right - LANE_HUG_OFFSET if cx_right is not None else hw

        elif hug_dir == 'RIGHT':
            # Hug right: track the right line edge
            if cx_right is not None:
                mid = cx_right - LANE_HUG_OFFSET
            else:
                mid = cx_left + LANE_HUG_OFFSET if cx_left is not None else hw

        elif msg.vector_count == 1:
            # Normal single-line following (no bias)
            if cx_right is not None:
                mid = cx_right - 150.0
            else:
                mid = cx_left + 150.0
        else:
            # Normal two-line following: stay in the middle
            mid = (cx_left + cx_right) / 2.0

        err               = hw - mid
        deriv             = err - self._prev_err
        self._prev_err    = err
        raw               = KP_LANE * err + KD_LANE * deriv
        raw               = max(min(raw, MAX_STEER), -MAX_STEER)
        self._steer_filt  = STEER_ALPHA * raw + (1 - STEER_ALPHA) * self._steer_filt

        # ── Junction detection: lane re-acquired on the target side ───
        if self._pending_direction and now - self._sign_seen_t >= SIGN_TO_JUNCTION_MIN_S:

            if self._pending_direction == 'STRAIGHT':
                # No lane change needed — just clear and continue straight in lane center
                self._junction_detect_cnt = 0
                self._sign_lock_until = now + SIGN_COOLDOWN_S
                self._sign_buffer.clear()
                self.get_logger().info(
                    f'[JUNCTION] ✓ STRAIGHT — continuing in lane center toward {self._pending_dest}')
                self._pending_direction = None
                self._pending_dest      = None
                return

            # For LEFT/RIGHT: wait until the buggy has naturally entered the new lane.
            # A real junction lane is clearly offset from the straight-ahead centre.
            if msg.vector_count == 2:
                entered_left  = (self._pending_direction == 'LEFT'  and cx_left  is not None and cx_left  < hw * 0.6)
                entered_right = (self._pending_direction == 'RIGHT' and cx_right is not None and cx_right > hw * 1.4)

                if entered_left or entered_right:
                    self._junction_detect_cnt += 1
                    self.get_logger().debug(
                        f'[JUNCTION] Lane re-acquired cnt={self._junction_detect_cnt}/{JUNCTION_DETECT_COUNT} '
                        f'dir={self._pending_direction} cxL={cx_left} cxR={cx_right}')
                    if self._junction_detect_cnt >= JUNCTION_DETECT_COUNT:
                        self._junction_detect_cnt = 0
                        self._sign_lock_until = now + SIGN_COOLDOWN_S
                        self._sign_buffer.clear()
                        self.get_logger().info(
                            f'[JUNCTION] ✓ Entered new lane toward {self._pending_dest}')
                        self._pending_direction = None
                        self._pending_dest      = None
                else:
                    self._junction_detect_cnt = 0


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

        IMPORTANT: The detect node re-publishes the same locked sign for up to 6 seconds.
        We must NOT reset _sign_seen_t or _junction_detect_cnt on repeated publications
        of the same sign, or the junction timer will never progress.
        """
        raw = (msg.data or '').strip()
        parts = raw.split(':')
        if len(parts) != 2:
            return
        dest, direction = parts[0].strip(), parts[1].strip().upper()

        now = time.time()
        if now < self._sign_lock_until:
            return  # in cooldown after a committed turn — ignore everything

        # ── Buffer / confirmation window ─────────────────────────────
        # Use a dict to track consecutive hits per-sign, in case detect node
        # publishes multiple signs (e.g. PATIENT_1 and PATIENT_2) in the same frame.
        key = f'{dest}:{direction}'
        self._sign_buffer[key] = self._sign_buffer.get(key, 0) + 1

        if self._sign_buffer[key] < SIGN_CONFIRM_CNT:
            return

        # ── Filter by what we're currently seeking ───────────────────
        if self._state in (S.SEEK_PATIENT, S.COMMITTED_TURN, S.STARTUP, S.PATIENT_QR_SEEN):
            patient_seeking = True
            target = self._current_patient
        else:
            patient_seeking = False
            target = self._assigned_hospital

        if patient_seeking:
            if not dest.startswith('PATIENT'):
                return
            if target and target.startswith('PATIENT') and dest != target:
                return  # sign is for a different patient
        else:
            if not dest.startswith('HOSPITAL'):
                return
            if target and target != 'HOSPITAL' and dest != target:
                return  # sign is for a different hospital

        # ── Lock: once a direction is committed for this destination, don't
        #    let alternating detections of the same dest flip the direction.
        #    Only a *new destination* is allowed to replace a pending direction.
        if self._pending_dest == dest and self._pending_direction is not None:
            if self._pending_direction != direction:
                # Same destination, different direction — the detect node is flickering.
                # Ignore; keep the first committed direction.
                self.get_logger().debug(
                    f'[SIGN] Ignoring flicker {dest}:{direction} '
                    f'(locked to {self._pending_direction})')
                return
            else:
                # Exact same sign repeated
                age = now - self._sign_seen_t
                self.get_logger().debug(
                    f'[SIGN] Re-pub {dest}:{direction} (age={age:.1f}s, '
                    f'jct_cnt={self._junction_detect_cnt})')
                return

        # ── Genuinely new sign (new destination or first time) — arm it ──
        old = f'{self._pending_dest}:{self._pending_direction}' if self._pending_dest else 'none'
        self._pending_direction   = direction
        self._pending_dest        = dest
        self._sign_seen_t         = now
        self._junction_detect_cnt = 0   # fresh watch for this new sign
        self._sign_buffer.clear()       # clear buffer so other signs don't accidentally confirm later
        self.get_logger().info(
            f'[SIGN] NEW {dest}:{direction} (replaced {old}) — driving to junction')

    def _commit_turn(self, direction, now=None):
        """Legacy entry point kept for compatibility. With lane-guided turning,
        all turn execution is now done by the PID itself. This just resets state."""
        now = now or time.time()
        self._sign_lock_until = now + SIGN_COOLDOWN_S
        self._sign_buffer.clear()
        self.get_logger().info(
            f'[SIGN] Direction {direction} consumed — cooldown {SIGN_COOLDOWN_S}s')
        # Do NOT enter COMMITTED_TURN state; let the PID guide the turn naturally

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
    #  (ported from the earlier, proven implementation: a committed,
    #  fixed-duration hard steer rather than a camera-PID lane hug)
    # ──────────────────────────────────────────────────────────────
    def _obstacle_check(self, current_state):
        """Returns True if we triggered avoidance.
        Requires OBSTACLE_PERSIST_CNT consecutive LiDAR ticks in the danger zone
        to filter out track wall / curve false-positives.
        """
        if self._front_dist > LIDAR_SLOW_DIST:
            self._obstacle_cnt = 0   # clear — no obstacle right now
            return False

        # Count consecutive ticks inside the danger zone
        self._obstacle_cnt += 1

        if self._front_dist < LIDAR_STOP_DIST:
            # Emergency: hard stop immediately, no need to wait
            self._obstacle_cnt = 0
            self._drive(SPEED_STOP, 0.0)
            self.get_logger().warn(
                f'[OBSTACLE] STOP front={self._front_dist:.2f}m')
            return True

        # For slow-zone: only commit to avoidance after N consecutive readings
        if self._obstacle_cnt < OBSTACLE_PERSIST_CNT:
            self.get_logger().info(
                f'[OBSTACLE] Pending ({self._obstacle_cnt}/{OBSTACLE_PERSIST_CNT}) '
                f'front={self._front_dist:.2f}m')
            return False

        # Persistent obstacle confirmed — commit to a fixed, timed avoidance steer
        self._obstacle_cnt = 0
        avoid = OBSTACLE_AVOID_STEER if self._left_dist > self._right_dist else -OBSTACLE_AVOID_STEER
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
            speed = SPEED_SLOW if self._pending_direction else self._lane_speed(s)
            self._drive(speed, s)
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
        speed = SPEED_SLOW if self._pending_direction else self._lane_speed(s)
        self._drive(speed, s)
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