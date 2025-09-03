from domino.aisystems._eval_tags import build_eval_result_tag

def test_build_eval_result_tags():
        assert build_eval_result_tag('my_metric', '1') ==  'domino.prog.metric.my_metric', 'numbers should be metrics'
        assert build_eval_result_tag('my_label', 'cat') ==  'domino.prog.label.my_label', 'strings should be labels'
