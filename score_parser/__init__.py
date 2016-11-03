#coding=utf-8

from . import evt61, score_match, medley_festival

parsers={
    'evt61': evt61.parse_score,
    'score_match': score_match.parse_score,
    'medley_festival': medley_festival.parse_score,
}