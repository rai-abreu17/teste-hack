"""Numerical and contract checks for the offline experiments (not hardware tests)."""
import unittest
from server import geometry as g
from .estimators import estimate_tin,estimate_parametric
from .measured_zero import MeasuredZero,estimate_with_zero
from .run_comparison import PROTOCOL,capture
from .run_zero import inject
from .truth import Scene,cell_volumes,analytical_volume,clip,integral


class ExperimentTests(unittest.TestCase):
    def test_clipped_linear_surface_has_exact_integral(self):
        # Triangle z=x+y over the unit right triangle has integral 1/3.
        face = [(0,0,0),(1,0,1),(0,1,1)]
        self.assertAlmostEqual(integral(face),1/3)
        left = clip(face,0,.5,False)
        right = clip(face,0,.5,True)
        self.assertAlmostEqual(integral(left)+integral(right),1/3)
        self.assertAlmostEqual(integral(right),5/48)

    def test_truth_cells_sum_to_independent_solid_formulas(self):
        for shape in range(5):
            for center in (.131,.15,.169):
                s = Scene(shape=shape,cx=center,fill=65)
                self.assertAlmostEqual(sum(cell_volumes(s)),analytical_volume(s),places=13)

    def test_baseline_matches_production_with_occlusion(self):
        for s in [Scene(),Scene(obstacle=1),Scene(shape=4),Scene(dropout=100)]:
            raw,_ = capture(s)
            a,b = estimate_tin(raw),g.estimate(raw)
            self.assertEqual(a['heights'],b['grid']['height_m'])
            self.assertEqual(a['measurement_state'],b['measurement_state'])
            self.assertEqual(a['total_volume_m3'],b['total_volume_m3'])

    def test_roi_never_promotes_partial_to_whole_volume(self):
        raw,_ = capture(Scene())
        r = estimate_tin(raw,roi=4)
        self.assertEqual(r['measurement_state'],'partial')
        self.assertIsNone(r['total_volume_m3'])
        self.assertTrue(any(h is None for h in r['heights']))

    def test_conditional_model_recovers_an_off_center_pyramid(self):
        scene = Scene(fill=65,cx=.147)
        raw,_ = capture(scene)
        r = estimate_parametric(raw,'square_pyramid',PROTOCOL['fit_bounds'],PROTOCOL['fit_gates'])
        self.assertEqual(r['measurement_state'],'model_supported')
        self.assertLess(abs(r['model_volume_m3']/analytical_volume(scene)-1),.03)
        self.assertNotIn('total_volume_m3',r)

    def test_conditional_model_rejects_unsupported_shapes_and_empty(self):
        for scene in [Scene(shape=1),Scene(shape=2),Scene(shape=3),Scene(shape=4),Scene(fill=0)]:
            raw,_ = capture(scene)
            r = estimate_parametric(raw,'square_pyramid',PROTOCOL['fit_bounds'],PROTOCOL['fit_gates'])
            self.assertEqual(r['measurement_state'],'inconclusive')
            self.assertIsNone(r['model_volume_m3'])

    def test_shared_vertical_offset_cancels_with_measured_zero(self):
        empty,_ = capture(Scene(fill=0))
        full,_ = capture(Scene())
        nominal = estimate_with_zero(full,MeasuredZero([empty]*8))
        for offset in (-10,10):
            biased = estimate_with_zero(inject(full,'declared_pose_z',offset),
                         MeasuredZero([inject(empty,'declared_pose_z',offset)]*8))
            self.assertEqual(biased['measurement_state'],nominal['measurement_state'])
            self.assertAlmostEqual(biased['observed_volume_m3'],nominal['observed_volume_m3'],places=11)

    def test_vertical_drift_after_zero_still_changes_volume(self):
        empty,_ = capture(Scene(fill=0))
        full,_ = capture(Scene())
        zero = MeasuredZero([empty]*8)
        nominal = estimate_with_zero(full,zero)
        moved = estimate_with_zero(inject(full,'declared_pose_z',1),zero)
        self.assertAlmostEqual(moved['observed_volume_m3']-nominal['observed_volume_m3'],.09*.001,places=8)
        self.assertTrue(moved['declared_pose_changed'])

    def test_measured_reference_does_not_extrapolate_outside_its_support(self):
        empty,_ = capture(Scene(fill=0))
        full,_ = capture(Scene())
        r = estimate_with_zero(inject(full,'range',1),MeasuredZero([empty]*8))
        self.assertGreater(r['missing_reference_points'],0)
        self.assertIsNone(r['total_volume_m3'])

    def test_bad_reference_and_corrupt_packet_are_rejected(self):
        empty,_ = capture(Scene(fill=0,dropout=100))
        with self.assertRaises(ValueError):
            MeasuredZero([empty])
        raw,_ = capture(Scene())
        corrupt = bytearray(raw)
        corrupt[-1] ^= 1
        with self.assertRaises(ValueError):
            estimate_tin(corrupt)
        with self.assertRaises(ValueError):
            estimate_parametric(corrupt,'square_pyramid',PROTOCOL['fit_bounds'],PROTOCOL['fit_gates'])


if __name__ == '__main__':
    unittest.main()
