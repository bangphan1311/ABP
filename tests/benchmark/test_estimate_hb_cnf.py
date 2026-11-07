from scripts.estimate_hb_cnf import estimate_order, estimate_pairwise

def test_pairwise_formula_matches_path4_reference():
    e=estimate_pairwise(4,3,2)
    assert e["variables_total"]==16 and e["assignment_alo_clauses"]==8
    assert e["amo_clauses"]==48 and e["distance_clauses"]==18 and e["clauses_total"]==74

def test_order_formula_matches_path4_reference():
    e=estimate_order(4,3,2)
    assert e["variables_total"]==12 and e["assignment_monotonicity_clauses"]==8
    assert e["permutation_assignment_clauses"]==24 and e["distance_clauses"]==18 and e["clauses_total"]==50

def test_can715_counts_are_reference_estimates_not_measurements():
    e=estimate_pairwise(715,2975,714)
    assert e["variables_total"]==511225 and e["distance_clauses"]==1518761300 and e["clauses_total"]==1883777380
    assert "does not allocate" in e["method"]
