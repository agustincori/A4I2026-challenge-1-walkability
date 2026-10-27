from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from agent import tools


class AgentToolsTests(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        tools.set_client(self.mock_client)

    def tearDown(self):
        tools.set_client(None)

    def test_atlanta_coverage_bounds(self):
        self.assertTrue(tools.is_in_atlanta_bounds(33.749, -84.388))
        self.assertFalse(tools.is_in_atlanta_bounds(40.7128, -74.0060)) # NYC
        self.assertFalse(tools.is_in_atlanta_bounds(32.7767, -96.7970)) # Dallas
        self.assertFalse(tools.is_in_atlanta_bounds(0.0, 0.0))

    def test_predict_heat_offset_rejects_out_of_bounds_coordinates(self):
        res = tools.predict_heat_offset_and_explain(latitude=40.7128, longitude=-74.0060)
        self.assertIn("error", res)
        self.assertIn("outside the supported Atlanta coverage area", res["error"])
        self.mock_client.query.assert_not_called()

    def test_predict_heat_offset_rejects_invalid_tract_id(self):
        res = tools.predict_heat_offset_and_explain(tract_id="123")
        self.assertIn("error", res)
        self.assertIn("Invalid 11-digit", res["error"])

    def test_predict_heat_offset_queries_and_returns_attributions(self):
        mock_row = MagicMock()
        mock_row.predicted_offset_f = 3.25
        mock_row.geo_id = "13121006802"
        mock_row.total_pop = 3200
        mock_row.poverty_rate = 0.22
        mock_row.no_vehicle_rate = 0.18
        mock_row.median_age = 35.4
        mock_row.median_year_structure_built = 1968
        mock_row.top_feature_attributions = [
            {"feature": "median_year_structure_built", "attribution": 1.45},
            {"feature": "poverty_rate", "attribution": 0.85},
            {"feature": "latitude", "attribution": 0.32},
        ]

        query_res = MagicMock()
        query_res.result.return_value = [mock_row]
        self.mock_client.query.return_value = query_res

        res = tools.predict_heat_offset_and_explain(latitude=33.749, longitude=-84.388, baseline_forecast_f=100.0)

        self.assertNotIn("error", res)
        self.assertEqual(res["predicted_heat_offset_f"], 3.25)
        self.assertEqual(res["predicted_surface_temp_f"], 103.25)
        self.assertEqual(len(res["top_feature_attributions"]), 3)
        self.assertEqual(res["top_feature_attributions"][0]["feature"], "median_year_structure_built")
        self.assertEqual(res["top_feature_attributions"][0]["attribution_deg_f"], 1.45)
        # Verify SQL contains negative income handling and bounds
        sql = self.mock_client.query.call_args[0][0]
        self.assertIn("WHEN median_income >= 0 THEN median_income ELSE 65000.0", sql)
        self.assertIn("WHEN poverty_rate BETWEEN 0 AND 1 THEN poverty_rate ELSE 0.15", sql)
        self.assertIn("ML.EXPLAIN_PREDICT", sql)

    def test_rank_cooling_centers_uses_explain_predict_and_returns_attributions(self):
        mock_row = MagicMock()
        mock_row.geo_id = "13121006802"
        mock_row.tract_lat = 33.74
        mock_row.tract_lon = -84.39
        mock_row.offset_f = 4.10
        mock_row.total_pop = 2800
        mock_row.poverty_pct = 28.5
        mock_row.no_vehicle_pct = 24.2
        mock_row.median_age = 38.0
        mock_row.composite_vulnerability_score = 3.22
        mock_row.top_feature_attributions = [
            {"feature": "median_income", "attribution": 1.20},
            {"feature": "median_age", "attribution": 0.80},
        ]

        query_res = MagicMock()
        query_res.result.return_value = [mock_row]
        self.mock_client.query.return_value = query_res

        res = tools.rank_cooling_center_sites(top_n=1)

        self.assertEqual(res["count"], 1)
        site = res["ranked_sites"][0]
        self.assertEqual(site["tract_id"], "13121006802")
        self.assertEqual(len(site["top_feature_attributions"]), 2)
        self.assertEqual(site["top_feature_attributions"][0]["feature"], "median_income")
        sql = self.mock_client.query.call_args[0][0]
        self.assertIn("ML.EXPLAIN_PREDICT", sql)
        self.assertIn("WHEN median_income >= 0 THEN median_income ELSE 65000.0", sql)

    def test_audit_equity_validates_tract_ids(self):
        res = tools.audit_equity([])
        self.assertIn("error", res)
        res = tools.audit_equity(["bad_id"])
        self.assertIn("error", res)
        self.assertIn("Invalid 11-digit", res["error"])

    def test_get_tract_demographics_coverage_check(self):
        res = tools.get_tract_demographics(latitude=40.0, longitude=-75.0)
        self.assertIn("error", res)
        self.assertIn("outside the supported Atlanta coverage area", res["error"])

    def test_compare_census_tracts_includes_canopy_metric(self):
        def mock_query_side_effect(sql, job_config=None):
            mock_res = MagicMock()
            row = MagicMock()
            row.tract_lat = 33.749
            row.tract_lon = -84.388
            row.predicted_offset_f = 2.5
            row.top_feature_attributions = []
            row.geo_id = "13121006802"
            row.total_pop = 3000
            row.poverty_rate = 0.20
            row.no_vehicle_rate = 0.15
            row.median_age = 35.0
            row.median_year_structure_built = 1970
            row.tree_canopy_pct = 15.0
            mock_res.result.return_value = [row]
            return mock_res

        self.mock_client.query.side_effect = mock_query_side_effect
        res = tools.compare_census_tracts("13121006802", "13121007808")
        self.assertNotIn("error", res)
        self.assertIn("lower_tree_canopy_tract", res["comparison_metrics"])

    def test_recommend_canopy_interventions(self):
        mock_row = MagicMock()
        mock_row.tract_id = "13121006802"
        mock_row.tract_name = "Census Tract 68.02"
        mock_row.population = 3500
        mock_row.pop_density = 4200.0
        mock_row.mean_temp_f = 93.4
        mock_row.tree_canopy_pct = 12.5
        mock_row.svi_percentile = 0.88
        mock_row.integrated_risk_score = 4.15
        mock_row.poverty_pct = 32.0
        mock_row.no_vehicle_pct = 28.0

        query_res = MagicMock()
        query_res.result.return_value = [mock_row]
        self.mock_client.query.return_value = query_res

        res = tools.recommend_canopy_interventions(top_n=1)
        self.assertEqual(res["count"], 1)
        self.assertEqual(res["city_target_canopy_pct"], 50.0)
        tract = res["recommended_priority_tracts"][0]
        self.assertEqual(tract["tract_id"], "13121006802")
        self.assertEqual(tract["city_target_gap_pct"], 37.5)
        self.assertTrue(len(tract["priority_interventions"]) >= 2)
        sql = self.mock_client.query.call_args[0][0]
        self.assertIn("atlanta_canopy_heat_svi_modeling", sql)

    def test_generate_council_proposal(self):
        # Mock responses for rank_cooling_center_sites, audit_equity, and recommend_canopy_interventions
        mock_ranked_row = MagicMock()
        mock_ranked_row.geo_id = "13121006802"
        mock_ranked_row.tract_lat = 33.74
        mock_ranked_row.tract_lon = -84.39
        mock_ranked_row.offset_f = 3.5
        mock_ranked_row.total_pop = 3200
        mock_ranked_row.poverty_pct = 30.0
        mock_ranked_row.no_vehicle_pct = 25.0
        mock_ranked_row.median_age = 36.0
        mock_ranked_row.composite_vulnerability_score = 3.5
        mock_ranked_row.tree_canopy_pct = 14.0
        mock_ranked_row.top_feature_attributions = [{"feature": "median_income", "attribution": 1.2}]

        mock_audit_row = MagicMock()
        mock_audit_row.city_avg_poverty_pct = 14.2
        mock_audit_row.selected_avg_poverty_pct = 30.0
        mock_audit_row.city_p75_poverty_pct = 22.0
        mock_audit_row.city_avg_no_vehicle_pct = 9.8
        mock_audit_row.selected_avg_no_vehicle_pct = 25.0
        mock_audit_row.city_p75_no_vehicle_pct = 18.0
        mock_audit_row.total_served_pop = 3200
        mock_audit_row.audit_status = "PASSED: Recommended placements concentrate in the highest quartile."

        mock_canopy_row = MagicMock()
        mock_canopy_row.tract_id = "13121006802"
        mock_canopy_row.tract_name = "Tract 68.02"
        mock_canopy_row.population = 3200
        mock_canopy_row.pop_density = 4000.0
        mock_canopy_row.mean_temp_f = 92.5
        mock_canopy_row.tree_canopy_pct = 14.0
        mock_canopy_row.svi_percentile = 0.85
        mock_canopy_row.integrated_risk_score = 3.8
        mock_canopy_row.poverty_pct = 30.0
        mock_canopy_row.no_vehicle_pct = 25.0

        def mock_query_calls(sql, job_config=None):
            mock_res = MagicMock()
            if "composite_vulnerability_score" in sql:
                mock_res.result.return_value = [mock_ranked_row]
            elif "city_baseline" in sql:
                mock_res.result.return_value = [mock_audit_row]
            else:
                mock_res.result.return_value = [mock_canopy_row]
            return mock_res

        self.mock_client.query.side_effect = mock_query_calls
        proposal = tools.generate_council_proposal(top_n=1, baseline_forecast_f=102.0)
        self.assertNotIn("error", proposal)
        self.assertIn("proposal_markdown", proposal)
        self.assertIn("# MEMORANDUM", proposal["proposal_markdown"])
        self.assertIn("13121006802", proposal["proposal_markdown"])
        self.assertIn("Title VI & Equity Audit Verification", proposal["proposal_markdown"])


if __name__ == "__main__":
    unittest.main()

