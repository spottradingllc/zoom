import mox
import datetime

from unittest import TestCase
from zoom.agent.predicate.pred_time import PredicateTime


class PredicateTimeTest(TestCase):

    def test_process_met_attributes_all_none(self):
        """
        Test that when all parameters are None 'met' is False
        """
        p = PredicateTime('test', {}, start=None, stop=None, weekdays=None,
                          parent=None, interval=0.1)
        p._process_met()
        self.assertEqual(p.met, False)

    def test_process_met_start(self):
        """
        Test _process_met method when setting 'start' parameter
        """
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
        # should not be 'met' if start is 1 and it is midnight
        self.assertEqual(p1.met, False)
        # should be 'met' if start is midnight it is one
        self.assertEqual(p2.met, True)

        m.VerifyAll()
        m.UnsetStubs()

    def test_process_met_stop(self):
        """
        Test _process_met method when setting 'stop' parameter
        """
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

        # should be 'met' if stop is one and it is midnight
        self.assertEqual(p1.met, True)
        # should not be 'met' if stop is midnight and it is one
        self.assertEqual(p2.met, False)

        m.VerifyAll()
        m.UnsetStubs()

    def test_process_met_weekdays(self):
        """
        Test _process_met method when setting weekdays parameter
        """
        m = mox.Mox()
        m_to_fri = '0-4'

        p1 = PredicateTime('test', {}, start=None, stop=None, weekdays=m_to_fri,
                           parent=None, interval=0.1)
        p2 = PredicateTime('test', {}, start=None, stop=None, weekdays=m_to_fri,
                           parent=None, interval=0.1)

        m.StubOutWithMock(p1, 'weekday')
        p1.weekday().AndReturn(1)  # pretend it's Tuesday
        m.StubOutWithMock(p2, 'weekday')
        p2.weekday().AndReturn(6)  # pretend it's Sunday

        m.ReplayAll()

        p1._process_met()
        p2._process_met()

        # should be 'met' if weekdays = mon-fri and it is Tuesday
        self.assertEqual(p1.met, True)
        # should not be 'met' if weekdays = mon-fri and it is Sunday
        self.assertEqual(p2.met, False)

        m.VerifyAll()
        m.UnsetStubs()

    def test_create_datetime_dict(self):
        """
        Test create_datetime_dict method creates proper dictionary
        """
        # test full date
        date_test = '1970-01-02 03:04:05'
        result = PredicateTime.create_datetime_dict(date_test)
        exp_date_dict = {'second': 5, 'hour': 3, 'year': 1970, 'day': 2,
                         'minute': 4, 'month': 1}
        self.assertEqual(exp_date_dict, result)

        # test timestamp with hours, minutes seconds
        time_test1 = '01:02:03'
        result = PredicateTime.create_datetime_dict(time_test1)
        exp_time1_dict = {'second': 3, 'hour': 1, 'year': None, 'day': None,
                          'minute': 2, 'month': None}
        self.assertEqual(exp_time1_dict, result)

        # test timestamp with hours, minutes
        time_test2 = '03:04'
        result = PredicateTime.create_datetime_dict(time_test2)
        exp_time2_dict = {'second': None, 'hour': 3, 'year': None, 'day': None,
                          'minute': 4, 'month': None}
        self.assertEqual(exp_time2_dict, result)

        # test timestamp with single-digit hour, minutes
        time_test3 = '5:06'
        result = PredicateTime.create_datetime_dict(time_test3)
        exp_time3_dict = {'second': None, 'hour': 5, 'year': None, 'day': None,
                          'minute': 6, 'month': None}
        self.assertEqual(exp_time3_dict, result)

    def test_get_datetime_object(self):
        """
        Test get_datetime_object method creates proper datetime.datetime or
        datetime.time object given the proper string
        """
        # test full date
        date_test = '1970-01-02 03:04:05'
        exp_dt_obj = datetime.datetime(1970, 1, 2, 3, 4, 5)
        result = PredicateTime.get_datetime_object(date_test)
        self.assertEqual(exp_dt_obj, result)

        # test timestamp with hours, minutes seconds
        time_test1 = '01:02:03'
        exp_tm_obj1 = datetime.time(1, 2, 3)
        result = PredicateTime.get_datetime_object(time_test1)
        self.assertEqual(exp_tm_obj1, result)

        # test timestamp with hours, minutes
        time_test2 = '03:04'
        exp_tm_obj2 = datetime.time(3, 4)
        result = PredicateTime.get_datetime_object(time_test2)
        self.assertEqual(exp_tm_obj2, result)

        # test timestamp with single-digit hour, minutes
        time_test3 = '5:06'
        exp_tm_obj3 = datetime.time(5, 6)
        result = PredicateTime.get_datetime_object(time_test3)
        self.assertEqual(exp_tm_obj3, result)

    def test_parse_range(self):
        """
        Test that the parse_range method returns the correct list of ints
        """
        # test comma-delimited
        one_three_five_str = '1,3,5'
        one_three_five_lst = [1, 3, 5]
        result = PredicateTime.parse_range(one_three_five_str)
        self.assertEqual(one_three_five_lst, result,
                         msg='Could not parse comma-delimeted str.')

        # test range
        one_to_three_str = '1-3'
        one_to_three_lst = [1, 2, 3]
        result = PredicateTime.parse_range(one_to_three_str)
        self.assertEqual(one_to_three_lst, result,
                         msg='Could not parse range str.')

        # test mix of commas and ranges
        one_three_four_to_six_str = '1,3,4-6'
        one_three_four_to_six_lst = [1, 3, 4, 5, 6]
        result = PredicateTime.parse_range(one_three_four_to_six_str)
        self.assertEqual(one_three_four_to_six_lst, result,
                         msg='Could not parse mix of comma-delimited and range str.')

        # test invalid range
        zero_to_10_str = '0-10'
        zero_to_6_lst = [0, 1, 2, 3, 4, 5, 6]
        result = PredicateTime.parse_range(zero_to_10_str)
        self.assertEqual(zero_to_6_lst, result)

        # test invalid single
        eleven_str = '11'
        empty_lst = []
        result = PredicateTime.parse_range(eleven_str)
        self.assertEqual(empty_lst, result)

    def test_equality(self):
        """
        Test object equality between two objects
        """
        p1 = PredicateTime('test', {}, start='00:00:00', stop='11:11:11',
                           weekdays='6', parent=None, interval=0.1)
        p2 = PredicateTime('test', {}, start='00:00:00', stop='11:11:11',
                           weekdays='6', parent=None, interval=0.1)

        self.assertEqual(p1, p2)

    def test_inequality(self):
        """
        Test object inequality between two objects
        """
        p1 = PredicateTime('test', {}, start='00:00:00', stop='11:11:11',
                           weekdays='6', parent=None, interval=0.1)
        p2 = PredicateTime('test', {}, start='11:11:11', stop='12:22:22',
                           weekdays=None, parent=None, interval=5.0)

        self.assertNotEquals(p1, p2)
