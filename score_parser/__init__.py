#coding=utf-8

from . import traditional, score_match, score_match_legacy, medley_festival, traditional_revive

parsers={
    'traditional': traditional.parse_score,
    'traditional_rev': traditional_revive.parse_score,
    'score_match_old': score_match_legacy.parse_score,
    'score_match': score_match.parse_score,
    'medley_fes': medley_festival.parse_score,
}

statgazers={ # returns [pts, songs, LPs, items]
    'traditional': traditional.parse_tuple,
    'traditional_rev': traditional_revive.parse_tuple,
    'score_match_old': score_match_legacy.parse_tuple,
    'score_match': score_match.parse_tuple,
    'medley_fes': medley_festival.parse_tuple,
}