import datetime
import struct

from . import crc
from . utils import *

START_OF_PACKET = 0xcc
WIFI_MSG = 0x1a
VIDEO_RATE_QUERY = 40
LIGHT_MSG = 53
FLIGHT_MSG = 0x56
LOG_MSG = 0x1050
LOG_DATA_MSG = 0x1051
LOG_CONFIG_MSG = 0x1052

VIDEO_ENCODER_RATE_CMD = 32
VIDEO_REQ_SPS_PPS_CMD = 37  # requests H.264 sequence parameter set, akin to I-frames
EXPOSURE_CMD = 52
TIME_CMD = 70
STICK_CMD = 80
TAKEOFF_CMD = 84
THROW_TAKEOFF_CMD = 93
LAND_CMD = 85
PALM_LAND_CMD = 94
FLIP_CMD = 92
FLATTRIM_CMD = 4180

FLIP_FRONT = 0
FLIP_LEFT = 1
FLIP_BACK = 2
FLIP_RIGHT = 3
FLIP_FRONT_LEFT = 4
FLIP_BACK_LEFT = 5
FLIP_BACK_RIGHT = 6
FLIP_FRONT_RIGHT = 7
FLIP_MAX_INT = 8

VIDRATE_AUTO = 0
VIDRATE_1000Kbps = 1
VIDRATE_1500Kbps = 2
VIDRATE_2000Kbps = 3
VIDRATE_2500Kbps = 4
VIDRATE_MAX_INT = 5


class Packet(object):
    def __init__(self, cmd, pkt_type=0x68):
        if isinstance(cmd, str):
            self.buf = bytearray()
            for c in cmd:
                self.buf.append(ord(c))
        elif isinstance(cmd, (bytearray, bytes)):
            self.buf = bytearray()
            self.buf[:] = cmd
        else:
            self.buf = bytearray([
                START_OF_PACKET,
                0, 0,
                0,
                pkt_type,
                (cmd & 0xff), ((cmd >> 8) & 0xff),
                0, 0])

    def fixup(self, seq_num=0):
        buf = self.get_buffer()
        if buf[0] == START_OF_PACKET:
            buf[1], buf[2] = le16(len(buf)+2)
            buf[1] = (buf[1] << 3)
            buf[3] = crc.crc8(buf[0:3])
            buf[7], buf[8] = le16(seq_num)
            self.add_int16(crc.crc16(buf))

    def get_buffer(self):
        return self.buf

    def get_data(self):
        return self.buf[9:len(self.buf)-2]

    def add_byte(self, val):
        self.buf.append(val & 0xff)

    def add_int16(self, val):
        self.add_byte(val)
        self.add_byte(val >> 8)

    def add_time(self, time=datetime.datetime.now()):
        self.add_int16(time.hour)
        self.add_int16(time.minute)
        self.add_int16(time.second)
        self.add_int16(int(time.microsecond/1000) & 0xff)
        self.add_int16((int(time.microsecond/1000) >> 8) & 0xff)

    def get_time(self, buf=None):
        if buf is None:
            buf = self.get_data()[1:]
        hour = int16(buf[0], buf[1])
        min = int16(buf[2], buf[3])
        sec = int16(buf[4], buf[5])
        millisec = int16(buf[6], buf[8])
        now = datetime.datetime.now()
        return datetime.datetime(now.year, now.month, now.day, hour, min, sec, millisec)


