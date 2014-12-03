import mox
import time
import datetime

from unittest import TestCase
from zoom.agent.predicate.pred_time import PredicateTime


class PredicateTimeTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_start(self):
        pass

    def test_process_met_attributes_all_none(self):
        p = PredicateTime('test', {}, start=None, stop=None, weekdays=None,
                          parent=None, interval=0.1)
        p._process_met()
        self.assertEqual(p.met, False)

    def test_process_met_start(self):
        m = mox.Mox()
        midnight = '00:00:00'
        one = '01:00:00'

        p1 = PredicateTime('test', {}, start=one, stop=None, weekdays=None,
                           parent=None, interval=0.1)
        p2 = PredicateTime('test', {}, start=midnight, stop=None, weekdays=None,
                           parent=None, interval=0.1)

        mid_time = datetime.datetime.strptime(midnight, '%H:%M:%S').time()
        one_time = datetime.datetime.strptime(one, '%H:%M:%S').time()

        m.StubOutWithMock(p1, '_get_comparison')
        p1._get_comparison(p1.start_time).AndReturn(mid_time)  # pretend it's midnight
        m.StubOutWithMock(p2, '_get_comparison')
        p2._get_comparison(p2.start_time).AndReturn(one_time)  # pretend it's one

        m.ReplayAll()

        p1._process_met()
        p2._process_met()
        self.assertEqual(p1.met, False)
        self.assertEqual(p2.met, True)

        m.VerifyAll()
        m.UnsetStubs()

    def test_process_met_stop(self):
        m = mox.Mox()
        midnight = '00:00:00'
        one = '01:00:00'

        p1 = PredicateTime('test', {}, start=None, stop=one, weekdays=None,
                           parent=None, interval=0.1)
        p2 = PredicateTime('test', {}, start=None, stop=midnight, weekdays=None,
                           parent=None, interval=0.1)

        mid_time = datetime.datetime.strptime(midnight, '%H:%M:%S').time()
        one_time = datetime.datetime.strptime(one, '%H:%M:%S').time()

        m.StubOutWithMock(p1, '_get_comparison')
        p1._get_comparison(p1.stop_time).AndReturn(mid_time)  # pretend it's midnight
        m.StubOutWithMock(p2, '_get_comparison')
        p2._get_comparison(p2.stop_time).AndReturn(one_time)  # pretend it's one

        m.ReplayAll()

        p1._process_met()
        p2._process_met()
        self.assertEqual(p1.met, True)
        self.assertEqual(p2.met, False)

        m.VerifyAll()
        m.UnsetStubs()

    def test_process_met_weekdays(self):
        m = mox.Mox()
        m_to_fri = '0-4'

        p1 = PredicateTime('test', {}, start=None, stop=None, weekdays=m_to_fri,
                           parent=None, interval=0.1)
        p2 = PredicateTime('test', {}, start=None, stop=None, weekdays=m_to_fri,
                           parent=None, interval=0.1)

        m.StubOutWithMock(p1, 'weekday')
        p1.weekday().AndReturn(1)
        m.StubOutWithMock(p2, 'weekday')
        p2.weekday().AndReturn(6)

        m.ReplayAll()

        p1._process_met()
        p2._process_met()

        self.assertEqual(p1.met, True)
        self.assertEqual(p2.met, False)

        m.VerifyAll()
        m.UnsetStubs()

    def test_create_dt_dict(self):
        pass

    def test_get_comparison(self):
        pass

    def test_get_datetime_object(self):
        pass

    def test_parse_range(self):
        pass

    def test_equality(self):
        pass

    def test_inequality(self):
        pass
