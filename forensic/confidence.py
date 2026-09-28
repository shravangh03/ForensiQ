def calculate_confidence_score(validation_res):
    """
    Computes a transparent rule-based confidence score (0-100%) based on validation metrics.
    Header valid    : +25
    Footer valid    : +25
    Structure valid : +25
    Renderable      : +25
    """
    score = 0
    breakdown = []

    if validation_res.get('header_valid'):
        score += 25
        breakdown.append("Valid Header (+25%)")
    else:
        breakdown.append("Missing/Invalid Header (+0%)")

    if validation_res.get('footer_valid'):
        score += 25
        breakdown.append("Valid Footer (+25%)")
    else:
        breakdown.append("Missing/Invalid Footer (+0%)")

    if validation_res.get('structure_valid'):
        score += 25
        breakdown.append("Valid Structure (+25%)")
    else:
        breakdown.append("Invalid Structure (+0%)")

    if validation_res.get('renderable'):
        score += 25
        breakdown.append("Successfully Rendered/Parsed (+25%)")
    else:
        breakdown.append("Parsing Failure (+0%)")

    return score, breakdown