class FlightData(object):
    def __init__(self, data):
        self.battery_low = 0
        self.battery_lower = 0
        self.battery_percentage = 0
        self.battery_state = 0
        self.camera_state = 0
        self.down_visual_state = 0
        self.drone_battery_left = 0
        self.drone_fly_time_left = 0
        self.drone_hover = 0
        self.em_open = 0
        self.em_sky = 0
        self.em_ground = 0
        self.east_speed = 0
        self.electrical_machinery_state = 0
        self.factory_mode = 0
        self.fly_mode = 0
        self.fly_speed = 0
        self.fly_time = 0
        self.front_in = 0
        self.front_lsc = 0
        self.front_out = 0
        self.gravity_state = 0
        self.vertical_speed = 0
        self.height = 0
        self.imu_calibration_state = 0
        self.imu_state = 0
        self.light_strength = 0
        self.north_speed = 0
        self.outage_recording = 0
        self.power_state = 0
        self.pressure_state = 0
        self.smart_video_exit_mode = 0
        self.temperature_height = 0
        self.throw_fly_timer = 0
        self.wifi_disturb = 0
        self.wifi_strength = 0
        self.wind_state = 0

        if len(data) < 24:
            return

        self.height = int16(data[0], data[1])
        self.north_speed = int16(data[2], data[3])
        self.east_speed = int16(data[4], data[5])
        self.vertical_speed = int16(data[6], data[7])
        self.fly_time = int16(data[8], data[9])

        self.imu_state = ((data[10] >> 0) & 0x1)
        self.pressure_state = ((data[10] >> 1) & 0x1)
        self.down_visual_state = ((data[10] >> 2) & 0x1)
        self.power_state = ((data[10] >> 3) & 0x1)
        self.battery_state = ((data[10] >> 4) & 0x1)
        self.gravity_state = ((data[10] >> 5) & 0x1)
        self.wind_state = ((data[10] >> 7) & 0x1)

        self.imu_calibration_state = data[11]
        self.battery_percentage = data[12]
        self.drone_fly_time_left = int16(data[13], data[14])
        self.drone_battery_left = int16(data[15], data[16])

        self.em_sky = ((data[17] >> 0) & 0x1)
        self.em_ground = ((data[17] >> 1) & 0x1)
        self.em_open = ((data[17] >> 2) & 0x1)
        self.drone_hover = ((data[17] >> 3) & 0x1)
        self.outage_recording = ((data[17] >> 4) & 0x1)
        self.battery_low = ((data[17] >> 5) & 0x1)
        self.battery_lower = ((data[17] >> 6) & 0x1)
        self.factory_mode = ((data[17] >> 7) & 0x1)

        self.fly_mode = data[18]
        self.throw_fly_timer = data[19]
        self.camera_state = data[20]
        self.electrical_machinery_state = data[21]

        self.front_in = ((data[22] >> 0) & 0x1)
        self.front_out = ((data[22] >> 1) & 0x1)
        self.front_lsc = ((data[22] >> 2) & 0x1)

        self.temperature_height = ((data[23] >> 0) & 0x1)

    def __str__(self):
        return (
            ("height=%2d" % self.height) +
            (", fly_mode=0x%02x" % self.fly_mode) +
            (", battery_percentage=%2d" % self.battery_percentage) +
            (", drone_battery_left=0x%04x" % self.drone_battery_left) +
            "")
            
class LogData(object):
    ID_NEW_MVO_FEEDBACK                = 29
    ID_IMU_ATTI                        = 2048
    unknowns = []

    def __init__(self, log, data = None):
        self.log = log
        self.count = 0
        self.mvo = LogNewMvoFeedback(log)
        self.imu = LogImuAtti(log)
        if data:
            self.update(data)

    def __str__(self):
        return ('MVO: ' + str(self.mvo) +
                '|IMU: ' + str(self.imu) +
                "")

    def format_cvs(self):
        return (
            self.mvo.format_cvs() +
            ',' + self.imu.format_cvs() +
            "")

    def format_cvs_header(self):
        return (
            self.mvo.format_cvs_header() +
            ',' + self.imu.format_cvs_header() +
            "")

    def update(self, data):
        if isinstance(data, bytearray):
            data = str(data)

        self.log.debug('LogData: data length=%d' % len(data))
        self.count += 1
        pos = 0
        while (pos < len(data) - 2):
            if (struct.unpack_from('B', data, pos+0)[0] != 0x55):
                raise Exception('LogData: corrupted data at pos=%d, data=%s'
                               % (pos, byte_to_hexstring(data[pos:])))
            length = struct.unpack_from('<h', data, pos+1)[0]
            checksum = data[pos+3]
            id = struct.unpack_from('<H', data, pos+4)[0]
            # 4bytes data[6:9] is tick
            # last 2 bytes are CRC
            # length-12 is the byte length of payload
            xorval = data[pos+6]
            if isinstance(data, str):
                payload = bytearray([ord(x) ^ ord(xorval) for x in data[pos+10:pos+10+length-12]])
            else:
                payload = bytearray([x ^ xorval for x in data[pos+10:pos+10+length-12]])
            if id == self.ID_NEW_MVO_FEEDBACK:
                self.mvo.update(payload, self.count)
            elif id == self.ID_IMU_ATTI:
                self.imu.update(payload, self.count)
            else:
                if not id in self.unknowns:
                    self.log.info('LogData: UNHANDLED LOG DATA: id=%5d, length=%4d' % (id, length-12))
                    self.unknowns.append(id)

            pos += length
        if pos != len(data) - 2:
            raise Exception('LogData: corrupted data at pos=%d, data=%s'
                            % (pos, byte_to_hexstring(data[pos:])))


