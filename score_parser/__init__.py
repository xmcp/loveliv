#coding=utf-8

from . import traditional, score_match, medley_festival

parsers={
    'traditional': traditional.parse_score,
    'score_match': score_match.parse_score,
    'medley_festival': medley_festival.parse_score,
}