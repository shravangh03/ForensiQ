def classify_artifacts(artifacts_list):
    """
    Summarizes recovered artifacts into type counts and confidence statistics.
    """
    summary = {
        'total': len(artifacts_list),
        'by_type': {},
        'high_confidence_count': 0,
        'medium_confidence_count': 0,
        'low_confidence_count': 0
    }

    for art in artifacts_list:
        ftype = art.get('file_type', 'UNKNOWN')
        summary['by_type'][ftype] = summary['by_type'].get(ftype, 0) + 1

        conf = art.get('confidence', 0)
        if conf >= 75:
            summary['high_confidence_count'] += 1
        elif conf >= 50:
            summary['medium_confidence_count'] += 1
        else:
            summary['low_confidence_count'] += 1

    return summary