class LogNewMvoFeedback(object):
    def __init__(self, log = None, data = None):
        self.log = log
        self.count = 0
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.vel_z = 0.0
        self.pos_x = 0.0
        self.pos_y = 0.0
        self.pos_z = 0.0
        if (data != None):
            self.update(data, count)

    def __str__(self):
        return (
            ("VEL: %5.2f %5.2f %5.2f" % (self.vel_x, self.vel_y, self.vel_z))+
            (" POS: %5.2f %5.2f %5.2f" % (self.pos_x, self.pos_y, self.pos_z))+
            "")

    def format_cvs(self):
        return (
            ("%f,%f,%f" % (self.vel_x, self.vel_y, self.vel_z))+
            (",%f,%f,%f" % (self.pos_x, self.pos_y, self.pos_z))+
            "")

    def format_cvs_header(self):
        return (
            "mvo.vel_x,mvo.vel_y,mvo.vel_z" + 
            ",mvo.pos_x,mvo.pos_y,mvo.pos_z" +
            "")

    def update(self, data, count = 0):
        self.log.debug('LogNewMvoFeedback: length=%d %s' % (len(data), byte_to_hexstring(data)))
        self.count = count
        (self.vel_x, self.vel_y, self.vel_z) = struct.unpack_from('<hhh', data, 2)
        self.vel_x /= 100.0
        self.vel_y /= 100.0
        self.vel_z /= 100.0
        (self.pos_x, self.pos_y, self.pos_z) = struct.unpack_from('fff', data, 8)
        self.log.debug('LogNewMvoFeedback: ' + str(self))


class LogImuAtti(object):
    def __init__(self, log = None, data = None):
        self.log = log
        self.count = 0
        self.acc_x = 0.0
        self.acc_y = 0.0
        self.acc_z = 0.0
        self.gyro_x = 0.0
        self.gyro_y = 0.0
        self.gyro_z = 0.0
        self.q0 = 0.0
        self.q1 = 0.0
        self.q2 = 0.0
        self.q3 = 0.0
        self.vg_x = 0.0
        self.vg_y = 0.0
        self.vg_z = 0.0
        if (data != None):
            self.update(data)

    def __str__(self):
        return (
            ("ACC: %5.2f %5.2f %5.2f" % (self.acc_x, self.acc_y, self.acc_z)) +
            (" GYRO: %5.2f %5.2f %5.2f" % (self.gyro_x, self.gyro_y, self.gyro_z)) +
            (" QUATERNION: %5.2f %5.2f %5.2f %5.2f" % (self.q0, self.q1, self.q2, self.q3)) +
            (" VG: %5.2f %5.2f %5.2f" % (self.vg_x, self.vg_y, self.vg_z)) +
            "")

    def format_cvs(self):
        return (
            ("%f,%f,%f" % (self.acc_x, self.acc_y, self.acc_z)) +
            (",%f,%f,%f" % (self.gyro_x, self.gyro_y, self.gyro_z)) +
            (",%f,%f,%f,%f" % (self.q0, self.q1, self.q2, self.q3)) +
            (",%f,%f,%f" % (self.vg_x, self.vg_y, self.vg_z)) +
            "")

    def format_cvs_header(self):
        return (
            "imu.acc_x,imu.acc_y,imu.acc_z" +
            ",imu.gyro_x,imu.gyro_y,imu.gyro_z" +
            ",imu.q0,imu.q1,imu.q2, self.q3" +
            ",imu.vg_x,imu.vg_y,imu.vg_z" +
            "")

    def update(self, data, count = 0):
        self.log.debug('LogImuAtti: length=%d %s' % (len(data), byte_to_hexstring(data)))
        self.count = count
        (self.acc_x, self.acc_y, self.acc_z) = struct.unpack_from('fff', data, 20)
        (self.gyro_x, self.gyro_y, self.gyro_z) = struct.unpack_from('fff', data, 32)
        (self.q0, self.q1, self.q2, self.q3) = struct.unpack_from('ffff', data, 48)
        (self.vg_x, self.vg_y, self.vg_z) = struct.unpack_from('fff', data, 76)
        self.log.debug('LogImuAtti: ' + str(self))
