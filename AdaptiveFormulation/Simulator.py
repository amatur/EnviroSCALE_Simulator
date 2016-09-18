import heapq;
import random;
import Queue;
import json
from Lagrange import LagrangeCalculator

############################################################################
# Read from config #
############################################################################
try:
    with open("sensor_config.json", 'r') as f:
        c = json.load(f)
except IOError:
    print IOError
    print("Error reading from config file: using default configuration")
###########################################################################


class Reading:
    def __init__(self, sensor_name, sensing_time, size):
        self.sensor_name = sensor_name
        self.sensing_time = sensing_time
        self.size = size

    def __repr__(self):
        return 'Sensor::%s' % self.sensor_name


class Callable:
    def call(sim):
        raise Exception('Call of %s is not implemented' % self)


class Sensor(Callable):

    def __init__(self, name, readlatency, period, size, gamma):
        """
        Construct a new 'Sensor' object.
        :param name: The name of Sensor
        :param readlatency: read latency
        :param period: The period to read
        :param size: The size of sensor reading in bytes
        :return: returns nothing
        """
        self.name = name
        self.readlatency = readlatency
        self.period = period
        self.size = size
        self.gamma = gamma
        self.flag = False

    def __repr__(self):
        return 'Sensor::%s' % self.name

    def set_period(self, period):
        self.period = period

    def call(self, sim):
        if self.flag:
            self.flag = False
            print 'Time %f sensor %s reading completed' % (sim.simclock, self)
            sim.add_event(sim.simclock + self.period, self)
        else:
            self.flag = True
            sim.read_queue = sim.read_queue + self.size
            reading = Reading(self.name, sim.simclock, self.size)
            sim.readings_queue.put(reading)
            print 'Time %f reading sensor %s current queue %d' % (sim.simclock, self, sim.read_queue)
            sim.add_event(sim.simclock + self.readlatency, self)


class Uploader(Callable):
    def __init__(self, period, bandwidth, upload_rate, up_time, down_time):
        self.period = period
        self.bandwidth = bandwidth
        self.upload_rate = upload_rate
        self.last_uploadtime = 0
        self.last_uploaded = 0

        self.up_time = up_time
        self.down_time = down_time

        self.failed = False
        self.flag = False
        self.currently_uploading = Queue.Queue()

    def __repr__(self):
        return 'Uploader'

    def call(self, sim):
        if self.failed:

            while not self.currently_uploading.empty():
                reading = self.currently_uploading.get()
                print '-----%f delay -- failed!' % (sim.simclock - reading.sensing_time)

            return

        if self.flag:
            self.flag = False
            print 'Time %f Upload completed' % sim.simclock

            while not self.currently_uploading.empty():
                reading = self.currently_uploading.get()
                print '----- %f delay encountered' % (sim.simclock - reading.sensing_time)

            sim.add_event(sim.simclock + self.period, self)
        else:
            bytes_to_upload = max(self.upload_rate * sim.simclock - self.last_uploaded, 0)
            bytes_to_be_uploaded = 0

            while (bytes_to_be_uploaded < bytes_to_upload) and not sim.readings_queue.empty():
                reading = sim.readings_queue.get()
                self.currently_uploading.put(reading)
                bytes_to_be_uploaded = bytes_to_be_uploaded + reading.size
            bytes_to_upload = bytes_to_be_uploaded

            upload_duration = 1.0 * bytes_to_upload / self.bandwidth
            sim.read_queue = max(sim.read_queue - bytes_to_upload, 0)
            self.last_uploaded = self.last_uploaded + bytes_to_upload

            print 'Time %f Uploading %d bytes, remaining %d in queue' % (sim.simclock, bytes_to_upload, sim.read_queue)
            self.flag = True
            sim.add_event(sim.simclock + upload_duration, self)


class PeriodUpdater(Callable):
    def __init__(self, sensors, time_gap):
        self.sensors = sensors
        self.interval = time_gap

    def __repr__(self):
        return "Period updater"

    def calculate_periods(self):
        # ...compute the periods...
        rate = 0.0

        for s in self.sensors:
            rate = rate + 1.0 * s.size / s.period
        print "rate ", rate
        l = LagrangeCalculator(self.sensors, rate, c["params"]["alpha"], c["params"]["beta"], c["params"]["lambda"])
        x = l.tester()
        return x[0], x[1], x[2]
        # return 5, 5, 5

    def call(self, sim):
        i = 0
        period_tuple = self.calculate_periods()
        for p in period_tuple:
            sim.sensors[i].set_period(p)
            i = i + 1
        sim.add_event(sim.simclock + self.interval, self)


class FailureHandler(Callable):
    def __init__(self, uploader):
        self.uploader = uploader
        self.flag = False

    def call(self, sim):
        if self.flag:
            duration = random.expovariate(1.0 / self.uploader.up_time)
            self.uploader.failed = False
            self.flag = False
            print 'Time %f Uploader Up' % sim.simclock
            sim.add_event(sim.simclock, self.uploader)
            sim.add_event(sim.simclock + duration, self)
        else:
            duration = random.expovariate(1.0 / self.uploader.down_time)
            self.uploader.failed = True
            print 'Time %f Uploader down' % sim.simclock
            self.flag = True
            sim.add_event(sim.simclock + duration, self)


class Simulator:
    def __init__(self, seed):

        self.simclock = 0.0
        self.event_queue = []
        self.readings_queue = Queue.Queue()
        self.read_queue = 0
        random.seed(seed)

    def set_endtime(self, time):
        self.endtime = time


    def init_scene(self):
        self.sensors = []
        num_sensors = len(c["sensors"])
        for i in range(0, num_sensors):
            s1 = Sensor(c["sensors"][i]["name"], c["sensors"][i]["readlatency"], c["sensors"][i]["period"],
                    c["sensors"][i]["size"], c["sensors"][i]["gamma"])
            self.sensors.append(s1)


        #s1 = Sensor(c["sensors"][0]["name"], c["sensors"][0]["readlatency"], c["sensors"][0]["period"], c["sensors"][0]["size"])
        #s2 = Sensor(c["sensors"][1]["name"], c["sensors"][1]["readlatency"], c["sensors"][1]["period"], c["sensors"][1]["size"])
        #s3 = Sensor(c["sensors"][2]["name"], c["sensors"][2]["readlatency"], c["sensors"][2]["period"], c["sensors"][2]["size"])
        #self.sensors = [s1, s2, s3]

        rate = 0.0

        for s in self.sensors:
            rate = rate + 1.0 * s.size / s.period

        print 'Rate %f' % rate

        u = Uploader(5, 100, 0.99 * rate, 3600, 10)
        f = FailureHandler(u)
        #p = PeriodUpdater(1, 20)
        p = PeriodUpdater(self.sensors, 20)

        for s in self.sensors:
            self.add_event(0, s)
        self.add_event(0, u)
        self.add_event(0, f)
        self.add_event(5, p)

    def add_event(self, time, event):
        heapq.heappush(self.event_queue, (time, event))

    def run(self):
        while len(self.event_queue) > 0:
            time, event = heapq.heappop(self.event_queue)
            if time > self.endtime:
                break
            # print 'Time %f Event %s' %(time, event)

            self.simclock = time
            event.call(self)


if __name__ == '__main__':
    sim = Simulator(123)
    sim.set_endtime(1000)

    sim.init_scene()
    sim.run()

