from streamlit.testing.v1 import AppTest


def test_app_default_and_direction_change():
    app = AppTest.from_file('../app.py', default_timeout=20).run()
    assert not app.exception
    assert app.metric[0].value == '3.2796'
    assert 'Reject H₀' in app.success[0].value
    app.selectbox[0].select('Below benchmark (left-tailed)').run()
    assert not app.exception
    assert any('Do not reject H₀' in v.value for v in app.info)
    assert float(app.metric[1].value) > .99


def test_app_invalid_input_blocks_stale_results():
    app = AppTest.from_file('../app.py', default_timeout=20).run()
    app.text_area[0].input('3 3 3').run()
    assert not app.exception
    assert 'zero' in app.error[0].value
    assert len(app.metric) == 0


def test_app_alpha_and_p_area_control():
    app = AppTest.from_file('../app.py', default_timeout=20).run()
    initial_p = app.metric[1].value
    app.slider[0].set_value(.001).run()
    assert not app.exception
    assert initial_p == app.metric[1].value
    assert any('Do not reject H₀' in v.value for v in app.info)
    next(v for v in app.radio if v.label == 'Shaded area').set_value('p-value area').run()
    assert not app.exception
