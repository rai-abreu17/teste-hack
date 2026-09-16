"""Check evaluator geometry and accounting independently of fused results."""
import unittest
from run_r006 import beam_blocked, in_fov, transition_edges, stats, grouped


class R006Tests(unittest.TestCase):
    def test_coplanar_diagonal_is_not_transition(self):
        a,b,c,d=(0,0,.1),(1,0,.1),(1,1,.1),(0,1,.1)
        edges=transition_edges([(a,b,c),(a,c,d)])
        self.assertEqual(len(edges),4)
        self.assertNotIn(((0,0),(1,1)),edges)

    def test_crease_is_transition(self):
        a,b,c,d=(0,0,.1),(1,0,.1),(1,1,.1),(0,1,.2)
        self.assertEqual(len(transition_edges([(a,b,c),(a,c,d)])),5)

    def test_beam_segment_stops_at_target(self):
        self.assertTrue(beam_blocked((.185,.15,.4),(.185,.15,0)))
        self.assertFalse(beam_blocked((.185,.15,.4),(.185,.15,.3)))
        self.assertFalse(beam_blocked((.1,.15,.4),(.1,.15,0)))

    def test_ideal_fov_is_not_zone_center_span(self):
        pose={'translation_m':[.15,.15,.4],'yaw_deg':0,'tilt_deg':0}
        self.assertTrue(in_fov(pose,(.15,.15,0)))
        self.assertFalse(in_fov(pose,(.15,.15,.5)))
        self.assertTrue(in_fov(pose,(.31,.15,0)))
        self.assertFalse(in_fov(pose,(.31,.15,0),.875))

    def test_volume_cancellation_not_spatial_accuracy(self):
        area=.015**2
        result=stats([.2,0],[.1*area,.1*area],[0,1])
        self.assertEqual(result['signed_error_m3'],0)
        self.assertAlmostEqual(result['spatial_error_percent'],100)
        empty=stats([0],[0],[0])
        self.assertIsNone(empty['absolute_error_percent'])
        self.assertEqual(empty['absolute_volume_error_m3'],0)

    def test_partitions_exclude_unsupported(self):
        result=grouped([.1,.2,None],[.00002,.00003,.1],[0,1],[True,False,True],[False,False,True])
        self.assertEqual(result['overall']['cell_count'],2)
        self.assertAlmostEqual(result['overall']['truth_volume_m3'],.00005)
        self.assertEqual(result['groups']['transition']['cell_count'],1)


if __name__=='__main__':
    unittest.main()
